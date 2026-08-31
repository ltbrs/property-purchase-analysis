from collections.abc import Generator, Iterator
from contextlib import contextmanager
from datetime import date
from typing import TypeVar
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db_session
from app.documents.classification.models import DocumentClassificationRecord, DocumentType
from app.documents.models import (
    DocumentExtractionPageRecord,
    DocumentExtractionRecord,
    DocumentRecord,
    DocumentStatus,
)
from app.documents.repository import DocumentRepository
from app.llm import StructuredOutputResult, get_structured_output_client
from app.main import create_app
from app.property.normalization.ag_minutes import (
    AgItemCandidate,
    AgItemKind,
    AgItemStatus,
    AgMinutesExtractionCandidate,
)
from app.property.normalization.structured import StructuredExtractionRecord
from app.reports.models import ReportRecord
from app.risks.models.findings import RiskFindingRecord

OutputModel = TypeVar("OutputModel", bound=BaseModel)


class FakeClient:
    def __init__(self, output: BaseModel) -> None:
        self.output = output
        self.calls = 0

    async def parse(
        self,
        *,
        system_prompt: str,
        user_content: str,
        response_model: type[OutputModel],
    ) -> StructuredOutputResult[OutputModel]:
        assert "vot" in system_prompt
        assert '<page number="1">' in user_content
        assert isinstance(self.output, response_model)
        self.calls += 1
        return StructuredOutputResult(
            output=self.output,
            response_id="resp_ag",
            requested_model="gpt-5.6-luna",
            resolved_model="gpt-5.6-luna",
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


def seed_ag(session: Session, user_id: UUID) -> tuple[UUID, UUID]:
    repository = DocumentRepository(session)
    analysis_case = repository.create_analysis_case(user_id, "AG test")
    document = DocumentRecord(
        analysis_case_id=analysis_case.id,
        original_filename="ag.pdf",
        content_type="application/pdf",
        size_bytes=100,
        sha256="b" * 64,
        storage_bucket="private",
        storage_key=f"test/{uuid4()}.pdf",
        status=DocumentStatus.EXTRACTED.value,
    )
    session.add(document)
    session.flush()
    session.add(
        DocumentExtractionRecord(
            document_id=document.id,
            parser_name="xberg",
            parser_version="1.0",
            duration_ms=5,
            document_metadata={},
            pages=[
                DocumentExtractionPageRecord(
                    page_number=1,
                    text=(
                        "AG du 12/05/2025 — Résolution 7 : réfection de la toiture "
                        "votée pour 120 000 €."
                    ),
                    tables=[],
                )
            ],
        )
    )
    session.add(
        DocumentClassificationRecord(
            document_id=document.id,
            document_type=DocumentType.AG_MINUTES.value,
            confidence=0.99,
            document_date=date(2025, 5, 12),
            covered_period_start=None,
            covered_period_end=None,
            issuer=None,
            extraction_strategy="text",
            requested_model="gpt-5.6-luna",
            resolved_model="gpt-5.6-luna",
            response_id="resp_class",
            prompt_version="test",
            raw_output={},
        )
    )
    session.commit()
    return analysis_case.id, document.id


@contextmanager
def client_for(session: Session, llm_client: FakeClient) -> Iterator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_structured_output_client] = lambda: llm_client
    with TestClient(application) as client:
        yield client


def test_structured_extraction_and_findings_refresh_are_persisted_and_idempotent(
    session: Session,
) -> None:
    user_id = uuid4()
    case_id, document_id = seed_ag(session, user_id)
    candidate = AgMinutesExtractionCandidate(
        meeting_date="2025-05-12",
        items=[
            AgItemCandidate(
                kind=AgItemKind.ROOF,
                description="Réfection de la toiture",
                meeting_date="2025-05-12",
                resolution_reference="7",
                status=AgItemStatus.VOTED,
                amount_eur="120 000 €",
                property_share_amount_eur=None,
                page_number=1,
                quote="Résolution 7 : réfection de la toiture votée pour 120 000 €",
            )
        ],
    )
    fake = FakeClient(candidate)
    extraction_url = f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-structured"
    headers = {"X-User-Id": str(user_id)}

    with client_for(session, fake) as client:
        first = client.post(extraction_url, headers=headers)
        second = client.post(extraction_url, headers=headers)
        refresh = client.post(f"/api/v1/analysis-cases/{case_id}/findings/refresh", headers=headers)
        listed = client.get(f"/api/v1/analysis-cases/{case_id}/findings", headers=headers)
        reviewed_finding = next(
            finding
            for finding in listed.json()
            if finding["code"] == "COPRO_MAJOR_WORKS_VOTED"
        )
        reviewed = client.patch(
            f"/api/v1/analysis-cases/{case_id}/findings/"
            f"{reviewed_finding['finding_key']}/review",
            headers=headers,
            json={"review_status": "not_problematic"},
        )
        refreshed_after_review = client.post(
            f"/api/v1/analysis-cases/{case_id}/findings/refresh", headers=headers
        )
        report_refresh = client.post(
            f"/api/v1/analysis-cases/{case_id}/report/refresh", headers=headers
        )
        report_get = client.get(f"/api/v1/analysis-cases/{case_id}/report", headers=headers)
        listed_documents = client.get(
            f"/api/v1/analysis-cases/{case_id}/documents", headers=headers
        )
        forbidden_report = client.get(
            f"/api/v1/analysis-cases/{case_id}/report",
            headers={"X-User-Id": str(uuid4())},
        )

    assert first.status_code == 200
    assert first.json()["normalized_facts"]["items"][0]["status"] == "voted"
    assert first.json()["id"] == second.json()["id"]
    assert fake.calls == 1
    assert {finding["code"] for finding in refresh.json()["findings"]} >= {
        "COPRO_MAJOR_WORKS_VOTED",
        "VOTED_WORK_WITHOUT_MATCHING_FUNDING_CALL",
    }
    assert {finding["finding_key"] for finding in listed.json()} == {
        finding["finding_key"] for finding in refresh.json()["findings"]
    }
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "not_problematic"
    assert next(
        finding
        for finding in refreshed_after_review.json()["findings"]
        if finding["finding_key"] == reviewed_finding["finding_key"]
    )["review_status"] == "not_problematic"
    assert session.scalar(select(StructuredExtractionRecord)) is not None
    assert len(list(session.scalars(select(RiskFindingRecord)))) == len(listed.json())
    assert {finding["code"] for finding in listed.json()} >= {
        "MISSING_DPE_DOCUMENT",
        "MISSING_COPROPERTY_FINANCIALS",
        "MISSING_WORKS_SUPPORTING_DOCUMENT",
    }
    assert report_refresh.status_code == 200
    assert report_get.json() == report_refresh.json()
    assert listed_documents.json()[0]["document_type"] == "ag_minutes"
    assert forbidden_report.status_code == 404
    assert [section["code"] for section in report_refresh.json()["sections"]] == [
        "financial",
        "building_coproperty",
        "energy",
        "diagnostics_safety",
        "inconsistencies",
        "missing_information",
        "reassuring",
    ]
    copro_finding = next(
        finding
        for section in report_refresh.json()["sections"]
        for finding in section["findings"]
        if finding["finding_key"] == reviewed_finding["finding_key"]
    )
    assert copro_finding["sources"][0]["document_name"] == "ag.pdf"
    assert copro_finding["sources"][0]["page_number"] == 1
    assert copro_finding["analysis_type"] == "reassuring"
    assert report_refresh.json()["summary"]["reassuring_count"] >= 1
    assert session.scalar(select(ReportRecord)) is not None


def test_structured_analysis_enforces_ownership(session: Session) -> None:
    owner_id = uuid4()
    case_id, document_id = seed_ag(session, owner_id)
    fake = FakeClient(AgMinutesExtractionCandidate(meeting_date=None, items=[]))
    with client_for(session, fake) as client:
        response = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-structured",
            headers={"X-User-Id": str(uuid4())},
        )
    assert response.status_code == 404
    assert fake.calls == 0
