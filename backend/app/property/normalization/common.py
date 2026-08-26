import re
import unicodedata
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from uuid import UUID

from app.property.normalization.dpe import SourceReference


def searchable(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def verified_source(
    *,
    document_id: UUID,
    page_number: int | None,
    quote: str | None,
    pages: dict[int, str],
    required_text: str | None = None,
) -> SourceReference | None:
    """Return page provenance only when the page exists and supports the claim."""

    if page_number is None or (page := pages.get(page_number)) is None:
        return None
    normalized_quote = searchable(quote or "")
    clean_quote = " ".join((quote or "").split())
    if normalized_quote and normalized_quote in searchable(page):
        return SourceReference(
            document_id=document_id,
            page_number=page_number,
            quote=clean_quote,
        )
    if required_text and searchable(required_text) in searchable(page):
        return SourceReference(document_id=document_id, page_number=page_number)
    return None


def normalize_optional_text(value: str | None, *, maximum: int = 1000) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    return normalized[:maximum] or None


def normalize_iso_date(value: str | None, *, minimum_year: int = 1900) -> date | None:
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    if not minimum_year <= parsed.year <= 2100:
        return None
    return parsed


_MONEY_CLEANUP = re.compile(r"[^0-9,.'’\-]")
_MONEY_TOKEN = re.compile(r"-?\d(?:[\d\s.'’]*\d)?(?:,\d+)?")
_FRENCH_MONTHS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def normalize_monetary_value(value: str | int | float | Decimal | None) -> Decimal | None:
    """Parse common French monetary notation without using model arithmetic."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, (int, float)):
        amount = Decimal(str(value))
    else:
        cleaned = _MONEY_CLEANUP.sub("", value.strip()).replace("’", "").replace("'", "")
        if not cleaned:
            return None
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif cleaned.count(".") > 1:
            cleaned = cleaned.replace(".", "")
        elif "." in cleaned:
            integer, decimal = cleaned.rsplit(".", 1)
            if len(decimal) == 3 and integer not in {"", "-"}:
                cleaned = integer + decimal
        try:
            amount = Decimal(cleaned)
        except InvalidOperation:
            return None
    if not amount.is_finite() or amount < 0 or amount > Decimal("1000000000"):
        return None
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def page_contains_monetary_value(value: Decimal | None, page: str) -> bool:
    if value is None:
        return False
    return any(normalize_monetary_value(token) == value for token in _MONEY_TOKEN.findall(page))


def date_is_page_backed(value: date | None, pages: dict[int, str]) -> bool:
    if value is None:
        return False
    representations = {
        value.isoformat(),
        value.strftime("%d/%m/%Y"),
        value.strftime("%d.%m.%Y"),
        value.strftime("%d-%m-%Y"),
        f"{value.day} {_FRENCH_MONTHS[value.month - 1]} {value.year}",
    }
    searchable_pages = " ".join(searchable(page) for page in pages.values())
    return any(searchable(representation) in searchable_pages for representation in representations)
