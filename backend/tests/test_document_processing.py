from collections.abc import Generator
from datetime import date
from typing import BinaryIO, TypeVar
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db_session
from app.documents.classification.models import (
    DocumentClassificationCandidate,
    DocumentType,
    ExtractionStrategy,
)
from app.documents.models import DocumentRecord, DocumentStatus
from app.documents.parsers import get_pdf_parser
from app.documents.parsers.base import ParsedPage, ParsedPdf
from app.llm import StructuredOutputResult, get_structured_output_client
from app.main import create_app
from app.property.normalization.dpe import (
    DpeDateFactCandidate,
    DpeExtractionCandidate,
    DpeNumberFactCandidate,
    DpeTextFactCandidate,
)
from app.risks.models.findings import RiskFindingRecord
from app.storage.object_storage import get_object_storage
from tests.pdf_fixtures import DPE_PDF

OutputModel = TypeVar("OutputModel", bound=BaseModel)


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
        assert pdf_bytes == DPE_PDF
        assert filename == "dpe.pdf"
        self.parse_count += 1
        return ParsedPdf(
            pages=[
                ParsedPage(
                    page_number=1,
                    text=(
                        "DPE établi le 15/06/2024. Classe énergie D. "
                        "Classe climat B. Consommation 182 kWh/m²/an."
                    ),
                )
            ]
        )


class FakeStructuredOutputClient:
    def __init__(self, outputs: list[BaseModel]) -> None:
        self.outputs = outputs
        self.calls = 0

    async def parse(
        self,
        *,
        system_prompt: str,
        user_content: str,
        response_model: type[OutputModel],
    ) -> StructuredOutputResult[OutputModel]:
        assert system_prompt
        assert '<page number="1">' in user_content
        output = self.outputs[self.calls]
        self.calls += 1
        assert isinstance(output, response_model)
        return StructuredOutputResult(
            output=output,
            response_id=f"resp_process_{self.calls}",
            requested_model="gpt-5.6-luna",
            resolved_model="gpt-5.6-luna",
        )


def null_text() -> DpeTextFactCandidate:
    return DpeTextFactCandidate(value=None, page_number=None, quote=None)


def null_number() -> DpeNumberFactCandidate:
    return DpeNumberFactCandidate(value=None, page_number=None, quote=None)


def null_date() -> DpeDateFactCandidate:
    return DpeDateFactCandidate(value=None, page_number=None, quote=None)


def dpe_outputs() -> list[BaseModel]:
    return [
        DocumentClassificationCandidate(
            document_type=DocumentType.DPE,
            confidence=0.99,
            document_date=date(2024, 6, 15),
            covered_period_start=None,
            covered_period_end=None,
            issuer="Cabinet Exemple",
            extraction_strategy=ExtractionStrategy.TEXT,
        ),
        DpeExtractionCandidate(
            dpe_rating=DpeTextFactCandidate(value="D", page_number=1, quote="Classe énergie D"),
            ges_rating=DpeTextFactCandidate(value="B", page_number=1, quote="Classe climat B"),
            energy_consumption_kwh_m2_year=DpeNumberFactCandidate(
                value=182,
                page_number=1,
                quote="Consommation 182 kWh/m²/an",
            ),
            greenhouse_gas_emissions_kg_co2_m2_year=null_number(),
            estimated_annual_energy_cost_min=null_number(),
            estimated_annual_energy_cost_max=null_number(),
            surface=null_number(),
            heating_type=null_text(),
            hot_water_type=null_text(),
            dpe_date=DpeDateFactCandidate(
                value="2024-06-15",
                page_number=1,
                quote="DPE établi le 15/06/2024",
            ),
            dpe_valid_until=null_date(),
            recommendations=[],
        ),
    ]


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


def auth(user_id: UUID) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


def test_process_runs_the_full_dpe_workflow_and_is_idempotent(
    session: Session,
) -> None:
    storage = MemoryObjectStorage()
    parser = FakePdfParser()
    llm_client = FakeStructuredOutputClient(dpe_outputs())
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_object_storage] = lambda: storage
    application.dependency_overrides[get_pdf_parser] = lambda: parser
    application.dependency_overrides[get_structured_output_client] = lambda: llm_client
    user_id = uuid4()

    with TestClient(application) as client:
        created = client.post(
            "/api/v1/analysis-cases",
            headers=auth(user_id),
            json={"title": "Appartement test", "property_type": "house"},
        )
        case_id = created.json()["id"]
        uploaded = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents",
            headers=auth(user_id),
            files={"file": ("dpe.pdf", DPE_PDF, "application/pdf")},
        )
        document_id = uploaded.json()["id"]
        process_url = f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/process"

        first = client.post(process_url, headers=auth(user_id))
        second = client.post(process_url, headers=auth(user_id))
        report = client.post(
            f"/api/v1/analysis-cases/{case_id}/report/refresh",
            headers=auth(user_id),
        )

    assert uploaded.status_code == 201
    assert uploaded.json()["status"] == "uploaded"
    assert first.status_code == 200
    assert first.json()["status"] == "completed"
    assert first.json()["document_type"] == "dpe"
    assert second.json() == first.json()
    assert storage.download_count == 1
    assert parser.parse_count == 1
    assert llm_client.calls == 2
    document = session.get(DocumentRecord, UUID(document_id))
    assert document is not None and document.status == DocumentStatus.COMPLETED.value
    report_codes = {
        finding["code"] for section in report.json()["sections"] for finding in section["findings"]
    }
    assert "MISSING_DPE_DOCUMENT" not in report_codes
    assert session.scalar(select(RiskFindingRecord)) is not None


def test_process_enforces_document_ownership(session: Session) -> None:
    storage = MemoryObjectStorage()
    parser = FakePdfParser()
    llm_client = FakeStructuredOutputClient(dpe_outputs())
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_object_storage] = lambda: storage
    application.dependency_overrides[get_pdf_parser] = lambda: parser
    application.dependency_overrides[get_structured_output_client] = lambda: llm_client
    owner_id = uuid4()

    with TestClient(application) as client:
        created = client.post(
            "/api/v1/analysis-cases",
            headers=auth(owner_id),
            json={"title": "Appartement test"},
        )
        case_id = created.json()["id"]
        uploaded = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents",
            headers=auth(owner_id),
            files={"file": ("dpe.pdf", DPE_PDF, "application/pdf")},
        )
        response = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{uploaded.json()['id']}/process",
            headers=auth(uuid4()),
        )

    assert response.status_code == 404
    assert storage.download_count == 0
    assert parser.parse_count == 0
    assert llm_client.calls == 0
