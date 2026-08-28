import json
import math
from datetime import date
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.property.normalization.dpe import (
    DPE_NUMBER_PATTERN,
    AdemeDpeData,
    AdemeVerificationStatus,
    DpeAdemeVerification,
    DpeRatingMethod,
    DpeTextFact,
    NormalizedDpeFacts,
    SourceReference,
    extract_dpe_number,
)


class AdemeApiUnavailable(RuntimeError):
    pass


class AdemeDpeRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    numero_dpe: str
    etiquette_dpe: str | None = None
    etiquette_ges: str | None = None
    conso_5_usages_par_m2_ep: float | None = None
    emission_ges_5_usages_par_m2: float | None = None
    surface_habitable_logement: float | None = None
    date_etablissement_dpe: date | None = None
    date_fin_validite_dpe: date | None = None

    def as_public_data(self) -> AdemeDpeData:
        return AdemeDpeData(
            dpe_rating=_rating(self.etiquette_dpe),
            ges_rating=_rating(self.etiquette_ges),
            energy_consumption_kwh_m2_year=self.conso_5_usages_par_m2_ep,
            greenhouse_gas_emissions_kg_co2_m2_year=(
                self.emission_ges_5_usages_par_m2
            ),
            surface=self.surface_habitable_logement,
            dpe_date=self.date_etablissement_dpe,
            dpe_valid_until=self.date_fin_validite_dpe,
        )


class AdemeDpeLookup(Protocol):
    def lookup(self, dpe_number: str) -> AdemeDpeRecord | None: ...


class PublicAdemeDpeClient:
    """Small dependency-free client for ADEME's public Data Fair dataset."""

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def lookup(self, dpe_number: str) -> AdemeDpeRecord | None:
        normalized_number = dpe_number.upper()
        if DPE_NUMBER_PATTERN.fullmatch(normalized_number) is None:
            return None
        selected_fields = ",".join(
            (
                "numero_dpe",
                "etiquette_dpe",
                "etiquette_ges",
                "conso_5_usages_par_m2_ep",
                "emission_ges_5_usages_par_m2",
                "surface_habitable_logement",
                "date_etablissement_dpe",
                "date_fin_validite_dpe",
            )
        )
        query = urlencode(
            {
                "size": 2,
                "qs": f'numero_dpe:"{normalized_number}"',
                "select": selected_fields,
            }
        )
        request = Request(
            f"{self.base_url}/lines?{query}",
            headers={"Accept": "application/json", "User-Agent": "property-purchase-analysis/1"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            raise AdemeApiUnavailable("ADEME DPE API is unavailable") from error

        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise AdemeApiUnavailable("ADEME DPE API returned an invalid response")
        exact_matches = [
            item
            for item in results
            if isinstance(item, dict)
            and str(item.get("numero_dpe", "")).upper() == normalized_number
        ]
        if not exact_matches:
            return None
        try:
            return AdemeDpeRecord.model_validate(exact_matches[0])
        except ValueError as error:
            raise AdemeApiUnavailable("ADEME DPE API returned invalid DPE data") from error


def find_dpe_number(
    pages: dict[int, str], *, document_id: UUID
) -> DpeTextFact:
    for page_number in sorted(pages):
        page = pages[page_number]
        dpe_number = extract_dpe_number(page)
        if dpe_number is not None:
            return DpeTextFact(
                value=dpe_number,
                source=SourceReference(
                    document_id=document_id,
                    page_number=page_number,
                    quote=dpe_number if dpe_number in page.upper() else None,
                ),
            )
    return DpeTextFact(value=None, source=None)


def _rating(value: str | None) -> str | None:
    normalized = (value or "").strip().upper()
    return normalized if normalized in set("ABCDEFG") else None


def _class_for_value(value: float, upper_bounds: tuple[int, ...]) -> str:
    rounded_down = math.floor(value)
    for index, upper_bound in enumerate(upper_bounds):
        if rounded_down < upper_bound:
            return "ABCDEFG"[index]
    return "G"


def calculate_dpe_rating(
    *,
    energy_consumption_kwh_m2_year: float | None,
    greenhouse_gas_emissions_kg_co2_m2_year: float | None,
    ges_rating: str | None,
    surface: float | None,
    dpe_date: date | None,
) -> str | None:
    """Calculate a post-2021 label only where the standard thresholds are unambiguous."""

    if (
        energy_consumption_kwh_m2_year is None
        or surface is None
        or surface <= 40
        or dpe_date is None
        or dpe_date < date(2021, 7, 1)
    ):
        return None
    energy_rating = _class_for_value(
        energy_consumption_kwh_m2_year, (70, 110, 180, 250, 330, 420)
    )
    climate_rating = _rating(ges_rating)
    if greenhouse_gas_emissions_kg_co2_m2_year is not None:
        climate_rating = _class_for_value(
            greenhouse_gas_emissions_kg_co2_m2_year, (6, 11, 30, 50, 70, 100)
        )
    if climate_rating is None:
        return None
    return max(energy_rating, climate_rating)


def _compare_ademe_data(
    facts: NormalizedDpeFacts, data: AdemeDpeData
) -> tuple[list[str], list[str]]:
    comparable = {
        "dpe_rating": (facts.dpe_rating.value, data.dpe_rating, None),
        "ges_rating": (facts.ges_rating.value, data.ges_rating, None),
        "energy_consumption_kwh_m2_year": (
            facts.energy_consumption_kwh_m2_year.value,
            data.energy_consumption_kwh_m2_year,
            1.0,
        ),
        "greenhouse_gas_emissions_kg_co2_m2_year": (
            facts.greenhouse_gas_emissions_kg_co2_m2_year.value,
            data.greenhouse_gas_emissions_kg_co2_m2_year,
            1.0,
        ),
        "surface": (facts.surface.value, data.surface, 0.2),
        "dpe_date": (facts.dpe_date.value, data.dpe_date, None),
        "dpe_valid_until": (
            facts.dpe_valid_until.value,
            data.dpe_valid_until,
            None,
        ),
    }
    consistent: list[str] = []
    inconsistent: list[str] = []
    for field, (document_value, ademe_value, tolerance) in comparable.items():
        if document_value is None or ademe_value is None:
            continue
        if tolerance is not None:
            if not isinstance(document_value, (int, float)) or not isinstance(
                ademe_value, (int, float)
            ):
                continue
            agrees = abs(document_value - ademe_value) <= tolerance
        else:
            agrees = document_value == ademe_value
        (consistent if agrees else inconsistent).append(field)
    return consistent, inconsistent


def resolve_dpe_facts(
    facts: NormalizedDpeFacts,
    *,
    dpe_number: DpeTextFact,
    ademe_record: AdemeDpeRecord | None = None,
    ademe_unavailable: bool = False,
) -> NormalizedDpeFacts:
    """Apply ADEME enrichment, then the deterministic no-OCR rating fallback."""

    updates: dict[str, object] = {"dpe_number": dpe_number}
    if dpe_number.value is not None and ademe_record is not None:
        data = ademe_record.as_public_data()
        consistent, inconsistent = _compare_ademe_data(facts, data)
        updates["ademe_verification"] = DpeAdemeVerification(
            status=(
                AdemeVerificationStatus.VERIFIED_WITH_INCONSISTENCIES
                if inconsistent
                else AdemeVerificationStatus.VERIFIED
            ),
            dpe_number=dpe_number.value,
            data=data,
            consistent_fields=consistent,
            inconsistent_fields=inconsistent,
        )
        if facts.dpe_rating.value is None and data.dpe_rating is not None:
            updates["dpe_rating"] = DpeTextFact(
                value=data.dpe_rating,
                source=dpe_number.source,
            )
            updates["dpe_rating_method"] = DpeRatingMethod.ADEME
        if facts.ges_rating.value is None and data.ges_rating is not None:
            updates["ges_rating"] = DpeTextFact(
                value=data.ges_rating,
                source=dpe_number.source,
            )
    elif dpe_number.value is not None:
        updates["ademe_verification"] = DpeAdemeVerification(
            status=(
                AdemeVerificationStatus.UNAVAILABLE
                if ademe_unavailable
                else AdemeVerificationStatus.NOT_FOUND
            ),
            dpe_number=dpe_number.value,
        )

    resolved = facts.model_copy(update=updates)
    if resolved.dpe_rating.value is not None:
        return resolved

    calculated_rating = calculate_dpe_rating(
        energy_consumption_kwh_m2_year=(
            resolved.energy_consumption_kwh_m2_year.value
        ),
        greenhouse_gas_emissions_kg_co2_m2_year=(
            resolved.greenhouse_gas_emissions_kg_co2_m2_year.value
        ),
        ges_rating=resolved.ges_rating.value,
        surface=resolved.surface.value,
        dpe_date=resolved.dpe_date.value,
    )
    if calculated_rating is None:
        return resolved
    return resolved.model_copy(
        update={
            "dpe_rating": DpeTextFact(
                value=calculated_rating,
                source=resolved.energy_consumption_kwh_m2_year.source,
            ),
            "dpe_rating_method": DpeRatingMethod.CALCULATED,
        }
    )
