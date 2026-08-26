from app.documents.models import DocumentExtractionRecord


def extraction_as_numbered_text(extraction: DocumentExtractionRecord) -> str:
    """Render persisted extraction without losing the page boundary used by citations."""

    sections: list[str] = []
    for page in extraction.pages:
        content = [f'<page number="{page.page_number}">', page.text.strip()]
        for table_index, table in enumerate(page.tables, start=1):
            markdown = table.get("markdown")
            if isinstance(markdown, str) and markdown.strip():
                content.extend([f'<table number="{table_index}">', markdown.strip(), "</table>"])
        content.append("</page>")
        sections.append("\n".join(content))
    return "\n\n".join(sections)


def page_source_text(extraction: DocumentExtractionRecord) -> dict[int, str]:
    sources: dict[int, str] = {}
    for page in extraction.pages:
        table_text = "\n".join(
            markdown
            for table in page.tables
            if isinstance((markdown := table.get("markdown")), str)
        )
        sources[page.page_number] = f"{page.text}\n{table_text}"
    return sources
