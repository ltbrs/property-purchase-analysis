from app.documents.classification.models import (
    DocumentClassificationCandidate,
    DocumentClassificationRecord,
    DocumentType,
    ExtractionStrategy,
)
from app.documents.classification.prompts import (
    CLASSIFICATION_PROMPT_VERSION,
    CLASSIFICATION_SYSTEM_PROMPT,
)
from app.documents.llm_content import extraction_as_numbered_text
from app.documents.models import DocumentExtractionRecord, DocumentRecord
from app.documents.repository import DocumentRepository
from app.llm import StructuredOutputClient

MIN_KNOWN_TYPE_CONFIDENCE = 0.70
CLASSIFICATION_FAILURE_REASON = "La classification du document a échoué. Vous pouvez réessayer."


class DocumentClassificationFailed(RuntimeError):
    pass


class DocumentClassificationService:
    def __init__(self, repository: DocumentRepository, llm_client: StructuredOutputClient) -> None:
        self.repository = repository
        self.llm_client = llm_client

    async def classify(
        self,
        document: DocumentRecord,
        extraction: DocumentExtractionRecord,
    ) -> DocumentClassificationRecord:
        existing = self.repository.get_classification(document.id)
        if existing is not None:
            return existing

        self.repository.mark_analyzing(document)
        try:
            result = await self.llm_client.parse(
                system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
                user_content=extraction_as_numbered_text(extraction),
                response_model=DocumentClassificationCandidate,
            )
            candidate = result.output
            document_type = candidate.document_type
            strategy = candidate.extraction_strategy
            if candidate.confidence < MIN_KNOWN_TYPE_CONFIDENCE:
                document_type = DocumentType.UNKNOWN
                strategy = ExtractionStrategy.NONE
            elif document_type == DocumentType.UNKNOWN:
                strategy = ExtractionStrategy.NONE

            return self.repository.save_classification(
                document=document,
                candidate=candidate,
                normalized_document_type=document_type,
                normalized_strategy=strategy,
                requested_model=result.requested_model,
                resolved_model=result.resolved_model,
                response_id=result.response_id,
                prompt_version=CLASSIFICATION_PROMPT_VERSION,
            )
        except Exception as error:
            self.repository.mark_analysis_failed(document, CLASSIFICATION_FAILURE_REASON)
            raise DocumentClassificationFailed(CLASSIFICATION_FAILURE_REASON) from error
