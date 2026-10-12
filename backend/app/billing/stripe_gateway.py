import secrets
import string
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Protocol
from uuid import UUID

import stripe
from fastapi import Depends, HTTPException, status
from stripe.params.checkout import SessionCreateParams

from app.billing.catalog import BillingOffer
from app.core.config import get_settings


@dataclass(frozen=True)
class CreatedCheckoutSession:
    id: str
    url: str


@dataclass(frozen=True)
class VerifiedStripeEvent:
    id: str
    type: str
    data_object: dict[str, object]


class StripeGateway(Protocol):
    def create_checkout_session(
        self,
        *,
        purchase_id: UUID,
        user_id: UUID,
        customer_email: str | None,
        offer: BillingOffer,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> CreatedCheckoutSession: ...

    def construct_webhook_event(self, payload: bytes, signature: str) -> VerifiedStripeEvent: ...


class StripeSdkGateway:
    def __init__(self, secret_key: str, webhook_secret: str) -> None:
        self._client = stripe.StripeClient(secret_key, max_network_retries=2)
        self._webhook_secret = webhook_secret
        self._live_mode = secret_key.startswith(("sk_live_", "rk_live_"))

    def create_checkout_session(
        self,
        *,
        purchase_id: UUID,
        user_id: UUID,
        customer_email: str | None,
        offer: BillingOffer,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> CreatedCheckoutSession:
        params: SessionCreateParams = {
            "mode": "payment",
            "ui_mode": "hosted_page",
            "locale": "fr",
            # Fulfillment requires the advertised EUR total and direct Acquora payments.
            "managed_payments": {"enabled": False},
            "adaptive_pricing": {"enabled": False},
            "integration_identifier": "acquora_"
            + "".join(secrets.choice(string.ascii_lowercase) for _ in range(8)),
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": str(purchase_id),
            "line_items": [{"price": price_id, "quantity": 1}],
            "metadata": {
                "purchase_id": str(purchase_id),
                "user_id": str(user_id),
                "offer_code": offer.code.value,
            },
        }
        if customer_email is not None:
            params["customer_email"] = customer_email
        session = self._client.v1.checkout.sessions.create(
            params,
            {"idempotency_key": f"acquora-purchase-{purchase_id}"},
        )
        if not session.id or not session.url:
            raise RuntimeError("Stripe returned an incomplete Checkout Session")
        return CreatedCheckoutSession(id=session.id, url=session.url)

    def construct_webhook_event(self, payload: bytes, signature: str) -> VerifiedStripeEvent:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            self._webhook_secret,
        )
        if event.livemode != self._live_mode:
            raise ValueError("Stripe webhook mode does not match the configured API key")
        return VerifiedStripeEvent(
            id=event.id,
            type=event.type,
            data_object=event.data.object.to_dict(),
        )


@lru_cache
def get_stripe_gateway() -> StripeSdkGateway:
    settings = get_settings()
    if settings.stripe_secret_key is None or settings.stripe_webhook_secret is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le paiement n’est pas configuré.",
        )
    key = settings.stripe_secret_key.get_secret_value()
    prefixes = (
        ("sk_live_", "rk_live_") if settings.app_env == "production" else ("sk_test_", "rk_test_")
    )
    if not key.startswith(prefixes):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le paiement n’est pas configuré pour cet environnement.",
        )
    return StripeSdkGateway(
        key,
        settings.stripe_webhook_secret.get_secret_value(),
    )


StripeGatewayDependency = Annotated[StripeGateway, Depends(get_stripe_gateway)]
