from collections.abc import Collection

from app.documents.models import DocumentExtractionRecord

TRUNCATION_MARKER = "\n[contenu de page tronqué]\n"


def _crop_page_content(content: str, max_chars: int | None) -> str:
    if max_chars is None or len(content) <= max_chars:
        return content
    if max_chars <= len(TRUNCATION_MARKER):
        return content[:max_chars]
    remaining = max_chars - len(TRUNCATION_MARKER)
    head_length = (remaining * 2) // 3
    tail_length = remaining - head_length
    return f"{content[:head_length]}{TRUNCATION_MARKER}{content[-tail_length:]}"


def extraction_as_numbered_text(
    extraction: DocumentExtractionRecord,
    *,
    page_numbers: Collection[int] | None = None,
    max_chars_per_page: int | None = None,
) -> str:
    """Render persisted extraction without losing the page boundary used by citations."""

    selected_pages = set(page_numbers) if page_numbers is not None else None
    sections: list[str] = []
    for page in extraction.pages:
        if selected_pages is not None and page.page_number not in selected_pages:
            continue
        page_content = [page.text.strip()]
        for table_index, table in enumerate(page.tables, start=1):
            markdown = table.get("markdown")
            if isinstance(markdown, str) and markdown.strip():
                page_content.extend(
                    [f'<table number="{table_index}">', markdown.strip(), "</table>"]
                )
        cropped_content = _crop_page_content(
            "\n".join(page_content),
            max_chars_per_page,
        )
        sections.append(f'<page number="{page.page_number}">\n{cropped_content}\n</page>')
    return "\n\n".join(sections)


def page_source_text(
    extraction: DocumentExtractionRecord,
    *,
    page_numbers: Collection[int] | None = None,
) -> dict[int, str]:
    selected_pages = set(page_numbers) if page_numbers is not None else None
    sources: dict[int, str] = {}
    for page in extraction.pages:
        if selected_pages is not None and page.page_number not in selected_pages:
            continue
        table_text = "\n".join(
            markdown
            for table in page.tables
            if isinstance((markdown := table.get("markdown")), str)
        )
        sources[page.page_number] = f"{page.text}\n{table_text}"
    return sources
