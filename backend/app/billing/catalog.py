from dataclasses import dataclass

from app.billing.models import BillingOfferCode
from app.core.config import Settings


@dataclass(frozen=True)
class BillingOffer:
    code: BillingOfferCode
    amount_cents: int
    currency: str
    credit_count: int
    credits_expire_after_days: int | None


OFFERS = {
    BillingOfferCode.SINGLE_ANALYSIS: BillingOffer(
        code=BillingOfferCode.SINGLE_ANALYSIS,
        amount_cents=1_900,
        currency="eur",
        credit_count=1,
        credits_expire_after_days=None,
    ),
    BillingOfferCode.SEARCH_PACK: BillingOffer(
        code=BillingOfferCode.SEARCH_PACK,
        amount_cents=3_900,
        currency="eur",
        credit_count=3,
        credits_expire_after_days=365,
    ),
}


def stripe_price_id(settings: Settings, offer_code: BillingOfferCode) -> str | None:
    if offer_code == BillingOfferCode.SINGLE_ANALYSIS:
        return settings.stripe_single_analysis_price_id
    return settings.stripe_search_pack_price_id
