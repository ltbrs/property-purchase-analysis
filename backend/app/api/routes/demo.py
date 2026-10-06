from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.api.routes.contact import limiter
from app.billing.models import AnalysisAccessStatus
from app.core.config import get_settings
from app.core.database import DatabaseSession
from app.documents.classification.models import DocumentType
from app.documents.models import (
    AnalysisCaseRead,
    DocumentExtractionRead,
    DocumentRead,
    DocumentRecord,
    DocumentViewUrlRead,
)
from app.documents.repository import DocumentRepository
from app.property.models import AnalysisCaseRecord
from app.property.normalization.dpe import DpeExtractionRead, NormalizedDpeFacts
from app.reports import BuyerReport
from app.reports.models import ReportRecord
from app.storage.object_storage import ObjectStorage, ObjectStorageError

router = APIRouter(prefix="/demo", tags=["demo"])


def _published_demo(session: DatabaseSession) -> AnalysisCaseRecord:
    demo = DocumentRepository(session).get_published_demo_analysis_case()
    if demo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Le dossier de démonstration est indisponible.",
        )
    return demo


def _published_demo_document(session: DatabaseSession, document_id: UUID) -> DocumentRecord:
    demo = _published_demo(session)
    document = session.scalar(
        select(DocumentRecord).where(
            DocumentRecord.id == document_id,
            DocumentRecord.analysis_case_id == demo.id,
        )
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/case", response_model=AnalysisCaseRead)
@limiter.limit("60/minute")
def get_public_demo_case(
    request: Request, response: Response, session: DatabaseSession
) -> AnalysisCaseRead:
    demo = _published_demo(session)
    response.headers["Cache-Control"] = "public, max-age=60"
    return AnalysisCaseRead.model_validate(demo).model_copy(
        update={"read_only": True, "analysis_access_status": AnalysisAccessStatus.ACTIVE}
    )


@router.get("/report", response_model=BuyerReport)
@limiter.limit("60/minute")
def get_public_demo_report(
    request: Request, response: Response, session: DatabaseSession
) -> BuyerReport:
    demo = _published_demo(session)
    record = session.scalar(select(ReportRecord).where(ReportRecord.analysis_case_id == demo.id))
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Le rapport de démonstration est indisponible.",
        )
    response.headers["Cache-Control"] = "public, max-age=60"
    return record.to_report()


@router.get("/documents", response_model=list[DocumentRead])
@limiter.limit("60/minute")
def list_public_demo_documents(
    request: Request, response: Response, session: DatabaseSession
) -> list[DocumentRead]:
    demo = _published_demo(session)
    repository = DocumentRepository(session)
    reader_id = UUID(int=0)
    classifications_by_document: dict[UUID, list[str]] = {}
    for classification in repository.list_case_classifications(demo.id, reader_id):
        types = classifications_by_document.setdefault(classification.document_id, [])
        if classification.document_type not in types:
            types.append(classification.document_type)
    ademe_statuses = {
        extraction.document_id: NormalizedDpeFacts.model_validate(
            extraction.normalized_facts
        ).ademe_verification.status.value
        for extraction in repository.list_case_dpe_extractions(demo.id, reader_id)
    }
    response.headers["Cache-Control"] = "public, max-age=60"
    return [
        DocumentRead.model_validate(document).model_copy(
            update={
                "document_types": classifications_by_document.get(document.id, []),
                "document_type": next(
                    (
                        item
                        for item in classifications_by_document.get(document.id, [])
                        if item != DocumentType.UNKNOWN.value
                    ),
                    classifications_by_document.get(document.id, [None])[0],
                ),
                "ademe_verification_status": ademe_statuses.get(document.id),
            }
        )
        for document in repository.list_documents(demo.id, reader_id)
    ]


@router.get("/documents/{document_id}/extraction", response_model=DocumentExtractionRead)
@limiter.limit("30/minute")
def get_public_demo_extraction(
    document_id: UUID,
    request: Request,
    response: Response,
    session: DatabaseSession,
) -> DocumentExtractionRead:
    document = _published_demo_document(session, document_id)
    extraction = DocumentRepository(session).get_extraction(document.id)
    if extraction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")
    response.headers["Cache-Control"] = "public, max-age=60"
    return DocumentExtractionRead.model_validate(extraction)


@router.get("/documents/{document_id}/dpe-extraction", response_model=DpeExtractionRead)
@limiter.limit("30/minute")
def get_public_demo_dpe_extraction(
    document_id: UUID,
    request: Request,
    response: Response,
    session: DatabaseSession,
) -> DpeExtractionRead:
    document = _published_demo_document(session, document_id)
    extraction = DocumentRepository(session).get_dpe_extraction(document.id)
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="DPE extraction not found"
        )
    response.headers["Cache-Control"] = "public, max-age=60"
    return DpeExtractionRead.model_validate(extraction)


@router.get("/documents/{document_id}/view-url", response_model=DocumentViewUrlRead)
@limiter.limit("30/minute")
async def get_public_demo_document_url(
    document_id: UUID,
    request: Request,
    response: Response,
    session: DatabaseSession,
    storage: ObjectStorage,
) -> DocumentViewUrlRead:
    document = _published_demo_document(session, document_id)
    ttl_seconds = get_settings().document_view_url_ttl_seconds
    try:
        url = await run_in_threadpool(
            storage.create_pdf_view_url,
            document.storage_bucket,
            document.storage_key,
            ttl_seconds,
        )
    except ObjectStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Le document ne peut pas être affiché pour le moment.",
        ) from error
    response.headers["Cache-Control"] = "no-store"
    return DocumentViewUrlRead(
        url=url,
        expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
    )
