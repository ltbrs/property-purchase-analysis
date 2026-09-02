from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.contact import limiter
from app.contact.models import ContactSubmissionRecord
from app.core.config import get_settings
from app.core.database import Base, get_db_session
from app.main import create_app


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
    limiter.reset()
    settings = get_settings()
    original_secret = settings.contact_proxy_secret
    settings.contact_proxy_secret = None
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    try:
        with TestClient(application) as test_client:
            yield test_client
    finally:
        settings.contact_proxy_secret = original_secret


def valid_payload() -> dict[str, object]:
    return {
        "name": "  Camille Martin  ",
        "email": "  CAMILLE@example.com ",
        "subject": "analysis",
        "message": "  Je souhaite comprendre les documents nécessaires pour mon achat.  ",
        "privacy_consent": True,
        "website": "",
    }


def test_contact_request_is_validated_normalized_and_persisted(
    client: TestClient, session: Session
) -> None:
    response = client.post("/api/v1/contact", json=valid_payload())

    assert response.status_code == 202
    assert response.json() == {"accepted": True}
    assert response.headers["cache-control"] == "no-store"
    submission = session.scalar(select(ContactSubmissionRecord))
    assert submission is not None
    assert submission.name == "Camille Martin"
    assert submission.email == "camille@example.com"
    assert submission.subject == "analysis"
    assert submission.ip_hash != "testclient"
    assert len(submission.ip_hash) == 64
    assert submission.privacy_consent_at is not None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", " "),
        ("email", "not-an-email"),
        ("subject", "sales"),
        ("message", "Too short"),
        ("privacy_consent", False),
        ("privacy_consent", "true"),
    ],
)
def test_contact_request_rejects_invalid_fields(
    client: TestClient, field: str, value: object
) -> None:
    payload = valid_payload()
    payload[field] = value

    response = client.post("/api/v1/contact", json=payload)

    assert response.status_code == 422


def test_honeypot_returns_success_without_storing_spam(
    client: TestClient, session: Session
) -> None:
    payload = valid_payload()
    payload["website"] = "https://spam.example"

    response = client.post("/api/v1/contact", json=payload)

    assert response.status_code == 202
    assert session.scalar(select(ContactSubmissionRecord)) is None


def test_contact_rate_limit_is_enforced(client: TestClient, session: Session) -> None:
    responses = [client.post("/api/v1/contact", json=valid_payload()) for _ in range(6)]

    assert [response.status_code for response in responses] == [202, 202, 202, 202, 202, 429]
    assert int(responses[-1].headers["retry-after"]) > 0
    assert responses[-1].headers["cache-control"] == "no-store"
    assert len(list(session.scalars(select(ContactSubmissionRecord)))) == 5


def test_configured_contact_boundary_requires_the_shared_proxy_secret(
    client: TestClient,
) -> None:
    settings = get_settings()
    original_secret = settings.contact_proxy_secret
    settings.contact_proxy_secret = SecretStr("shared-contact-secret")
    try:
        forbidden = client.post("/api/v1/contact", json=valid_payload())
        accepted = client.post(
            "/api/v1/contact",
            headers={
                "X-Contact-Proxy-Secret": "shared-contact-secret",
                "X-Contact-Client-Ip": "203.0.113.42",
            },
            json=valid_payload(),
        )
    finally:
        settings.contact_proxy_secret = original_secret

    assert forbidden.status_code == 403
    assert accepted.status_code == 202
