from collections.abc import Generator
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.billing.models import (
    AnalysisAccessRecord,
    AnalysisCreditRecord,
    StripePurchaseRecord,
)
from app.billing.stripe_gateway import (
    CreatedCheckoutSession,
    VerifiedStripeEvent,
    get_stripe_gateway,
)
from app.core.config import get_settings
from app.core.database import Base, get_db_session
from app.documents.repository import DocumentRepository
from app.main import create_app
from tests.billing_fixtures import grant_analysis_credit


class FakeStripeGateway:
    def __init__(self) -> None:
        self.purchase_id: UUID | None = None
        self.event: VerifiedStripeEvent | None = None

    def create_checkout_session(self, **kwargs: object) -> CreatedCheckoutSession:
        self.purchase_id = kwargs["purchase_id"]  # type: ignore[assignment]
        assert kwargs["price_id"] == "price_pack"
        assert kwargs["customer_email"] == "buyer@example.com"
        return CreatedCheckoutSession(
            id="cs_test_pack",
            url="https://checkout.stripe.test/cs_test_pack",
        )

    def construct_webhook_event(
        self, payload: bytes, signature: str
    ) -> VerifiedStripeEvent:
        assert payload == b"{}"
        assert signature == "valid-signature"
        if self.event is None:
            raise ValueError("invalid event")
        return self.event


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
def billing_client(
    session: Session,
) -> Generator[tuple[TestClient, FakeStripeGateway]]:
    settings = get_settings()
    original = (
        settings.backend_proxy_secret,
        settings.stripe_secret_key,
        settings.stripe_webhook_secret,
        settings.stripe_single_analysis_price_id,
        settings.stripe_search_pack_price_id,
    )
    settings.backend_proxy_secret = None
    settings.stripe_secret_key = SecretStr("sk_test_secret")
    settings.stripe_webhook_secret = SecretStr("whsec_test")
    settings.stripe_single_analysis_price_id = "price_single"
    settings.stripe_search_pack_price_id = "price_pack"
    gateway = FakeStripeGateway()
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_stripe_gateway] = lambda: gateway
    try:
        with TestClient(application) as client:
            yield client, gateway
    finally:
        (
            settings.backend_proxy_secret,
            settings.stripe_secret_key,
            settings.stripe_webhook_secret,
            settings.stripe_single_analysis_price_id,
            settings.stripe_search_pack_price_id,
        ) = original


def auth(user_id: UUID) -> dict[str, str]:
    return {
        "X-User-Id": str(user_id),
        "X-User-Email": "buyer@example.com",
        "X-User-Email-Verified": "true",
    }


def test_paid_checkout_grants_pack_once_and_activates_one_case(
    billing_client: tuple[TestClient, FakeStripeGateway],
    session: Session,
) -> None:
    client, gateway = billing_client
    user_id = uuid4()
    checkout = client.post(
        "/api/v1/billing/checkout-sessions",
        headers=auth(user_id),
        json={"offer_code": "search_pack"},
    )
    assert checkout.status_code == 200
    assert checkout.json() == {
        "checkout_url": "https://checkout.stripe.test/cs_test_pack"
    }
    assert gateway.purchase_id is not None

    gateway.event = VerifiedStripeEvent(
        id="evt_paid_pack",
        type="checkout.session.completed",
        data_object={
            "id": "cs_test_pack",
            "client_reference_id": str(gateway.purchase_id),
            "amount_total": 3_900,
            "currency": "eur",
            "payment_status": "paid",
            "customer": "cus_test",
            "payment_intent": "pi_test",
        },
    )
    first_webhook = client.post(
        "/api/v1/billing/stripe/webhook",
        headers={"Stripe-Signature": "valid-signature"},
        content=b"{}",
    )
    duplicate_webhook = client.post(
        "/api/v1/billing/stripe/webhook",
        headers={"Stripe-Signature": "valid-signature"},
        content=b"{}",
    )
    summary = client.get("/api/v1/billing/summary", headers=auth(user_id))
    created_case = client.post(
        "/api/v1/analysis-cases",
        headers=auth(user_id),
        json={"title": "Appartement test"},
    )
    activation = client.post(
        f"/api/v1/billing/analysis-cases/{created_case.json()['id']}/activate",
        headers=auth(user_id),
    )
    second_activation = client.post(
        f"/api/v1/billing/analysis-cases/{created_case.json()['id']}/activate",
        headers=auth(user_id),
    )

    assert first_webhook.status_code == 200
    assert duplicate_webhook.status_code == 200
    assert summary.json()["available_analyses"] == 3
    assert activation.status_code == 200
    assert activation.json()["status"] == "active"
    assert second_activation.json() == activation.json()
    assert session.scalar(select(func.count()).select_from(AnalysisCreditRecord)) == 3
    assert (
        session.scalar(
            select(func.count())
            .select_from(AnalysisCreditRecord)
            .where(AnalysisCreditRecord.consumed_at.is_not(None))
        )
        == 1
    )
    access = session.scalar(select(AnalysisAccessRecord))
    assert access is not None
    assert access.expires_at - access.activated_at == timedelta(days=30)
    purchase = session.scalar(select(StripePurchaseRecord))
    assert purchase is not None and purchase.status == "paid"


def test_activation_requires_an_available_credit(
    billing_client: tuple[TestClient, FakeStripeGateway],
    session: Session,
) -> None:
    client, _gateway = billing_client
    user_id = uuid4()
    rejected_creation = client.post(
        "/api/v1/analysis-cases",
        headers=auth(user_id),
        json={"title": "Maison test"},
    )
    analysis_case = DocumentRepository(session).create_analysis_case(user_id, "Maison test")

    response = client.post(
        f"/api/v1/billing/analysis-cases/{analysis_case.id}/activate",
        headers=auth(user_id),
    )

    assert rejected_creation.status_code == 402
    assert response.status_code == 402
    assert "Aucune analyse disponible" in response.json()["detail"]


def test_manual_credit_can_activate_a_case_without_a_fake_stripe_purchase(
    billing_client: tuple[TestClient, FakeStripeGateway],
    session: Session,
) -> None:
    client, _gateway = billing_client
    user_id = uuid4()
    grant_analysis_credit(session, user_id)
    created_case = client.post(
        "/api/v1/analysis-cases",
        headers=auth(user_id),
        json={"title": "Dossier bêta"},
    )

    summary = client.get("/api/v1/billing/summary", headers=auth(user_id))
    activation = client.post(
        f"/api/v1/billing/analysis-cases/{created_case.json()['id']}/activate",
        headers=auth(user_id),
    )

    assert summary.status_code == 200
    assert summary.json()["available_analyses"] == 1
    assert activation.status_code == 200
    assert activation.json()["status"] == "active"
    assert session.scalar(select(func.count()).select_from(StripePurchaseRecord)) == 0


def test_existing_cases_remain_readable_without_an_available_credit(
    billing_client: tuple[TestClient, FakeStripeGateway],
    session: Session,
) -> None:
    client, _gateway = billing_client
    user_id = uuid4()
    grant_analysis_credit(session, user_id)
    created = client.post(
        "/api/v1/analysis-cases",
        headers=auth(user_id),
        json={"title": "Dossier existant"},
    )
    activation = client.post(
        f"/api/v1/billing/analysis-cases/{created.json()['id']}/activate",
        headers=auth(user_id),
    )

    summary = client.get("/api/v1/billing/summary", headers=auth(user_id))
    listed = client.get("/api/v1/analysis-cases", headers=auth(user_id))
    opened = client.get(
        f"/api/v1/analysis-cases/{created.json()['id']}",
        headers=auth(user_id),
    )

    assert activation.status_code == 200
    assert summary.json()["available_analyses"] == 0
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]
    assert opened.status_code == 200


def test_webhook_rejects_an_invalid_signature(
    billing_client: tuple[TestClient, FakeStripeGateway],
) -> None:
    client, _gateway = billing_client

    response = client.post(
        "/api/v1/billing/stripe/webhook",
        headers={"Stripe-Signature": "valid-signature"},
        content=b"{}",
    )

    assert response.status_code == 400
