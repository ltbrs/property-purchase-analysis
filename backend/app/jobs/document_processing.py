from uuid import UUID

from starlette.concurrency import run_in_threadpool

from app.documents.classification.models import (
    DocumentClassificationRecord,
    DocumentType,
)
from app.documents.classification.service import DocumentClassificationService
from app.documents.extraction.service import DocumentExtractionService
from app.documents.models import DocumentRecord
from app.documents.parsers.base import PdfParser
from app.documents.repository import DocumentRepository
from app.llm import StructuredOutputClient
from app.property.normalization.dpe_service import DpeExtractionService
from app.property.normalization.structured import StructuredExtractionType
from app.property.normalization.structured_service import (
    StructuredExtractionService,
    structured_extraction_type,
)
from app.storage.object_storage import PrivateObjectStorage

STRUCTURED_DOCUMENT_TYPES = {
    DocumentType.AG_MINUTES,
    DocumentType.COPRO_FINANCIALS,
    DocumentType.CHARGES,
    DocumentType.WORKS_CALL,
    DocumentType.DIAGNOSTICS,
    DocumentType.RISK_STATEMENT,
}


class DocumentProcessingService:
    """Run the explicit, idempotent processing stages for one uploaded PDF."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: PrivateObjectStorage,
        parser: PdfParser,
        llm_client: StructuredOutputClient,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.parser = parser
        self.llm_client = llm_client

    async def process(
        self,
        document: DocumentRecord,
        user_id: UUID,
        *,
        full_analysis: bool = True,
    ) -> list[DocumentClassificationRecord]:
        extraction = self.repository.get_extraction(document.id)
        if extraction is None:
            pdf_bytes = await run_in_threadpool(
                self.storage.download_pdf,
                document.storage_bucket,
                document.storage_key,
            )
            extraction = await DocumentExtractionService(self.repository, self.parser).extract(
                document, pdf_bytes
            )

        classifications = await DocumentClassificationService(
            self.repository, self.llm_client
        ).classify(document, extraction, user_id)

        if not full_analysis:
            return classifications

        dpe_classifications = [
            classification
            for classification in classifications
            if classification.document_type == DocumentType.DPE.value
        ]
        if dpe_classifications:
            await DpeExtractionService(self.repository, self.llm_client).extract(
                document, extraction, dpe_classifications, user_id
            )

        structured_groups: dict[StructuredExtractionType, list[DocumentClassificationRecord]] = {}
        for classification in classifications:
            document_type = DocumentType(classification.document_type)
            if document_type not in STRUCTURED_DOCUMENT_TYPES:
                continue
            extraction_type = structured_extraction_type(document_type)
            structured_groups.setdefault(extraction_type, []).append(classification)
        for grouped_classifications in structured_groups.values():
            await StructuredExtractionService(self.repository, self.llm_client).extract(
                document,
                extraction,
                grouped_classifications,
                user_id,
            )

        self.repository.mark_completed(document)

        return classifications
