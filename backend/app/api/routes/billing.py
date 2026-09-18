import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID

import stripe
from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from starlette.concurrency import run_in_threadpool

from app.api.routes.contact import limiter
from app.billing.catalog import OFFERS, stripe_price_id
from app.billing.models import (
    AnalysisAccessRead,
    BillingSummaryRead,
    CheckoutSessionCreate,
    CheckoutSessionRead,
    StripeWebhookAccepted,
)
from app.billing.repository import (
    BillingRepository,
    InvalidStripePayment,
    NoAnalysisCredit,
)
from app.billing.stripe_gateway import StripeGatewayDependency
from app.core.auth import CurrentUserId
from app.core.config import get_settings
from app.core.database import DatabaseSession
from app.property.models import UserRecord

router = APIRouter(prefix="/billing", tags=["billing"])


def _billing_rate_limit_key(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    client = request.client.host if request.client is not None else "unknown"
    material = authorization if authorization else client
    secret = get_settings().backend_proxy_secret
    key = secret.get_secret_value() if secret is not None else "acquora-billing-development"
    return hmac.new(key.encode(), material.encode(), hashlib.sha256).hexdigest()


@router.get("/summary", response_model=BillingSummaryRead)
def get_billing_summary(
    response: Response,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> BillingSummaryRead:
    response.headers["Cache-Control"] = "no-store"
    return BillingRepository(session).billing_summary(current_user_id, datetime.now(UTC))


@router.post("/checkout-sessions", response_model=CheckoutSessionRead)
@limiter.limit("10/hour", key_func=_billing_rate_limit_key)
async def create_checkout_session(
    payload: CheckoutSessionCreate,
    request: Request,
    response: Response,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
    stripe_gateway: StripeGatewayDependency,
) -> CheckoutSessionRead:
    response.headers["Cache-Control"] = "no-store"
    settings = get_settings()
    offer = OFFERS[payload.offer_code]
    price_id = stripe_price_id(settings, payload.offer_code)
    if price_id is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cette offre de paiement n’est pas configurée.",
        )

    repository = BillingRepository(session)
    purchase = repository.create_purchase(current_user_id, offer)
    user = session.get(UserRecord, current_user_id)
    account_url = f"{settings.frontend_origin.rstrip('/')}/app/compte"
    try:
        checkout = await run_in_threadpool(
            stripe_gateway.create_checkout_session,
            purchase_id=purchase.id,
            user_id=current_user_id,
            customer_email=user.email if user is not None and user.email_verified else None,
            offer=offer,
            price_id=price_id,
            success_url=(f"{account_url}?paiement=succes&session_id={{CHECKOUT_SESSION_ID}}"),
            cancel_url=f"{account_url}?paiement=annule",
        )
    except stripe.StripeError as error:
        repository.mark_purchase_failed(purchase)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe n’a pas pu préparer le paiement. Veuillez réessayer.",
        ) from error
    except Exception as error:
        repository.mark_purchase_failed(purchase)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Le paiement n’a pas pu être préparé. Veuillez réessayer.",
        ) from error

    repository.attach_checkout_session(purchase, checkout.id)
    return CheckoutSessionRead(checkout_url=checkout.url)


@router.post(
    "/analysis-cases/{analysis_case_id}/activate",
    response_model=AnalysisAccessRead,
)
def activate_analysis_case(
    analysis_case_id: UUID,
    response: Response,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> AnalysisAccessRead:
    response.headers["Cache-Control"] = "no-store"
    try:
        return BillingRepository(session).activate_case(
            analysis_case_id,
            current_user_id,
            datetime.now(UTC),
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis case not found",
        ) from error
    except NoAnalysisCredit as error:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Aucune analyse disponible. Choisissez une offre pour continuer.",
        ) from error


@router.post("/stripe/webhook", response_model=StripeWebhookAccepted)
async def receive_stripe_webhook(
    request: Request,
    session: DatabaseSession,
    stripe_gateway: StripeGatewayDependency,
    stripe_signature: str | None = Header(default=None),
) -> StripeWebhookAccepted:
    if stripe_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature",
        )
    payload = await request.body()
    try:
        event = stripe_gateway.construct_webhook_event(payload, stripe_signature)
    except (ValueError, stripe.SignatureVerificationError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook",
        ) from error

    if event.type not in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        return StripeWebhookAccepted()
    if event.data_object.get("payment_status") != "paid":
        return StripeWebhookAccepted()

    try:
        BillingRepository(session).fulfill_checkout_session(
            event_id=event.id,
            event_type=event.type,
            checkout_session=event.data_object,
        )
    except InvalidStripePayment as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe payment does not match a purchase",
        ) from error
    return StripeWebhookAccepted()
