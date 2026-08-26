from datetime import date

from app.property.normalization.diagnostics import (
    DiagnosticKind,
    DiagnosticResult,
    NormalizedDiagnostics,
)
from app.risks.models import FindingStatus, RiskCategory, RiskFinding, RiskSeverity


def evaluate_diagnostic_risks(
    documents: list[NormalizedDiagnostics], *, as_of: date
) -> list[RiskFinding]:
    risks: list[RiskFinding] = []
    for item in (finding for document in documents for finding in document.findings):
        source_key = f"{item.source.document_id}:{item.source.page_number}:{item.kind.value}"
        if item.kind == DiagnosticKind.ASBESTOS and item.result == DiagnosticResult.PRESENT:
            code, title, severity = (
                "DIAGNOSTIC_ASBESTOS_PRESENT",
                "Présence d’amiante signalée",
                RiskSeverity.HIGH,
            )
        elif item.kind == DiagnosticKind.LEAD and item.result in {
            DiagnosticResult.PRESENT,
            DiagnosticResult.ANOMALY,
        }:
            code, title, severity = (
                "DIAGNOSTIC_LEAD_PRESENT",
                "Présence de plomb signalée",
                RiskSeverity.HIGH,
            )
        elif (
            item.kind in {DiagnosticKind.ELECTRICITY, DiagnosticKind.GAS}
            and item.result == DiagnosticResult.ANOMALY
        ):
            code, title, severity = (
                f"DIAGNOSTIC_{item.kind.value.upper()}_ANOMALY",
                f"Anomalie du diagnostic {item.kind.value}",
                RiskSeverity.HIGH,
            )
        elif (
            item.kind == DiagnosticKind.ENVIRONMENTAL_RISK
            and item.result == DiagnosticResult.RISK_IDENTIFIED
        ):
            code, title, severity = (
                "DIAGNOSTIC_ENVIRONMENTAL_RISK_IDENTIFIED",
                "Risque environnemental déclaré",
                RiskSeverity.MEDIUM,
            )
        else:
            code = ""
            title = ""
            severity = RiskSeverity.INFO
        if code:
            risks.append(
                RiskFinding(
                    code=code,
                    finding_key=f"{code}:{source_key}",
                    category=RiskCategory.DIAGNOSTICS,
                    title=title,
                    severity=severity,
                    description=(
                        item.description
                        + " Le document établit un fait; ses conséquences juridiques "
                        "ne sont pas déduites."
                    ),
                    status=FindingStatus.CONFIRMED,
                    sources=[item.source],
                )
            )
        if item.valid_until is not None and item.valid_until < as_of:
            risks.append(
                RiskFinding(
                    code="DIAGNOSTIC_VALIDITY_EXPIRED",
                    finding_key=f"DIAGNOSTIC_VALIDITY_EXPIRED:{source_key}",
                    category=RiskCategory.DIAGNOSTICS,
                    title="Date de validité d’un diagnostic dépassée",
                    severity=RiskSeverity.MEDIUM,
                    description=(
                        f"La date de validité extraite pour {item.kind.value} "
                        f"({item.valid_until.isoformat()}) est dépassée."
                    ),
                    status=FindingStatus.CONFIRMED,
                    sources=[item.source],
                )
            )
    return risks
