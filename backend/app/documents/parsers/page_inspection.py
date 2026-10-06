"""Inspect poor Xberg pages locally. Render only candidates, with bounded memory."""

from __future__ import annotations

from contextlib import closing
from io import BytesIO
from threading import Lock
from typing import TYPE_CHECKING, cast

from PIL import Image

if TYPE_CHECKING:
    import pypdfium2 as pdfium

from app.documents.parsers.base import ParsedPage, ParsedPdf, PdfParserError

# PDFium is not thread safe, including across different PDF documents.
PDFIUM_LOCK = Lock()
MIN_TEXT_CHARACTERS = 40
MAX_DOCUMENT_PAGES = 2000
UNREAD_STATUSES = {"unreadable", "partial", "failed", "limit_exceeded"}
PENDING_STATUSES = {"pending", "retry"}


def usable_characters(page: ParsedPage) -> int:
    content = page.text + " ".join(
        table.markdown + " ".join(cell for row in table.cells for cell in row)
        for table in page.tables
    )
    # A broken text layer full of replacement characters is not usable text.
    return sum(character.isalnum() for character in content)


def _render(page: pdfium.PdfPage, longest_side: int) -> Image.Image:
    width, height = page.get_size()
    if width <= 0 or height <= 0:
        raise PdfParserError("Invalid PDF page dimensions")
    bitmap = page.render(scale=min(longest_side / max(width, height), 3))
    try:
        return cast(Image.Image, bitmap.to_pil().convert("RGB"))
    finally:
        bitmap.close()


def inspect_pages(pdf_bytes: bytes, parsed: ParsedPdf, max_fallback_pages: int) -> ParsedPdf:
    """Reconcile true page numbers and discard visually empty poor-text pages."""
    import pypdfium2 as pdfium
    from PIL import Image, ImageChops

    with PDFIUM_LOCK, pdfium.PdfDocument(pdf_bytes) as pdf:
        page_count = len(pdf)
        if not 1 <= page_count <= MAX_DOCUMENT_PAGES:
            raise PdfParserError("PDF page count exceeds the processing limit")
        by_number = {page.page_number: page for page in parsed.pages}
        if len(by_number) != len(parsed.pages) or any(n > page_count for n in by_number):
            raise PdfParserError("Parser page numbers do not match the PDF")
        candidates = 0
        pages: list[ParsedPage] = []
        for number in range(1, page_count + 1):
            extracted = by_number.get(number, ParsedPage(page_number=number))
            characters = usable_characters(extracted)
            poor_text = characters < MIN_TEXT_CHARACTERS
            if not poor_text and characters < 200:
                with closing(pdf[number - 1]) as page:
                    # A scan may retain a small digital footer or page number.
                    area = max(1, page.get_width() * page.get_height())
                    for image in page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_IMAGE]):
                        left, bottom, right, top = image.get_bounds()
                        if abs((right - left) * (top - bottom)) / area > 0.5:
                            poor_text = True
                            break
            if not poor_text:
                pages.append(extracted)
                continue
            with closing(pdf[number - 1]) as page:
                preview = _render(page, 768)
                assert isinstance(preview, Image.Image)
                gray = preview.convert("L")
                # Compare with background estimated from the corners, so gray scan
                # backgrounds are not mistaken for text. Sparse ink is still kept.
                background = sorted(
                    [
                        cast(int, gray.getpixel((0, 0))),
                        cast(int, gray.getpixel((gray.width - 1, 0))),
                        cast(int, gray.getpixel((0, gray.height - 1))),
                        cast(int, gray.getpixel((gray.width - 1, gray.height - 1))),
                    ]
                )[2]
                difference = ImageChops.difference(gray, Image.new("L", gray.size, background))
                histogram = difference.histogram()
                ink_pixels = sum(histogram[25:])
                blank = ink_pixels < max(12, gray.width * gray.height * 0.00003)
            if blank and usable_characters(extracted) == 0:
                extracted.read_status = "blank"
            else:
                candidates += 1
                extracted.read_status = (
                    "pending" if candidates <= max_fallback_pages else "limit_exceeded"
                )
            pages.append(extracted)
        return ParsedPdf(
            pages=pages,
            metadata={**parsed.metadata, "page_count": page_count, "scan_inspection_version": 1},
        )


def render_page_image(pdf_bytes: bytes, page_number: int) -> bytes:
    """Render one page, never the entire document, and never persist the image."""
    import pypdfium2 as pdfium

    with PDFIUM_LOCK, pdfium.PdfDocument(pdf_bytes) as pdf:
        with closing(pdf[page_number - 1]) as page:
            rendered = _render(page, 2048)
            assert isinstance(rendered, Image.Image)
    # PNG encoding does not use PDFium and can run concurrently with another render.
    output = BytesIO()
    rendered.save(output, format="PNG", optimize=False)
    return output.getvalue()
