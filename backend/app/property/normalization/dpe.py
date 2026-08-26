import re
import unicodedata
from datetime import date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DpeTextFactCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str | None
    page_number: int | None
    quote: str | None = Field(max_length=300)


class DpeNumberFactCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(allow_inf_nan=False)
    page_number: int | None
    quote: str | None = Field(max_length=300)


class DpeDateFactCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str | None
    page_number: int | None
    quote: str | None = Field(max_length=300)


class DpeRecommendationCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    page_number: int
    quote: str = Field(max_length=300)


class DpeExtractionCandidate(BaseModel):
    """Provider schema. Semantic and provenance validation happens after parsing."""

    model_config = ConfigDict(extra="forbid")

    dpe_rating: DpeTextFactCandidate
    ges_rating: DpeTextFactCandidate
    energy_consumption_kwh_m2_year: DpeNumberFactCandidate
    estimated_annual_energy_cost_min: DpeNumberFactCandidate
    estimated_annual_energy_cost_max: DpeNumberFactCandidate
    surface: DpeNumberFactCandidate
    heating_type: DpeTextFactCandidate
    hot_water_type: DpeTextFactCandidate
    dpe_date: DpeDateFactCandidate
    dpe_valid_until: DpeDateFactCandidate
    recommendations: list[DpeRecommendationCandidate]


class SourceReference(BaseModel):
    document_id: UUID
    page_number: int = Field(gt=0)
    quote: str | None = Field(default=None, min_length=1, max_length=300)


class DpeTextFact(BaseModel):
    value: str | None
    source: SourceReference | None


class DpeNumberFact(BaseModel):
    value: float | None
    source: SourceReference | None


class DpeDateFact(BaseModel):
    value: date | None
    source: SourceReference | None


class DpeRecommendation(BaseModel):
    description: str
    source: SourceReference


class NormalizedDpeFacts(BaseModel):
    dpe_rating: DpeTextFact
    ges_rating: DpeTextFact
    energy_consumption_kwh_m2_year: DpeNumberFact
    estimated_annual_energy_cost_min: DpeNumberFact
    estimated_annual_energy_cost_max: DpeNumberFact
    surface: DpeNumberFact
    heating_type: DpeTextFact
    hot_water_type: DpeTextFact
    dpe_date: DpeDateFact
    dpe_valid_until: DpeDateFact
    recommendations: list[DpeRecommendation]


class DpeExtractionRecord(Base):
    __tablename__ = "dpe_extractions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    normalized_facts: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    requested_model: Mapped[str] = mapped_column(String(100), nullable=False)
    resolved_model: Mapped[str] = mapped_column(String(100), nullable=False)
    response_id: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DpeExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    normalized_facts: NormalizedDpeFacts
    requested_model: str
    resolved_model: str
    prompt_version: str
    created_at: datetime


def _searchable(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def _source(
    *,
    document_id: UUID,
    page_number: int | None,
    quote: str | None,
    pages: dict[int, str],
) -> SourceReference | None:
    if page_number is None:
        return None
    page = pages.get(page_number)
    if page is None:
        return None
    normalized_quote = _searchable(quote or "")
    verified_quote = None
    if normalized_quote and normalized_quote in _searchable(page):
        verified_quote = " ".join((quote or "").split())
    return SourceReference(
        document_id=document_id,
        page_number=page_number,
        quote=verified_quote,
    )


def _page_contains_text(value: str, page_number: int, pages: dict[int, str]) -> bool:
    return _searchable(value) in _searchable(pages.get(page_number, ""))


def _page_contains_number(value: float, page_number: int, pages: dict[int, str]) -> bool:
    page = _searchable(pages.get(page_number, "")).replace(",", ".")
    page = re.sub(r"(?<=\d)\s+(?=\d)", "", page)
    candidates = {str(value), f"{value:g}"}
    if value.is_integer():
        candidates.add(str(int(value)))
    return any(candidate in page for candidate in candidates)


def _text_fact(
    candidate: DpeTextFactCandidate,
    *,
    document_id: UUID,
    pages: dict[int, str],
    rating: bool = False,
) -> DpeTextFact:
    source = _source(
        document_id=document_id,
        page_number=candidate.page_number,
        quote=candidate.quote,
        pages=pages,
    )
    if candidate.value is None or source is None:
        return DpeTextFact(value=None, source=None)
    value = " ".join(candidate.value.split())
    if rating:
        value = value.upper()
        if value not in set("ABCDEFG") or source.quote is None:
            return DpeTextFact(value=None, source=None)
    if not value or len(value) > 500:
        return DpeTextFact(value=None, source=None)
    if source.quote is None and not _page_contains_text(value, source.page_number, pages):
        return DpeTextFact(value=None, source=None)
    return DpeTextFact(value=value, source=source)


def _number_fact(
    candidate: DpeNumberFactCandidate,
    *,
    document_id: UUID,
    pages: dict[int, str],
    minimum: float,
    maximum: float,
    precision: int,
) -> DpeNumberFact:
    source = _source(
        document_id=document_id,
        page_number=candidate.page_number,
        quote=candidate.quote,
        pages=pages,
    )
    if candidate.value is None or source is None:
        return DpeNumberFact(value=None, source=None)
    if not minimum <= candidate.value <= maximum:
        return DpeNumberFact(value=None, source=None)
    if source.quote is None and not _page_contains_number(
        candidate.value, source.page_number, pages
    ):
        return DpeNumberFact(value=None, source=None)
    return DpeNumberFact(value=round(candidate.value, precision), source=source)


def _date_fact(
    candidate: DpeDateFactCandidate,
    *,
    document_id: UUID,
    pages: dict[int, str],
) -> DpeDateFact:
    source = _source(
        document_id=document_id,
        page_number=candidate.page_number,
        quote=candidate.quote,
        pages=pages,
    )
    if candidate.value is None or source is None:
        return DpeDateFact(value=None, source=None)
    try:
        parsed = date.fromisoformat(candidate.value)
    except ValueError:
        return DpeDateFact(value=None, source=None)
    if not 2000 <= parsed.year <= 2100:
        return DpeDateFact(value=None, source=None)
    if source.quote is None:
        representations = (
            parsed.isoformat(),
            parsed.strftime("%d/%m/%Y"),
            parsed.strftime("%d.%m.%Y"),
        )
        if not any(
            _page_contains_text(value, source.page_number, pages) for value in representations
        ):
            return DpeDateFact(value=None, source=None)
    return DpeDateFact(value=parsed, source=source)


def normalize_dpe_candidate(
    candidate: DpeExtractionCandidate,
    *,
    document_id: UUID,
    pages: dict[int, str],
) -> NormalizedDpeFacts:
    """Normalize only explicit, page-backed values; invalid claims become null."""

    dpe_date = _date_fact(candidate.dpe_date, document_id=document_id, pages=pages)
    valid_until = _date_fact(candidate.dpe_valid_until, document_id=document_id, pages=pages)
    if (
        dpe_date.value is not None
        and valid_until.value is not None
        and valid_until.value < dpe_date.value
    ):
        valid_until = DpeDateFact(value=None, source=None)

    cost_min = _number_fact(
        candidate.estimated_annual_energy_cost_min,
        document_id=document_id,
        pages=pages,
        minimum=0,
        maximum=1_000_000,
        precision=2,
    )
    cost_max = _number_fact(
        candidate.estimated_annual_energy_cost_max,
        document_id=document_id,
        pages=pages,
        minimum=0,
        maximum=1_000_000,
        precision=2,
    )
    if (
        cost_min.value is not None
        and cost_max.value is not None
        and cost_min.value > cost_max.value
    ):
        cost_min = DpeNumberFact(value=None, source=None)
        cost_max = DpeNumberFact(value=None, source=None)

    recommendations: list[DpeRecommendation] = []
    for recommendation in candidate.recommendations:
        source = _source(
            document_id=document_id,
            page_number=recommendation.page_number,
            quote=recommendation.quote,
            pages=pages,
        )
        description = " ".join(recommendation.description.split())
        if (
            source is not None
            and source.quote is not None
            and description
            and len(description) <= 1000
        ):
            recommendations.append(DpeRecommendation(description=description, source=source))

    return NormalizedDpeFacts(
        dpe_rating=_text_fact(
            candidate.dpe_rating,
            document_id=document_id,
            pages=pages,
            rating=True,
        ),
        ges_rating=_text_fact(
            candidate.ges_rating,
            document_id=document_id,
            pages=pages,
            rating=True,
        ),
        energy_consumption_kwh_m2_year=_number_fact(
            candidate.energy_consumption_kwh_m2_year,
            document_id=document_id,
            pages=pages,
            minimum=0,
            maximum=10_000,
            precision=2,
        ),
        estimated_annual_energy_cost_min=cost_min,
        estimated_annual_energy_cost_max=cost_max,
        surface=_number_fact(
            candidate.surface,
            document_id=document_id,
            pages=pages,
            minimum=0.1,
            maximum=100_000,
            precision=2,
        ),
        heating_type=_text_fact(
            candidate.heating_type,
            document_id=document_id,
            pages=pages,
        ),
        hot_water_type=_text_fact(
            candidate.hot_water_type,
            document_id=document_id,
            pages=pages,
        ),
        dpe_date=dpe_date,
        dpe_valid_until=valid_until,
        recommendations=recommendations,
    )
