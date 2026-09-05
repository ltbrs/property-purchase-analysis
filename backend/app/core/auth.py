import hmac
import re
from typing import Annotated
from urllib.parse import unquote
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import DatabaseSession
from app.property.models import AuthAccountRecord, UserRecord

PROVIDER_PATTERN = re.compile(r"[a-z0-9_-]{1,50}")


def _decoded_header(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    decoded = unquote(value).strip()
    if not decoded or len(decoded) > max_length:
        return None
    return decoded


def _sync_authenticated_identity(
    session: Session,
    *,
    user_id: UUID,
    name: str | None,
    email: str | None,
    email_verified: bool,
    provider: str | None,
    provider_account_id: str | None,
) -> None:
    user = session.get(UserRecord, user_id)
    if user is None:
        user = UserRecord(id=user_id)
        session.add(user)

    if name is not None:
        user.name = name
    if email is not None:
        user.email = email.casefold()
        user.email_verified = email_verified

    if provider is not None and provider_account_id is not None:
        account = session.get(AuthAccountRecord, (provider, provider_account_id))
        if account is not None and account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication account mismatch",
            )
        if account is None:
            session.add(
                AuthAccountRecord(
                    provider=provider,
                    provider_account_id=provider_account_id,
                    user_id=user_id,
                )
            )

    session.commit()


def get_current_user_id(
    session: DatabaseSession,
    x_backend_proxy_secret: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
    x_user_email: Annotated[str | None, Header()] = None,
    x_user_email_verified: Annotated[bool, Header()] = False,
    x_auth_provider: Annotated[str | None, Header()] = None,
    x_auth_provider_account_id: Annotated[str | None, Header()] = None,
) -> UUID:
    """Read the identity asserted by the trusted authentication boundary.

    Auth.js asserts this identity through the private Next.js backend proxy.
    Deployments must protect these headers, and clients must never be allowed to
    assert arbitrary identities at the public edge.
    """

    settings = get_settings()
    configured_proxy_secret = settings.backend_proxy_secret
    if configured_proxy_secret is None:
        if settings.app_env == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication boundary is not configured",
            )
    elif not hmac.compare_digest(
        x_backend_proxy_secret or "",
        configured_proxy_secret.get_secret_value(),
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        user_id = UUID(x_user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user",
        ) from error

    provider = _decoded_header(x_auth_provider, 50)
    if provider is not None:
        provider = provider.casefold()
        if PROVIDER_PATTERN.fullmatch(provider) is None:
            provider = None

    _sync_authenticated_identity(
        session,
        user_id=user_id,
        name=_decoded_header(x_user_name, 200),
        email=_decoded_header(x_user_email, 254),
        email_verified=x_user_email_verified,
        provider=provider,
        provider_account_id=_decoded_header(x_auth_provider_account_id, 255),
    )
    return user_id


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
