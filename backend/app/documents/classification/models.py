from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import JSON, CheckConstraint, Date, DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentType(StrEnum):
    DPE = "dpe"
    AG_MINUTES = "ag_minutes"
    DIAGNOSTICS = "diagnostics"
    COPRO_FINANCIALS = "copro_financials"
    CHARGES = "charges"
    WORKS_CALL = "works_call"
    PROPERTY_TAX = "property_tax"
    COPRO_RULES = "copro_rules"
    MAINTENANCE_LOG = "maintenance_log"
    RISK_STATEMENT = "risk_statement"
    UNKNOWN = "unknown"


class ExtractionStrategy(StrEnum):
    TEXT = "text"
    TABLES = "tables"
    MIXED = "mixed"
    VISION_FALLBACK = "vision_fallback"
    NONE = "none"


class DocumentClassificationCandidate(BaseModel):
    """Strict schema returned by the model before deterministic normalization."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    confidence: float = Field(ge=0, le=1)
    document_date: date | None
    covered_period_start: date | None
    covered_period_end: date | None
    issuer: str | None
    extraction_strategy: ExtractionStrategy | None

    @field_validator("issuer")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized[:500] or None

    @model_validator(mode="after")
    def validate_period(self) -> "DocumentClassificationCandidate":
        if (
            self.covered_period_start is not None
            and self.covered_period_end is not None
            and self.covered_period_start > self.covered_period_end
        ):
            raise ValueError("covered period start must not be after its end")
        return self


class DocumentClassificationRecord(Base):
    __tablename__ = "document_classifications"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_classification_confidence",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    document_date: Mapped[date | None] = mapped_column(Date)
    covered_period_start: Mapped[date | None] = mapped_column(Date)
    covered_period_end: Mapped[date | None] = mapped_column(Date)
    issuer: Mapped[str | None] = mapped_column(String(500))
    extraction_strategy: Mapped[str | None] = mapped_column(String(50))
    requested_model: Mapped[str] = mapped_column(String(100), nullable=False)
    resolved_model: Mapped[str] = mapped_column(String(100), nullable=False)
    response_id: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_output: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DocumentClassificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    document_type: DocumentType
    confidence: float
    document_date: date | None
    covered_period_start: date | None
    covered_period_end: date | None
    issuer: str | None
    extraction_strategy: ExtractionStrategy | None
    requested_model: str
    resolved_model: str
    prompt_version: str
    created_at: datetime
