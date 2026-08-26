from time import perf_counter

from app.documents.models import DocumentExtractionRecord, DocumentRecord
from app.documents.parsers.base import PdfParser, PdfParserError
from app.documents.repository import DocumentRepository

EXTRACTION_FAILURE_REASON = "L’extraction du PDF a échoué. Vous pouvez réessayer."


class DocumentExtractionFailed(RuntimeError):
    pass


class DocumentExtractionService:
    def __init__(self, repository: DocumentRepository, parser: PdfParser) -> None:
        self.repository = repository
        self.parser = parser

    async def extract(self, document: DocumentRecord, pdf_bytes: bytes) -> DocumentExtractionRecord:
        existing = self.repository.get_extraction(document.id)
        if existing is not None:
            return existing

        self.repository.mark_extracting(document)
        started_at = perf_counter()
        try:
            parsed = await self.parser.parse(pdf_bytes, filename=document.original_filename)
            duration_ms = max(0, round((perf_counter() - started_at) * 1000))
            return self.repository.save_extraction(
                document=document,
                parsed=parsed,
                parser_name=self.parser.name,
                parser_version=self.parser.version,
                duration_ms=duration_ms,
            )
        except PdfParserError as error:
            self.repository.mark_extraction_failed(document, EXTRACTION_FAILURE_REASON)
            raise DocumentExtractionFailed(EXTRACTION_FAILURE_REASON) from error
        except Exception:
            self.repository.mark_extraction_failed(document, EXTRACTION_FAILURE_REASON)
            raise
