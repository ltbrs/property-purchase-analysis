import logging
from time import perf_counter

from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.documents.classification.models import DocumentClassificationRecord, DocumentType
from app.documents.llm_content import extraction_as_numbered_text, page_source_text
from app.documents.models import DocumentExtractionRecord, DocumentRecord
from app.documents.repository import DocumentRepository
from app.llm import StructuredOutputClient
from app.property.normalization.dpe import (
    DpeExtractionCandidate,
    DpeExtractionRecord,
    NormalizedDpeFacts,
    normalize_dpe_candidate,
)
from app.property.normalization.dpe_ademe import (
    AdemeApiUnavailable,
    AdemeDpeLookup,
    PublicAdemeDpeClient,
    find_dpe_number,
    resolve_dpe_facts,
)
from app.property.normalization.dpe_prompts import (
    DPE_EXTRACTION_PROMPT_VERSION,
    DPE_EXTRACTION_SYSTEM_PROMPT,
)

DPE_EXTRACTION_FAILURE_REASON = "L’extraction structurée du DPE a échoué. Vous pouvez réessayer."
# Use Uvicorn's configured application logger so INFO events are visible in API logs.
logger = logging.getLogger("uvicorn.error")


class DpeExtractionFailed(RuntimeError):
    pass


class DpeClassificationRequired(RuntimeError):
    pass


class DpeExtractionService:
    def __init__(
        self,
        repository: DocumentRepository,
        llm_client: StructuredOutputClient,
        ademe_client: AdemeDpeLookup | None = None,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client
        settings = get_settings()
        self.ademe_client = ademe_client or PublicAdemeDpeClient(
            settings.ademe_dpe_api_url,
            settings.ademe_dpe_api_timeout_seconds,
        )

    async def extract(
        self,
        document: DocumentRecord,
        extraction: DocumentExtractionRecord,
        classification: DocumentClassificationRecord,
    ) -> DpeExtractionRecord:
        existing = self.repository.get_dpe_extraction(document.id)
        if existing is not None:
            existing_facts = NormalizedDpeFacts.model_validate(existing.normalized_facts)
            logger.info(
                "DPE extraction reused document_id=%s ademe_status=%s api_call=false",
                document.id,
                existing_facts.ademe_verification.status.value,
            )
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
            pages = page_source_text(extraction)
            facts = normalize_dpe_candidate(
                result.output,
                document_id=document.id,
                pages=pages,
            )
            dpe_number = find_dpe_number(pages, document_id=document.id)
            ademe_record = None
            ademe_unavailable = False
            if dpe_number.value is not None:
                lookup_started_at = perf_counter()
                logger.info(
                    "ADEME DPE lookup started document_id=%s dpe_number=%s",
                    document.id,
                    dpe_number.value,
                )
                try:
                    ademe_record = await run_in_threadpool(
                        self.ademe_client.lookup, dpe_number.value
                    )
                    logger.info(
                        "ADEME DPE lookup completed document_id=%s status=%s duration_ms=%d",
                        document.id,
                        "found" if ademe_record is not None else "not_found",
                        round((perf_counter() - lookup_started_at) * 1000),
                    )
                except AdemeApiUnavailable as error:
                    ademe_unavailable = True
                    logger.warning(
                        "ADEME DPE lookup failed document_id=%s error_type=%s duration_ms=%d",
                        document.id,
                        type(error.__cause__ or error).__name__,
                        round((perf_counter() - lookup_started_at) * 1000),
                    )
            else:
                logger.info(
                    "ADEME DPE lookup skipped document_id=%s reason=dpe_number_not_found",
                    document.id,
                )
            facts = resolve_dpe_facts(
                facts,
                dpe_number=dpe_number,
                ademe_record=ademe_record,
                ademe_unavailable=ademe_unavailable,
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
