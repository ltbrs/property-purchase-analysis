from datetime import date

from app.property.normalization.ag_minutes import NormalizedAgMinutes
from app.property.normalization.diagnostics import NormalizedDiagnostics
from app.property.normalization.dpe import NormalizedDpeFacts
from app.property.normalization.financials import NormalizedFinancials
from app.property.reconciliation import ReconciliationResult, reconcile_case
from app.risks.models import RiskFinding, RiskSeverity
from app.risks.rules.coproperty import evaluate_coproperty_risks
from app.risks.rules.diagnostics import evaluate_diagnostic_risks
from app.risks.rules.dpe import evaluate_dpe_risks
from app.risks.rules.financials import evaluate_financial_risks


class CaseRiskEvaluation:
    def __init__(self, findings: list[RiskFinding], reconciliation: ReconciliationResult) -> None:
        self.findings = findings
        self.reconciliation = reconciliation


def evaluate_case_risks(
    *,
    dpe_documents: list[NormalizedDpeFacts],
    minutes: list[NormalizedAgMinutes],
    financials: list[NormalizedFinancials],
    diagnostics: list[NormalizedDiagnostics],
    as_of: date,
) -> CaseRiskEvaluation:
    reconciliation = reconcile_case(
        dpe_documents=dpe_documents,
        minutes=minutes,
        financials=financials,
        diagnostics=diagnostics,
    )
    findings = [
        *(finding for facts in dpe_documents for finding in evaluate_dpe_risks(facts, as_of=as_of)),
        *evaluate_coproperty_risks(minutes),
        *evaluate_financial_risks(financials, as_of=as_of),
        *evaluate_diagnostic_risks(diagnostics, as_of=as_of),
        *reconciliation.findings,
    ]
    # Finding keys are persistence identities. Preserve the first deterministic
    # result if duplicate source material was uploaded in multiple formats.
    unique: list[RiskFinding] = []
    seen: set[str] = set()
    for finding in findings:
        if finding.finding_key not in seen:
            seen.add(finding.finding_key)
            unique.append(finding)
    severity_order = {
        RiskSeverity.CRITICAL: 5,
        RiskSeverity.HIGH: 4,
        RiskSeverity.MEDIUM: 3,
        RiskSeverity.LOW: 2,
        RiskSeverity.INFO: 1,
    }
    unique.sort(
        key=lambda finding: (
            -severity_order[finding.severity],
            finding.category.value,
            finding.code,
            finding.finding_key,
        )
    )
    return CaseRiskEvaluation(unique, reconciliation)
