import ctypes
import os
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from app.documents.parsers.base import (
    ParsedBoundingBox,
    ParsedPage,
    ParsedPdf,
    ParsedTable,
    PdfParserError,
)


def _preload_vercel_onnxruntime() -> None:
    """Load Xberg's packaged ONNX runtime when Vercel omits its sibling libs."""
    if os.getenv("VERCEL") != "1":
        return

    bundled_library = Path(__file__).resolve().parents[2] / "_native/libonnxruntime.bin"
    if bundled_library.is_file():
        ctypes.CDLL(str(bundled_library), mode=ctypes.RTLD_GLOBAL)
        return

    package_spec = find_spec("xberg")
    if package_spec is None or package_spec.origin is None:
        return

    candidates = sorted(Path(package_spec.origin).parent.glob("libonnxruntime*.so*"))
    if candidates:
        ctypes.CDLL(str(candidates[0]), mode=ctypes.RTLD_GLOBAL)


_preload_vercel_onnxruntime()

from xberg import ExtractInput, ExtractionConfig, PageConfig, PdfConfig, extract  # noqa: E402


class XbergPdfParser:
    name = "xberg"

    @property
    def version(self) -> str | None:
        try:
            return version("xberg")
        except PackageNotFoundError:
            return None

    async def parse(self, pdf_bytes: bytes, filename: str | None = None) -> ParsedPdf:
        try:
            result = await extract(
                ExtractInput(
                    kind="bytes",
                    bytes=pdf_bytes,
                    mime_type="application/pdf",
                    filename=filename,
                ),
                ExtractionConfig(
                    use_cache=False,
                    pages=PageConfig(extract_pages=True, insert_page_markers=False),
                    pdf_options=PdfConfig(
                        extract_tables=True,
                        extract_metadata=True,
                        ocr_inline_images=False,
                    ),
                ),
            )
        except Exception as error:
            raise PdfParserError("Xberg could not parse the PDF") from error

        if result.errors or len(result.results) != 1:
            raise PdfParserError("Xberg could not parse the PDF")

        try:
            document = result.results[0]
            if not document.pages:
                raise PdfParserError("Xberg did not return page-level content")

            pages = [
                ParsedPage(
                    page_number=page.page_number,
                    text=page.content,
                    tables=[self._parse_table(table) for table in page.tables],
                )
                for page in document.pages
            ]
            page_numbers = [page.page_number for page in pages]
            if len(page_numbers) != len(set(page_numbers)):
                raise PdfParserError("Xberg returned duplicate page numbers")

            pages.sort(key=lambda page: page.page_number)
            return ParsedPdf(pages=pages, metadata=self._parse_metadata(document.metadata))
        except PdfParserError:
            raise
        except Exception as error:
            raise PdfParserError("Xberg returned invalid extraction output") from error

    @staticmethod
    def _parse_table(table: Any) -> ParsedTable:
        bounding_box = None
        if table.bounding_box is not None:
            bounding_box = ParsedBoundingBox(
                x0=table.bounding_box.x0,
                y0=table.bounding_box.y0,
                x1=table.bounding_box.x1,
                y1=table.bounding_box.y1,
            )
        return ParsedTable(
            cells=table.cells,
            markdown=table.markdown,
            table_id=table.table_id,
            columns=table.columns,
            bounding_box=bounding_box,
        )

    @staticmethod
    def _parse_metadata(metadata: Any) -> dict[str, object]:
        values: dict[str, object] = {}
        for field in (
            "title",
            "subject",
            "authors",
            "keywords",
            "language",
            "created_at",
            "modified_at",
            "created_by",
            "modified_by",
            "category",
            "tags",
            "document_version",
            "abstract_text",
            "output_format",
            "ocr_used",
        ):
            value = getattr(metadata, field, None)
            if value not in (None, "", [], {}):
                values[field] = value

        format_metadata = getattr(metadata, "format", None)
        if format_metadata is not None:
            values["format"] = format_metadata.format_type

        page_structure = getattr(metadata, "pages", None)
        if page_structure is not None:
            values["page_count"] = page_structure.total_count

        additional = getattr(metadata, "additional", None)
        if additional:
            values["additional"] = additional
        return values
