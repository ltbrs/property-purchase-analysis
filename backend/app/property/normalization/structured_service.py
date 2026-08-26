from app.documents.classification.models import DocumentClassificationRecord, DocumentType
from app.documents.llm_content import extraction_as_numbered_text, page_source_text
from app.documents.models import DocumentExtractionRecord, DocumentRecord
from app.documents.repository import DocumentRepository
from app.llm import StructuredOutputClient
from app.property.normalization.ag_minutes import (
    AgMinutesExtractionCandidate,
    normalize_ag_minutes_candidate,
)
from app.property.normalization.ag_prompts import (
    AG_EXTRACTION_PROMPT_VERSION,
    AG_EXTRACTION_SYSTEM_PROMPT,
)
from app.property.normalization.diagnostic_prompts import (
    DIAGNOSTIC_EXTRACTION_PROMPT_VERSION,
    DIAGNOSTIC_EXTRACTION_SYSTEM_PROMPT,
)
from app.property.normalization.diagnostics import (
    DiagnosticExtractionCandidate,
    normalize_diagnostics_candidate,
)
from app.property.normalization.financial_prompts import (
    FINANCIAL_EXTRACTION_PROMPT_VERSION,
    FINANCIAL_EXTRACTION_SYSTEM_PROMPT,
)
from app.property.normalization.financials import (
    FinancialExtractionCandidate,
    normalize_financial_candidate,
)
from app.property.normalization.structured import (
    StructuredExtractionRecord,
    StructuredExtractionType,
)

STRUCTURED_EXTRACTION_FAILURE_REASON = (
    "L’extraction structurée du document a échoué. Vous pouvez réessayer."
)


class StructuredExtractionFailed(RuntimeError):
    pass


class UnsupportedStructuredDocument(RuntimeError):
    pass


class StructuredExtractionService:
    def __init__(self, repository: DocumentRepository, llm_client: StructuredOutputClient) -> None:
        self.repository = repository
        self.llm_client = llm_client

    async def extract(
        self,
        document: DocumentRecord,
        extraction: DocumentExtractionRecord,
        classification: DocumentClassificationRecord,
    ) -> StructuredExtractionRecord:
        document_type = DocumentType(classification.document_type)
        if document_type == DocumentType.AG_MINUTES:
            extraction_type = StructuredExtractionType.AG_MINUTES
        elif document_type in {
            DocumentType.COPRO_FINANCIALS,
            DocumentType.CHARGES,
            DocumentType.WORKS_CALL,
        }:
            extraction_type = StructuredExtractionType.FINANCIALS
        elif document_type in {DocumentType.DIAGNOSTICS, DocumentType.RISK_STATEMENT}:
            extraction_type = StructuredExtractionType.DIAGNOSTICS
        else:
            raise UnsupportedStructuredDocument(
                f"No structured extractor is available for {document_type.value}"
            )

        existing = self.repository.get_structured_extraction(document.id, extraction_type)
        if existing is not None:
            return existing
        self.repository.mark_analyzing(document)
        content = extraction_as_numbered_text(extraction)
        pages = page_source_text(extraction)
        try:
            if extraction_type == StructuredExtractionType.AG_MINUTES:
                ag_result = await self.llm_client.parse(
                    system_prompt=AG_EXTRACTION_SYSTEM_PROMPT,
                    user_content=content,
                    response_model=AgMinutesExtractionCandidate,
                )
                facts = normalize_ag_minutes_candidate(
                    ag_result.output, document_id=document.id, pages=pages
                )
                return self.repository.save_structured_extraction(
                    document=document,
                    extraction_type=extraction_type,
                    normalized_facts=facts,
                    requested_model=ag_result.requested_model,
                    resolved_model=ag_result.resolved_model,
                    response_id=ag_result.response_id,
                    prompt_version=AG_EXTRACTION_PROMPT_VERSION,
                )
            elif extraction_type == StructuredExtractionType.FINANCIALS:
                financial_result = await self.llm_client.parse(
                    system_prompt=FINANCIAL_EXTRACTION_SYSTEM_PROMPT,
                    user_content=content,
                    response_model=FinancialExtractionCandidate,
                )
                financial_facts = normalize_financial_candidate(
                    financial_result.output, document_id=document.id, pages=pages
                )
                return self.repository.save_structured_extraction(
                    document=document,
                    extraction_type=extraction_type,
                    normalized_facts=financial_facts,
                    requested_model=financial_result.requested_model,
                    resolved_model=financial_result.resolved_model,
                    response_id=financial_result.response_id,
                    prompt_version=FINANCIAL_EXTRACTION_PROMPT_VERSION,
                )
            else:
                diagnostic_result = await self.llm_client.parse(
                    system_prompt=DIAGNOSTIC_EXTRACTION_SYSTEM_PROMPT,
                    user_content=content,
                    response_model=DiagnosticExtractionCandidate,
                )
                diagnostic_facts = normalize_diagnostics_candidate(
                    diagnostic_result.output, document_id=document.id, pages=pages
                )
                return self.repository.save_structured_extraction(
                    document=document,
                    extraction_type=extraction_type,
                    normalized_facts=diagnostic_facts,
                    requested_model=diagnostic_result.requested_model,
                    resolved_model=diagnostic_result.resolved_model,
                    response_id=diagnostic_result.response_id,
                    prompt_version=DIAGNOSTIC_EXTRACTION_PROMPT_VERSION,
                )
        except Exception as error:
            self.repository.mark_analysis_failed(document, STRUCTURED_EXTRACTION_FAILURE_REASON)
            raise StructuredExtractionFailed(STRUCTURED_EXTRACTION_FAILURE_REASON) from error
