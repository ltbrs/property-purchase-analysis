from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import JSON, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.risks.models import (
    DocumentExpectation,
    FindingStatus,
    MissingDocumentReason,
    RiskSeverity,
)


class ReportSectionCode(StrEnum):
    FINANCIAL = "financial"
    BUILDING_COPROPERTY = "building_coproperty"
    ENERGY = "energy"
    DIAGNOSTICS_SAFETY = "diagnostics_safety"
    INCONSISTENCIES = "inconsistencies"
    MISSING_INFORMATION = "missing_information"
    REASSURING = "reassuring"


class ReportSource(BaseModel):
    document_id: UUID
    document_name: str
    page_number: int = Field(gt=0)
    quote: str | None = None


class ReportFinding(BaseModel):
    code: str
    finding_key: str
    severity: RiskSeverity
    title: str
    explanation: str
    status: FindingStatus
    confidence: float | None = None
    amount_eur: Decimal | None = None
    expectation_level: DocumentExpectation | None = None
    missing_reason: MissingDocumentReason | None = None
    sources: list[ReportSource] = Field(default_factory=list)


class ReportSection(BaseModel):
    code: ReportSectionCode
    title: str
    findings: list[ReportFinding]


class ReportSummary(BaseModel):
    finding_count: int = Field(ge=0)
    analyzed_count: int = Field(ge=0)
    risk_count: int = Field(ge=0)
    high_or_critical_count: int = Field(ge=0)
    missing_information_count: int = Field(ge=0)
    reassuring_count: int = Field(ge=0)
    risk_severity_counts: dict[RiskSeverity, int]


class BuyerReport(BaseModel):
    analysis_case_id: UUID
    title: str
    generated_at: datetime
    summary: ReportSummary
    sections: list[ReportSection]
    disclaimer: str


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    analysis_case_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("analysis_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    content: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def update_from_report(self, report: BuyerReport) -> None:
        self.content = report.model_dump(mode="json")
        self.generated_at = report.generated_at

    @classmethod
    def from_report(cls, report: BuyerReport) -> "ReportRecord":
        record = cls(analysis_case_id=report.analysis_case_id)
        record.update_from_report(report)
        return record

    def to_report(self) -> BuyerReport:
        return BuyerReport.model_validate(self.content)


def report_generated_at() -> datetime:
    return datetime.now(UTC)
