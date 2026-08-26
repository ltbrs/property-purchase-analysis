"""PDF parser dependency boundary, with Xberg as the default adapter."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.documents.parsers.base import PdfParser
from app.documents.parsers.xberg_parser import XbergPdfParser


@lru_cache
def get_pdf_parser() -> XbergPdfParser:
    return XbergPdfParser()


PdfParserDependency = Annotated[PdfParser, Depends(get_pdf_parser)]
