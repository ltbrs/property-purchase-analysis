import re
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, StrictBool, field_validator
from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ContactSubject(StrEnum):
    PRODUCT = "product"
    ANALYSIS = "analysis"
    PRICING = "pricing"
    PRIVACY = "privacy"
    TECHNICAL = "technical"
    PARTNERSHIP = "partnership"
    OTHER = "other"


class ContactSubmissionStatus(StrEnum):
    NEW = "new"
    ARCHIVED = "archived"


class ContactSubmissionRecord(Base):
    __tablename__ = "contact_submissions"
    __table_args__ = (
        CheckConstraint(
            "subject IN ('product', 'analysis', 'pricing', 'privacy', 'technical', "
            "'partnership', 'other')",
            name="ck_contact_submissions_subject",
        ),
        CheckConstraint(
            "status IN ('new', 'archived')",
            name="ck_contact_submissions_status",
        ),
        Index("ix_contact_submissions_status_created_at", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    subject: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ContactSubmissionStatus.NEW.value,
        server_default=ContactSubmissionStatus.NEW.value,
        nullable=False,
    )
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    privacy_consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactSubmissionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    subject: ContactSubject
    message: str = Field(min_length=20, max_length=4000)
    privacy_consent: StrictBool
    website: str = Field(default="", max_length=200)

    @field_validator("name", "message", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        email = value.strip().casefold()
        if not EMAIL_PATTERN.fullmatch(email):
            raise ValueError("invalid email address")
        return email

    @field_validator("privacy_consent")
    @classmethod
    def require_privacy_consent(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("privacy consent is required")
        return value


class ContactSubmissionAccepted(BaseModel):
    accepted: bool = True
