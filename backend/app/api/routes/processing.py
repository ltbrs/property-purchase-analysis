from secrets import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import get_settings
from app.core.database import DatabaseSession
from app.documents.parsers import PdfParserDependency
from app.jobs.persistent_processing import run_document_jobs
from app.llm import StructuredOutputClientDependency
from app.storage.object_storage import ObjectStorage

router = APIRouter(prefix="/internal", tags=["processing"])


def require_cron_secret(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    secret = get_settings().processing_cron_secret
    if secret is None:
        raise HTTPException(status_code=503, detail="Processing scheduler is not configured")
    if authorization is None or not compare_digest(
        authorization, "Bearer " + secret.get_secret_value()
    ):
        raise HTTPException(status_code=401, detail="Invalid scheduler credentials")


@router.post("/document-processing", dependencies=[Depends(require_cron_secret)])
async def process_due_documents(
    session: DatabaseSession,
    storage: ObjectStorage,
    parser: PdfParserDependency,
    client: StructuredOutputClientDependency,
) -> dict[str, int]:
    return {
        "processed_documents": await run_document_jobs(session.get_bind(), storage, parser, client)
    }
