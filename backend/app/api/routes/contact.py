import hmac
from datetime import UTC, datetime
from hashlib import sha256
from typing import cast

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter

from app.contact.models import ContactSubmissionAccepted, ContactSubmissionCreate
from app.contact.repository import ContactRepository
from app.core.config import get_settings
from app.core.database import DatabaseSession

router = APIRouter(prefix="/contact", tags=["contact"])


def _rate_limit_secret() -> str:
    configured_secret = get_settings().contact_proxy_secret
    return (
        configured_secret.get_secret_value()
        if configured_secret is not None
        else "acquora-contact-development-only"
    )


def _contact_client_ip(request: Request) -> str:
    settings = get_settings()
    configured_secret = settings.contact_proxy_secret
    if (
        configured_secret is not None
        and hmac.compare_digest(
            request.headers.get("X-Contact-Proxy-Secret", ""),
            configured_secret.get_secret_value(),
        )
        and (forwarded_ip := request.headers.get("X-Contact-Client-Ip"))
    ):
        return forwarded_ip
    return request.client.host if request.client is not None else "unknown"


def _contact_rate_limit_key(request: Request) -> str:
    return hmac.new(
        _rate_limit_secret().encode(),
        _contact_client_ip(request).encode(),
        sha256,
    ).hexdigest()


limiter = Limiter(key_func=_contact_rate_limit_key, headers_enabled=True)


def _short_rate_limit() -> str:
    return f"{get_settings().contact_short_rate_limit}/15 minutes"


def _daily_rate_limit() -> str:
    return f"{get_settings().contact_daily_rate_limit}/day"


def rate_limit_exceeded_handler(request: Request, _: Exception) -> Response:
    response = JSONResponse(
        {"detail": "Too many contact requests"},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Cache-Control": "no-store"},
    )
    return cast(
        Response,
        request.app.state.limiter._inject_headers(response, request.state.view_rate_limit),
    )


@router.post(
    "",
    response_model=ContactSubmissionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit(_daily_rate_limit)
@limiter.limit(_short_rate_limit)
def submit_contact_request(
    payload: ContactSubmissionCreate,
    request: Request,
    response: Response,
    session: DatabaseSession,
    x_contact_proxy_secret: str | None = Header(default=None),
    x_contact_client_ip: str | None = Header(default=None),
) -> ContactSubmissionAccepted:
    settings = get_settings()
    configured_secret = settings.contact_proxy_secret
    if configured_secret is None and settings.app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Contact service is not configured",
        )

    secret = _rate_limit_secret()
    if configured_secret is not None and not hmac.compare_digest(
        x_contact_proxy_secret or "", secret
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    client_ip = _contact_client_ip(request)
    ip_hash = hmac.new(secret.encode(), client_ip.encode(), sha256).hexdigest()
    now = datetime.now(UTC)
    repository = ContactRepository(session)

    if payload.website:
        return ContactSubmissionAccepted()

    repository.create_submission(payload, ip_hash=ip_hash, now=now)
    response.headers["Cache-Control"] = "no-store"
    return ContactSubmissionAccepted()
