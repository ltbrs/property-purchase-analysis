from datetime import datetime
from uuid import UUID

from app.property.normalization.diagnostics import (
    DiagnosticKind,
    DiagnosticResult,
    NormalizedDiagnostics,
)
from app.property.normalization.dpe import (
    AdemeVerificationStatus,
    DpeRatingMethod,
    NormalizedDpeFacts,
    SourceReference,
)
from app.reports.models import (
    BuyerReport,
    ReportFinding,
    ReportSection,
    ReportSectionCode,
    ReportSource,
    ReportSummary,
    report_generated_at,
)
from app.risks.models import FindingStatus, RiskCategory, RiskFinding, RiskSeverity

SECTION_TITLES = {
    ReportSectionCode.FINANCIAL: "Risques financiers majeurs",
    ReportSectionCode.BUILDING_COPROPERTY: "Immeuble et copropriété",
    ReportSectionCode.ENERGY: "Énergie",
    ReportSectionCode.DIAGNOSTICS_SAFETY: "Diagnostics et sécurité",
    ReportSectionCode.INCONSISTENCIES: "Incohérences",
    ReportSectionCode.MISSING_INFORMATION: "Informations manquantes",
    ReportSectionCode.REASSURING: "Éléments rassurants",
}
SECTION_ORDER = tuple(ReportSectionCode)


def _report_sources(
    sources: list[SourceReference], document_names: dict[UUID, str]
) -> list[ReportSource]:
    report_sources: list[ReportSource] = []
    seen: set[tuple[UUID, int]] = set()
    for source in sources:
        key = (source.document_id, source.page_number)
        if key in seen:
            continue
        seen.add(key)
        report_sources.append(
            ReportSource(
                document_id=source.document_id,
                document_name=document_names.get(source.document_id, "Document fourni"),
                page_number=source.page_number,
                quote=source.quote,
            )
        )
    return report_sources


def _section_for_finding(finding: RiskFinding) -> ReportSectionCode:
    if (
        finding.category == RiskCategory.MISSING_INFORMATION
        or finding.status == FindingStatus.MISSING_INFORMATION
    ):
        return ReportSectionCode.MISSING_INFORMATION
    return {
        RiskCategory.FINANCIAL: ReportSectionCode.FINANCIAL,
        RiskCategory.COPROPERTY: ReportSectionCode.BUILDING_COPROPERTY,
        RiskCategory.ENERGY: ReportSectionCode.ENERGY,
        RiskCategory.DIAGNOSTICS: ReportSectionCode.DIAGNOSTICS_SAFETY,
        RiskCategory.CONSISTENCY: ReportSectionCode.INCONSISTENCIES,
    }[finding.category]


def _reassuring_findings(
    *,
    dpe_documents: list[NormalizedDpeFacts],
    diagnostics: list[NormalizedDiagnostics],
    document_names: dict[UUID, str],
) -> list[ReportFinding]:
    findings: list[ReportFinding] = []
    for facts in dpe_documents:
        if (
            facts.ademe_verification.status == AdemeVerificationStatus.VERIFIED
            and facts.dpe_number.value is not None
            and facts.dpe_number.source is not None
        ):
            findings.append(
                ReportFinding(
                    code="REASSURING_DPE_ADEME_VERIFIED",
                    finding_key=(
                        "REASSURING_DPE_ADEME_VERIFIED:"
                        f"{facts.dpe_number.source.document_id}"
                    ),
                    severity=RiskSeverity.INFO,
                    title="Enregistrement ADEME vérifié",
                    explanation=(
                        f"Le DPE n° {facts.dpe_number.value} a été retrouvé dans le registre "
                        "public de l’ADEME et les données comparables sont cohérentes."
                    ),
                    status=FindingStatus.CONFIRMED,
                    sources=_report_sources([facts.dpe_number.source], document_names),
                )
            )
        rating = facts.dpe_rating.value
        source = facts.dpe_rating.source
        if rating in {"A", "B", "C", "D"} and source is not None:
            explanation = f"Le DPE fourni indique une classe énergétique {rating}."
            if facts.dpe_rating_method == DpeRatingMethod.ADEME:
                explanation = (
                    f"Le registre ADEME associé au numéro du document indique une classe "
                    f"énergétique {rating}."
                )
            elif facts.dpe_rating_method == DpeRatingMethod.CALCULATED:
                explanation = (
                    f"La classe énergétique {rating} a été recalculée à partir des valeurs "
                    "énergie et GES extraites du document."
                )
            findings.append(
                ReportFinding(
                    code="REASSURING_DPE_RATING",
                    finding_key=f"REASSURING_DPE_RATING:{source.document_id}",
                    severity=RiskSeverity.INFO,
                    title=f"Classe énergétique {rating}",
                    explanation=explanation,
                    status=FindingStatus.CONFIRMED,
                    sources=_report_sources([source], document_names),
                )
            )
    diagnostic_labels = {
        DiagnosticKind.ASBESTOS: "amiante",
        DiagnosticKind.LEAD: "plomb",
        DiagnosticKind.ELECTRICITY: "installation électrique",
        DiagnosticKind.GAS: "installation gaz",
        DiagnosticKind.ENVIRONMENTAL_RISK: "risques environnementaux",
    }
    for item in (item for document in diagnostics for item in document.findings):
        if item.result not in {DiagnosticResult.ABSENT, DiagnosticResult.CLEAR}:
            continue
        label = diagnostic_labels.get(item.kind)
        if label is None:
            continue
        findings.append(
            ReportFinding(
                code=f"REASSURING_{item.kind.value.upper()}",
                finding_key=(
                    f"REASSURING_{item.kind.value.upper()}:"
                    f"{item.source.document_id}:{item.source.page_number}"
                ),
                severity=RiskSeverity.INFO,
                title=f"Constat favorable — {label}",
                explanation=item.description,
                status=FindingStatus.CONFIRMED,
                sources=_report_sources([item.source], document_names),
            )
        )
    return findings


def build_buyer_report(
    *,
    analysis_case_id: UUID,
    title: str,
    findings: list[RiskFinding],
    document_names: dict[UUID, str],
    dpe_documents: list[NormalizedDpeFacts],
    diagnostics: list[NormalizedDiagnostics],
    generated_at: datetime | None = None,
) -> BuyerReport:
    grouped: dict[ReportSectionCode, list[ReportFinding]] = {
        section: [] for section in SECTION_ORDER
    }
    for finding in findings:
        grouped[_section_for_finding(finding)].append(
            ReportFinding(
                code=finding.code,
                finding_key=finding.finding_key,
                severity=finding.severity,
                title=finding.title,
                explanation=finding.description,
                status=finding.status,
                confidence=finding.confidence,
                amount_eur=finding.amount_eur,
                expectation_level=finding.expectation_level,
                missing_reason=finding.missing_reason,
                sources=_report_sources(finding.sources, document_names),
            )
        )
    reassuring = _reassuring_findings(
        dpe_documents=dpe_documents,
        diagnostics=diagnostics,
        document_names=document_names,
    )
    grouped[ReportSectionCode.REASSURING] = reassuring
    risk_findings = [
        finding
        for finding in findings
        if finding.category != RiskCategory.MISSING_INFORMATION
        and finding.status != FindingStatus.MISSING_INFORMATION
    ]
    missing_information_count = len(findings) - len(risk_findings)
    high_severities = {RiskSeverity.HIGH, RiskSeverity.CRITICAL}
    return BuyerReport(
        analysis_case_id=analysis_case_id,
        title=title,
        generated_at=generated_at or report_generated_at(),
        summary=ReportSummary(
            finding_count=len(findings),
            analyzed_count=len(risk_findings) + len(reassuring),
            risk_count=len(risk_findings),
            high_or_critical_count=sum(
                finding.severity in high_severities for finding in risk_findings
            ),
            missing_information_count=missing_information_count,
            reassuring_count=len(reassuring),
            risk_severity_counts={
                severity: sum(finding.severity == severity for finding in risk_findings)
                for severity in RiskSeverity
            },
        ),
        sections=[
            ReportSection(code=code, title=SECTION_TITLES[code], findings=grouped[code])
            for code in SECTION_ORDER
        ],
        disclaimer=(
            "Ce rapport est une aide à la décision fondée sur les documents fournis. "
            "Il ne remplace pas un avis juridique, notarial, technique, énergétique ou financier."
        ),
    )
