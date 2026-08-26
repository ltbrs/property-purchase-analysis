import asyncio

import pytest

from app.documents.parsers.base import PdfParserError
from app.documents.parsers.xberg_parser import XbergPdfParser
from tests.pdf_fixtures import AG_MINUTES_PDF, DPE_PDF


@pytest.mark.parametrize(
    ("filename", "pdf_bytes", "expected_pages", "expected_title", "last_page_text"),
    [
        ("dpe.pdf", DPE_PDF, 2, "DPE appartement", "Montant maximum 2100 EUR"),
        ("pv-ag.pdf", AG_MINUTES_PDF, 3, "Proces-verbal AG 2025", "Signature du syndic"),
    ],
)
def test_xberg_extracts_page_boundaries_and_metadata_from_representative_pdfs(
    filename: str,
    pdf_bytes: bytes,
    expected_pages: int,
    expected_title: str,
    last_page_text: str,
) -> None:
    parsed = asyncio.run(XbergPdfParser().parse(pdf_bytes, filename=filename))

    assert [page.page_number for page in parsed.pages] == list(range(1, expected_pages + 1))
    assert last_page_text in parsed.pages[-1].text
    assert parsed.metadata["title"] == expected_title
    assert parsed.metadata["page_count"] == expected_pages


def test_xberg_exposes_detected_tables_on_their_source_page() -> None:
    parsed = asyncio.run(XbergPdfParser().parse(DPE_PDF, filename="dpe.pdf"))

    tables = [table for page in parsed.pages for table in page.tables]
    assert tables
    assert all(isinstance(table.cells, list) for table in tables)
    assert any("| Classe | energie | E |" in table.markdown for table in tables)


def test_xberg_wraps_invalid_pdf_failures() -> None:
    with pytest.raises(PdfParserError, match="Xberg could not parse"):
        asyncio.run(XbergPdfParser().parse(b"not a PDF", filename="broken.pdf"))
