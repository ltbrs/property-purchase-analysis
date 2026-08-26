from datetime import date
from decimal import Decimal

from app.property.normalization.financials import (
    FinancialItemKind,
    NormalizedFinancials,
    calculate_charge_evolution,
    known_upcoming_payments,
)
from app.risks.models import FindingStatus, RiskCategory, RiskFinding, RiskSeverity


def evaluate_financial_risks(
    financial_documents: list[NormalizedFinancials], *, as_of: date
) -> list[RiskFinding]:
    combined = NormalizedFinancials(
        items=[item for document in financial_documents for item in document.items]
    )
    risks: list[RiskFinding] = []
    for change in calculate_charge_evolution(combined):
        if not change.material_increase or change.change_amount_eur <= 0:
            continue
        label = (
            f"{change.change_percent}%"
            if change.change_percent is not None
            else "montant non comparable"
        )
        risks.append(
            RiskFinding(
                code="FINANCIAL_MATERIAL_CHARGE_INCREASE",
                finding_key=(
                    "FINANCIAL_MATERIAL_CHARGE_INCREASE:"
                    f"{change.previous_period_end}:{change.current_period_end}"
                ),
                category=RiskCategory.FINANCIAL,
                title="Hausse matérielle des charges annuelles",
                severity=(
                    RiskSeverity.HIGH
                    if (change.change_percent or Decimal("0")) >= Decimal("40")
                    else RiskSeverity.MEDIUM
                ),
                description=(
                    f"Les charges explicites passent de {change.previous_amount_eur} € à "
                    f"{change.current_amount_eur} € ({label})."
                ),
                status=FindingStatus.CONFIRMED,
                amount_eur=change.change_amount_eur,
                sources=change.sources,
            )
        )
    for payment in known_upcoming_payments(combined, as_of=as_of):
        source_key = f"{payment.source.document_id}:{payment.source.page_number}"
        amount_scope = (
            "quote-part explicite du lot" if payment.is_property_share else "montant collectif"
        )
        risks.append(
            RiskFinding(
                code="FINANCIAL_UPCOMING_PAYMENT",
                finding_key=f"FINANCIAL_UPCOMING_PAYMENT:{source_key}:{payment.due_date}",
                category=RiskCategory.FINANCIAL,
                title="Paiement à venir identifié",
                severity=(
                    RiskSeverity.HIGH
                    if payment.is_property_share and payment.amount_eur >= Decimal("10000")
                    else RiskSeverity.MEDIUM
                ),
                description=(
                    f"{payment.description} — échéance explicite au "
                    f"{payment.due_date.isoformat()} ({amount_scope})."
                ),
                status=FindingStatus.CONFIRMED,
                amount_eur=payment.amount_eur,
                sources=[payment.source],
            )
        )
    for item in combined.items:
        if (
            item.kind != FinancialItemKind.UNPAID_CHARGES
            or item.amount_eur is None
            or item.amount_eur < Decimal("5000")
        ):
            continue
        source_key = f"{item.source.document_id}:{item.source.page_number}"
        risks.append(
            RiskFinding(
                code="FINANCIAL_UNPAID_COPRO_CHARGES",
                finding_key=f"FINANCIAL_UNPAID_COPRO_CHARGES:{source_key}",
                category=RiskCategory.FINANCIAL,
                title="Impayés de copropriété documentés",
                severity=(
                    RiskSeverity.HIGH
                    if item.amount_eur >= Decimal("10000")
                    else RiskSeverity.MEDIUM
                ),
                description=item.description,
                status=FindingStatus.CONFIRMED,
                amount_eur=item.amount_eur,
                sources=[item.source],
            )
        )
    return risks
