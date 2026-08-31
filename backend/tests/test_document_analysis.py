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
from app.documents.classification.models import (
    DocumentClassificationCandidate,
    DocumentClassificationRecord,
    DocumentType,
    ExtractionStrategy,
)
from app.documents.models import (
    DocumentExtractionPageRecord,
    DocumentExtractionRecord,
    DocumentRecord,
    DocumentStatus,
)
from app.documents.repository import DocumentRepository
from app.llm import StructuredOutputResult, get_structured_output_client
from app.main import create_app
from app.property.normalization.dpe import (
    DpeDateFactCandidate,
    DpeExtractionCandidate,
    DpeExtractionRecord,
    DpeNumberFactCandidate,
    DpeTextFactCandidate,
)

OutputModel = TypeVar("OutputModel", bound=BaseModel)


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
            response_id=f"resp_test_{self.calls}",
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
    Base.metadata.drop_all(engine)


def seed_extracted_dpe(session: Session, user_id: UUID) -> tuple[UUID, UUID]:
    repository = DocumentRepository(session)
    analysis_case = repository.create_analysis_case(user_id, "Appartement test")
    document = DocumentRecord(
        analysis_case_id=analysis_case.id,
        original_filename="dpe.pdf",
        content_type="application/pdf",
        size_bytes=100,
        sha256="a" * 64,
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
            duration_ms=10,
            document_metadata={},
            pages=[
                DocumentExtractionPageRecord(
                    page_number=1,
                    text=(
                        "DPE établi le 15/06/2024. Classe énergie D. Classe climat B. "
                        "Consommation 182 kWh/m²/an. Surface de référence 67,4 m²."
                    ),
                    tables=[],
                ),
                DocumentExtractionPageRecord(
                    page_number=2,
                    text="Estimation des coûts annuels : entre 980 € et 1 350 €.",
                    tables=[],
                ),
            ],
        )
    )
    session.commit()
    return analysis_case.id, document.id


def classification_candidate(confidence: float = 0.99) -> DocumentClassificationCandidate:
    return DocumentClassificationCandidate(
        document_type=DocumentType.DPE,
        confidence=confidence,
        document_date=date(2024, 6, 15),
        covered_period_start=None,
        covered_period_end=None,
        issuer="Cabinet Exemple",
        extraction_strategy=ExtractionStrategy.MIXED,
    )


def null_text() -> DpeTextFactCandidate:
    return DpeTextFactCandidate(value=None, page_number=None, quote=None)


def null_number() -> DpeNumberFactCandidate:
    return DpeNumberFactCandidate(value=None, page_number=None, quote=None)


def null_date() -> DpeDateFactCandidate:
    return DpeDateFactCandidate(value=None, page_number=None, quote=None)


def dpe_candidate() -> DpeExtractionCandidate:
    return DpeExtractionCandidate(
        dpe_rating=DpeTextFactCandidate(value="d", page_number=1, quote="Classe énergie D"),
        ges_rating=DpeTextFactCandidate(value="B", page_number=1, quote="Classe climat B"),
        energy_consumption_kwh_m2_year=DpeNumberFactCandidate(
            value=182, page_number=1, quote="Consommation 182 kWh/m²/an"
        ),
        greenhouse_gas_emissions_kg_co2_m2_year=null_number(),
        estimated_annual_energy_cost_min=DpeNumberFactCandidate(
            value=980, page_number=2, quote="entre 980 € et 1 350 €"
        ),
        estimated_annual_energy_cost_max=DpeNumberFactCandidate(
            value=1350, page_number=2, quote="entre 980 € et 1 350 €"
        ),
        surface=DpeNumberFactCandidate(
            value=67.4, page_number=1, quote="Surface de référence 67,4 m²"
        ),
        heating_type=null_text(),
        hot_water_type=null_text(),
        dpe_date=DpeDateFactCandidate(
            value="2024-06-15", page_number=1, quote="DPE établi le 15/06/2024"
        ),
        dpe_valid_until=null_date(),
        recommendations=[],
    )


@contextmanager
def make_client(session: Session, llm_client: FakeStructuredOutputClient) -> Iterator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_structured_output_client] = lambda: llm_client
    with TestClient(application) as client:
        yield client


def auth(user_id: UUID) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


def test_low_confidence_classification_is_persisted_as_unknown(session: Session) -> None:
    user_id = uuid4()
    case_id, document_id = seed_extracted_dpe(session, user_id)
    llm_client = FakeStructuredOutputClient([classification_candidate(confidence=0.42)])

    with make_client(session, llm_client) as client:
        response = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/classify",
            headers=auth(user_id),
        )

    assert response.status_code == 200
    assert response.json()["document_type"] == "unknown"
    assert response.json()["extraction_strategy"] == "none"
    assert response.json()["requested_model"] == "gpt-5.6-luna"
    persisted = session.scalar(select(DocumentClassificationRecord))
    assert persisted is not None
    assert persisted.raw_output["document_type"] == "dpe"


def test_dpe_extraction_persists_normalized_facts_with_page_sources(session: Session) -> None:
    user_id = uuid4()
    case_id, document_id = seed_extracted_dpe(session, user_id)
    llm_client = FakeStructuredOutputClient([classification_candidate(), dpe_candidate()])

    with make_client(session, llm_client) as client:
        classify_response = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/classify",
            headers=auth(user_id),
        )
        response = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-dpe",
            headers=auth(user_id),
        )
        read_response = client.get(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/dpe-extraction",
            headers=auth(user_id),
        )

    assert classify_response.status_code == 200
    assert response.status_code == 200
    assert read_response.status_code == 200
    assert read_response.json()["id"] == response.json()["id"]
    facts = response.json()["normalized_facts"]
    assert facts["dpe_rating"]["value"] == "D"
    assert facts["dpe_rating"]["source"] == {
        "document_id": str(document_id),
        "page_number": 1,
        "quote": "Classe énergie D",
    }
    assert facts["estimated_annual_energy_cost_max"]["value"] == 1350
    assert facts["estimated_annual_energy_cost_max"]["source"]["page_number"] == 2
    assert facts["heating_type"] == {"value": None, "source": None}
    assert facts["dpe_date"]["value"] == "2024-06-15"

    record = session.scalar(select(DpeExtractionRecord))
    document = session.get(DocumentRecord, document_id)
    assert record is not None and record.requested_model == "gpt-5.6-luna"
    assert document is not None and document.status == DocumentStatus.COMPLETED.value


def test_analysis_endpoints_are_idempotent(
    session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    user_id = uuid4()
    case_id, document_id = seed_extracted_dpe(session, user_id)
    llm_client = FakeStructuredOutputClient([classification_candidate(), dpe_candidate()])

    caplog.set_level("INFO", logger="uvicorn.error")
    with make_client(session, llm_client) as client:
        classify_url = f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/classify"
        dpe_url = f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-dpe"
        first_classification = client.post(classify_url, headers=auth(user_id))
        second_classification = client.post(classify_url, headers=auth(user_id))
        first_dpe = client.post(dpe_url, headers=auth(user_id))
        second_dpe = client.post(dpe_url, headers=auth(user_id))

    assert first_classification.json()["id"] == second_classification.json()["id"]
    assert first_dpe.json()["id"] == second_dpe.json()["id"]
    assert llm_client.calls == 2
    assert "DPE extraction reused" in caplog.text
    assert "api_call=false" in caplog.text


def test_list_documents_exposes_verified_ademe_status(session: Session) -> None:
    user_id = uuid4()
    case_id, document_id = seed_extracted_dpe(session, user_id)
    llm_client = FakeStructuredOutputClient([classification_candidate(), dpe_candidate()])

    with make_client(session, llm_client) as client:
        client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/classify",
            headers=auth(user_id),
        )
        client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-dpe",
            headers=auth(user_id),
        )

        record = session.scalar(select(DpeExtractionRecord))
        assert record is not None
        normalized_facts = dict(record.normalized_facts)
        normalized_facts["ademe_verification"] = {
            **dict(normalized_facts["ademe_verification"]),
            "status": "verified",
        }
        record.normalized_facts = normalized_facts
        session.commit()

        response = client.get(
            f"/api/v1/analysis-cases/{case_id}/documents",
            headers=auth(user_id),
        )

    assert response.status_code == 200
    assert response.json()[0]["ademe_verification_status"] == "verified"


def test_dpe_extraction_rejects_non_dpe_classification(session: Session) -> None:
    user_id = uuid4()
    case_id, document_id = seed_extracted_dpe(session, user_id)
    candidate = classification_candidate()
    candidate.document_type = DocumentType.AG_MINUTES
    llm_client = FakeStructuredOutputClient([candidate])

    with make_client(session, llm_client) as client:
        client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/classify",
            headers=auth(user_id),
        )
        response = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/extract-dpe",
            headers=auth(user_id),
        )

    assert response.status_code == 409
    assert session.scalar(select(DpeExtractionRecord)) is None


def test_analysis_enforces_ownership_before_calling_the_model(session: Session) -> None:
    owner_id = uuid4()
    case_id, document_id = seed_extracted_dpe(session, owner_id)
    llm_client = FakeStructuredOutputClient([classification_candidate()])

    with make_client(session, llm_client) as client:
        response = client.post(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/classify",
            headers=auth(uuid4()),
        )

    assert response.status_code == 404
    assert llm_client.calls == 0


def test_dpe_extraction_read_enforces_ownership(session: Session) -> None:
    owner_id = uuid4()
    case_id, document_id = seed_extracted_dpe(session, owner_id)
    llm_client = FakeStructuredOutputClient([])

    with make_client(session, llm_client) as client:
        response = client.get(
            f"/api/v1/analysis-cases/{case_id}/documents/{document_id}/dpe-extraction",
            headers=auth(uuid4()),
        )

    assert response.status_code == 404
