import hashlib
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db_session
from app.demo.config import DEMO_DOCUMENT_LOGICAL_IDS
from app.demo.manifest import load_demo_manifest
from app.main import create_app
from app.property.models import (
    AnalysisCaseAccessMode,
    AnalysisCaseKind,
    AnalysisCaseRecord,
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
    manifest_path = (
        Path(__file__).resolve().parents[2] / "docs/demo-dossier-lyon/manifest.json"
    )
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
