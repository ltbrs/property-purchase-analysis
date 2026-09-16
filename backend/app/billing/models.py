from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BillingOfferCode(StrEnum):
    SINGLE_ANALYSIS = "single_analysis"
    SEARCH_PACK = "search_pack"


class StripePurchaseStatus(StrEnum):
    PENDING = "pending"
    OPEN = "open"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"


class AnalysisAccessStatus(StrEnum):
    NOT_ACTIVATED = "not_activated"
    ACTIVE = "active"
    EXPIRED = "expired"


class StripePurchaseRecord(Base):
    __tablename__ = "stripe_purchases"
    __table_args__ = (
        CheckConstraint(
            "offer_code IN ('single_analysis', 'search_pack')",
            name="ck_stripe_purchases_offer_code",
        ),
        CheckConstraint(
            "status IN ('pending', 'open', 'paid', 'failed', 'expired')",
            name="ck_stripe_purchases_status",
        ),
        CheckConstraint("expected_amount_cents > 0", name="ck_stripe_purchases_amount_positive"),
        CheckConstraint("credit_count > 0", name="ck_stripe_purchases_credit_count_positive"),
        Index("ix_stripe_purchases_user_created", "user_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    offer_code: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=StripePurchaseStatus.PENDING.value,
        server_default=StripePurchaseStatus.PENDING.value,
        nullable=False,
    )
    expected_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    credit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), unique=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AnalysisCreditRecord(Base):
    __tablename__ = "analysis_credits"
    __table_args__ = (
        Index(
            "ix_analysis_credits_available",
            "user_id",
            "consumed_at",
            "expires_at",
        ),
        Index("ix_analysis_credits_purchase_id", "purchase_id"),
        Index("ix_analysis_credits_consumed_case", "consumed_by_case_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("stripe_purchases.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_by_case_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("analysis_cases.id", ondelete="SET NULL"),
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AnalysisAccessRecord(Base):
    __tablename__ = "analysis_accesses"
    __table_args__ = (
        CheckConstraint("expires_at > activated_at", name="ck_analysis_accesses_valid_window"),
        UniqueConstraint("credit_id", name="uq_analysis_accesses_credit_id"),
    )

    analysis_case_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("analysis_cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    credit_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("analysis_credits.id", ondelete="RESTRICT"),
        nullable=False,
    )
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    report_refresh_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )


class StripeWebhookEventRecord(Base):
    __tablename__ = "stripe_webhook_events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CheckoutSessionCreate(BaseModel):
    offer_code: BillingOfferCode


class CheckoutSessionRead(BaseModel):
    checkout_url: str


class AnalysisAccessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: AnalysisAccessStatus
    activated_at: datetime | None = None
    expires_at: datetime | None = None


class BillingSummaryRead(BaseModel):
    available_analyses: int
    next_credit_expiration: datetime | None = None


class StripeWebhookAccepted(BaseModel):
    received: bool = True
