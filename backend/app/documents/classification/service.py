from uuid import UUID
from xml.sax.saxutils import quoteattr

from app.documents.classification.models import (
    DocumentClassificationCandidate,
    DocumentClassificationRecord,
    DocumentClassificationSegmentCandidate,
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
MAX_CLASSIFICATION_CHARS_PER_PAGE = 2_000
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
        user_id: UUID,
    ) -> list[DocumentClassificationRecord]:
        existing = self.repository.list_document_classifications(document.id)
        if existing:
            return existing

        self.repository.mark_analyzing(document)
        try:
            classification_text = extraction_as_numbered_text(
                extraction,
                max_chars_per_page=MAX_CLASSIFICATION_CHARS_PER_PAGE,
            )
            result = await self.llm_client.parse(
                system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
                user_content=(
                    f"<document filename={quoteattr(document.original_filename)}>\n"
                    f"{classification_text}\n"
                    "</document>"
                ),
                response_model=DocumentClassificationCandidate,
                user_id=user_id,
                document_id=document.id,
            )
            segments = self._validated_segments(result.output, extraction)
            normalized_segments: list[
                tuple[
                    DocumentClassificationSegmentCandidate,
                    DocumentType,
                    ExtractionStrategy | None,
                ]
            ] = []
            for segment in segments:
                document_type = segment.document_type
                strategy = segment.extraction_strategy
                if segment.confidence < MIN_KNOWN_TYPE_CONFIDENCE:
                    document_type = DocumentType.UNKNOWN
                    strategy = ExtractionStrategy.NONE
                elif document_type == DocumentType.UNKNOWN:
                    strategy = ExtractionStrategy.NONE
                normalized_segments.append((segment, document_type, strategy))

            return self.repository.save_classifications(
                document=document,
                segments=normalized_segments,
                requested_model=result.requested_model,
                resolved_model=result.resolved_model,
                response_id=result.response_id,
                prompt_version=CLASSIFICATION_PROMPT_VERSION,
            )
        except Exception as error:
            self.repository.mark_analysis_failed(document, CLASSIFICATION_FAILURE_REASON)
            raise DocumentClassificationFailed(CLASSIFICATION_FAILURE_REASON) from error

    @staticmethod
    def _validated_segments(
        candidate: DocumentClassificationCandidate,
        extraction: DocumentExtractionRecord,
    ) -> list[DocumentClassificationSegmentCandidate]:
        segments = sorted(candidate.segments, key=lambda item: (item.start_page, item.end_page))
        available_pages = {page.page_number for page in extraction.pages}
        covered_pages: set[int] = set()
        for segment in segments:
            segment_pages = set(range(segment.start_page, segment.end_page + 1))
            if not segment_pages <= available_pages:
                raise ValueError("classification segment references an unavailable page")
            if covered_pages & segment_pages:
                raise ValueError("classification segments overlap")
            covered_pages.update(segment_pages)
        if covered_pages != available_pages:
            raise ValueError("classification segments must cover every extracted page")
        return segments
