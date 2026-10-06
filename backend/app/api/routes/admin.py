from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.api.routes.billing import _billing_rate_limit_key
from app.api.routes.contact import limiter
from app.billing.models import AnalysisCreditRecord, AnalysisCreditSource, StripePurchaseRecord
from app.core.auth import CurrentUserId
from app.core.database import DatabaseSession
from app.property.models import UserRecord

ADMIN_EMAIL = "lambertbruyas@gmail.com"
router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user_id: CurrentUserId, session: DatabaseSession) -> UUID:
    admin = session.get(UserRecord, current_user_id)
    if (
        admin is None
        or not admin.is_admin
        or not admin.email_verified
        or admin.email != ADMIN_EMAIL
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        auth_email = session.execute(
            text(
                "SELECT email FROM auth.users "
                "WHERE id = :user_id AND email_confirmed_at IS NOT NULL"
            ),
            {"user_id": current_user_id},
        ).scalar_one_or_none()
        if auth_email is None or auth_email.casefold() != ADMIN_EMAIL:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return current_user_id


AdminUserId = Annotated[UUID, Depends(require_admin)]


class AdminStatusRead(BaseModel):
    is_admin: bool = True


class AdminUserRead(BaseModel):
    id: UUID
    email: str | None
    name: str | None
    created_at: datetime
    email_verified: bool
    plan: str | None
    available_credits: int
    paid_credits: int
    granted_credits: int


class AdminUsersRead(BaseModel):
    users: list[AdminUserRead]
    total: int
    page: int
    page_size: int


class AdminCreditGrant(BaseModel):
    count: int = Field(ge=1, le=10)
    reason: str = Field(min_length=5, max_length=200)


class AdminCreditGrantRead(BaseModel):
    granted: int
    available_credits: int


def _auth_users(
    session: Session, page: int, page_size: int, search: str
) -> tuple[list[tuple[UUID, str | None, str | None, datetime, bool]], int]:
    offset = (page - 1) * page_size
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        # auth.users is deliberately accessed only by the backend's database role.
        # It is not exposed through the Supabase Data API.
        pattern = f"%{search}%"
        total = session.execute(
            text("SELECT count(*) FROM auth.users WHERE :search = '' OR email ILIKE :pattern"),
            {"search": search, "pattern": pattern},
        ).scalar_one()
        rows = session.execute(
            text(
                "SELECT a.id, a.email, u.name, a.created_at, "
                "(a.email_confirmed_at IS NOT NULL) AS email_verified "
                "FROM auth.users AS a LEFT JOIN public.users AS u ON u.id = a.id "
                "WHERE :search = '' OR a.email ILIKE :pattern "
                "ORDER BY a.created_at DESC, a.id DESC LIMIT :limit OFFSET :offset"
            ),
            {"search": search, "pattern": pattern, "limit": page_size, "offset": offset},
        ).all()
        return [(UUID(str(r[0])), r[1], r[2], r[3], r[4]) for r in rows], int(total)

    # The isolated SQLite test database has no Supabase Auth schema.
    query = select(UserRecord)
    if search:
        query = query.where(UserRecord.email.ilike(f"%{search}%"))
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    users = session.scalars(
        query.order_by(UserRecord.created_at.desc(), UserRecord.id.desc())
        .limit(page_size)
        .offset(offset)
    ).all()
    return [(u.id, u.email, u.name, u.created_at, u.email_verified) for u in users], int(total)


@router.get("/me", response_model=AdminStatusRead)
def get_admin_status(response: Response, admin_id: AdminUserId) -> AdminStatusRead:
    response.headers["Cache-Control"] = "no-store"
    return AdminStatusRead()


@router.get("/users", response_model=AdminUsersRead)
def list_users(
    response: Response,
    admin_id: AdminUserId,
    session: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    search: Annotated[str, Query(max_length=254)] = "",
) -> AdminUsersRead:
    response.headers["Cache-Control"] = "no-store"
    auth_users, total = _auth_users(session, page, page_size, search.strip())
    user_ids = [user[0] for user in auth_users]
    if not user_ids:
        return AdminUsersRead(users=[], total=total, page=page, page_size=page_size)

    now = datetime.now(UTC)
    credits = session.execute(
        select(
            AnalysisCreditRecord.user_id,
            AnalysisCreditRecord.source,
            AnalysisCreditRecord.consumed_at,
            AnalysisCreditRecord.expires_at,
        ).where(AnalysisCreditRecord.user_id.in_(user_ids))
    ).all()
    credit_counts: dict[UUID, dict[str, int]] = {
        user_id: {"available": 0, "paid": 0, "granted": 0} for user_id in user_ids
    }
    for user_id, source, consumed_at, expires_at in credits:
        counts = credit_counts[user_id]
        if source == AnalysisCreditSource.MANUAL_GRANT.value:
            counts["granted"] += 1
        else:
            counts["paid"] += 1
        if consumed_at is None and (expires_at is None or expires_at > now):
            counts["available"] += 1

    purchases = session.execute(
        select(StripePurchaseRecord.user_id, StripePurchaseRecord.offer_code)
        .where(
            StripePurchaseRecord.user_id.in_(user_ids),
            StripePurchaseRecord.status == "paid",
        )
        .order_by(StripePurchaseRecord.created_at.desc(), StripePurchaseRecord.id.desc())
    ).all()
    latest_plan: dict[UUID, str] = {}
    for user_id, offer_code in purchases:
        latest_plan.setdefault(user_id, offer_code)

    return AdminUsersRead(
        users=[
            AdminUserRead(
                id=user_id,
                email=email,
                name=name,
                created_at=created_at,
                email_verified=email_verified,
                plan=latest_plan.get(user_id),
                available_credits=credit_counts[user_id]["available"],
                paid_credits=credit_counts[user_id]["paid"],
                granted_credits=credit_counts[user_id]["granted"],
            )
            for user_id, email, name, created_at, email_verified in auth_users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/users/{user_id}/credits", response_model=AdminCreditGrantRead)
@limiter.limit("20/hour", key_func=_billing_rate_limit_key)
def grant_credits(
    user_id: UUID,
    payload: AdminCreditGrant,
    request: Request,
    response: Response,
    admin_id: AdminUserId,
    session: DatabaseSession,
) -> AdminCreditGrantRead:
    response.headers["Cache-Control"] = "no-store"
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        auth_user = session.execute(
            text("SELECT email, email_confirmed_at FROM auth.users WHERE id = :user_id"),
            {"user_id": user_id},
        ).one_or_none()
        if auth_user is None:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        user = session.get(UserRecord, user_id)
        if user is None:
            user = UserRecord(
                id=user_id,
                email=auth_user.email.casefold() if auth_user.email else None,
                email_verified=auth_user.email_confirmed_at is not None,
            )
            session.add(user)
            session.flush()
    elif session.get(UserRecord, user_id) is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    reason = payload.reason.strip()
    if len(reason) < 5:
        raise HTTPException(status_code=422, detail="Précisez la raison du crédit.")
    for _ in range(payload.count):
        session.add(
            AnalysisCreditRecord(
                user_id=user_id,
                source=AnalysisCreditSource.MANUAL_GRANT.value,
                grant_note=reason,
                granted_by_user_id=admin_id,
            )
        )
    session.commit()
    available = session.scalar(
        select(func.count())
        .select_from(AnalysisCreditRecord)
        .where(
            AnalysisCreditRecord.user_id == user_id,
            AnalysisCreditRecord.consumed_at.is_(None),
            or_(
                AnalysisCreditRecord.expires_at.is_(None),
                AnalysisCreditRecord.expires_at > datetime.now(UTC),
            ),
        )
    )
    return AdminCreditGrantRead(granted=payload.count, available_credits=int(available or 0))
