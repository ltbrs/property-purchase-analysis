from collections.abc import Generator
from typing import BinaryIO
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db_session
from app.documents.models import DocumentExtractionRecord, DocumentRecord
from app.documents.parsers import get_pdf_parser
from app.documents.parsers.base import ParsedPage, ParsedPdf, ParsedTable, PdfParserError
from app.main import create_app
from app.storage.object_storage import get_object_storage
from tests.pdf_fixtures import DPE_PDF


class MemoryObjectStorage:
    bucket = "private-test-documents"

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.download_count = 0

    def upload_pdf(self, file: BinaryIO, key: str) -> None:
        self.objects[key] = file.read()

    def download_pdf(self, bucket: str, key: str) -> bytes:
        assert bucket == self.bucket
        self.download_count += 1
        return self.objects[key]


class FakePdfParser:
    name = "fake-xberg"
    version = "test-1"

    def __init__(self) -> None:
        self.parse_count = 0

    async def parse(self, pdf_bytes: bytes, filename: str | None = None) -> ParsedPdf:
        self.parse_count += 1
        assert pdf_bytes == DPE_PDF
        assert filename == "dpe.pdf"
        return ParsedPdf(
            metadata={"title": "DPE appartement", "page_count": 2},
            pages=[
                ParsedPage(
                    page_number=1,
                    text="Classe energie E",
                    tables=[
                        ParsedTable(
                            cells=[["Classe", "E"]],
                            markdown="| Classe | E |",
                        )
                    ],
                ),
                ParsedPage(page_number=2, text="Cout annuel 1500 EUR"),
            ],
        )


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
def parser() -> FakePdfParser:
    return FakePdfParser()


@pytest.fixture
def client(
    session: Session, storage: MemoryObjectStorage, parser: FakePdfParser
) -> Generator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_object_storage] = lambda: storage
    application.dependency_overrides[get_pdf_parser] = lambda: parser
    with TestClient(application) as test_client:
        yield test_client


def auth(user_id: UUID) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


def upload_document(client: TestClient, user_id: UUID) -> tuple[UUID, UUID]:
    case_response = client.post(
        "/api/v1/analysis-cases",
        headers=auth(user_id),
        json={"title": "Appartement a Lyon"},
    )
    analysis_case_id = UUID(case_response.json()["id"])
    upload_response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents",
        headers=auth(user_id),
        files={"file": ("dpe.pdf", DPE_PDF, "application/pdf")},
    )
    assert upload_response.status_code == 201
    return analysis_case_id, UUID(upload_response.json()["id"])


def test_extraction_persists_ordered_page_output_and_parser_details(
    client: TestClient,
    session: Session,
    parser: FakePdfParser,
) -> None:
    user_id = uuid4()
    analysis_case_id, document_id = upload_document(client, user_id)

    response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}/extract",
        headers=auth(user_id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["parser_name"] == "fake-xberg"
    assert body["parser_version"] == "test-1"
    assert body["duration_ms"] >= 0
    assert body["metadata"]["title"] == "DPE appartement"
    assert [page["page_number"] for page in body["pages"]] == [1, 2]
    assert body["pages"][0]["tables"][0]["cells"] == [["Classe", "E"]]
    assert parser.parse_count == 1

    document = session.get(DocumentRecord, document_id)
    extraction = session.scalar(select(DocumentExtractionRecord))
    assert document is not None and document.status == "extracted"
    assert document.failure_reason is None
    assert extraction is not None and extraction.document_id == document_id


def test_extraction_is_idempotent(client: TestClient, parser: FakePdfParser) -> None:
    user_id = uuid4()
    analysis_case_id, document_id = upload_document(client, user_id)
    url = f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}/extract"

    first = client.post(url, headers=auth(user_id))
    second = client.post(url, headers=auth(user_id))

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert parser.parse_count == 1


def test_raw_extraction_can_be_read_without_running_the_parser_again(
    client: TestClient, parser: FakePdfParser
) -> None:
    user_id = uuid4()
    analysis_case_id, document_id = upload_document(client, user_id)
    client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}/extract",
        headers=auth(user_id),
    )

    response = client.get(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}/extraction",
        headers=auth(user_id),
    )

    assert response.status_code == 200
    assert response.json()["parser_name"] == "fake-xberg"
    assert [page["text"] for page in response.json()["pages"]] == [
        "Classe energie E",
        "Cout annuel 1500 EUR",
    ]
    assert parser.parse_count == 1


def test_raw_extraction_enforces_document_ownership(client: TestClient) -> None:
    owner_id = uuid4()
    analysis_case_id, document_id = upload_document(client, owner_id)

    response = client.get(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}/extraction",
        headers=auth(uuid4()),
    )

    assert response.status_code == 404


def test_extraction_enforces_document_ownership(
    client: TestClient,
    storage: MemoryObjectStorage,
    parser: FakePdfParser,
) -> None:
    owner_id = uuid4()
    analysis_case_id, document_id = upload_document(client, owner_id)

    response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}/extract",
        headers=auth(uuid4()),
    )

    assert response.status_code == 404
    assert storage.download_count == 0
    assert parser.parse_count == 0


def test_parser_failure_marks_document_failed_without_partial_output(
    client: TestClient,
    session: Session,
    parser: FakePdfParser,
) -> None:
    async def fail(pdf_bytes: bytes, filename: str | None = None) -> ParsedPdf:
        raise PdfParserError("native parser detail that must stay internal")

    parser.parse = fail  # type: ignore[method-assign]
    user_id = uuid4()
    analysis_case_id, document_id = upload_document(client, user_id)

    response = client.post(
        f"/api/v1/analysis-cases/{analysis_case_id}/documents/{document_id}/extract",
        headers=auth(user_id),
    )

    assert response.status_code == 422
    assert "réessayer" in response.json()["detail"]
    assert "native parser detail" not in response.json()["detail"]
    document = session.get(DocumentRecord, document_id)
    assert document is not None and document.status == "failed"
    assert session.scalar(select(DocumentExtractionRecord)) is None
