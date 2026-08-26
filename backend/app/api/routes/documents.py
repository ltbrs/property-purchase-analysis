from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.auth import CurrentUserId
from app.core.config import get_settings
from app.core.database import DatabaseSession
from app.documents.extraction.service import (
    DocumentExtractionFailed,
    DocumentExtractionService,
)
from app.documents.models import (
    AnalysisCaseCreate,
    AnalysisCaseRead,
    DocumentExtractionRead,
    DocumentRead,
    DocumentRecord,
    DocumentStatus,
)
from app.documents.parsers import PdfParserDependency
from app.documents.repository import DocumentRepository
from app.documents.validation import InvalidDocument, validate_pdf
from app.storage.object_storage import ObjectStorage, ObjectStorageError

router = APIRouter(prefix="/analysis-cases", tags=["documents"])


@router.post("", response_model=AnalysisCaseRead, status_code=status.HTTP_201_CREATED)
def create_analysis_case(
    payload: AnalysisCaseCreate,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> AnalysisCaseRead:
    analysis_case = DocumentRepository(session).create_analysis_case(
        current_user_id, payload.title.strip()
    )
    return AnalysisCaseRead.model_validate(analysis_case)


@router.get("/{analysis_case_id}/documents", response_model=list[DocumentRead])
def list_documents(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> list[DocumentRead]:
    repository = DocumentRepository(session)
    if repository.get_owned_analysis_case(analysis_case_id, current_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")
    return [
        DocumentRead.model_validate(document)
        for document in repository.list_documents(analysis_case_id, current_user_id)
    ]


@router.post(
    "/{analysis_case_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    storage: ObjectStorage,
    response: Response,
    file: Annotated[UploadFile, File(description="PDF document to analyze")],
) -> DocumentRead:
    repository = DocumentRepository(session)
    if repository.get_owned_analysis_case(analysis_case_id, current_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")

    try:
        validated = await validate_pdf(file, get_settings().max_upload_size_bytes)
    except InvalidDocument as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    existing = repository.find_by_checksum(analysis_case_id, current_user_id, validated.sha256)
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return DocumentRead.model_validate(existing)

    storage_key = f"analysis-cases/{analysis_case_id}/documents/{validated.sha256}.pdf"
    try:
        await run_in_threadpool(storage.upload_pdf, file.file, storage_key)
    except ObjectStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Le stockage du document a échoué. Veuillez réessayer.",
        ) from error

    document = DocumentRecord(
        analysis_case_id=analysis_case_id,
        original_filename=validated.filename,
        content_type="application/pdf",
        size_bytes=validated.size_bytes,
        sha256=validated.sha256,
        storage_bucket=storage.bucket,
        storage_key=storage_key,
        status=DocumentStatus.UPLOADED.value,
    )
    persisted = repository.create_document(document, current_user_id)
    return DocumentRead.model_validate(persisted)


@router.post(
    "/{analysis_case_id}/documents/{document_id}/extract",
    response_model=DocumentExtractionRead,
)
async def extract_document(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    storage: ObjectStorage,
    parser: PdfParserDependency,
) -> DocumentExtractionRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(analysis_case_id, document_id, current_user_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    existing = repository.get_extraction(document.id)
    if existing is not None:
        return DocumentExtractionRead.model_validate(existing)
    if document.status == DocumentStatus.EXTRACTING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document extraction is already in progress",
        )

    try:
        pdf_bytes = await run_in_threadpool(
            storage.download_pdf, document.storage_bucket, document.storage_key
        )
    except ObjectStorageError as error:
        repository.mark_extraction_failed(
            document, "Le document n’a pas pu être relu depuis le stockage privé."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Le document n’a pas pu être relu depuis le stockage privé.",
        ) from error

    try:
        extraction = await DocumentExtractionService(repository, parser).extract(
            document, pdf_bytes
        )
    except DocumentExtractionFailed as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    return DocumentExtractionRead.model_validate(extraction)
