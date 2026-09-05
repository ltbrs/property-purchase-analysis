"""PDF parser dependency boundary, with Xberg as the default adapter."""

from functools import lru_cache
from importlib import import_module
from typing import Annotated, cast

from fastapi import Depends

from app.documents.parsers.base import PdfParser


@lru_cache
def get_pdf_parser() -> PdfParser:
    # Keep Xberg's large native wheel outside application startup. Besides
    # avoiding work on routes that do not parse documents, this lets serverless
    # runtimes install the wheel and its adjacent shared libraries atomically.
    parser_module = import_module("app.documents.parsers.xberg_parser")
    parser_class = parser_module.XbergPdfParser
    return cast(PdfParser, parser_class())


PdfParserDependency = Annotated[PdfParser, Depends(get_pdf_parser)]
