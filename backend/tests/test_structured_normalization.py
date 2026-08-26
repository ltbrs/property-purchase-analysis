from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.property.normalization.ag_minutes import (
    AgItemCandidate,
    AgItemKind,
    AgItemStatus,
    AgMinutesExtractionCandidate,
    normalize_ag_minutes_candidate,
)
from app.property.normalization.common import normalize_monetary_value
from app.property.normalization.diagnostics import (
    DiagnosticExtractionCandidate,
    DiagnosticFindingCandidate,
    DiagnosticKind,
    DiagnosticResult,
    normalize_diagnostics_candidate,
)
from app.property.normalization.financials import (
    FinancialExtractionCandidate,
    FinancialItemCandidate,
    FinancialItemKind,
    calculate_charge_evolution,
    explicit_property_share_exposure,
    normalize_financial_candidate,
)


def test_french_monetary_normalization_is_deterministic() -> None:
    assert normalize_monetary_value("1 234,56 €") == Decimal("1234.56")
    assert normalize_monetary_value("12.345 €") == Decimal("12345.00")
    assert normalize_monetary_value("-50 €") is None
    assert normalize_monetary_value("non communiqué") is None


def test_ag_normalization_requires_exact_page_provenance_and_never_calculates_share() -> None:
    candidate = AgMinutesExtractionCandidate(
        meeting_date="2025-05-12",
        items=[
            AgItemCandidate(
                kind=AgItemKind.ROOF,
                description="Réfection de la toiture",
                meeting_date=None,
                resolution_reference="Résolution 7",
                status=AgItemStatus.VOTED,
                amount_eur="120 000 €",
                property_share_amount_eur=None,
                page_number=2,
                quote="Résolution 7 : réfection de la toiture votée pour 120 000 €",
            ),
            AgItemCandidate(
                kind=AgItemKind.FACADE,
                description="Façade",
                meeting_date=None,
                resolution_reference=None,
                status=AgItemStatus.DISCUSSED,
                amount_eur=None,
                property_share_amount_eur=None,
                page_number=3,
                quote="Citation inventée",
            ),
        ],
    )
    facts = normalize_ag_minutes_candidate(
        candidate,
        document_id=uuid4(),
        pages={
            1: "Assemblée générale du 12 mai 2025",
            2: "Résolution 7 : réfection de la toiture votée pour 120 000 €",
        },
    )
    assert len(facts.items) == 1
    assert facts.items[0].amount_eur == Decimal("120000.00")
    assert facts.items[0].property_share_amount_eur is None
    assert facts.items[0].meeting_date == date(2025, 5, 12)


def test_page_backed_item_does_not_validate_an_unquoted_amount_or_date() -> None:
    candidate = AgMinutesExtractionCandidate(
        meeting_date="2025-05-12",
        items=[
            AgItemCandidate(
                kind=AgItemKind.ROOF,
                description="Réfection de la toiture",
                meeting_date="2025-05-12",
                resolution_reference="7",
                status=AgItemStatus.VOTED,
                amount_eur="120 000 €",
                property_share_amount_eur="3 500 €",
                page_number=1,
                quote="Résolution 7 : réfection de la toiture votée",
            )
        ],
    )
    facts = normalize_ag_minutes_candidate(
        candidate,
        document_id=uuid4(),
        pages={1: "Résolution 7 : réfection de la toiture votée"},
    )
    assert facts.meeting_date is None
    assert facts.items[0].meeting_date is None
    assert facts.items[0].amount_eur is None
    assert facts.items[0].property_share_amount_eur is None


def test_financial_normalization_periods_calculations_and_explicit_exposure() -> None:
    candidate = FinancialExtractionCandidate(
        items=[
            FinancialItemCandidate(
                kind=FinancialItemKind.ANNUAL_CHARGES,
                description="Charges 2024",
                amount_eur="2 000 €",
                property_share_amount_eur=None,
                period_start="2024-01-01",
                period_end="2024-12-31",
                due_date=None,
                related_project=None,
                page_number=1,
                quote="Charges 2024 : 2 000 €",
            ),
            FinancialItemCandidate(
                kind=FinancialItemKind.ANNUAL_CHARGES,
                description="Charges 2025",
                amount_eur="2 400 €",
                property_share_amount_eur=None,
                period_start="2025-01-01",
                period_end="2025-12-31",
                due_date=None,
                related_project=None,
                page_number=2,
                quote="Charges 2025 : 2 400 €",
            ),
            FinancialItemCandidate(
                kind=FinancialItemKind.FUNDING_CALL,
                description="Appel travaux",
                amount_eur="10 000 €",
                property_share_amount_eur="1 500 €",
                period_start="2026-12-31",
                period_end="2026-01-01",
                due_date="2026-06-30",
                related_project="Toiture",
                page_number=3,
                quote="Appel travaux toiture : quote-part lot 1 500 €, échéance 30/06/2026",
            ),
        ]
    )
    pages = {
        1: "Du 01/01/2024 au 31/12/2024. Charges 2024 : 2 000 €",
        2: "Du 01/01/2025 au 31/12/2025. Charges 2025 : 2 400 €",
        3: (
            "Période du 31/12/2026 au 01/01/2026. Appel travaux toiture : "
            "quote-part lot 1 500 €, échéance 30/06/2026"
        ),
    }
    facts = normalize_financial_candidate(candidate, document_id=uuid4(), pages=pages)
    evolution = calculate_charge_evolution(facts)
    assert evolution[0].change_percent == Decimal("20.00")
    assert evolution[0].material_increase is True
    assert facts.items[2].period_start is None and facts.items[2].period_end is None
    assert explicit_property_share_exposure(facts, as_of=date(2026, 1, 1)) == Decimal("1500.00")


def test_charge_evolution_ignores_a_period_with_contradictory_totals() -> None:
    yearly_values = ((2024, "2 000 €"), (2024, "2 500 €"), (2025, "3 000 €"))
    candidate = FinancialExtractionCandidate(
        items=[
            FinancialItemCandidate(
                kind=FinancialItemKind.ANNUAL_CHARGES,
                description=f"Charges {year}",
                amount_eur=amount,
                property_share_amount_eur=None,
                period_start=f"{year}-01-01",
                period_end=f"{year}-12-31",
                due_date=None,
                related_project=None,
                page_number=index,
                quote=f"Charges {year} : {amount}",
            )
            for index, (year, amount) in enumerate(yearly_values, start=1)
        ]
    )
    pages = {
        index: f"Du 01/01/{year} au 31/12/{year}. Charges {year} : {amount}"
        for index, (year, amount) in enumerate(yearly_values, start=1)
    }
    facts = normalize_financial_candidate(candidate, document_id=uuid4(), pages=pages)
    assert calculate_charge_evolution(facts) == []


def test_diagnostics_normalization_keeps_facts_without_legal_inference() -> None:
    candidate = DiagnosticExtractionCandidate(
        findings=[
            DiagnosticFindingCandidate(
                kind=DiagnosticKind.CARREZ,
                result=DiagnosticResult.CLEAR,
                description="Surface privative de 64,20 m²",
                diagnostic_date="2025-04-01",
                valid_until=None,
                measured_surface_m2="64,20",
                page_number=1,
                quote="Surface privative de 64,20 m²",
            ),
            DiagnosticFindingCandidate(
                kind=DiagnosticKind.GAS,
                result=DiagnosticResult.ANOMALY,
                description="Anomalie",
                diagnostic_date=None,
                valid_until=None,
                measured_surface_m2=None,
                page_number=9,
                quote="Anomalie gaz",
            ),
        ]
    )
    facts = normalize_diagnostics_candidate(
        candidate,
        document_id=uuid4(),
        pages={1: "Surface privative de 64,20 m²"},
    )
    assert len(facts.findings) == 1
    assert facts.findings[0].measured_surface_m2 == Decimal("64.20")
