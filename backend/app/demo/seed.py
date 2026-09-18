import argparse
import asyncio
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.analysis import CaseAnalysisService
from app.core.config import get_settings
from app.core.database import get_engine
from app.demo.config import DEMO_DOCUMENT_LOGICAL_IDS, DEMO_TEMPLATE_KEY
from app.demo.manifest import DemoDocumentManifest, load_demo_manifest
from app.documents.models import DocumentRecord, DocumentStatus
from app.documents.parsers import get_pdf_parser
from app.documents.repository import DocumentRepository
from app.documents.validation import validate_pdf_bytes
from app.jobs.document_processing import DocumentProcessingService
from app.llm import get_structured_output_client
from app.property.models import AnalysisCaseRecord, PropertyType
from app.reports.models import BuyerReport
from app.storage.object_storage import ObjectStorageError, S3ObjectStorage

DEMO_PROCESSING_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _validate_source_file(
    manifest_path: Path,
    document_manifest: DemoDocumentManifest,
) -> bytes:
    path = manifest_path.parent / document_manifest.filename
    content = path.read_bytes()
    validated = validate_pdf_bytes(
        content,
        document_manifest.filename,
        "application/pdf",
        get_settings().max_upload_size_bytes,
    )
    if validated.size_bytes != document_manifest.size_bytes:
        raise ValueError(f"Unexpected file size for {document_manifest.filename}")
    if validated.sha256 != document_manifest.sha256:
        raise ValueError(f"Unexpected SHA-256 for {document_manifest.filename}")
    return content


def _ensure_storage_object(
    storage: S3ObjectStorage,
    key: str,
    content: bytes,
) -> None:
    try:
        metadata = storage.get_object_metadata(storage.bucket, key)
    except ObjectStorageError:
        storage.upload_pdf(BytesIO(content), key)
        return
    if metadata.size_bytes != len(content) or metadata.content_type != "application/pdf":
        raise ValueError(f"The existing storage object is inconsistent: {key}")


def _validate_processed_document(
    repository: DocumentRepository,
    document: DocumentRecord,
    expected: DemoDocumentManifest,
) -> None:
    extraction = repository.get_extraction(document.id)
    if extraction is None:
        raise ValueError(f"No extraction was persisted for {expected.filename}")
    page_numbers = [page.page_number for page in extraction.pages]
    if page_numbers != list(range(1, expected.page_count + 1)):
        raise ValueError(f"Unexpected extracted pages for {expected.filename}: {page_numbers}")
    if document.status != DocumentStatus.COMPLETED.value:
        raise ValueError(f"Document processing did not complete for {expected.filename}")


def _validate_report_sources(
    report: BuyerReport,
    documents: list[DocumentRecord],
    manifests_by_sha256: dict[str, DemoDocumentManifest],
) -> None:
    documents_by_id = {document.id: document for document in documents}
    for finding in (finding for section in report.sections for finding in section.findings):
        for source in finding.sources:
            document = documents_by_id.get(source.document_id)
            if document is None:
                raise ValueError(
                    f"Report source references an unknown document: {source.document_id}"
                )
            document_manifest = manifests_by_sha256[document.sha256]
            if not 1 <= source.page_number <= document_manifest.page_count:
                raise ValueError(
                    f"Report source page is invalid for {document.original_filename}: "
                    f"{source.page_number}"
                )


async def seed_demo(
    *,
    manifest_path: Path,
    template_key: str,
    publish: bool,
) -> AnalysisCaseRecord:
    manifest_path = manifest_path.resolve()
    manifest = load_demo_manifest(manifest_path)
    selected = manifest.selected_documents(DEMO_DOCUMENT_LOGICAL_IDS)
    fingerprint = manifest.fingerprint(DEMO_DOCUMENT_LOGICAL_IDS)
    source_files = {
        document.logical_id: _validate_source_file(manifest_path, document) for document in selected
    }
    settings = get_settings()
    storage = S3ObjectStorage(settings)
    parser = get_pdf_parser()
    llm_client = get_structured_output_client()

    with Session(get_engine()) as session:
        repository = DocumentRepository(session)
        analysis_case = repository.get_demo_analysis_case(template_key)
        if analysis_case is not None:
            if analysis_case.template_manifest_sha256 != fingerprint:
                raise ValueError(
                    f"Template {template_key} already exists with another manifest. "
                    "Use a new template key."
                )
            if analysis_case.published_at is not None:
                return analysis_case
        else:
            try:
                property_type = PropertyType(manifest.case.property_type)
            except ValueError as error:
                raise ValueError("Unsupported demo property type") from error
            analysis_case = repository.create_demo_analysis_case(
                title=manifest.case.title,
                property_type=property_type,
                price_eur=manifest.case.price_eur,
                surface_m2=manifest.case.surface_m2,
                lot_count=manifest.case.lot_count,
                template_key=template_key,
                template_manifest_sha256=fingerprint,
            )

        existing_documents = {
            document.sha256: document
            for document in repository.list_documents(
                analysis_case.id,
                DEMO_PROCESSING_USER_ID,
                include_unpublished_demo=True,
            )
        }
        processing = DocumentProcessingService(repository, storage, parser, llm_client)
        for expected in selected:
            content = source_files[expected.logical_id]
            storage_key = f"demo-templates/{template_key}/{expected.sha256}.pdf"
            _ensure_storage_object(storage, storage_key, content)
            document = existing_documents.get(expected.sha256)
            if document is None:
                document = repository.create_demo_document(
                    DocumentRecord(
                        analysis_case_id=analysis_case.id,
                        original_filename=expected.filename,
                        content_type="application/pdf",
                        size_bytes=expected.size_bytes,
                        sha256=expected.sha256,
                        storage_bucket=storage.bucket,
                        storage_key=storage_key,
                        status=DocumentStatus.UPLOADED.value,
                    )
                )
            if document.status != DocumentStatus.COMPLETED.value:
                await processing.process(
                    document,
                    DEMO_PROCESSING_USER_ID,
                    full_analysis=True,
                )
            _validate_processed_document(repository, document, expected)

        report = CaseAnalysisService(repository).refresh_report(
            analysis_case=analysis_case,
            user_id=DEMO_PROCESSING_USER_ID,
            demo_seed=True,
        )
        persisted_documents = repository.list_documents(
            analysis_case.id,
            DEMO_PROCESSING_USER_ID,
            include_unpublished_demo=True,
        )
        _validate_report_sources(
            report,
            persisted_documents,
            {document.sha256: document for document in selected},
        )
        if publish:
            repository.publish_demo_analysis_case(analysis_case, datetime.now(UTC))
        return analysis_case


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the global Lyon demonstration case")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--template-key", default=DEMO_TEMPLATE_KEY)
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    analysis_case = asyncio.run(
        seed_demo(
            manifest_path=args.manifest,
            template_key=args.template_key,
            publish=args.publish,
        )
    )
    state = "published" if analysis_case.published_at is not None else "draft"
    print(f"Demo case {analysis_case.id} is {state}.")


if __name__ == "__main__":
    main()
