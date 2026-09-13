from uuid import uuid4

from app.documents.llm_content import TRUNCATION_MARKER, extraction_as_numbered_text
from app.documents.models import DocumentExtractionPageRecord, DocumentExtractionRecord


def test_numbered_text_caps_each_page_while_preserving_its_start_and_end() -> None:
    extraction = DocumentExtractionRecord(
        document_id=uuid4(),
        parser_name="test",
        parser_version=None,
        duration_ms=0,
        document_metadata={},
        pages=[
            DocumentExtractionPageRecord(
                page_number=1,
                text=f"START-{'a' * 200}-END",
                tables=[],
            )
        ],
    )

    rendered = extraction_as_numbered_text(extraction, max_chars_per_page=80)
    page_content = rendered.removeprefix('<page number="1">\n').removesuffix("\n</page>")

    assert len(page_content) == 80
    assert page_content.startswith("START-")
    assert page_content.endswith("-END")
    assert TRUNCATION_MARKER.strip() in page_content


def test_numbered_text_can_select_non_contiguous_pages() -> None:
    extraction = DocumentExtractionRecord(
        document_id=uuid4(),
        parser_name="test",
        parser_version=None,
        duration_ms=0,
        document_metadata={},
        pages=[
            DocumentExtractionPageRecord(page_number=1, text="one", tables=[]),
            DocumentExtractionPageRecord(page_number=2, text="two", tables=[]),
            DocumentExtractionPageRecord(page_number=3, text="three", tables=[]),
        ],
    )

    rendered = extraction_as_numbered_text(extraction, page_numbers={1, 3})

    assert '<page number="1">' in rendered
    assert '<page number="2">' not in rendered
    assert '<page number="3">' in rendered
