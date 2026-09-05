from datetime import date
from decimal import Decimal

from app.property.normalization.dpe import (
    AdemeVerificationStatus,
    NormalizedDpeFacts,
    SourceReference,
)
from app.risks.models import (
    FindingStatus,
    RiskCategory,
    RiskFinding,
    RiskSeverity,
)


def _sources(*sources: SourceReference | None) -> list[SourceReference]:
    return [source for source in sources if source is not None]


def _finding_key(
    code: str, facts: NormalizedDpeFacts, source: SourceReference | None = None
) -> str:
    if source is not None:
        return f"{code}:{source.document_id}"
    candidates = (
        facts.dpe_rating.source,
        facts.energy_consumption_kwh_m2_year.source,
        facts.dpe_date.source,
        facts.surface.source,
    )
    document_source = next((candidate for candidate in candidates if candidate is not None), None)
    return f"{code}:{document_source.document_id}" if document_source is not None else code


def evaluate_dpe_risks(facts: NormalizedDpeFacts, *, as_of: date) -> list[RiskFinding]:
    risks: list[RiskFinding] = []
    if facts.ademe_verification.status == AdemeVerificationStatus.VERIFIED_WITH_INCONSISTENCIES:
        fields = ", ".join(facts.ademe_verification.inconsistent_fields)
        risks.append(
            RiskFinding(
                code="DPE_ADEME_INCONSISTENCY",
                finding_key=_finding_key("DPE_ADEME_INCONSISTENCY", facts, facts.dpe_number.source),
                category=RiskCategory.CONSISTENCY,
                title="Écart avec le registre ADEME",
                severity=(
                    RiskSeverity.HIGH
                    if {"dpe_rating", "dpe_date"}
                    & set(facts.ademe_verification.inconsistent_fields)
                    else RiskSeverity.MEDIUM
                ),
                description=(
                    "Le numéro DPE existe dans le registre ADEME, mais certaines données "
                    f"diffèrent du document extrait : {fields}. Le document et sa version "
                    "doivent être contrôlés."
                ),
                status=FindingStatus.POSSIBLE,
                sources=_sources(facts.dpe_number.source),
            )
        )
    rating = facts.dpe_rating.value
    rating_severity = {
        "E": RiskSeverity.MEDIUM,
        "F": RiskSeverity.HIGH,
        "G": RiskSeverity.CRITICAL,
    }
    if rating in rating_severity:
        risks.append(
            RiskFinding(
                code="DPE_POOR_ENERGY_RATING",
                finding_key=_finding_key("DPE_POOR_ENERGY_RATING", facts, facts.dpe_rating.source),
                category=RiskCategory.ENERGY,
                title=f"Classe énergétique {rating}",
                severity=rating_severity[rating],
                description=(
                    f"Le DPE indique une classe énergétique {rating}. Cette constatation est "
                    "factuelle; les conséquences réglementaires doivent être vérifiées "
                    "selon le projet."
                ),
                status=FindingStatus.CONFIRMED,
                sources=_sources(facts.dpe_rating.source),
            )
        )

    consumption = facts.energy_consumption_kwh_m2_year.value
    consumption_source = facts.energy_consumption_kwh_m2_year.source
    if (
        consumption is None
        and facts.ademe_verification.status == AdemeVerificationStatus.VERIFIED
        and facts.ademe_verification.data is not None
    ):
        consumption = facts.ademe_verification.data.energy_consumption_kwh_m2_year
        consumption_source = facts.dpe_number.source
    if consumption is not None and consumption >= 250:
        severity = RiskSeverity.MEDIUM
        if consumption >= 330:
            severity = RiskSeverity.HIGH
        if consumption >= 450:
            severity = RiskSeverity.CRITICAL
        risks.append(
            RiskFinding(
                code="DPE_HIGH_ENERGY_CONSUMPTION",
                finding_key=_finding_key(
                    "DPE_HIGH_ENERGY_CONSUMPTION",
                    facts,
                    consumption_source,
                ),
                category=RiskCategory.ENERGY,
                title="Consommation énergétique élevée",
                severity=severity,
                description=f"La consommation indiquée est de {consumption:g} kWh/m²/an.",
                status=FindingStatus.CONFIRMED,
                sources=_sources(consumption_source),
            )
        )

    annual_cost = facts.estimated_annual_energy_cost_max.value
    if annual_cost is not None and annual_cost >= 2_000:
        risks.append(
            RiskFinding(
                code="DPE_HIGH_PROJECTED_ENERGY_COST",
                finding_key=_finding_key(
                    "DPE_HIGH_PROJECTED_ENERGY_COST",
                    facts,
                    facts.estimated_annual_energy_cost_max.source,
                ),
                category=RiskCategory.ENERGY,
                title="Estimation haute du coût énergétique",
                severity=(RiskSeverity.HIGH if annual_cost >= 3_000 else RiskSeverity.MEDIUM),
                description=(
                    f"La borne haute publiée par le DPE atteint {annual_cost:,.0f} € par an."
                ),
                status=FindingStatus.CONFIRMED,
                amount_eur=Decimal(str(annual_cost)),
                sources=_sources(facts.estimated_annual_energy_cost_max.source),
            )
        )

    valid_until = facts.dpe_valid_until.value
    dpe_date = facts.dpe_date.value
    if valid_until is not None and valid_until < as_of:
        risks.append(
            RiskFinding(
                code="DPE_EXPIRED",
                finding_key=_finding_key("DPE_EXPIRED", facts, facts.dpe_valid_until.source),
                category=RiskCategory.ENERGY,
                title="Date de validité du DPE dépassée",
                severity=RiskSeverity.HIGH,
                description=(
                    f"La date de validité indiquée ({valid_until.isoformat()}) est dépassée."
                ),
                status=FindingStatus.CONFIRMED,
                sources=_sources(facts.dpe_valid_until.source),
            )
        )
    elif dpe_date is not None and dpe_date > as_of:
        risks.append(
            RiskFinding(
                code="DPE_DATE_INCONSISTENT",
                finding_key=_finding_key("DPE_DATE_INCONSISTENT", facts, facts.dpe_date.source),
                category=RiskCategory.CONSISTENCY,
                title="Date du DPE incohérente",
                severity=RiskSeverity.MEDIUM,
                description="La date d’établissement extraite est postérieure à la date d’analyse.",
                status=FindingStatus.POSSIBLE,
                sources=_sources(facts.dpe_date.source),
            )
        )

    missing: list[str] = []
    if rating is None:
        missing.append("classe énergétique")
    if consumption is None:
        missing.append("consommation")
    if dpe_date is None:
        missing.append("date d’établissement")
    if valid_until is None:
        missing.append("date de validité")
    if missing:
        risks.append(
            RiskFinding(
                code="DPE_MISSING_CRITICAL_INFORMATION",
                finding_key=_finding_key("DPE_MISSING_CRITICAL_INFORMATION", facts),
                category=RiskCategory.ENERGY,
                title="DPE présent, données énergétiques non extraites",
                severity=RiskSeverity.MEDIUM,
                description=(
                    "Le document DPE est bien présent, mais certaines valeurs n’ont pas "
                    "pu être vérifiées dans son extraction : " + ", ".join(missing) + "."
                ),
                status=FindingStatus.MISSING_INFORMATION,
                sources=[],
            )
        )
    return risks
