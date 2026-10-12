import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import stripe
from fastapi import HTTPException
from pydantic import SecretStr

from app.billing.catalog import OFFERS
from app.billing.models import BillingOfferCode
from app.billing.stripe_gateway import StripeSdkGateway, get_stripe_gateway
from app.core.config import get_settings
from scripts.configure_stripe_production import validate_price


def test_checkout_uses_supported_hosted_mode_and_preserves_fixed_eur_pricing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    client.v1.checkout.sessions.create.return_value = SimpleNamespace(
        id="cs_test_example", url="https://checkout.stripe.test/example"
    )
    monkeypatch.setattr(stripe, "StripeClient", lambda *args, **kwargs: client)
    gateway = StripeSdkGateway("rk_test_placeholder", "whsec_placeholder")
    purchase_id = uuid4()
    gateway.create_checkout_session(
        purchase_id=purchase_id,
        user_id=uuid4(),
        customer_email=None,
        offer=OFFERS[BillingOfferCode.SINGLE_ANALYSIS],
        price_id="price_example",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )
    params, options = client.v1.checkout.sessions.create.call_args.args
    assert params["ui_mode"] == "hosted_page"
    assert params["managed_payments"] == {"enabled": False}
    assert params["adaptive_pricing"] == {"enabled": False}
    assert params["client_reference_id"] == str(purchase_id)
    assert options["idempotency_key"] == f"acquora-purchase-{purchase_id}"


@pytest.mark.parametrize(
    ("environment", "key"),
    [("production", "sk_test_wrong"), ("development", "rk_live_wrong")],
)
def test_wrong_mode_key_disables_billing(
    monkeypatch: pytest.MonkeyPatch, environment: str, key: str
) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", environment)
    monkeypatch.setattr(settings, "stripe_secret_key", SecretStr(key))
    monkeypatch.setattr(settings, "stripe_webhook_secret", SecretStr("whsec_test"))
    get_stripe_gateway.cache_clear()
    try:
        with pytest.raises(HTTPException) as raised:
            get_stripe_gateway()
        assert raised.value.status_code == 503
    finally:
        get_stripe_gateway.cache_clear()


@pytest.mark.parametrize("key_mode", ["test", "live"])
@pytest.mark.parametrize("event_is_live", [False, True])
def test_signed_webhook_must_match_key_mode(key_mode: str, event_is_live: bool) -> None:
    gateway = StripeSdkGateway(f"rk_{key_mode}_placeholder", "whsec_placeholder")
    payload = json.dumps(
        {
            "id": "evt_verified",
            "object": "event",
            "type": "checkout.session.completed",
            "livemode": event_is_live,
            "data": {"object": {"id": "cs_example", "payment_status": "paid"}},
        }
    ).encode()
    timestamp = int(time.time())
    signature = hmac.new(
        b"whsec_placeholder", str(timestamp).encode() + b"." + payload, hashlib.sha256
    ).hexdigest()
    header = f"t={timestamp},v1={signature}"
    if event_is_live != (key_mode == "live"):
        with pytest.raises(ValueError, match="mode does not match"):
            gateway.construct_webhook_event(payload, header)
    else:
        assert gateway.construct_webhook_event(payload, header).id == "evt_verified"


def test_tampered_webhook_is_rejected_before_mode_checks() -> None:
    gateway = StripeSdkGateway("rk_live_placeholder", "whsec_placeholder")
    with pytest.raises(stripe.SignatureVerificationError):
        gateway.construct_webhook_event(b"{}", f"t={int(time.time())},v1=invalid")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("livemode", False),
        ("active", False),
        ("type", "recurring"),
        ("currency", "usd"),
        ("unit_amount", 190),
    ],
)
def test_production_setup_rejects_an_incompatible_price(field: str, value: object) -> None:
    data = {
        "id": "price_example",
        "livemode": True,
        "active": True,
        "type": "one_time",
        "currency": "eur",
        "unit_amount": 1900,
    }
    offer = OFFERS[BillingOfferCode.SINGLE_ANALYSIS]
    validate_price(stripe.Price.construct_from(data, None), offer)
    data[field] = value
    with pytest.raises(ValueError, match="does not match offer"):
        validate_price(stripe.Price.construct_from(data, None), offer)
