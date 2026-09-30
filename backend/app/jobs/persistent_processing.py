"""Small durable worker: lease a document, checkpoint pages and each analysis stage."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, or_, select, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.documents.classification.models import DocumentClassificationRecord, DocumentType
from app.documents.classification.service import DocumentClassificationService
from app.documents.models import (
    DocumentExtractionPageRecord,
    DocumentExtractionRecord,
    DocumentRecord,
    DocumentStatus,
)
from app.documents.parsers.base import ParsedPage, ParsedPdf, ParsedTable, PdfParser
from app.documents.parsers.page_inspection import (
    PENDING_STATUSES,
    UNREAD_STATUSES,
    inspect_pages,
    render_page_image,
)
from app.documents.parsers.vision import transcribe_page
from app.documents.repository import DocumentRepository
from app.jobs.document_processing import STRUCTURED_DOCUMENT_TYPES
from app.llm.rate_budget import (
    BudgetedStructuredClient,
    DeferredLLMCall,
    LLMRateBudget,
    retry_at_for,
    retryable_error,
    utc,
)
from app.llm.structured_output import OPENAI_MODEL
from app.property.normalization.dpe import DpeExtractionRecord
from app.property.normalization.dpe_service import DpeExtractionService
from app.property.normalization.structured import StructuredExtractionRecord
from app.property.normalization.structured_service import (
    StructuredExtractionService,
    structured_extraction_type,
)
from app.reports.models import ReportRecord
from app.storage.object_storage import PrivateObjectStorage

ACTIVE_STAGES = ("queued", "xberg", "vision", "classification", "structured")
logger = logging.getLogger(__name__)
# Background tasks from simultaneous uploads share a process. Running several
# native PDF parses at once exhausts the batch deadline and repeats the work.
_local_worker_lock = asyncio.Lock()


def enqueue_document(session: Session, document: DocumentRecord) -> bool:
    """Atomic idempotent enqueue. Repeated clicks never restart active work."""
    if document.status == DocumentStatus.COMPLETED.value:
        return False
    result = session.scalar(
        update(DocumentRecord)
        .where(
            DocumentRecord.id == document.id,
            or_(
                DocumentRecord.processing_stage.is_(None),
                DocumentRecord.processing_stage == "failed",
            ),
        )
        .values(
            processing_stage="queued",
            next_attempt_at=datetime.now(UTC),
            processing_attempts=0,
            status="extracting",
            failure_reason=None,
            processing_progress={**document.processing_progress, "retry_reason": None},
            lease_token=None,
            lease_until=None,
        )
        .returning(DocumentRecord.id)
    )
    session.commit()
    session.refresh(document)
    return result is not None


def claim_document(
    session: Session,
    settings: Settings,
    document_id: UUID | None = None,
) -> DocumentRecord | None:
    now = datetime.now(UTC)
    due = (
        DocumentRecord.processing_stage.in_(ACTIVE_STAGES),
        or_(DocumentRecord.next_attempt_at.is_(None), DocumentRecord.next_attempt_at <= now),
        or_(DocumentRecord.lease_until.is_(None), DocumentRecord.lease_until <= now),
    )
    statement = select(DocumentRecord.id).where(*due)
    if document_id is not None:
        statement = statement.where(DocumentRecord.id == document_id)
    selected = session.scalar(
        statement.order_by(DocumentRecord.next_attempt_at, DocumentRecord.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if selected is None:
        session.commit()
        return None
    token = uuid4()
    claimed = session.scalar(
        update(DocumentRecord)
        .where(DocumentRecord.id == selected, *due)
        .values(
            lease_token=token,
            lease_until=now + timedelta(seconds=settings.processing_lease_seconds),
        )
        .returning(DocumentRecord)
        .execution_options(populate_existing=True, synchronize_session="fetch")
    )
    session.commit()
    return claimed


class LostLease(RuntimeError):
    pass


class BatchDeadlineExceeded(RuntimeError):
    pass


class PersistentDocumentWorker:
    def __init__(
        self,
        session: Session,
        storage: PrivateObjectStorage,
        parser: PdfParser,
        client: Any,
        settings: Settings,
    ) -> None:
        self.session = session
        self.repository = DocumentRepository(session)
        self.storage = storage
        self.parser = parser
        self.settings = settings
        self.client = client
        self.budget = LLMRateBudget(session, settings, OPENAI_MODEL)
        self.text_client = BudgetedStructuredClient(client, self.budget)
        self.pdf_bytes: bytes | None = None

    def guard(self, document: DocumentRecord, token: UUID | None) -> None:
        owned = self.session.scalar(
            select(DocumentRecord.id)
            .where(
                DocumentRecord.id == document.id,
                DocumentRecord.lease_token == token,
                DocumentRecord.lease_until > datetime.now(UTC),
            )
            .with_for_update()
        )
        if owned is None:
            self.session.rollback()
            raise LostLease("Document deleted or processing lease expired")

    def stage(self, document: DocumentRecord, stage: str) -> None:
        document.processing_stage = stage
        document.processing_attempts = 0
        document.next_attempt_at = datetime.now(UTC) if stage in ACTIVE_STAGES else None
        document.processing_progress = {**document.processing_progress, "retry_reason": None}
        self.session.commit()

    async def download(self, document: DocumentRecord) -> bytes:
        if self.pdf_bytes is None:
            self.pdf_bytes = await run_in_threadpool(
                self.storage.download_pdf,
                document.storage_bucket,
                document.storage_key,
            )
        return self.pdf_bytes

    def progress(self, document: DocumentRecord, extraction: DocumentExtractionRecord) -> None:
        pages = extraction.pages
        document.processing_progress = {
            "total_pages": len(pages),
            "processed_pages": sum(p.read_status not in PENDING_STATUSES for p in pages),
            "fallback_pages": sum(
                p.read_status in PENDING_STATUSES
                or p.extraction_method == "vision"
                or p.read_status == "limit_exceeded"
                for p in pages
            ),
            "fallback_completed": sum(
                p.extraction_method == "vision" and p.read_status not in PENDING_STATUSES
                for p in pages
            ),
            "unread_pages": [p.page_number for p in pages if p.read_status in UNREAD_STATUSES],
            "retry_reason": None,
        }
        self.session.commit()

    async def inspect_legacy_extraction(
        self,
        document: DocumentRecord,
        extraction: DocumentExtractionRecord,
        token: UUID | None,
    ) -> None:
        if extraction.document_metadata.get("scan_inspection_version") == 1:
            return
        pdf_bytes = await self.download(document)
        parsed = ParsedPdf(
            pages=[
                ParsedPage(
                    page_number=p.page_number,
                    text=p.text,
                    tables=[ParsedTable.model_validate(table) for table in p.tables],
                )
                for p in extraction.pages
            ],
            metadata=extraction.document_metadata,
        )
        inspected = await run_in_threadpool(
            inspect_pages, pdf_bytes, parsed, self.settings.vision_max_pages
        )
        self.guard(document, token)
        existing = {page.page_number: page for page in extraction.pages}
        for page in inspected.pages:
            if page.page_number not in existing:
                extraction.pages.append(
                    DocumentExtractionPageRecord(
                        page_number=page.page_number,
                        text=page.text,
                        tables=[table.model_dump(mode="json") for table in page.tables],
                        extraction_method="xberg",
                        read_status=page.read_status,
                    )
                )
            else:
                existing[page.page_number].read_status = page.read_status
        extraction.pages.sort(key=lambda page: page.page_number)
        extraction.document_metadata = inspected.metadata
        if any(page.read_status in PENDING_STATUSES | UNREAD_STATUSES for page in inspected.pages):
            # Old analyses based on omitted scan text must not mask newly recovered facts.
            for model in (
                DocumentClassificationRecord,
                DpeExtractionRecord,
                StructuredExtractionRecord,
            ):
                self.session.execute(delete(model).where(model.document_id == document.id))
            self.session.execute(
                delete(ReportRecord).where(
                    ReportRecord.analysis_case_id == document.analysis_case_id
                )
            )
        self.session.commit()

    async def vision_batch(
        self,
        document: DocumentRecord,
        extraction: DocumentExtractionRecord,
        token: UUID | None,
    ) -> None:
        user_id = document.analysis_case.user_id
        if user_id is None:
            raise ValueError("Processing requires an owned analysis case")
        now = datetime.now(UTC)
        pending = [p for p in extraction.pages if p.read_status in PENDING_STATUSES]
        for page in pending:
            if page.attempts >= self.settings.vision_max_attempts:
                page.read_status = "failed"
                page.extraction_method = "vision"
        self.session.commit()
        ready = [
            p
            for p in pending
            if p.read_status in PENDING_STATUSES
            and (p.next_attempt_at is None or utc(p.next_attempt_at) <= now)
        ][: self.settings.vision_batch_pages]
        if ready:
            pdf_bytes = await self.download(document)

            async def read_page(page: Any) -> None:
                try:
                    image_bytes = await run_in_threadpool(
                        render_page_image, pdf_bytes, page.page_number
                    )

                    def admitted() -> None:
                        self.guard(document, token)
                        page.attempts += 1
                        page.extraction_method = "vision"
                        self.session.commit()

                    result = await self.budget.call(
                        lambda: transcribe_page(
                            self.client,
                            image_bytes=image_bytes,
                            page_number=page.page_number,
                            user_id=user_id,
                            document_id=document.id,
                        ),
                        tokens=24000,
                        on_admitted=admitted,
                    )
                    self.guard(document, token)
                    output = result.output
                    if output.content_kind == "text":
                        page.text = output.text
                        page.tables = []  # Full-page transcription already contains visible tables.
                        page.read_status = "partial" if output.has_unreadable_regions else "read"
                    elif output.content_kind == "no_text":
                        # Keep any short, confirmed Xberg text if vision misses it.
                        page.read_status = "read" if page.text.strip() or page.tables else "no_text"
                    else:
                        if output.text.strip():
                            page.text = output.text
                            page.tables = []
                        page.read_status = "unreadable"
                    page.next_attempt_at = None
                    page.vision_metadata = {
                        "response_id": result.response_id,
                        "model": result.resolved_model,
                        "input_tokens": result.input_tokens,
                        "output_tokens": result.output_tokens,
                        "content_kind": output.content_kind,
                        "prompt_version": "vision-ocr-v1",
                    }
                    self.session.commit()
                except LostLease:
                    raise
                except Exception as error:
                    self.guard(document, token)
                    retryable = retryable_error(error)
                    if retryable is not None:
                        if page.attempts >= self.settings.vision_max_attempts:
                            page.read_status = "failed"
                        else:
                            page.read_status = "retry"
                            page.next_attempt_at = retry_at_for(
                                retryable, page.attempts, datetime.now(UTC)
                            )
                    elif isinstance(error, Exception):
                        # Authentication, quota and permission errors affect all pages.
                        from openai import APIStatusError

                        if isinstance(error, APIStatusError) and error.status_code in {
                            401,
                            403,
                            429,
                        }:
                            raise
                        page.read_status = "failed"
                        page.extraction_method = "vision"
                    self.session.commit()

            tasks = [asyncio.create_task(read_page(page)) for page in ready]
            try:
                await asyncio.gather(*tasks)
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        self.guard(document, token)
        self.progress(document, extraction)
        remaining = [p for p in extraction.pages if p.read_status in PENDING_STATUSES]
        if remaining:
            document.next_attempt_at = min(
                utc(p.next_attempt_at) if p.next_attempt_at else now for p in remaining
            )
            if document.next_attempt_at > datetime.now(UTC):
                document.processing_progress = {
                    **document.processing_progress,
                    "retry_reason": "rate_limit",
                }
            self.session.commit()
        else:
            self.stage(document, "classification")

    async def step(self, document: DocumentRecord, token: UUID | None) -> None:
        user_id = document.analysis_case.user_id
        if user_id is None:
            raise ValueError("Processing requires an owned analysis case")
        self.guard(document, token)
        self.session.commit()
        extraction = self.repository.get_extraction(document.id)
        if document.processing_stage in {"queued", "xberg"}:
            if extraction is None:
                self.stage(document, "xberg")
                started = perf_counter()
                pdf_bytes = await self.download(document)
                parsed = await self.parser.parse(pdf_bytes, filename=document.original_filename)
                parsed = await run_in_threadpool(
                    inspect_pages, pdf_bytes, parsed, self.settings.vision_max_pages
                )
                self.guard(document, token)
                extraction = self.repository.save_extraction(
                    document,
                    parsed,
                    self.parser.name,
                    self.parser.version,
                    max(0, round((perf_counter() - started) * 1000)),
                )
            else:
                await self.inspect_legacy_extraction(document, extraction, token)
            self.progress(document, extraction)
            self.stage(document, "vision")
            document.status = "extracting"
            self.session.commit()
            return
        assert extraction is not None
        if document.processing_stage == "vision":
            await self.vision_batch(document, extraction, token)
            return
        if document.processing_stage == "classification":
            if not any(page.text.strip() or page.tables for page in extraction.pages):
                # No document facts can be classified when every page is empty or unreadable.
                self.repository.mark_completed(document)
                self.stage(document, "completed")
                return
            await DocumentClassificationService(self.repository, self.text_client).classify(
                document,
                extraction,
                user_id,
            )
            self.guard(document, token)
            self.stage(document, "structured")
            return
        classifications = self.repository.list_document_classifications(document.id)
        dpe = [c for c in classifications if c.document_type == "dpe"]
        if dpe and self.repository.get_dpe_extraction(document.id) is None:
            await DpeExtractionService(self.repository, self.text_client).extract(
                document,
                extraction,
                dpe,
                user_id,
            )
            self.guard(document, token)
            document.status = "analyzing"
            self.session.commit()
            return
        groups: dict[Any, list[Any]] = {}
        for classification in classifications:
            kind = DocumentType(classification.document_type)
            if kind in STRUCTURED_DOCUMENT_TYPES:
                groups.setdefault(structured_extraction_type(kind), []).append(classification)
        for kind, group in groups.items():
            if self.repository.get_structured_extraction(document.id, kind) is None:
                await StructuredExtractionService(self.repository, self.text_client).extract(
                    document,
                    extraction,
                    group,
                    user_id,
                )
                self.guard(document, token)
                document.status = "analyzing"
                self.session.commit()
                return
        self.guard(document, token)
        self.repository.mark_completed(document)
        self.stage(document, "completed")

    async def run(self, document: DocumentRecord, *, seconds: float | None = None) -> None:
        token = document.lease_token
        deadline = perf_counter() + (seconds or self.settings.processing_batch_seconds)
        try:
            while document.processing_stage in ACTIVE_STAGES and perf_counter() < deadline:
                if document.next_attempt_at is not None and utc(
                    document.next_attempt_at
                ) > datetime.now(UTC):
                    break
                document.lease_until = datetime.now(UTC) + timedelta(
                    seconds=self.settings.processing_lease_seconds
                )
                self.session.commit()
                remaining = deadline - perf_counter()
                # A new provider call can use the entire provider timeout. Leave
                # it for the next batch instead of admitting and canceling it.
                if document.processing_stage in {"vision", "classification", "structured"} and (
                    remaining < self.settings.openai_timeout_seconds + 2
                ):
                    break
                try:
                    await asyncio.wait_for(self.step(document, token), timeout=max(0.1, remaining))
                except TimeoutError as error:
                    if perf_counter() >= deadline - 0.1:
                        raise BatchDeadlineExceeded from error
                    raise
                document.processing_attempts = 0
                self.session.commit()
            if document.processing_stage in ACTIVE_STAGES and (
                document.next_attempt_at is None
                or utc(document.next_attempt_at) <= datetime.now(UTC)
            ):
                document.next_attempt_at = datetime.now(UTC)
                document.processing_progress = {
                    **document.processing_progress,
                    "retry_reason": "batch_deadline",
                }
                self.session.commit()
        except LostLease:
            logger.warning("Document processing lease lost: document_id=%s", document.id)
        except Exception as error:
            self.session.rollback()
            self.guard(document, token)
            batch_deadline = isinstance(error, BatchDeadlineExceeded)
            retryable = None if batch_deadline else retryable_error(error)
            attempted = not isinstance(retryable, DeferredLLMCall) or retryable.attempted
            document.processing_attempts += int(attempted and not batch_deadline)
            logger.warning(
                "Document processing interrupted: document_id=%s stage=%s error_type=%s "
                "retryable=%s attempts=%s",
                document.id,
                document.processing_stage,
                type(error).__name__,
                batch_deadline or retryable is not None,
                document.processing_attempts,
            )
            if (
                batch_deadline or retryable is not None
            ) and document.processing_attempts < self.settings.vision_max_attempts:
                if batch_deadline:
                    next_attempt_at = datetime.now(UTC)
                    retry_reason = "batch_deadline"
                else:
                    assert retryable is not None
                    next_attempt_at = retry_at_for(
                        retryable, document.processing_attempts, datetime.now(UTC)
                    )
                    retry_reason = (
                        "rate_limit"
                        if isinstance(retryable, DeferredLLMCall)
                        else "temporary_error"
                    )
                document.next_attempt_at = next_attempt_at
                document.processing_progress = {
                    **document.processing_progress,
                    "retry_reason": retry_reason,
                }
                document.status = (
                    "extracting"
                    if document.processing_stage in {"xberg", "vision"}
                    else "analyzing"
                )
                document.failure_reason = None
            else:
                document.processing_stage = "failed"
                document.status = "failed"
                document.next_attempt_at = None
                document.failure_reason = "La lecture ou l’analyse a échoué. Vous pouvez réessayer."
            self.session.commit()
        finally:
            self.session.execute(
                update(DocumentRecord)
                .where(DocumentRecord.id == document.id, DocumentRecord.lease_token == token)
                .values(lease_token=None, lease_until=None)
            )
            self.session.commit()


async def run_document_jobs(
    engine: Engine | Connection,
    storage: PrivateObjectStorage,
    parser: PdfParser,
    client: Any,
    document_id: UUID | None = None,
) -> int:
    """Use a fresh session, independent of the HTTP request's session lifecycle."""
    async with _local_worker_lock:
        settings = get_settings()
        deadline = perf_counter() + settings.processing_batch_seconds
        processed = 0
        with Session(engine) as session:
            while perf_counter() < deadline:
                document = claim_document(session, settings, document_id)
                if document is None:
                    break
                await PersistentDocumentWorker(session, storage, parser, client, settings).run(
                    document, seconds=max(0.1, deadline - perf_counter())
                )
                processed += 1
                if document_id is not None:
                    break
        return processed
