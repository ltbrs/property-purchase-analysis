import hashlib
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db_session
from app.demo.config import DEMO_DOCUMENT_LOGICAL_IDS
from app.demo.manifest import load_demo_manifest
from app.documents.classification.models import DocumentClassificationRecord
from app.documents.models import (
    DocumentExtractionPageRecord,
    DocumentExtractionRecord,
    DocumentRecord,
)
from app.main import create_app
from app.property.models import (
    AnalysisCaseAccessMode,
    AnalysisCaseKind,
    AnalysisCaseRecord,
)
from app.property.normalization.dpe import DpeExtractionRecord
from app.reports.models import BuyerReport, ReportRecord
from app.storage.object_storage import get_object_storage


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
def client(session: Session) -> Generator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    with TestClient(application) as test_client:
        yield test_client


def auth(user_id: UUID) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


def seed_published_demo(
    session: Session,
    *,
    template_key: str = "lyon_v1",
) -> AnalysisCaseRecord:
    analysis_case = AnalysisCaseRecord(
        user_id=None,
        title="24 rue des Tisseurs, 69004 Lyon • Démo",
        property_type="apartment_coproperty",
        price_eur="395000.00",
        surface_m2="64.80",
        lot_count=2,
        access_mode=AnalysisCaseAccessMode.GRANDFATHERED.value,
        case_kind=AnalysisCaseKind.DEMO.value,
        template_key=template_key,
        template_manifest_sha256="a" * 64,
        published_at=datetime.now(UTC),
    )
    session.add(analysis_case)
    session.commit()
    session.refresh(analysis_case)
    return analysis_case


def test_database_allows_only_one_published_demo(session: Session) -> None:
    seed_published_demo(session)

    with pytest.raises(IntegrityError):
        seed_published_demo(session, template_key="lyon_v2")

    session.rollback()


def test_demo_document_configuration_selects_requested_pdf_numbers() -> None:
    manifest_path = Path(__file__).resolve().parents[2] / "docs/demo-dossier-lyon/manifest.json"
    manifest = load_demo_manifest(manifest_path)

    selected = manifest.selected_documents(DEMO_DOCUMENT_LOGICAL_IDS)

    assert [document.filename[:2] for document in selected] == [
        "02",
        "03",
        "04",
        "05",
        "09",
        "11",
        "12",
        "14",
        "15",
    ]
    assert len(manifest.fingerprint(DEMO_DOCUMENT_LOGICAL_IDS)) == 64
    for document in selected:
        content = (manifest_path.parent / document.filename).read_bytes()
        assert content[:1024].find(b"%PDF-") >= 0
        assert len(content) == document.size_bytes
        assert hashlib.sha256(content).hexdigest() == document.sha256


def test_published_demo_is_visible_and_active_for_every_authenticated_user(
    client: TestClient,
    session: Session,
) -> None:
    demo = seed_published_demo(session)

    first = client.get("/api/v1/analysis-cases", headers=auth(uuid4()))
    second = client.get(f"/api/v1/analysis-cases/{demo.id}", headers=auth(uuid4()))

    assert first.status_code == 200
    assert first.json() == [
        {
            "id": str(demo.id),
            "title": demo.title,
            "property_type": "apartment_coproperty",
            "price_eur": "395000.00",
            "surface_m2": "64.80",
            "lot_count": 2,
            "case_kind": "demo",
            "read_only": True,
            "analysis_access_status": "active",
            "analysis_access_activated_at": None,
            "analysis_access_expires_at": None,
            "created_at": first.json()[0]["created_at"],
            "updated_at": first.json()[0]["updated_at"],
        }
    ]
    assert second.status_code == 200
    assert second.json()["id"] == str(demo.id)
    assert second.json()["read_only"] is True


def test_public_report_only_exposes_published_demo(
    client: TestClient,
    session: Session,
) -> None:
    assert client.get("/api/v1/demo/report").status_code == 404
    assert client.get("/api/v1/demo/case").status_code == 404
    assert client.get("/api/v1/demo/documents").status_code == 404

    demo = seed_published_demo(session)
    report = BuyerReport.model_validate(
        {
            "analysis_case_id": str(demo.id),
            "title": demo.title,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "finding_count": 0,
                "analyzed_count": 0,
                "risk_count": 0,
                "verification_count": 0,
                "high_or_critical_count": 0,
                "missing_information_count": 0,
                "reassuring_count": 0,
                "risk_severity_counts": {},
            },
            "sections": [],
            "disclaimer": "Dossier fictif.",
        }
    )
    session.add(ReportRecord.from_report(report))
    session.commit()

    public = client.get("/api/v1/demo/report")
    assert public.status_code == 200
    assert public.json()["analysis_case_id"] == str(demo.id)
    assert public.json()["disclaimer"] == "Dossier fictif."
    public_case = client.get("/api/v1/demo/case")
    assert public_case.status_code == 200
    assert public_case.json()["id"] == str(demo.id)
    assert public_case.json()["read_only"] is True
    assert public_case.json()["analysis_access_status"] == "active"

    demo.published_at = None
    session.commit()
    assert client.get("/api/v1/demo/report").status_code == 404
    assert client.get("/api/v1/demo/case").status_code == 404


def test_public_document_url_is_limited_to_published_demo(
    client: TestClient,
    session: Session,
) -> None:
    demo = seed_published_demo(session)
    document = DocumentRecord(
        analysis_case_id=demo.id,
        original_filename="demo.pdf",
        content_type="application/pdf",
        size_bytes=100,
        sha256="b" * 64,
        storage_bucket="private",
        storage_key="demo-templates/lyon_v1/demo.pdf",
        status="completed",
    )
    session.add(document)
    session.commit()
    extraction = DocumentExtractionRecord(
        document_id=document.id,
        parser_name="xberg",
        duration_ms=25,
        document_metadata={},
        pages=[DocumentExtractionPageRecord(page_number=1, text="Dossier fictif", tables=[])],
    )
    session.add(extraction)
    session.add(
        DocumentClassificationRecord(
            document_id=document.id,
            start_page=1,
            end_page=1,
            document_type="dpe",
            confidence=1,
            requested_model="fixture",
            resolved_model="fixture",
            response_id="fixture",
            prompt_version="test",
            raw_output={},
        )
    )
    null_fact = {"value": None, "source": None}
    session.add(
        DpeExtractionRecord(
            document_id=document.id,
            normalized_facts={
                "dpe_rating": null_fact,
                "ges_rating": null_fact,
                "energy_consumption_kwh_m2_year": null_fact,
                "estimated_annual_energy_cost_min": null_fact,
                "estimated_annual_energy_cost_max": null_fact,
                "surface": null_fact,
                "heating_type": null_fact,
                "hot_water_type": null_fact,
                "dpe_date": null_fact,
                "dpe_valid_until": null_fact,
                "recommendations": [],
            },
            requested_model="fixture",
            resolved_model="fixture",
            response_id="fixture",
            prompt_version="test",
        )
    )
    session.commit()

    class FakeStorage:
        def create_pdf_view_url(self, bucket: str, key: str, expires_in_seconds: int) -> str:
            assert (bucket, key) == ("private", "demo-templates/lyon_v1/demo.pdf")
            return "https://storage.example/signed-demo.pdf"

    assert isinstance(client.app, FastAPI)
    client.app.dependency_overrides[get_object_storage] = lambda: FakeStorage()

    assert client.get(f"/api/v1/demo/documents/{uuid4()}/view-url").status_code == 404
    public = client.get(f"/api/v1/demo/documents/{document.id}/view-url")
    assert public.status_code == 200
    assert public.json()["url"] == "https://storage.example/signed-demo.pdf"
    listed = client.get("/api/v1/demo/documents")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == str(document.id)
    assert listed.json()[0]["original_filename"] == "demo.pdf"
    assert listed.json()[0]["analysis_case_id"] == str(demo.id)
    assert listed.json()[0]["document_types"] == ["dpe"]
    assert listed.json()[0]["ademe_verification_status"] == "not_attempted"
    assert client.get(f"/api/v1/demo/documents/{uuid4()}/extraction").status_code == 404
    assert client.get(f"/api/v1/demo/documents/{uuid4()}/dpe-extraction").status_code == 404
    public_extraction = client.get(f"/api/v1/demo/documents/{document.id}/extraction")
    assert public_extraction.status_code == 200
    assert public_extraction.json()["pages"][0]["text"] == "Dossier fictif"
    public_dpe = client.get(f"/api/v1/demo/documents/{document.id}/dpe-extraction")
    assert public_dpe.status_code == 200
    assert public_dpe.json()["normalized_facts"]["dpe_rating"]["value"] is None

    demo.published_at = None
    session.commit()
    assert client.get(f"/api/v1/demo/documents/{document.id}/view-url").status_code == 404
    assert client.get("/api/v1/demo/documents").status_code == 404
    assert client.get(f"/api/v1/demo/documents/{document.id}/extraction").status_code == 404
    assert client.get(f"/api/v1/demo/documents/{document.id}/dpe-extraction").status_code == 404


def test_demo_visibility_preference_hides_only_the_list_entry(
    client: TestClient,
    session: Session,
) -> None:
    demo = seed_published_demo(session)
    user_id = uuid4()

    defaults = client.get("/api/v1/me/preferences", headers=auth(user_id))
    hidden = client.patch(
        "/api/v1/me/preferences",
        headers=auth(user_id),
        json={"show_demo_case": False},
    )
    listed = client.get("/api/v1/analysis-cases", headers=auth(user_id))
    direct = client.get(f"/api/v1/analysis-cases/{demo.id}", headers=auth(user_id))

    assert defaults.json() == {"show_demo_case": True}
    assert hidden.json() == {"show_demo_case": False}
    assert listed.json() == []
    assert direct.status_code == 200


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("patch", "/api/v1/analysis-cases/{case_id}", {"property_type": "house"}),
        (
            "post",
            "/api/v1/analysis-cases/{case_id}/documents/upload-url",
            {
                "original_filename": "document.pdf",
                "content_type": "application/pdf",
                "size_bytes": 100,
            },
        ),
        ("post", "/api/v1/analysis-cases/{case_id}/findings/refresh", None),
        ("post", "/api/v1/analysis-cases/{case_id}/report/refresh", None),
        ("post", "/api/v1/billing/analysis-cases/{case_id}/activate", None),
    ],
)
def test_demo_mutations_are_rejected(
    client: TestClient,
    session: Session,
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    demo = seed_published_demo(session)
    response = client.request(
        method,
        path.format(case_id=demo.id),
        headers=auth(uuid4()),
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Ce dossier de démonstration est en lecture seule."
