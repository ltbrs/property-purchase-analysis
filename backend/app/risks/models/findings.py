from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.property.normalization.dpe import SourceReference


class RiskCategory(StrEnum):
    ENERGY = "energy"
    COPROPERTY = "coproperty"
    FINANCIAL = "financial"
    DIAGNOSTICS = "diagnostics"
    CONSISTENCY = "consistency"


class RiskSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(StrEnum):
    CONFIRMED = "confirmed"
    LIKELY = "likely"
    POSSIBLE = "possible"
    MISSING_INFORMATION = "missing_information"


class RiskFinding(BaseModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    finding_key: str = Field(min_length=1, max_length=300)
    category: RiskCategory
    title: str = Field(min_length=1, max_length=200)
    severity: RiskSeverity
    description: str = Field(min_length=1, max_length=2000)
    status: FindingStatus
    confidence: float | None = Field(default=None, ge=0, le=1)
    amount_eur: Decimal | None = Field(default=None, ge=0)
    sources: list[SourceReference] = Field(default_factory=list)


class RiskFindingRecord(Base):
    __tablename__ = "risk_findings"
    __table_args__ = (
        UniqueConstraint("analysis_case_id", "finding_key", name="uq_risk_findings_case_key"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_risk_findings_confidence",
        ),
        CheckConstraint("amount_eur IS NULL OR amount_eur >= 0", name="ck_risk_amount_nonnegative"),
        CheckConstraint(
            "category IN ('energy', 'coproperty', 'financial', 'diagnostics', 'consistency')",
            name="ck_risk_findings_category",
        ),
        CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high', 'critical')",
            name="ck_risk_findings_severity",
        ),
        CheckConstraint(
            "status IN ('confirmed', 'likely', 'possible', 'missing_information')",
            name="ck_risk_findings_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    analysis_case_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("analysis_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    finding_key: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    amount_eur: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    sources: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    @classmethod
    def from_finding(cls, *, analysis_case_id: UUID, finding: RiskFinding) -> "RiskFindingRecord":
        return cls(
            analysis_case_id=analysis_case_id,
            code=finding.code,
            finding_key=finding.finding_key,
            category=finding.category.value,
            title=finding.title,
            severity=finding.severity.value,
            description=finding.description,
            status=finding.status.value,
            confidence=finding.confidence,
            amount_eur=finding.amount_eur,
            sources=[source.model_dump(mode="json") for source in finding.sources],
        )


class RiskFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_case_id: UUID
    code: str
    finding_key: str
    category: RiskCategory
    title: str
    severity: RiskSeverity
    description: str
    status: FindingStatus
    confidence: float | None
    amount_eur: Decimal | None
    sources: list[SourceReference]
    created_at: datetime
