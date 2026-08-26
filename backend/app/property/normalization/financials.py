from datetime import date
from decimal import ROUND_HALF_UP, Decimal
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


class FinancialItemKind(StrEnum):
    ANNUAL_CHARGES = "annual_charges"
    EXCEPTIONAL_CHARGES = "exceptional_charges"
    WORKS_FUND = "works_fund"
    FUNDING_CALL = "funding_call"
    UNPAID_CHARGES = "unpaid_charges"


class FinancialItemCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: FinancialItemKind
    description: str
    amount_eur: str | None
    property_share_amount_eur: str | None
    period_start: str | None
    period_end: str | None
    due_date: str | None
    related_project: str | None
    page_number: int
    quote: str = Field(max_length=300)


class FinancialExtractionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FinancialItemCandidate]


class NormalizedFinancialItem(BaseModel):
    kind: FinancialItemKind
    description: str
    amount_eur: Decimal | None
    property_share_amount_eur: Decimal | None
    period_start: date | None
    period_end: date | None
    due_date: date | None
    related_project: str | None
    source: SourceReference


class NormalizedFinancials(BaseModel):
    items: list[NormalizedFinancialItem]


class ChargeEvolution(BaseModel):
    previous_amount_eur: Decimal
    current_amount_eur: Decimal
    previous_period_end: date
    current_period_end: date
    change_amount_eur: Decimal
    change_percent: Decimal | None
    material_increase: bool
    sources: list[SourceReference]


class KnownUpcomingPayment(BaseModel):
    description: str
    due_date: date
    amount_eur: Decimal
    is_property_share: bool
    source: SourceReference


def normalize_financial_candidate(
    candidate: FinancialExtractionCandidate,
    *,
    document_id: UUID,
    pages: dict[int, str],
) -> NormalizedFinancials:
    items: list[NormalizedFinancialItem] = []
    for item in candidate.items:
        description = normalize_optional_text(item.description)
        source = verified_source(
            document_id=document_id,
            page_number=item.page_number,
            quote=item.quote,
            pages=pages,
        )
        start = normalize_iso_date(item.period_start)
        end = normalize_iso_date(item.period_end)
        due_date = normalize_iso_date(item.due_date)
        if description is None or source is None or source.quote is None:
            continue
        if not date_is_page_backed(start, pages):
            start = None
        if not date_is_page_backed(end, pages):
            end = None
        if not date_is_page_backed(due_date, pages):
            due_date = None
        if start is not None and end is not None and start > end:
            start = None
            end = None
        amount = normalize_monetary_value(item.amount_eur)
        if not page_contains_monetary_value(amount, pages[item.page_number]):
            amount = None
        share = normalize_monetary_value(item.property_share_amount_eur)
        if not page_contains_monetary_value(share, pages[item.page_number]):
            share = None
        items.append(
            NormalizedFinancialItem(
                kind=item.kind,
                description=description,
                amount_eur=amount,
                property_share_amount_eur=share,
                period_start=start,
                period_end=end,
                due_date=due_date,
                related_project=normalize_optional_text(item.related_project, maximum=300),
                source=source,
            )
        )
    return NormalizedFinancials(items=items)


def calculate_charge_evolution(financials: NormalizedFinancials) -> list[ChargeEvolution]:
    """Compare explicit successive annual totals; never delegate arithmetic to the model."""

    by_period: dict[date, list[NormalizedFinancialItem]] = {}
    for item in financials.items:
        if (
            item.kind == FinancialItemKind.ANNUAL_CHARGES
            and item.amount_eur is not None
            and item.period_end is not None
        ):
            by_period.setdefault(item.period_end, []).append(item)
    annual = [
        period_items[0]
        for _, period_items in sorted(by_period.items())
        if len({item.amount_eur for item in period_items}) == 1
    ]
    changes: list[ChargeEvolution] = []
    for previous, current in zip(annual, annual[1:], strict=False):
        assert previous.amount_eur is not None and previous.period_end is not None
        assert current.amount_eur is not None and current.period_end is not None
        difference = current.amount_eur - previous.amount_eur
        percentage = None
        if previous.amount_eur > 0:
            percentage = (difference * 100 / previous.amount_eur).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        changes.append(
            ChargeEvolution(
                previous_amount_eur=previous.amount_eur,
                current_amount_eur=current.amount_eur,
                previous_period_end=previous.period_end,
                current_period_end=current.period_end,
                change_amount_eur=difference,
                change_percent=percentage,
                material_increase=(difference >= Decimal("500") or (percentage or 0) >= 20),
                sources=[previous.source, current.source],
            )
        )
    return changes


def known_upcoming_payments(
    financials: NormalizedFinancials, *, as_of: date
) -> list[KnownUpcomingPayment]:
    payments: list[KnownUpcomingPayment] = []
    for item in financials.items:
        if (
            item.kind
            not in {
                FinancialItemKind.EXCEPTIONAL_CHARGES,
                FinancialItemKind.WORKS_FUND,
                FinancialItemKind.FUNDING_CALL,
            }
            or item.due_date is None
            or item.due_date < as_of
        ):
            continue
        amount = (
            item.property_share_amount_eur
            if item.property_share_amount_eur is not None
            else item.amount_eur
        )
        if amount is None:
            continue
        payments.append(
            KnownUpcomingPayment(
                description=item.description,
                due_date=item.due_date,
                amount_eur=amount,
                is_property_share=item.property_share_amount_eur is not None,
                source=item.source,
            )
        )
    return sorted(payments, key=lambda item: item.due_date)


def explicit_property_share_exposure(financials: NormalizedFinancials, *, as_of: date) -> Decimal:
    return sum(
        (
            payment.amount_eur
            for payment in known_upcoming_payments(financials, as_of=as_of)
            if payment.is_property_share
        ),
        start=Decimal("0.00"),
    )
