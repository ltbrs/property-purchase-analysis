from datetime import UTC, date, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from app.core.auth import CurrentUserId
from app.core.config import get_settings
from app.core.database import DatabaseSession
from app.documents.classification.models import DocumentClassificationRead
from app.documents.classification.service import (
    DocumentClassificationFailed,
    DocumentClassificationService,
)
from app.documents.extraction.service import (
    DocumentExtractionFailed,
    DocumentExtractionService,
)
from app.documents.models import (
    AnalysisCaseCreate,
    AnalysisCaseRead,
    AnalysisCaseUpdate,
    DocumentExtractionRead,
    DocumentRead,
    DocumentRecord,
    DocumentStatus,
    DocumentViewUrlRead,
)
from app.documents.parsers import PdfParserDependency
from app.documents.repository import DocumentRepository
from app.documents.validation import InvalidDocument, validate_pdf
from app.jobs.document_processing import DocumentProcessingService
from app.llm import StructuredOutputClientDependency
from app.property.models import PropertyType
from app.property.normalization.ag_minutes import NormalizedAgMinutes
from app.property.normalization.diagnostics import NormalizedDiagnostics
from app.property.normalization.dpe import DpeExtractionRead, NormalizedDpeFacts
from app.property.normalization.dpe_service import (
    DpeClassificationRequired,
    DpeExtractionFailed,
    DpeExtractionService,
)
from app.property.normalization.financials import NormalizedFinancials
from app.property.normalization.structured import (
    StructuredExtractionRead,
    StructuredExtractionType,
)
from app.property.normalization.structured_service import (
    StructuredExtractionFailed,
    StructuredExtractionService,
    UnsupportedStructuredDocument,
)
from app.property.reconciliation import TimelineEvent
from app.reports import BuyerReport, build_buyer_report
from app.risks.engine import evaluate_case_risks
from app.risks.models import RiskFindingRead
from app.risks.rules.missing_documents import AvailableDocument, MissingDocumentContext
from app.storage.object_storage import ObjectStorage, ObjectStorageError

router = APIRouter(prefix="/analysis-cases", tags=["documents"])


class CaseFindingsRefreshRead(BaseModel):
    findings: list[RiskFindingRead]
    timeline: list[TimelineEvent]


def _load_normalized_case_data(
    repository: DocumentRepository,
    analysis_case_id: UUID,
    user_id: UUID,
) -> tuple[
    list[NormalizedDpeFacts],
    list[NormalizedAgMinutes],
    list[NormalizedFinancials],
    list[NormalizedDiagnostics],
    list[AvailableDocument],
]:
    dpe_documents = [
        NormalizedDpeFacts.model_validate(record.normalized_facts)
        for record in repository.list_case_dpe_extractions(analysis_case_id, user_id)
    ]
    minutes: list[NormalizedAgMinutes] = []
    financials: list[NormalizedFinancials] = []
    diagnostics: list[NormalizedDiagnostics] = []
    for record in repository.list_case_structured_extractions(analysis_case_id, user_id):
        if record.extraction_type == StructuredExtractionType.AG_MINUTES.value:
            minutes.append(NormalizedAgMinutes.model_validate(record.normalized_facts))
        elif record.extraction_type == StructuredExtractionType.FINANCIALS.value:
            financials.append(NormalizedFinancials.model_validate(record.normalized_facts))
        elif record.extraction_type == StructuredExtractionType.DIAGNOSTICS.value:
            diagnostics.append(NormalizedDiagnostics.model_validate(record.normalized_facts))
    available_documents = [
        AvailableDocument.model_validate(
            {
                "document_id": record.document_id,
                "document_type": record.document_type,
                "document_date": record.document_date,
                "covered_period_end": record.covered_period_end,
            }
        )
        for record in repository.list_case_classifications(analysis_case_id, user_id)
    ]
    return dpe_documents, minutes, financials, diagnostics, available_documents


def _refresh_case_findings(
    repository: DocumentRepository,
    analysis_case_id: UUID,
    user_id: UUID,
) -> tuple[
    list[RiskFindingRead],
    list[TimelineEvent],
    list[NormalizedDpeFacts],
    list[NormalizedDiagnostics],
]:
    dpe_documents, minutes, financials, diagnostics, available_documents = (
        _load_normalized_case_data(repository, analysis_case_id, user_id)
    )
    analysis_case = repository.get_owned_analysis_case(analysis_case_id, user_id)
    missing_document_context = MissingDocumentContext(
        is_coproperty=(
            None
            if analysis_case is None or analysis_case.property_type == PropertyType.UNKNOWN.value
            else analysis_case.property_type == PropertyType.APARTMENT_COPROPERTY.value
        )
    )
    evaluation = evaluate_case_risks(
        dpe_documents=dpe_documents,
        minutes=minutes,
        financials=financials,
        diagnostics=diagnostics,
        available_documents=available_documents,
        missing_document_context=missing_document_context,
        as_of=date.today(),
    )
    records = repository.replace_case_findings(
        analysis_case_id=analysis_case_id,
        user_id=user_id,
        findings=evaluation.findings,
    )
    return (
        [RiskFindingRead.model_validate(record) for record in records],
        evaluation.reconciliation.timeline,
        dpe_documents,
        diagnostics,
    )


@router.post("", response_model=AnalysisCaseRead, status_code=status.HTTP_201_CREATED)
def create_analysis_case(
    payload: AnalysisCaseCreate,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> AnalysisCaseRead:
    analysis_case = DocumentRepository(session).create_analysis_case(
        current_user_id,
        payload.title.strip(),
        payload.property_type,
        price_eur=payload.price_eur,
        surface_m2=payload.surface_m2,
        lot_count=payload.lot_count,
    )
    return AnalysisCaseRead.model_validate(analysis_case)


@router.get("", response_model=list[AnalysisCaseRead])
def list_analysis_cases(
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> list[AnalysisCaseRead]:
    analysis_cases = DocumentRepository(session).list_analysis_cases(current_user_id)
    return [AnalysisCaseRead.model_validate(item) for item in analysis_cases]


@router.get("/{analysis_case_id}", response_model=AnalysisCaseRead)
def get_analysis_case(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> AnalysisCaseRead:
    analysis_case = DocumentRepository(session).get_owned_analysis_case(
        analysis_case_id, current_user_id
    )
    if analysis_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")
    return AnalysisCaseRead.model_validate(analysis_case)


@router.patch("/{analysis_case_id}", response_model=AnalysisCaseRead)
def update_analysis_case(
    analysis_case_id: UUID,
    payload: AnalysisCaseUpdate,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> AnalysisCaseRead:
    repository = DocumentRepository(session)
    analysis_case = repository.get_owned_analysis_case(analysis_case_id, current_user_id)
    if analysis_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")
    updated = repository.update_analysis_case_property_type(
        analysis_case, payload.property_type
    )
    return AnalysisCaseRead.model_validate(updated)


@router.get("/{analysis_case_id}/documents", response_model=list[DocumentRead])
def list_documents(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> list[DocumentRead]:
    repository = DocumentRepository(session)
    if repository.get_owned_analysis_case(analysis_case_id, current_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")
    classifications = {
        classification.document_id: classification.document_type
        for classification in repository.list_case_classifications(
            analysis_case_id, current_user_id
        )
    }
    return [
        DocumentRead.model_validate(document).model_copy(
            update={"document_type": classifications.get(document.id)}
        )
        for document in repository.list_documents(analysis_case_id, current_user_id)
    ]


@router.get(
    "/{analysis_case_id}/documents/{document_id}/view-url",
    response_model=DocumentViewUrlRead,
)
async def create_document_view_url(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    storage: ObjectStorage,
) -> DocumentViewUrlRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(
        analysis_case_id, document_id, current_user_id
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

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

    return DocumentViewUrlRead(
        url=url,
        expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
    )


@router.get(
    "/{analysis_case_id}/documents/{document_id}/extraction",
    response_model=DocumentExtractionRead,
)
def get_document_extraction(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> DocumentExtractionRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(
        analysis_case_id, document_id, current_user_id
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    extraction = repository.get_extraction(document.id)
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune extraction brute n’est disponible pour ce document.",
        )
    return DocumentExtractionRead.model_validate(extraction)


@router.get(
    "/{analysis_case_id}/documents/{document_id}/dpe-extraction",
    response_model=DpeExtractionRead,
)
def get_dpe_extraction(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> DpeExtractionRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(
        analysis_case_id, document_id, current_user_id
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    extraction = repository.get_dpe_extraction(document.id)
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune donnée DPE structurée n’est disponible pour ce document.",
        )
    return DpeExtractionRead.model_validate(extraction)


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
    "/{analysis_case_id}/documents/{document_id}/process",
    response_model=DocumentRead,
)
async def process_document(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    storage: ObjectStorage,
    parser: PdfParserDependency,
    llm_client: StructuredOutputClientDependency,
) -> DocumentRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(
        analysis_case_id, document_id, current_user_id
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    if document.status in {
        DocumentStatus.EXTRACTING.value,
        DocumentStatus.ANALYZING.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document processing is already in progress",
        )

    try:
        classification = await DocumentProcessingService(
            repository, storage, parser, llm_client
        ).process(document)
    except ObjectStorageError as error:
        repository.mark_extraction_failed(
            document, "Le document n’a pas pu être relu depuis le stockage privé."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Le document n’a pas pu être relu depuis le stockage privé.",
        ) from error
    except DocumentExtractionFailed as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except (
        DocumentClassificationFailed,
        DpeExtractionFailed,
        StructuredExtractionFailed,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    session.refresh(document)
    return DocumentRead.model_validate(document).model_copy(
        update={"document_type": classification.document_type}
    )


@router.delete(
    "/{analysis_case_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    storage: ObjectStorage,
) -> Response:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(analysis_case_id, document_id, current_user_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        await run_in_threadpool(
            storage.delete_pdf, document.storage_bucket, document.storage_key
        )
    except ObjectStorageError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="La suppression du document a échoué. Veuillez réessayer.",
        ) from error

    repository.delete_document(document)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.post(
    "/{analysis_case_id}/documents/{document_id}/classify",
    response_model=DocumentClassificationRead,
)
async def classify_document(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    llm_client: StructuredOutputClientDependency,
) -> DocumentClassificationRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(analysis_case_id, document_id, current_user_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    extraction = repository.get_extraction(document.id)
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Extract the document before classification",
        )
    if (
        document.status == DocumentStatus.ANALYZING.value
        and repository.get_classification(document.id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document analysis is already in progress",
        )

    try:
        classification = await DocumentClassificationService(repository, llm_client).classify(
            document, extraction
        )
    except DocumentClassificationFailed as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    return DocumentClassificationRead.model_validate(classification)


@router.post(
    "/{analysis_case_id}/documents/{document_id}/extract-dpe",
    response_model=DpeExtractionRead,
)
async def extract_dpe_document(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    llm_client: StructuredOutputClientDependency,
) -> DpeExtractionRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(analysis_case_id, document_id, current_user_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    extraction = repository.get_extraction(document.id)
    classification = repository.get_classification(document.id)
    if extraction is None or classification is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Extract and classify the document before DPE extraction",
        )
    if (
        document.status == DocumentStatus.ANALYZING.value
        and repository.get_dpe_extraction(document.id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document analysis is already in progress",
        )

    try:
        dpe_extraction = await DpeExtractionService(repository, llm_client).extract(
            document, extraction, classification
        )
    except DpeClassificationRequired as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except DpeExtractionFailed as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    return DpeExtractionRead.model_validate(dpe_extraction)


@router.post(
    "/{analysis_case_id}/documents/{document_id}/extract-structured",
    response_model=StructuredExtractionRead,
)
async def extract_structured_document(
    analysis_case_id: UUID,
    document_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    llm_client: StructuredOutputClientDependency,
) -> StructuredExtractionRead:
    repository = DocumentRepository(session)
    document = repository.get_owned_document(analysis_case_id, document_id, current_user_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    extraction = repository.get_extraction(document.id)
    classification = repository.get_classification(document.id)
    if extraction is None or classification is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Extract and classify the document before structured extraction",
        )
    try:
        result = await StructuredExtractionService(repository, llm_client).extract(
            document, extraction, classification
        )
    except UnsupportedStructuredDocument as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except StructuredExtractionFailed as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    return StructuredExtractionRead.model_validate(result)


@router.post(
    "/{analysis_case_id}/findings/refresh",
    response_model=CaseFindingsRefreshRead,
)
def refresh_case_findings(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> CaseFindingsRefreshRead:
    repository = DocumentRepository(session)
    if repository.get_owned_analysis_case(analysis_case_id, current_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")

    findings, timeline, _, _ = _refresh_case_findings(repository, analysis_case_id, current_user_id)
    return CaseFindingsRefreshRead(findings=findings, timeline=timeline)


@router.get(
    "/{analysis_case_id}/findings",
    response_model=list[RiskFindingRead],
)
def list_case_findings(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> list[RiskFindingRead]:
    repository = DocumentRepository(session)
    if repository.get_owned_analysis_case(analysis_case_id, current_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")
    return [
        RiskFindingRead.model_validate(record)
        for record in repository.list_case_findings(analysis_case_id, current_user_id)
    ]


@router.post("/{analysis_case_id}/report/refresh", response_model=BuyerReport)
def refresh_case_report(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> BuyerReport:
    repository = DocumentRepository(session)
    analysis_case = repository.get_owned_analysis_case(analysis_case_id, current_user_id)
    if analysis_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")
    _, _, dpe_documents, diagnostics = _refresh_case_findings(
        repository, analysis_case_id, current_user_id
    )
    documents = repository.list_documents(analysis_case_id, current_user_id)
    report = build_buyer_report(
        analysis_case_id=analysis_case_id,
        title=analysis_case.title,
        findings=[
            record.to_finding()
            for record in repository.list_case_findings(analysis_case_id, current_user_id)
        ],
        document_names={document.id: document.original_filename for document in documents},
        dpe_documents=dpe_documents,
        diagnostics=diagnostics,
    )
    repository.save_case_report(
        analysis_case_id=analysis_case_id,
        user_id=current_user_id,
        report=report,
    )
    return report


@router.get("/{analysis_case_id}/report", response_model=BuyerReport)
def get_case_report(
    analysis_case_id: UUID,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> BuyerReport:
    repository = DocumentRepository(session)
    if repository.get_owned_analysis_case(analysis_case_id, current_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis case not found")
    record = repository.get_case_report(analysis_case_id, current_user_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not generated")
    return record.to_report()
