from app.documents.classification.models import DocumentClassificationRecord, DocumentType
from app.documents.llm_content import extraction_as_numbered_text, page_source_text
from app.documents.models import DocumentExtractionRecord, DocumentRecord
from app.documents.repository import DocumentRepository
from app.llm import StructuredOutputClient
from app.property.normalization.dpe import (
    DpeExtractionCandidate,
    DpeExtractionRecord,
    normalize_dpe_candidate,
)
from app.property.normalization.dpe_prompts import (
    DPE_EXTRACTION_PROMPT_VERSION,
    DPE_EXTRACTION_SYSTEM_PROMPT,
)

DPE_EXTRACTION_FAILURE_REASON = "L’extraction structurée du DPE a échoué. Vous pouvez réessayer."


class DpeExtractionFailed(RuntimeError):
    pass


class DpeClassificationRequired(RuntimeError):
    pass


class DpeExtractionService:
    def __init__(self, repository: DocumentRepository, llm_client: StructuredOutputClient) -> None:
        self.repository = repository
        self.llm_client = llm_client

    async def extract(
        self,
        document: DocumentRecord,
        extraction: DocumentExtractionRecord,
        classification: DocumentClassificationRecord,
    ) -> DpeExtractionRecord:
        existing = self.repository.get_dpe_extraction(document.id)
        if existing is not None:
            return existing
        if classification.document_type != DocumentType.DPE.value:
            raise DpeClassificationRequired("Document is not classified as a DPE")

        self.repository.mark_analyzing(document)
        try:
            result = await self.llm_client.parse(
                system_prompt=DPE_EXTRACTION_SYSTEM_PROMPT,
                user_content=extraction_as_numbered_text(extraction),
                response_model=DpeExtractionCandidate,
            )
            facts = normalize_dpe_candidate(
                result.output,
                document_id=document.id,
                pages=page_source_text(extraction),
            )
            return self.repository.save_dpe_extraction(
                document=document,
                facts=facts,
                requested_model=result.requested_model,
                resolved_model=result.resolved_model,
                response_id=result.response_id,
                prompt_version=DPE_EXTRACTION_PROMPT_VERSION,
            )
        except Exception as error:
            self.repository.mark_analysis_failed(document, DPE_EXTRACTION_FAILURE_REASON)
            raise DpeExtractionFailed(DPE_EXTRACTION_FAILURE_REASON) from error
