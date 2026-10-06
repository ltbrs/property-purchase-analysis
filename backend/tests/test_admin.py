from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.billing.models import AnalysisCreditRecord
from app.core.database import Base, get_db_session
from app.main import create_app
from app.property.models import UserRecord


@pytest.fixture
def admin_client() -> Generator[tuple[TestClient, Session]]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        application = create_app()
        application.dependency_overrides[get_db_session] = lambda: session
        with TestClient(application) as client:
            yield client, session
    Base.metadata.drop_all(engine)


def auth(user_id: UUID, email: str) -> dict[str, str]:
    return {
        "X-User-Id": str(user_id),
        "X-User-Email": email,
        "X-User-Email-Verified": "true",
    }


def test_only_database_promoted_owner_can_access_admin_routes(
    admin_client: tuple[TestClient, Session],
) -> None:
    client, session = admin_client
    owner_id = uuid4()
    friend_id = uuid4()
    owner_auth = auth(owner_id, "lambertbruyas@gmail.com")
    friend_auth = auth(friend_id, "friend@example.com")

    assert client.get("/api/v1/admin/me", headers=owner_auth).status_code == 404
    assert client.get("/api/v1/admin/users", headers=friend_auth).status_code == 404
    assert (
        client.post(
            f"/api/v1/admin/users/{friend_id}/credits",
            headers=friend_auth,
            json={"count": 1, "reason": "Friend test"},
        ).status_code
        == 404
    )

    owner = session.get(UserRecord, owner_id)
    assert owner is not None
    owner.is_admin = True
    session.commit()
    assert client.get("/api/v1/admin/me", headers=owner_auth).json() == {"is_admin": True}

    friend = session.get(UserRecord, friend_id)
    assert friend is not None
    friend.is_admin = True
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_admin_lists_users_and_grants_traceable_credits(
    admin_client: tuple[TestClient, Session],
) -> None:
    client, session = admin_client
    owner_id = uuid4()
    friend_id = uuid4()
    owner_auth = auth(owner_id, "lambertbruyas@gmail.com")
    friend_auth = auth(friend_id, "friend@example.com")
    client.get("/api/v1/billing/summary", headers=owner_auth)
    client.get("/api/v1/billing/summary", headers=friend_auth)
    owner = session.get(UserRecord, owner_id)
    assert owner is not None
    owner.is_admin = True
    session.commit()

    result = client.get("/api/v1/admin/users?search=friend", headers=owner_auth)
    assert result.status_code == 200
    assert result.headers["cache-control"] == "no-store"
    assert result.json()["total"] == 1
    assert result.json()["users"][0]["available_credits"] == 0

    grant = client.post(
        f"/api/v1/admin/users/{friend_id}/credits",
        headers=owner_auth,
        json={"count": 2, "reason": "Test avec un proche"},
    )
    assert grant.status_code == 200
    assert grant.json() == {"granted": 2, "available_credits": 2}
    credits = session.scalars(
        select(AnalysisCreditRecord).where(AnalysisCreditRecord.user_id == friend_id)
    ).all()
    assert len(credits) == 2
    assert all(c.source == "manual_grant" for c in credits)
    assert all(c.granted_by_user_id == owner_id for c in credits)
    assert all(c.grant_note == "Test avec un proche" for c in credits)
    assert (
        client.get("/api/v1/billing/summary", headers=friend_auth).json()["available_analyses"] == 2
    )
    updated = client.get("/api/v1/admin/users?search=friend", headers=owner_auth).json()
    assert updated["users"][0]["granted_credits"] == 2

    invalid = client.post(
        f"/api/v1/admin/users/{friend_id}/credits",
        headers=owner_auth,
        json={"count": 11, "reason": "Test avec un proche"},
    )
    assert invalid.status_code == 422
    assert (
        client.post(
            f"/api/v1/admin/users/{uuid4()}/credits",
            headers=owner_auth,
            json={"count": 1, "reason": "Test avec un proche"},
        ).status_code
        == 404
    )
