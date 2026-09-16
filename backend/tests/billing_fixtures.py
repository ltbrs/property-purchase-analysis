from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.billing.models import (
    AnalysisAccessRecord,
    AnalysisCreditRecord,
    BillingOfferCode,
    StripePurchaseRecord,
    StripePurchaseStatus,
)


def grant_analysis_access(session: Session, user_id: UUID, case_id: UUID | str) -> None:
    now = datetime.now(UTC)
    purchase = StripePurchaseRecord(
        user_id=user_id,
        offer_code=BillingOfferCode.SINGLE_ANALYSIS.value,
        status=StripePurchaseStatus.PAID.value,
        expected_amount_cents=1_900,
        currency="eur",
        credit_count=1,
        completed_at=now,
    )
    session.add(purchase)
    session.flush()
    credit = AnalysisCreditRecord(
        user_id=user_id,
        purchase_id=purchase.id,
        consumed_by_case_id=UUID(str(case_id)),
        consumed_at=now,
    )
    session.add(credit)
    session.flush()
    session.add(
        AnalysisAccessRecord(
            analysis_case_id=UUID(str(case_id)),
            credit_id=credit.id,
            activated_at=now,
            expires_at=now + timedelta(days=30),
        )
    )
    session.commit()
