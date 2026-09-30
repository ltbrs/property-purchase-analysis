from collections.abc import Generator
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes import documents, processing
from app.core.config import get_settings
from app.core.database import Base, get_db_session
from app.documents.parsers import get_pdf_parser
from app.llm import get_structured_output_client
from app.main import create_app
from app.storage.object_storage import get_object_storage
from tests.billing_fixtures import grant_analysis_access, grant_analysis_credit
from tests.test_document_processing import (
    FakePdfParser,
    FakeStructuredOutputClient,
    MemoryObjectStorage,
    auth,
    dpe_outputs,
    upload_document,
)


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session
    engine.dispose()


def test_cron_requires_its_own_secret_before_loading_provider_dependencies(
    monkeypatch: Any,
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "processing_cron_secret", SecretStr("cron-test-secret"))
    application = create_app()

    def must_not_load() -> None:
        raise AssertionError("Unauthorized scheduler must not load document providers")

    application.dependency_overrides[get_object_storage] = must_not_load
    with TestClient(application) as client:
        response = client.post("/api/v1/internal/document-processing")
        wrong_secret = client.post(
            "/api/v1/internal/document-processing", headers={"Authorization": "Bearer wrong"}
        )
    assert response.status_code == 401
    assert wrong_secret.status_code == 401


def test_duplicate_process_requests_and_reload_keep_queued_progress(
    session: Session, monkeypatch: Any
) -> None:
    storage = MemoryObjectStorage()
    parser = FakePdfParser()
    llm_client = FakeStructuredOutputClient(dpe_outputs())
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_object_storage] = lambda: storage
    application.dependency_overrides[get_pdf_parser] = lambda: parser
    application.dependency_overrides[get_structured_output_client] = lambda: llm_client
    scheduled = 0

    async def defer_worker(*args: Any) -> None:
        nonlocal scheduled
        scheduled += 1

    monkeypatch.setattr(documents, "run_document_jobs", defer_worker)
    user_id = uuid4()
    with TestClient(application) as client:
        grant_analysis_credit(session, user_id)
        case_id = client.post(
            "/api/v1/analysis-cases", headers=auth(user_id), json={"title": "Async test"}
        ).json()["id"]
        grant_analysis_access(session, user_id, case_id)
        document_id = upload_document(client, storage, case_id, user_id).json()["id"]
        url = f"/api/v1/analysis-cases/{case_id}/documents/{document_id}"
        first = client.post(url + "/process", headers=auth(user_id))
        second = client.post(url + "/process", headers=auth(user_id))
        reloaded = client.get(f"/api/v1/analysis-cases/{case_id}/documents", headers=auth(user_id))
        direct_analysis = client.post(url + "/classify", headers=auth(user_id))
    assert first.status_code == second.status_code == 202
    assert first.json() == second.json() == reloaded.json()[0]
    assert first.json()["processing_stage"] == "queued"
    assert scheduled == 1
    assert direct_analysis.status_code == 409
    assert llm_client.calls == parser.parse_count == 0


def test_configured_scheduler_runs_due_batch(session: Session, monkeypatch: Any) -> None:
    monkeypatch.setattr(get_settings(), "processing_cron_secret", SecretStr("cron-test-secret"))
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_object_storage] = lambda: MemoryObjectStorage()
    application.dependency_overrides[get_pdf_parser] = lambda: FakePdfParser()
    application.dependency_overrides[get_structured_output_client] = lambda: (
        FakeStructuredOutputClient([])
    )

    async def batch(*args: Any) -> int:
        return 2

    monkeypatch.setattr(processing, "run_document_jobs", batch)
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/internal/document-processing",
            headers={"Authorization": "Bearer cron-test-secret"},
        )
    assert response.status_code == 200
    assert response.json() == {"processed_documents": 2}
