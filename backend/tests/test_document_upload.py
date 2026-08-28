from collections.abc import Generator
from io import BytesIO
from typing import BinaryIO, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db_session
from app.documents.models import DocumentRecord
from app.main import create_app
from app.storage.object_storage import ObjectStorageError, get_object_storage

PDF_CONTENT = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


class MemoryObjectStorage:
    bucket = "private-test-documents"

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload_pdf(self, file: BinaryIO, key: str) -> None:
        self.objects[key] = file.read()

    def delete_pdf(self, bucket: str, key: str) -> None:
        assert bucket == self.bucket
        self.objects.pop(key, None)


@pytest.fixture
def session() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session
    Base.metadata.drop_all(engine)


@pytest.fixture
def storage() -> MemoryObjectStorage:
    return MemoryObjectStorage()


@pytest.fixture
def client(session: Session, storage: MemoryObjectStorage) -> Generator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_object_storage] = lambda: storage
    with TestClient(application) as test_client:
        yield test_client


def auth(user_id: UUID) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


def create_case(client: TestClient, user_id: UUID) -> UUID:
    response = client.post(
        "/api/v1/analysis-cases",
        headers=auth(user_id),
        json={"title": "Appartement rue de Rivoli"},
    )
    assert response.status_code == 201
    return UUID(response.json()["id"])


def test_property_type_updates_the_expected_coproperty_documents(client: TestClient) -> None:
    user_id = uuid4()
    created = client.post(
        "/api/v1/analysis-cases",
        headers=auth(user_id),
        json={
            "title": "Maison à tester",
            "property_type": "house",
        },
    )
    case_id = created.json()["id"]

    house_report = client.post(
        f"/api/v1/analysis-cases/{case_id}/report/refresh",
        headers=auth(user_id),
    )
    updated = client.patch(
        f"/api/v1/analysis-cases/{case_id}",
        headers=auth(user_id),
        json={"property_type": "apartment_coproperty"},
    )
    apartment_report = client.post(
        f"/api/v1/analysis-cases/{case_id}/report/refresh",
        headers=auth(user_id),
    )

    assert created.status_code == 201
    assert created.json()["property_type"] == "house"
    assert house_report.status_code == 200
    house_codes = {
        finding["code"]
        for section in house_report.json()["sections"]
        for finding in section["findings"]
    }
    assert house_codes == {"MISSING_DPE_DOCUMENT"}
    assert updated.status_code == 200
    assert updated.json()["property_type"] == "apartment_coproperty"
    apartment_codes = {
        finding["code"]
        for section in apartment_report.json()["sections"]
        for finding in section["findings"]
    }
    assert apartment_codes >= {
        "MISSING_DPE_DOCUMENT",
        "MISSING_RECENT_AG_MINUTES",
        "MISSING_COPROPERTY_FINANCIALS",
    }


def test_upload_requires_an_authenticated_identity(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/analysis-cases/{uuid4()}/documents",
        files={"file": ("dpe.pdf", PDF_CONTENT, "application/pdf")},
    )

    assert response.status_code == 401


def test_a_user_cannot_upload_or_list_another_users_documents(
    client: TestClient, storage: MemoryObjectStorage
) -> None:
    owner_id = uuid4()
    analysis_case_id = create_case(client, owner_id)
    other_user_id = uuid4()

    upload_response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(other_user_id),
        files={"file": ("dpe.pdf", PDF_CONTENT, "application/pdf")},
    )
    list_response = client.get(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(other_user_id),
    )

    assert upload_response.status_code == 404
    assert list_response.status_code == 404
    assert storage.objects == {}


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "expected_message"),
    [
        ("diagnostic.txt", b"not a pdf", "text/plain", "PDF"),
        ("diagnostic.pdf", b"not a pdf", "application/pdf", "contenu"),
        ("diagnostic.pdf", b"", "application/pdf", "vide"),
    ],
)
def test_upload_rejects_invalid_files(
    client: TestClient,
    filename: str,
    content: bytes,
    content_type: str,
    expected_message: str,
) -> None:
    user_id = uuid4()
    analysis_case_id = create_case(client, user_id)

    response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": (filename, content, content_type)},
    )

    assert response.status_code == 422
    assert expected_message in response.json()["detail"]


def test_upload_persists_private_metadata_and_exposes_status(
    client: TestClient,
    session: Session,
    storage: MemoryObjectStorage,
) -> None:
    user_id = uuid4()
    analysis_case_id = create_case(client, user_id)

    response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": ("DPE appartement.pdf", PDF_CONTENT, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "DPE appartement.pdf"
    assert body["size_bytes"] == len(PDF_CONTENT)
    assert body["status"] == "uploaded"
    assert "storage_key" not in body
    assert "sha256" not in body

    persisted = session.scalar(select(DocumentRecord))
    assert persisted is not None
    assert persisted.analysis_case_id == analysis_case_id
    assert persisted.storage_bucket == storage.bucket
    assert persisted.storage_key.startswith(f"analysis-cases/{analysis_case_id}/documents/")
    assert storage.objects[persisted.storage_key] == PDF_CONTENT

    listed = client.get(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
    )
    assert listed.status_code == 200
    assert listed.json() == [body]


def test_upload_is_idempotent_for_the_same_file(
    client: TestClient,
    session: Session,
    storage: MemoryObjectStorage,
) -> None:
    user_id = uuid4()
    analysis_case_id = create_case(client, user_id)

    first = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": ("dpe.pdf", PDF_CONTENT, "application/pdf")},
    )
    second = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": ("dpe.pdf", PDF_CONTENT, "application/pdf")},
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert len(list(session.scalars(select(DocumentRecord)))) == 1
    assert len(storage.objects) == 1


def test_storage_failure_does_not_persist_metadata(
    client: TestClient,
    session: Session,
) -> None:
    class FailingStorage:
        bucket = "private-test-documents"

        def upload_pdf(self, file: BinaryIO, key: str) -> None:
            raise ObjectStorageError("storage unavailable")

    cast(FastAPI, client.app).dependency_overrides[get_object_storage] = FailingStorage
    user_id = uuid4()
    analysis_case_id = create_case(client, user_id)

    response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": ("dpe.pdf", BytesIO(PDF_CONTENT), "application/pdf")},
    )

    assert response.status_code == 502
    assert session.scalar(select(DocumentRecord)) is None


def test_delete_removes_document_metadata_and_private_file(
    client: TestClient,
    session: Session,
    storage: MemoryObjectStorage,
) -> None:
    user_id = uuid4()
    analysis_case_id = create_case(client, user_id)
    uploaded = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": ("dpe.pdf", PDF_CONTENT, "application/pdf")},
    )
    document_id = uploaded.json()["id"]

    response = client.delete(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}",
        headers=auth(user_id),
    )

    assert response.status_code == 204
    assert response.content == b""
    assert session.scalar(select(DocumentRecord)) is None
    assert storage.objects == {}


def test_a_user_cannot_delete_another_users_document(
    client: TestClient,
    session: Session,
    storage: MemoryObjectStorage,
) -> None:
    owner_id = uuid4()
    analysis_case_id = create_case(client, owner_id)
    uploaded = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(owner_id),
        files={"file": ("dpe.pdf", PDF_CONTENT, "application/pdf")},
    )

    response = client.delete(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{uploaded.json()['id']}",
        headers=auth(uuid4()),
    )

    assert response.status_code == 404
    assert session.scalar(select(DocumentRecord)) is not None
    assert len(storage.objects) == 1


def test_storage_delete_failure_keeps_document_metadata(
    client: TestClient,
    session: Session,
) -> None:
    class FailingDeleteStorage:
        bucket = "private-test-documents"

        def upload_pdf(self, file: BinaryIO, key: str) -> None:
            pass

        def delete_pdf(self, bucket: str, key: str) -> None:
            raise ObjectStorageError("storage unavailable")

    cast(FastAPI, client.app).dependency_overrides[get_object_storage] = FailingDeleteStorage
    user_id = uuid4()
    analysis_case_id = create_case(client, user_id)
    uploaded = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": ("dpe.pdf", PDF_CONTENT, "application/pdf")},
    )

    response = client.delete(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{uploaded.json()['id']}",
        headers=auth(user_id),
    )

    assert response.status_code == 502
    assert session.scalar(select(DocumentRecord)) is not None
