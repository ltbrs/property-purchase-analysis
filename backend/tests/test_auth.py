from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import auth as auth_module
from app.core.config import get_settings
from app.core.database import Base, get_db_session
from app.main import create_app
from app.property.models import UserRecord


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
def supabase_client(
    monkeypatch: pytest.MonkeyPatch,
    session: Session,
) -> Generator[tuple[TestClient, rsa.RSAPrivateKey]]:
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "backend_proxy_secret", SecretStr("proxy-secret"))
    monkeypatch.setattr(settings, "supabase_url", "https://project.supabase.co")
    monkeypatch.setattr(settings, "supabase_jwt_audience", "authenticated")

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    signing_key = SimpleNamespace(key=private_key.public_key())
    jwks_client = SimpleNamespace(get_signing_key_from_jwt=lambda _token: signing_key)
    monkeypatch.setattr(auth_module, "_jwks_client", lambda _url: jwks_client)

    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    with TestClient(application) as client:
        yield client, private_key


def access_token(
    private_key: rsa.RSAPrivateKey,
    *,
    subject: str,
    audience: str = "authenticated",
    role: str = "authenticated",
    is_anonymous: bool = False,
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "aud": audience,
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "iss": "https://project.supabase.co/auth/v1",
            "sub": subject,
            "role": role,
            "is_anonymous": is_anonymous,
            "email": "Lea.Martin@Example.com",
            "user_metadata": {"full_name": "Léa Martin"},
            "app_metadata": {"provider": "google", "providers": ["google"]},
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def request_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Backend-Proxy-Secret": "proxy-secret",
    }


def test_verified_supabase_identity_is_used_as_application_user(
    supabase_client: tuple[TestClient, rsa.RSAPrivateKey],
    session: Session,
) -> None:
    client, private_key = supabase_client
    user_id = uuid4()

    response = client.get(
        "/api/v1/analysis-cases",
        headers=request_headers(access_token(private_key, subject=str(user_id))),
    )

    assert response.status_code == 200
    user = session.get(UserRecord, user_id)
    assert user is not None
    assert user.name == "Léa Martin"
    assert user.email == "lea.martin@example.com"
    assert user.email_verified is True


def test_forged_identity_header_is_rejected_when_supabase_is_configured(
    supabase_client: tuple[TestClient, rsa.RSAPrivateKey],
) -> None:
    client, _private_key = supabase_client

    response = client.get(
        "/api/v1/analysis-cases",
        headers={
            "X-Backend-Proxy-Secret": "proxy-secret",
            "X-User-Id": str(uuid4()),
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("audience", "role", "is_anonymous"),
    [
        ("another-service", "authenticated", False),
        ("authenticated", "service_role", False),
        ("authenticated", "authenticated", True),
    ],
)
def test_invalid_supabase_claims_are_rejected(
    supabase_client: tuple[TestClient, rsa.RSAPrivateKey],
    audience: str,
    role: str,
    is_anonymous: bool,
) -> None:
    client, private_key = supabase_client
    token = access_token(
        private_key,
        subject=str(uuid4()),
        audience=audience,
        role=role,
        is_anonymous=is_anonymous,
    )

    response = client.get("/api/v1/analysis-cases", headers=request_headers(token))

    assert response.status_code == 401
