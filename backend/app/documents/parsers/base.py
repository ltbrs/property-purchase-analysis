from typing import Protocol

from pydantic import BaseModel, Field


class PdfParserError(RuntimeError):
    """A PDF parser could not produce trustworthy page-level output."""


class ParsedBoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class ParsedTable(BaseModel):
    cells: list[list[str]] = Field(default_factory=list)
    markdown: str = ""
    table_id: str | None = None
    columns: list[str] | None = None
    bounding_box: ParsedBoundingBox | None = None


class ParsedPage(BaseModel):
    page_number: int = Field(gt=0)
    text: str = ""
    tables: list[ParsedTable] = Field(default_factory=list)


class ParsedPdf(BaseModel):
    pages: list[ParsedPage] = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class PdfParser(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str | None: ...

    async def parse(self, pdf_bytes: bytes, filename: str | None = None) -> ParsedPdf: ...
