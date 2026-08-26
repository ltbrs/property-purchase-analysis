from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.property.normalization.ag_minutes import (
    AgItemKind,
    AgItemStatus,
    NormalizedAgItem,
    NormalizedAgMinutes,
)
from app.property.normalization.diagnostics import (
    DiagnosticKind,
    DiagnosticResult,
    NormalizedDiagnosticFinding,
    NormalizedDiagnostics,
)
from app.property.normalization.dpe import (
    DpeDateFact,
    DpeNumberFact,
    DpeTextFact,
    NormalizedDpeFacts,
    SourceReference,
)
from app.property.normalization.financials import (
    FinancialItemKind,
    NormalizedFinancialItem,
    NormalizedFinancials,
)
from app.property.reconciliation import reconcile_case
from app.risks.models import FindingStatus, RiskSeverity
from app.risks.rules.coproperty import evaluate_coproperty_risks
from app.risks.rules.diagnostics import evaluate_diagnostic_risks
from app.risks.rules.dpe import evaluate_dpe_risks
from app.risks.rules.financials import evaluate_financial_risks


def source(page: int = 1) -> SourceReference:
    return SourceReference(document_id=uuid4(), page_number=page, quote="Source")


def dpe_facts(
    *,
    rating: str | None = "D",
    consumption: float | None = 180,
    cost_max: float | None = 1500,
    dpe_date: date | None = date(2024, 1, 1),
    valid_until: date | None = date(2034, 1, 1),
    surface: float | None = 70,
    heating: str | None = "gaz collectif",
) -> NormalizedDpeFacts:
    return NormalizedDpeFacts(
        dpe_rating=DpeTextFact(value=rating, source=source() if rating else None),
        ges_rating=DpeTextFact(value="B", source=source()),
        energy_consumption_kwh_m2_year=DpeNumberFact(
            value=consumption, source=source() if consumption is not None else None
        ),
        estimated_annual_energy_cost_min=DpeNumberFact(value=1000, source=source()),
        estimated_annual_energy_cost_max=DpeNumberFact(
            value=cost_max, source=source() if cost_max is not None else None
        ),
        surface=DpeNumberFact(value=surface, source=source() if surface is not None else None),
        heating_type=DpeTextFact(value=heating, source=source() if heating else None),
        hot_water_type=DpeTextFact(value=None, source=None),
        dpe_date=DpeDateFact(value=dpe_date, source=source() if dpe_date else None),
        dpe_valid_until=DpeDateFact(value=valid_until, source=source() if valid_until else None),
        recommendations=[],
    )


def ag_item(
    kind: AgItemKind,
    status: AgItemStatus,
    *,
    meeting_date: date,
    amount: str | None = None,
    share: str | None = None,
    page: int = 1,
    description: str = "Réfection complète de la toiture",
) -> NormalizedAgItem:
    return NormalizedAgItem(
        kind=kind,
        description=description,
        meeting_date=meeting_date,
        resolution_reference="7",
        status=status,
        amount_eur=Decimal(amount) if amount else None,
        property_share_amount_eur=Decimal(share) if share else None,
        source=source(page),
    )


def financial_item(
    kind: FinancialItemKind,
    *,
    amount: str,
    period_end: date | None = None,
    due_date: date | None = None,
    share: str | None = None,
    project: str | None = None,
) -> NormalizedFinancialItem:
    return NormalizedFinancialItem(
        kind=kind,
        description=project or "Charges de copropriété",
        amount_eur=Decimal(amount),
        property_share_amount_eur=Decimal(share) if share else None,
        period_start=None,
        period_end=period_end,
        due_date=due_date,
        related_project=project,
        source=source(),
    )


def test_dpe_rule_boundaries_and_missing_information() -> None:
    at_boundaries = evaluate_dpe_risks(
        dpe_facts(rating="E", consumption=250, cost_max=2000), as_of=date(2026, 1, 1)
    )
    by_code = {risk.code: risk for risk in at_boundaries}
    assert by_code["DPE_POOR_ENERGY_RATING"].severity == RiskSeverity.MEDIUM
    assert by_code["DPE_HIGH_ENERGY_CONSUMPTION"].severity == RiskSeverity.MEDIUM
    assert by_code["DPE_HIGH_PROJECTED_ENERGY_COST"].severity == RiskSeverity.MEDIUM

    below = evaluate_dpe_risks(
        dpe_facts(rating="D", consumption=249.99, cost_max=1999.99),
        as_of=date(2026, 1, 1),
    )
    assert not {risk.code for risk in below} & {
        "DPE_POOR_ENERGY_RATING",
        "DPE_HIGH_ENERGY_CONSUMPTION",
        "DPE_HIGH_PROJECTED_ENERGY_COST",
    }

    expired = evaluate_dpe_risks(dpe_facts(valid_until=date(2025, 12, 31)), as_of=date(2026, 1, 1))
    assert "DPE_EXPIRED" in {risk.code for risk in expired}
    still_valid = evaluate_dpe_risks(
        dpe_facts(valid_until=date(2026, 1, 1)), as_of=date(2026, 1, 1)
    )
    assert "DPE_EXPIRED" not in {risk.code for risk in still_valid}

    missing = evaluate_dpe_risks(
        dpe_facts(rating=None, consumption=None, dpe_date=None, valid_until=None),
        as_of=date(2026, 1, 1),
    )
    missing_risk = next(risk for risk in missing if risk.code == "DPE_MISSING_CRITICAL_INFORMATION")
    assert missing_risk.status == FindingStatus.MISSING_INFORMATION
    assert missing_risk.sources == []


@pytest.mark.parametrize(
    ("rating", "consumption", "cost", "expected_severity"),
    [
        ("F", 330, 2000, RiskSeverity.HIGH),
        ("G", 450, 3000, RiskSeverity.CRITICAL),
    ],
)
def test_dpe_high_and_critical_severity_boundaries(
    rating: str, consumption: float, cost: float, expected_severity: RiskSeverity
) -> None:
    risks = evaluate_dpe_risks(
        dpe_facts(rating=rating, consumption=consumption, cost_max=cost),
        as_of=date(2026, 1, 1),
    )
    by_code = {risk.code: risk for risk in risks}
    assert by_code["DPE_POOR_ENERGY_RATING"].severity == expected_severity
    assert by_code["DPE_HIGH_ENERGY_CONSUMPTION"].severity == expected_severity
    assert by_code["DPE_HIGH_PROJECTED_ENERGY_COST"].severity == (
        RiskSeverity.HIGH if cost >= 3000 else RiskSeverity.MEDIUM
    )


def test_copro_rules_do_not_confuse_discussed_and_voted_works() -> None:
    discussed = ag_item(AgItemKind.ROOF, AgItemStatus.DISCUSSED, meeting_date=date(2024, 1, 1))
    voted = ag_item(AgItemKind.ROOF, AgItemStatus.VOTED, meeting_date=date(2025, 1, 1))

    discussed_codes = {
        risk.code
        for risk in evaluate_coproperty_risks(
            [NormalizedAgMinutes(meeting_date=date(2024, 1, 1), items=[discussed])]
        )
    }
    voted_codes = {
        risk.code
        for risk in evaluate_coproperty_risks(
            [NormalizedAgMinutes(meeting_date=date(2025, 1, 1), items=[voted])]
        )
    }
    assert "COPRO_MAJOR_WORKS_VOTED" not in discussed_codes
    assert "COPRO_MAJOR_WORKS_VOTED" in voted_codes


def test_copro_cost_recurrence_unpaid_and_litigation_rules() -> None:
    first = ag_item(
        AgItemKind.WATER_INFILTRATION,
        AgItemStatus.DISCUSSED,
        meeting_date=date(2023, 1, 1),
    )
    second = ag_item(
        AgItemKind.WATER_INFILTRATION,
        AgItemStatus.ONGOING,
        meeting_date=date(2024, 1, 1),
        page=2,
    )
    high_share = ag_item(
        AgItemKind.FACADE,
        AgItemStatus.VOTED,
        meeting_date=date(2024, 1, 1),
        share="10000",
        page=3,
    )
    unpaid = ag_item(
        AgItemKind.UNPAID_CHARGES,
        AgItemStatus.ONGOING,
        meeting_date=date(2024, 1, 1),
        amount="12000",
        page=4,
    )
    dispute = ag_item(
        AgItemKind.LEGAL_DISPUTE,
        AgItemStatus.ONGOING,
        meeting_date=date(2024, 1, 1),
        page=5,
    )
    risks = evaluate_coproperty_risks(
        [
            NormalizedAgMinutes(
                meeting_date=date(2024, 1, 1), items=[first, second, high_share, unpaid, dispute]
            )
        ]
    )
    by_code = {risk.code: risk for risk in risks}
    assert by_code["COPRO_RECURRING_WATER_INFILTRATION"].status == FindingStatus.LIKELY
    assert by_code["COPRO_HIGH_PROPERTY_SHARE_COST"].severity == RiskSeverity.HIGH
    assert by_code["COPRO_SIGNIFICANT_UNPAID_CHARGES"].severity == RiskSeverity.HIGH
    assert by_code["COPRO_LEGAL_DISPUTE"].severity == RiskSeverity.HIGH


def test_repeated_discussed_major_work_is_likely_not_confirmed() -> None:
    documents = [
        NormalizedAgMinutes(
            meeting_date=meeting_date,
            items=[
                ag_item(
                    AgItemKind.FACADE,
                    AgItemStatus.DISCUSSED,
                    meeting_date=meeting_date,
                    page=page,
                )
            ],
        )
        for page, meeting_date in enumerate((date(2024, 1, 1), date(2025, 1, 1)), start=1)
    ]
    risk = next(
        risk
        for risk in evaluate_coproperty_risks(documents)
        if risk.code == "COPRO_MAJOR_WORKS_REPEATEDLY_DISCUSSED"
    )
    assert risk.status == FindingStatus.LIKELY
    codes = {risk.code for risk in evaluate_coproperty_risks(documents)}
    assert "COPRO_RECURRING_BUILDING_ENVELOPE_ISSUE" in codes


@pytest.mark.parametrize(
    ("kind", "result", "expected_code"),
    [
        (DiagnosticKind.LEAD, DiagnosticResult.PRESENT, "DIAGNOSTIC_LEAD_PRESENT"),
        (
            DiagnosticKind.ELECTRICITY,
            DiagnosticResult.ANOMALY,
            "DIAGNOSTIC_ELECTRICITY_ANOMALY",
        ),
        (
            DiagnosticKind.ENVIRONMENTAL_RISK,
            DiagnosticResult.RISK_IDENTIFIED,
            "DIAGNOSTIC_ENVIRONMENTAL_RISK_IDENTIFIED",
        ),
    ],
)
def test_each_supported_diagnostic_rule(
    kind: DiagnosticKind, result: DiagnosticResult, expected_code: str
) -> None:
    diagnostic = NormalizedDiagnostics(
        findings=[
            NormalizedDiagnosticFinding(
                kind=kind,
                result=result,
                description="Constat factuel",
                diagnostic_date=None,
                valid_until=None,
                measured_surface_m2=None,
                source=source(),
            )
        ]
    )
    assert expected_code in {
        risk.code for risk in evaluate_diagnostic_risks([diagnostic], as_of=date(2026, 1, 1))
    }


def test_financial_and_diagnostic_rules() -> None:
    financials = NormalizedFinancials(
        items=[
            financial_item(
                FinancialItemKind.ANNUAL_CHARGES,
                amount="2000",
                period_end=date(2024, 12, 31),
            ),
            financial_item(
                FinancialItemKind.ANNUAL_CHARGES,
                amount="2500",
                period_end=date(2025, 12, 31),
            ),
            financial_item(
                FinancialItemKind.FUNDING_CALL,
                amount="15000",
                share="6000",
                due_date=date(2026, 6, 1),
                project="Toiture",
            ),
            financial_item(FinancialItemKind.UNPAID_CHARGES, amount="11000"),
        ]
    )
    codes = {
        risk.code: risk for risk in evaluate_financial_risks([financials], as_of=date(2026, 1, 1))
    }
    assert codes["FINANCIAL_MATERIAL_CHARGE_INCREASE"].amount_eur == Decimal("500")
    assert codes["FINANCIAL_UPCOMING_PAYMENT"].amount_eur == Decimal("6000")
    assert codes["FINANCIAL_UNPAID_COPRO_CHARGES"].severity == RiskSeverity.HIGH

    diagnostic = NormalizedDiagnostics(
        findings=[
            NormalizedDiagnosticFinding(
                kind=DiagnosticKind.ASBESTOS,
                result=DiagnosticResult.PRESENT,
                description="Amiante repérée dans un conduit",
                diagnostic_date=date(2020, 1, 1),
                valid_until=date(2025, 1, 1),
                measured_surface_m2=None,
                source=source(),
            ),
            NormalizedDiagnosticFinding(
                kind=DiagnosticKind.GAS,
                result=DiagnosticResult.ANOMALY,
                description="Anomalie A2",
                diagnostic_date=None,
                valid_until=None,
                measured_surface_m2=None,
                source=source(2),
            ),
        ]
    )
    diagnostic_codes = {
        risk.code for risk in evaluate_diagnostic_risks([diagnostic], as_of=date(2026, 1, 1))
    }
    assert diagnostic_codes == {
        "DIAGNOSTIC_ASBESTOS_PRESENT",
        "DIAGNOSTIC_GAS_ANOMALY",
        "DIAGNOSTIC_VALIDITY_EXPIRED",
    }


def test_reconciliation_detects_conflicts_missing_links_and_builds_timeline() -> None:
    voted_roof = ag_item(
        AgItemKind.ROOF,
        AgItemStatus.VOTED,
        meeting_date=date(2024, 5, 1),
        description="Réfection de la toiture",
    )
    old_facade = ag_item(
        AgItemKind.FACADE,
        AgItemStatus.DISCUSSED,
        meeting_date=date(2023, 5, 1),
        page=2,
    )
    later_other = ag_item(
        AgItemKind.HEATING,
        AgItemStatus.DISCUSSED,
        meeting_date=date(2024, 5, 1),
        page=3,
    )
    minutes = [
        NormalizedAgMinutes(meeting_date=date(2023, 5, 1), items=[old_facade]),
        NormalizedAgMinutes(meeting_date=date(2024, 5, 1), items=[voted_roof, later_other]),
    ]
    contradictory_financials = NormalizedFinancials(
        items=[
            financial_item(
                FinancialItemKind.ANNUAL_CHARGES,
                amount="2000",
                period_end=date(2024, 12, 31),
            ),
            financial_item(
                FinancialItemKind.ANNUAL_CHARGES,
                amount="2400",
                period_end=date(2024, 12, 31),
            ),
        ]
    )
    carrez = NormalizedDiagnostics(
        findings=[
            NormalizedDiagnosticFinding(
                kind=DiagnosticKind.CARREZ,
                result=DiagnosticResult.CLEAR,
                description="Surface privative 65 m²",
                diagnostic_date=None,
                valid_until=None,
                measured_surface_m2=Decimal("65"),
                source=source(4),
            )
        ]
    )
    result = reconcile_case(
        dpe_documents=[dpe_facts(surface=70), dpe_facts(surface=70, heating="électrique")],
        minutes=minutes,
        financials=[contradictory_financials],
        diagnostics=[carrez],
    )
    codes = {finding.code for finding in result.findings}
    assert {
        "INCONSISTENT_HEATING_TYPE",
        "INCONSISTENT_PROPERTY_SURFACE",
        "VOTED_WORK_WITHOUT_MATCHING_FUNDING_CALL",
        "AG_PROJECT_NOT_FOLLOWED_UP",
        "INCONSISTENT_ANNUAL_CHARGES",
    } <= codes
    assert result.timeline == sorted(result.timeline, key=lambda event: event.event_date)


def test_matching_named_funding_call_suppresses_missing_link() -> None:
    work = ag_item(
        AgItemKind.ROOF,
        AgItemStatus.VOTED,
        meeting_date=date(2024, 1, 1),
        description="Réfection complète de la toiture",
    )
    call = financial_item(
        FinancialItemKind.FUNDING_CALL,
        amount="20000",
        due_date=date(2024, 6, 1),
        project="Appel toiture première échéance",
    )
    result = reconcile_case(
        dpe_documents=[],
        minutes=[NormalizedAgMinutes(meeting_date=date(2024, 1, 1), items=[work])],
        financials=[NormalizedFinancials(items=[call])],
        diagnostics=[],
    )
    assert "VOTED_WORK_WITHOUT_MATCHING_FUNDING_CALL" not in {
        finding.code for finding in result.findings
    }
