from uuid import uuid4

from app.property.normalization.dpe import (
    DpeDateFactCandidate,
    DpeExtractionCandidate,
    DpeNumberFactCandidate,
    DpeRecommendationCandidate,
    DpeTextFactCandidate,
    normalize_dpe_candidate,
)


def absent_text() -> DpeTextFactCandidate:
    return DpeTextFactCandidate(value=None, page_number=None, quote=None)


def absent_number() -> DpeNumberFactCandidate:
    return DpeNumberFactCandidate(value=None, page_number=None, quote=None)


def absent_date() -> DpeDateFactCandidate:
    return DpeDateFactCandidate(value=None, page_number=None, quote=None)


def empty_candidate(**changes: object) -> DpeExtractionCandidate:
    values: dict[str, object] = {
        "dpe_rating": absent_text(),
        "ges_rating": absent_text(),
        "energy_consumption_kwh_m2_year": absent_number(),
        "greenhouse_gas_emissions_kg_co2_m2_year": absent_number(),
        "estimated_annual_energy_cost_min": absent_number(),
        "estimated_annual_energy_cost_max": absent_number(),
        "surface": absent_number(),
        "heating_type": absent_text(),
        "hot_water_type": absent_text(),
        "dpe_date": absent_date(),
        "dpe_valid_until": absent_date(),
        "recommendations": [],
    }
    values.update(changes)
    return DpeExtractionCandidate.model_validate(values)


def test_value_with_nonexistent_or_inexact_source_is_discarded() -> None:
    candidate = empty_candidate(
        dpe_rating=DpeTextFactCandidate(value="E", page_number=9, quote="Classe énergie E"),
        ges_rating=DpeTextFactCandidate(value="B", page_number=1, quote="quote not present"),
    )

    facts = normalize_dpe_candidate(
        candidate,
        document_id=uuid4(),
        pages={1: "Classe énergie E et émissions B"},
    )

    assert facts.dpe_rating.value is None and facts.dpe_rating.source is None
    assert facts.ges_rating.value is None and facts.ges_rating.source is None


def test_invalid_ranges_dates_and_cost_order_normalize_to_null() -> None:
    page = "Consommation 99999. Coûts entre 5000 et 2000. Établi 2024-06-15 valide 2020-06-15."
    candidate = empty_candidate(
        energy_consumption_kwh_m2_year=DpeNumberFactCandidate(
            value=99999, page_number=1, quote="Consommation 99999"
        ),
        estimated_annual_energy_cost_min=DpeNumberFactCandidate(
            value=5000, page_number=1, quote="Coûts entre 5000 et 2000"
        ),
        estimated_annual_energy_cost_max=DpeNumberFactCandidate(
            value=2000, page_number=1, quote="Coûts entre 5000 et 2000"
        ),
        dpe_date=DpeDateFactCandidate(value="2024-06-15", page_number=1, quote="Établi 2024-06-15"),
        dpe_valid_until=DpeDateFactCandidate(
            value="2020-06-15", page_number=1, quote="valide 2020-06-15"
        ),
    )

    facts = normalize_dpe_candidate(candidate, document_id=uuid4(), pages={1: page})

    assert facts.energy_consumption_kwh_m2_year.value is None
    assert facts.estimated_annual_energy_cost_min.value is None
    assert facts.estimated_annual_energy_cost_max.value is None
    assert facts.dpe_date.value is not None
    assert facts.dpe_valid_until.value is None


def test_recommendations_require_page_backed_quotes() -> None:
    candidate = empty_candidate(
        recommendations=[
            DpeRecommendationCandidate(
                description="Isoler les murs", page_number=2, quote="Isolation des murs"
            ),
            DpeRecommendationCandidate(
                description="Changer la chaudière", page_number=3, quote="Chaudière"
            ),
        ]
    )

    facts = normalize_dpe_candidate(
        candidate,
        document_id=uuid4(),
        pages={2: "Recommandation : Isolation des murs"},
    )

    assert [item.description for item in facts.recommendations] == ["Isoler les murs"]


def test_page_only_provenance_is_kept_when_numeric_value_is_verifiable() -> None:
    candidate = empty_candidate(
        estimated_annual_energy_cost_max=DpeNumberFactCandidate(
            value=1300,
            page_number=3,
            quote="Entre 960€ et 1 300€ par an",
        )
    )

    facts = normalize_dpe_candidate(
        candidate,
        document_id=uuid4(),
        pages={3: "Montant haut\n1 300 €\npar an"},
    )

    assert facts.estimated_annual_energy_cost_max.value == 1300
    assert facts.estimated_annual_energy_cost_max.source is not None
    assert facts.estimated_annual_energy_cost_max.source.page_number == 3
    assert facts.estimated_annual_energy_cost_max.source.quote is None
