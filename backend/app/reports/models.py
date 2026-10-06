from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import JSON, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.risks.models import (
    TECHNICAL_FINDING_CODES,
    DocumentExpectation,
    FindingReviewStatus,
    FindingStatus,
    MissingDocumentReason,
    RiskSeverity,
)


class AnalysisFindingType(StrEnum):
    RISK = "risk"
    VERIFICATION = "verification"
    REASSURING = "reassuring"
    MISSING_INFORMATION = "missing_information"


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
    analysis_type: AnalysisFindingType = AnalysisFindingType.RISK
    review_status: FindingReviewStatus = FindingReviewStatus.OPEN
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
    verification_count: int = Field(default=0, ge=0)
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

    def without_technical_findings(self) -> "BuyerReport":
        """Hide technical entries in saved reports without requiring regeneration."""
        removed = [
            finding
            for section in self.sections
            for finding in section.findings
            if finding.code in TECHNICAL_FINDING_CODES
        ]
        if not removed:
            return self
        removed_counts = {
            kind: sum(finding.analysis_type == kind for finding in removed)
            for kind in AnalysisFindingType
        }
        removed_risks = [
            finding for finding in removed if finding.analysis_type == AnalysisFindingType.RISK
        ]
        summary = self.summary.model_copy(
            update={
                "finding_count": max(0, self.summary.finding_count - len(removed)),
                "analyzed_count": max(
                    0,
                    self.summary.analyzed_count
                    - sum(
                        count
                        for kind, count in removed_counts.items()
                        if kind != AnalysisFindingType.MISSING_INFORMATION
                    ),
                ),
                "risk_count": max(
                    0, self.summary.risk_count - removed_counts[AnalysisFindingType.RISK]
                ),
                "verification_count": max(
                    0,
                    self.summary.verification_count
                    - removed_counts[AnalysisFindingType.VERIFICATION],
                ),
                "missing_information_count": max(
                    0,
                    self.summary.missing_information_count
                    - removed_counts[AnalysisFindingType.MISSING_INFORMATION],
                ),
                "reassuring_count": max(
                    0,
                    self.summary.reassuring_count - removed_counts[AnalysisFindingType.REASSURING],
                ),
                "high_or_critical_count": max(
                    0,
                    self.summary.high_or_critical_count
                    - sum(
                        finding.severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL}
                        for finding in removed_risks
                    ),
                ),
                "risk_severity_counts": {
                    severity: max(
                        0, count - sum(finding.severity == severity for finding in removed_risks)
                    )
                    for severity, count in self.summary.risk_severity_counts.items()
                },
            }
        )
        return self.model_copy(
            update={
                "summary": summary,
                "sections": [
                    section.model_copy(
                        update={
                            "findings": [
                                finding
                                for finding in section.findings
                                if finding.code not in TECHNICAL_FINDING_CODES
                            ],
                        }
                    )
                    for section in self.sections
                ],
            }
        )


class BuyerReportPreview(BaseModel):
    analysis_case_id: UUID
    generated_at: datetime
    risk_count: int = Field(ge=0)
    verification_count: int = Field(ge=0)
    missing_information_count: int = Field(ge=0)
    reassuring_count: int = Field(ge=0)


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
        return BuyerReport.model_validate(self.content).without_technical_findings()


def report_generated_at() -> datetime:
    return datetime.now(UTC)
