from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.property.normalization.common import (
    date_is_page_backed,
    normalize_iso_date,
    normalize_monetary_value,
    normalize_optional_text,
    page_contains_monetary_value,
    verified_source,
)
from app.property.normalization.dpe import SourceReference


class AgItemKind(StrEnum):
    WORKS = "works"
    FACADE = "facade"
    ROOF = "roof"
    ELEVATOR = "elevator"
    HEATING = "heating"
    WATER_INFILTRATION = "water_infiltration"
    STRUCTURAL = "structural"
    MAJOR_MAINTENANCE = "major_maintenance"
    LEGAL_DISPUTE = "legal_dispute"
    UNPAID_CHARGES = "unpaid_charges"
    EXCEPTIONAL_EXPENSE = "exceptional_expense"
    OTHER = "other"


class AgItemStatus(StrEnum):
    VOTED = "voted"
    PLANNED = "planned"
    DISCUSSED = "discussed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class AgItemCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: AgItemKind
    description: str
    meeting_date: str | None
    resolution_reference: str | None
    status: AgItemStatus
    amount_eur: str | None
    property_share_amount_eur: str | None
    page_number: int
    quote: str = Field(max_length=300)


class AgMinutesExtractionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meeting_date: str | None
    items: list[AgItemCandidate]


class NormalizedAgItem(BaseModel):
    kind: AgItemKind
    description: str
    meeting_date: date | None
    resolution_reference: str | None
    status: AgItemStatus
    amount_eur: Decimal | None
    property_share_amount_eur: Decimal | None
    source: SourceReference


class NormalizedAgMinutes(BaseModel):
    meeting_date: date | None
    items: list[NormalizedAgItem]


def normalize_ag_minutes_candidate(
    candidate: AgMinutesExtractionCandidate,
    *,
    document_id: UUID,
    pages: dict[int, str],
) -> NormalizedAgMinutes:
    document_date = normalize_iso_date(candidate.meeting_date)
    if not date_is_page_backed(document_date, pages):
        document_date = None
    items: list[NormalizedAgItem] = []
    for item in candidate.items:
        description = normalize_optional_text(item.description)
        source = verified_source(
            document_id=document_id,
            page_number=item.page_number,
            quote=item.quote,
            pages=pages,
        )
        if description is None or source is None or source.quote is None:
            continue
        meeting_date = normalize_iso_date(item.meeting_date)
        if not date_is_page_backed(meeting_date, pages):
            meeting_date = document_date
        amount = normalize_monetary_value(item.amount_eur)
        if not page_contains_monetary_value(amount, pages[item.page_number]):
            amount = None
        share = normalize_monetary_value(item.property_share_amount_eur)
        if not page_contains_monetary_value(share, pages[item.page_number]):
            share = None
        items.append(
            NormalizedAgItem(
                kind=item.kind,
                description=description,
                meeting_date=meeting_date,
                resolution_reference=normalize_optional_text(
                    item.resolution_reference, maximum=100
                ),
                status=item.status,
                amount_eur=amount,
                property_share_amount_eur=share,
                source=source,
            )
        )
    return NormalizedAgMinutes(meeting_date=document_date, items=items)
