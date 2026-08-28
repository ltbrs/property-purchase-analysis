from datetime import date
from uuid import uuid4

from app.property.normalization.dpe import (
    AdemeVerificationStatus,
    DpeDateFact,
    DpeNumberFact,
    DpeRatingMethod,
    DpeTextFact,
    NormalizedDpeFacts,
    SourceReference,
    extract_dpe_number,
)
from app.property.normalization.dpe_ademe import (
    AdemeDpeRecord,
    calculate_dpe_rating,
    find_dpe_number,
    resolve_dpe_facts,
)
from app.risks.rules.dpe import evaluate_dpe_risks


def source(page_number: int = 1) -> SourceReference:
    return SourceReference(
        document_id=uuid4(),
        page_number=page_number,
        quote="valeur extraite",
    )


def facts(*, rating: str | None = None) -> NormalizedDpeFacts:
    energy_source = source()
    return NormalizedDpeFacts(
        dpe_rating=DpeTextFact(value=rating, source=source() if rating else None),
        dpe_rating_method=(
            DpeRatingMethod.DOCUMENT if rating else DpeRatingMethod.MISSING
        ),
        ges_rating=DpeTextFact(value=None, source=None),
        energy_consumption_kwh_m2_year=DpeNumberFact(
            value=170, source=energy_source
        ),
        greenhouse_gas_emissions_kg_co2_m2_year=DpeNumberFact(
            value=34, source=source()
        ),
        estimated_annual_energy_cost_min=DpeNumberFact(value=None, source=None),
        estimated_annual_energy_cost_max=DpeNumberFact(value=None, source=None),
        surface=DpeNumberFact(value=62.71, source=source()),
        heating_type=DpeTextFact(value=None, source=None),
        hot_water_type=DpeTextFact(value=None, source=None),
        dpe_date=DpeDateFact(value=date(2024, 12, 6), source=source()),
        dpe_valid_until=DpeDateFact(value=date(2034, 12, 5), source=source()),
        recommendations=[],
    )


def ademe_record(**changes: object) -> AdemeDpeRecord:
    values: dict[str, object] = {
        "numero_dpe": "2475E4333306Q",
        "etiquette_dpe": "D",
        "etiquette_ges": "D",
        "conso_5_usages_par_m2_ep": 170.3,
        "emission_ges_5_usages_par_m2": 34,
        "surface_habitable_logement": 62.7,
        "date_etablissement_dpe": "2024-12-06",
        "date_fin_validite_dpe": "2034-12-05",
    }
    values.update(changes)
    return AdemeDpeRecord.model_validate(values)


def test_extract_dpe_number_tolerates_layout_whitespace() -> None:
    assert extract_dpe_number("n° : 2475 E433 3306 Q") == "2475E4333306Q"
    assert (
        extract_dpe_number("n° : 2475E4333306Q  établi le : 06/12/2024")
        == "2475E4333306Q"
    )
    assert extract_dpe_number("aucune référence") is None


def test_find_dpe_number_keeps_the_pdf_page_as_provenance() -> None:
    document_id = uuid4()
    number = find_dpe_number(
        {1: "Couverture", 8: "Référence du DPE : 2475E4333306Q"},
        document_id=document_id,
    )

    assert number.value == "2475E4333306Q"
    assert number.source is not None
    assert number.source.document_id == document_id
    assert number.source.page_number == 8


def test_ademe_match_supplies_missing_rating_and_verification_details() -> None:
    dpe_number = DpeTextFact(value="2475E4333306Q", source=source())

    resolved = resolve_dpe_facts(
        facts(), dpe_number=dpe_number, ademe_record=ademe_record()
    )

    assert resolved.dpe_rating.value == "D"
    assert resolved.dpe_rating.source == dpe_number.source
    assert resolved.dpe_rating_method == DpeRatingMethod.ADEME
    assert resolved.ges_rating.value == "D"
    assert resolved.ademe_verification.status == AdemeVerificationStatus.VERIFIED
    assert resolved.ademe_verification.inconsistent_fields == []
    assert set(resolved.ademe_verification.consistent_fields) == {
        "energy_consumption_kwh_m2_year",
        "greenhouse_gas_emissions_kg_co2_m2_year",
        "surface",
        "dpe_date",
        "dpe_valid_until",
    }


def test_ademe_mismatch_is_exposed_and_does_not_overwrite_document_rating() -> None:
    resolved = resolve_dpe_facts(
        facts(rating="E"),
        dpe_number=DpeTextFact(value="2475E4333306Q", source=source()),
        ademe_record=ademe_record(),
    )

    assert resolved.dpe_rating.value == "E"
    assert resolved.dpe_rating_method == DpeRatingMethod.DOCUMENT
    assert (
        resolved.ademe_verification.status
        == AdemeVerificationStatus.VERIFIED_WITH_INCONSISTENCIES
    )
    assert resolved.ademe_verification.inconsistent_fields == ["dpe_rating"]
    risks = evaluate_dpe_risks(resolved, as_of=date(2026, 8, 28))
    inconsistency = next(risk for risk in risks if risk.code == "DPE_ADEME_INCONSISTENCY")
    assert inconsistency.severity.value == "high"
    assert inconsistency.status.value == "possible"


def test_rating_fallback_uses_the_worse_energy_or_ges_class() -> None:
    assert (
        calculate_dpe_rating(
            energy_consumption_kwh_m2_year=170.3,
            greenhouse_gas_emissions_kg_co2_m2_year=34,
            ges_rating=None,
            surface=62.71,
            dpe_date=date(2024, 12, 6),
        )
        == "D"
    )
    resolved = resolve_dpe_facts(
        facts(),
        dpe_number=DpeTextFact(value="2475E4333306Q", source=source()),
        ademe_unavailable=True,
    )
    assert resolved.dpe_rating.value == "D"
    assert resolved.dpe_rating_method == DpeRatingMethod.CALCULATED
    assert resolved.ademe_verification.status == AdemeVerificationStatus.UNAVAILABLE


def test_rating_fallback_refuses_small_surfaces_with_variable_thresholds() -> None:
    assert (
        calculate_dpe_rating(
            energy_consumption_kwh_m2_year=170,
            greenhouse_gas_emissions_kg_co2_m2_year=34,
            ges_rating=None,
            surface=39,
            dpe_date=date(2024, 12, 6),
        )
        is None
    )


def test_verified_ademe_consumption_is_usable_by_the_risk_engine() -> None:
    document_facts = facts().model_copy(
        update={
            "energy_consumption_kwh_m2_year": DpeNumberFact(
                value=None, source=None
            )
        }
    )
    resolved = resolve_dpe_facts(
        document_facts,
        dpe_number=DpeTextFact(value="2475E4333306Q", source=source()),
        ademe_record=ademe_record(conso_5_usages_par_m2_ep=350),
    )

    risks = evaluate_dpe_risks(resolved, as_of=date(2026, 8, 28))
    by_code = {risk.code: risk for risk in risks}

    assert by_code["DPE_HIGH_ENERGY_CONSUMPTION"].severity.value == "high"
    missing = by_code.get("DPE_MISSING_CRITICAL_INFORMATION")
    assert missing is None or "consommation" not in missing.description
