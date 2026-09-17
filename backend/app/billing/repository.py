from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.billing.catalog import OFFERS, BillingOffer
from app.billing.models import (
    AnalysisAccessRead,
    AnalysisAccessRecord,
    AnalysisAccessStatus,
    AnalysisCreditRecord,
    BillingOfferCode,
    BillingSummaryRead,
    StripePurchaseRecord,
    StripePurchaseStatus,
    StripeWebhookEventRecord,
)
from app.property.models import AnalysisCaseRecord

ANALYSIS_ACCESS_DAYS = 30


def _is_after(value: datetime, reference: datetime) -> bool:
    if value.tzinfo is None and reference.tzinfo is not None:
        reference = reference.replace(tzinfo=None)
    return value > reference


class NoAnalysisCredit(RuntimeError):
    """The current user has no unexpired analysis credit to consume."""


class InvalidStripePayment(RuntimeError):
    """A signed Stripe event does not match the server-side purchase record."""


class BillingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_purchase(self, user_id: UUID, offer: BillingOffer) -> StripePurchaseRecord:
        purchase = StripePurchaseRecord(
            user_id=user_id,
            offer_code=offer.code.value,
            expected_amount_cents=offer.amount_cents,
            currency=offer.currency,
            credit_count=offer.credit_count,
        )
        self.session.add(purchase)
        self.session.commit()
        self.session.refresh(purchase)
        return purchase

    def attach_checkout_session(
        self, purchase: StripePurchaseRecord, checkout_session_id: str
    ) -> None:
        purchase.stripe_checkout_session_id = checkout_session_id
        if purchase.status == StripePurchaseStatus.PENDING.value:
            purchase.status = StripePurchaseStatus.OPEN.value
        self.session.commit()

    def mark_purchase_failed(self, purchase: StripePurchaseRecord) -> None:
        purchase.status = StripePurchaseStatus.FAILED.value
        self.session.commit()

    def billing_summary(self, user_id: UUID, now: datetime) -> BillingSummaryRead:
        available_filter = (
            AnalysisCreditRecord.user_id == user_id,
            AnalysisCreditRecord.consumed_at.is_(None),
            or_(
                AnalysisCreditRecord.expires_at.is_(None),
                AnalysisCreditRecord.expires_at > now,
            ),
        )
        available = self.session.scalar(
            select(func.count()).select_from(AnalysisCreditRecord).where(*available_filter)
        )
        next_expiration = self.session.scalar(
            select(func.min(AnalysisCreditRecord.expires_at)).where(
                *available_filter,
                AnalysisCreditRecord.expires_at.is_not(None),
            )
        )
        return BillingSummaryRead(
            available_analyses=int(available or 0),
            next_credit_expiration=next_expiration,
        )

    def has_available_credit(self, user_id: UUID, now: datetime) -> bool:
        credit_id = self.session.scalar(
            select(AnalysisCreditRecord.id)
            .where(
                AnalysisCreditRecord.user_id == user_id,
                AnalysisCreditRecord.consumed_at.is_(None),
                or_(
                    AnalysisCreditRecord.expires_at.is_(None),
                    AnalysisCreditRecord.expires_at > now,
                ),
            )
            .limit(1)
        )
        return credit_id is not None

    def get_case_access(
        self, analysis_case_id: UUID, user_id: UUID, now: datetime
    ) -> AnalysisAccessRead:
        access = self.session.scalar(
            select(AnalysisAccessRecord)
            .join(
                AnalysisCaseRecord,
                AnalysisCaseRecord.id == AnalysisAccessRecord.analysis_case_id,
            )
            .where(
                AnalysisAccessRecord.analysis_case_id == analysis_case_id,
                AnalysisCaseRecord.user_id == user_id,
            )
        )
        return self._access_read(access, now)

    def list_case_accesses(
        self, user_id: UUID, now: datetime
    ) -> dict[UUID, AnalysisAccessRead]:
        accesses = self.session.scalars(
            select(AnalysisAccessRecord)
            .join(
                AnalysisCaseRecord,
                AnalysisCaseRecord.id == AnalysisAccessRecord.analysis_case_id,
            )
            .where(AnalysisCaseRecord.user_id == user_id)
        )
        return {access.analysis_case_id: self._access_read(access, now) for access in accesses}

    @staticmethod
    def _access_read(
        access: AnalysisAccessRecord | None, now: datetime
    ) -> AnalysisAccessRead:
        if access is None:
            return AnalysisAccessRead(status=AnalysisAccessStatus.NOT_ACTIVATED)
        status = (
            AnalysisAccessStatus.ACTIVE
            if _is_after(access.expires_at, now)
            else AnalysisAccessStatus.EXPIRED
        )
        return AnalysisAccessRead(
            status=status,
            activated_at=access.activated_at,
            expires_at=access.expires_at,
        )

    def activate_case(
        self, analysis_case_id: UUID, user_id: UUID, now: datetime
    ) -> AnalysisAccessRead:
        analysis_case = self.session.scalar(
            select(AnalysisCaseRecord)
            .where(
                AnalysisCaseRecord.id == analysis_case_id,
                AnalysisCaseRecord.user_id == user_id,
            )
            .with_for_update()
        )
        if analysis_case is None:
            raise LookupError("Analysis case not found")

        access = self.session.get(AnalysisAccessRecord, analysis_case_id)
        if access is not None and _is_after(access.expires_at, now):
            return self._access_read(access, now)

        credit = self.session.scalar(
            select(AnalysisCreditRecord)
            .where(
                AnalysisCreditRecord.user_id == user_id,
                AnalysisCreditRecord.consumed_at.is_(None),
                or_(
                    AnalysisCreditRecord.expires_at.is_(None),
                    AnalysisCreditRecord.expires_at > now,
                ),
            )
            .order_by(
                case((AnalysisCreditRecord.expires_at.is_(None), 1), else_=0),
                AnalysisCreditRecord.expires_at,
                AnalysisCreditRecord.created_at,
                AnalysisCreditRecord.id,
            )
            .with_for_update()
        )
        if credit is None:
            raise NoAnalysisCredit

        credit.consumed_at = now
        credit.consumed_by_case_id = analysis_case_id
        expires_at = now + timedelta(days=ANALYSIS_ACCESS_DAYS)
        if access is None:
            access = AnalysisAccessRecord(
                analysis_case_id=analysis_case_id,
                credit_id=credit.id,
                activated_at=now,
                expires_at=expires_at,
            )
            self.session.add(access)
        else:
            access.credit_id = credit.id
            access.activated_at = now
            access.expires_at = expires_at
        self.session.commit()
        return self._access_read(access, now)

    def record_report_refresh(self, analysis_case_id: UUID, user_id: UUID) -> None:
        access = self.session.scalar(
            select(AnalysisAccessRecord)
            .join(
                AnalysisCaseRecord,
                AnalysisCaseRecord.id == AnalysisAccessRecord.analysis_case_id,
            )
            .where(
                AnalysisAccessRecord.analysis_case_id == analysis_case_id,
                AnalysisCaseRecord.user_id == user_id,
            )
            .with_for_update()
        )
        if access is None:
            raise LookupError("Analysis access not found")
        access.report_refresh_count += 1
        self.session.commit()

    def report_refresh_count(self, analysis_case_id: UUID, user_id: UUID) -> int:
        count = self.session.scalar(
            select(AnalysisAccessRecord.report_refresh_count)
            .join(
                AnalysisCaseRecord,
                AnalysisCaseRecord.id == AnalysisAccessRecord.analysis_case_id,
            )
            .where(
                AnalysisAccessRecord.analysis_case_id == analysis_case_id,
                AnalysisCaseRecord.user_id == user_id,
            )
        )
        return int(count or 0)

    def fulfill_checkout_session(
        self,
        *,
        event_id: str,
        event_type: str,
        checkout_session: dict[str, object],
        now: datetime | None = None,
    ) -> bool:
        processed_at = now or datetime.now(UTC)
        if self.session.get(StripeWebhookEventRecord, event_id) is not None:
            return False

        reference = checkout_session.get("client_reference_id")
        try:
            purchase_id = UUID(str(reference))
        except (TypeError, ValueError) as error:
            raise InvalidStripePayment("Missing purchase reference") from error

        purchase = self.session.scalar(
            select(StripePurchaseRecord)
            .where(StripePurchaseRecord.id == purchase_id)
            .with_for_update()
        )
        if purchase is None:
            raise InvalidStripePayment("Unknown purchase")
        if self.session.get(StripeWebhookEventRecord, event_id) is not None:
            return False

        session_id = checkout_session.get("id")
        amount_total = checkout_session.get("amount_total")
        currency = checkout_session.get("currency")
        payment_status = checkout_session.get("payment_status")
        if not isinstance(session_id, str) or not session_id:
            raise InvalidStripePayment("Missing Checkout Session identifier")
        if purchase.stripe_checkout_session_id not in (None, session_id):
            raise InvalidStripePayment("Checkout Session mismatch")
        if amount_total != purchase.expected_amount_cents or currency != purchase.currency:
            raise InvalidStripePayment("Payment amount mismatch")
        if payment_status != "paid":
            raise InvalidStripePayment("Checkout Session is not paid")

        purchase.stripe_checkout_session_id = session_id
        if purchase.status != StripePurchaseStatus.PAID.value:
            purchase.status = StripePurchaseStatus.PAID.value
            purchase.completed_at = processed_at
            customer = checkout_session.get("customer")
            payment_intent = checkout_session.get("payment_intent")
            purchase.stripe_customer_id = customer if isinstance(customer, str) else None
            purchase.stripe_payment_intent_id = (
                payment_intent if isinstance(payment_intent, str) else None
            )
            offer_expiration_days = OFFERS[
                BillingOfferCode(purchase.offer_code)
            ].credits_expire_after_days
            expires_at = (
                processed_at + timedelta(days=offer_expiration_days)
                if offer_expiration_days is not None
                else None
            )
            self.session.add_all(
                [
                    AnalysisCreditRecord(
                        user_id=purchase.user_id,
                        purchase_id=purchase.id,
                        expires_at=expires_at,
                    )
                    for _ in range(purchase.credit_count)
                ]
            )

        self.session.add(
            StripeWebhookEventRecord(
                id=event_id,
                event_type=event_type,
                processed_at=processed_at,
            )
        )
        self.session.commit()
        return True
