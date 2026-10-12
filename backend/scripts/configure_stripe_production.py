"""Inspect or provision Acquora's live prices and Vercel billing configuration.

Run from backend: uv run python -m scripts.configure_stripe_production [--apply]
The default is read-only. Secrets are sent to Vercel through stdin, never printed.
"""

import argparse
import os
import shutil
import subprocess

import stripe
from dotenv import dotenv_values

from app.billing.catalog import OFFERS, BillingOffer
from app.billing.models import BillingOfferCode
from app.core.config import REPOSITORY_ROOT

WEBHOOK_EVENTS = ["checkout.session.completed", "checkout.session.async_payment_succeeded"]
WEBHOOK_URL = "https://acquora-api-acquora.vercel.app/api/v1/billing/stripe/webhook"
PRICE_VARIABLES = {
    BillingOfferCode.SINGLE_ANALYSIS: "STRIPE_SINGLE_ANALYSIS_PRICE_ID",
    BillingOfferCode.SEARCH_PACK: "STRIPE_SEARCH_PACK_PRICE_ID",
}
PRODUCT_NAMES = {
    BillingOfferCode.SINGLE_ANALYSIS: "Acquora : une analyse immobilière",
    BillingOfferCode.SEARCH_PACK: "Acquora : pack de trois analyses immobilières",
}


def validate_price(price: stripe.Price, offer: BillingOffer) -> None:
    if (
        not price.livemode
        or not price.active
        or price.type != "one_time"
        or price.currency != offer.currency
        or price.unit_amount != offer.amount_cents
    ):
        raise ValueError(f"Live price {price.id} does not match offer {offer.code.value}")


def set_vercel_variable(name: str, value: str, *, sensitive: bool = False) -> None:
    command = [
        "vercel",
        "env",
        "add",
        name,
        "production",
        "--force",
        "--yes",
        "--scope",
        "acquora",
        "--cwd",
        str(REPOSITORY_ROOT / "backend"),
    ]
    if sensitive:
        command.append("--sensitive")
    result = subprocess.run(command, input=value, text=True, capture_output=True, timeout=60)
    if result.returncode:
        # Do not print CLI output: it could contain an echoed value.
        raise RuntimeError(f"Vercel could not save {name}; check CLI authentication/permissions")
    print(f"Configured {name} in acquora-api Production")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Create missing live resources and env vars"
    )
    args = parser.parse_args()
    local = dotenv_values(REPOSITORY_ROOT / ".env")
    key = os.environ.get("STRIPE_LIVE_SECRET_KEY") or local.get("STRIPE_LIVE_SECRET_KEY")
    if not key or not key.startswith(("sk_live_", "rk_live_")):
        parser.error("Add a live key as STRIPE_LIVE_SECRET_KEY in the ignored root .env")
    if args.apply and shutil.which("vercel") is None:
        parser.error("Install and authenticate the Vercel CLI before applying configuration")
    client = stripe.StripeClient(key, max_network_retries=2)
    account = client.v1.accounts.retrieve_current()
    print(f"Live Stripe account: {account.id}")
    print(f"Charges enabled: {account.charges_enabled}; payouts enabled: {account.payouts_enabled}")
    if not account.charges_enabled:
        raise RuntimeError(
            "Complete Stripe account activation before configuring production payments"
        )

    prices: dict[str, str] = {}
    for code, offer in OFFERS.items():
        lookup_key = f"acquora_{code.value}"
        matches = client.v1.prices.list({"lookup_keys": [lookup_key], "limit": 2}).data
        if len(matches) > 1:
            raise ValueError(f"Multiple prices found for {lookup_key}")
        if matches:
            price = matches[0]
        elif args.apply:
            price = client.v1.prices.create(
                {
                    "currency": offer.currency,
                    "unit_amount": offer.amount_cents,
                    "lookup_key": lookup_key,
                    "tax_behavior": "inclusive",
                    "product_data": {
                        "name": PRODUCT_NAMES[code],
                        "metadata": {"application": "acquora", "offer_code": code.value},
                    },
                },
                {"idempotency_key": f"acquora-live-price-{code.value}-{offer.amount_cents}"},
            )
        else:
            print(f"Missing: {lookup_key}, {offer.amount_cents / 100:.2f} EUR")
            continue
        validate_price(price, offer)
        prices[PRICE_VARIABLES[code]] = price.id
        print(f"{code.value}: {price.id}, {offer.amount_cents / 100:.2f} EUR")

    endpoints = [
        endpoint
        for endpoint in client.v1.webhook_endpoints.list({"limit": 100}).auto_paging_iter()
        if endpoint.url == WEBHOOK_URL
    ]
    if len(endpoints) > 1:
        raise ValueError("Multiple live webhooks target Acquora; resolve the duplicates first")
    signing_secret = os.environ.get("STRIPE_LIVE_WEBHOOK_SECRET") or local.get(
        "STRIPE_LIVE_WEBHOOK_SECRET"
    )
    if endpoints:
        endpoint = endpoints[0]
        if not endpoint.livemode or endpoint.status != "enabled":
            raise ValueError("The production webhook is not an enabled live endpoint")
        if not set(WEBHOOK_EVENTS).issubset(endpoint.enabled_events) and "*" not in (
            endpoint.enabled_events
        ):
            raise ValueError("The existing webhook does not subscribe to both Checkout events")
        print(f"Webhook: {endpoint.id}, {endpoint.url}")
        if args.apply and not signing_secret:
            raise ValueError(
                "Existing webhook: add its signing secret as STRIPE_LIVE_WEBHOOK_SECRET in .env "
                "before --apply. Stripe only returns this secret when an endpoint is created."
            )
    elif args.apply:
        endpoint = client.v1.webhook_endpoints.create(
            {
                "url": WEBHOOK_URL,
                "enabled_events": [
                    "checkout.session.completed",
                    "checkout.session.async_payment_succeeded",
                ],
                "api_version": "2026-08-26.dahlia",
                "description": "Acquora production analysis credits",
            },
        )
        signing_secret = endpoint.secret
        if signing_secret is None:
            raise RuntimeError("Stripe did not return the new endpoint's signing secret")
        # Save immediately: Stripe does not return it on subsequent retrievals.
        set_vercel_variable("STRIPE_WEBHOOK_SECRET", signing_secret, sensitive=True)
        print(f"Created webhook: {endpoint.id}, {endpoint.url}")
    else:
        print(f"Missing webhook: {WEBHOOK_URL}")

    if not args.apply:
        print("Read-only inspection complete. Use --apply to provision and configure Production.")
        return
    if signing_secret is None or not signing_secret.startswith("whsec_"):
        raise ValueError("A valid live webhook signing secret is required")
    set_vercel_variable("STRIPE_WEBHOOK_SECRET", signing_secret, sensitive=True)
    set_vercel_variable("STRIPE_SECRET_KEY", key, sensitive=True)
    for name, value in prices.items():
        set_vercel_variable(name, value)
    print(
        "Redeploy acquora-api Production to activate these variables. "
        "Local test settings are intact."
    )


if __name__ == "__main__":
    try:
        main()
    except stripe.StripeError as error:
        # Stripe errors can include request parameters. Only report the category.
        raise SystemExit(
            f"Stripe setup failed ({type(error).__name__}); check live key permissions"
        ) from None
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error)) from None
