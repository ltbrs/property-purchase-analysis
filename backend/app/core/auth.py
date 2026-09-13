import hmac
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any
from urllib.parse import unquote
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import DatabaseSession
from app.property.models import AuthAccountRecord, UserRecord

PROVIDER_PATTERN = re.compile(r"[a-z0-9_-]{1,50}")
SUPPORTED_JWT_ALGORITHMS = ("ES256", "RS256")


@dataclass(frozen=True)
class SupabaseIdentity:
    user_id: UUID
    name: str | None
    email: str | None
    email_verified: bool


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=600)


def _optional_claim(value: object, max_length: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or len(normalized) > max_length:
        return None
    return normalized


def _verify_supabase_access_token(token: str) -> SupabaseIdentity:
    settings = get_settings()
    if settings.supabase_url is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured",
        )

    issuer = f"{settings.supabase_url}/auth/v1"
    try:
        signing_key = _jwks_client(f"{issuer}/.well-known/jwks.json").get_signing_key_from_jwt(
            token
        )
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=list(SUPPORTED_JWT_ALGORITHMS),
            audience=settings.supabase_jwt_audience,
            issuer=issuer,
            options={"require": ["aud", "exp", "iat", "iss", "sub"]},
        )
        user_id = UUID(str(claims["sub"]))
    except (InvalidTokenError, PyJWKClientError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    if claims.get("role") != "authenticated" or claims.get("is_anonymous") is True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = _optional_claim(claims.get("email"), 254)
    user_metadata = claims.get("user_metadata")
    metadata = user_metadata if isinstance(user_metadata, dict) else {}
    name = _optional_claim(metadata.get("full_name"), 200) or _optional_claim(
        metadata.get("name"), 200
    )
    return SupabaseIdentity(
        user_id=user_id,
        name=name,
        email=email.casefold() if email else None,
        email_verified=email is not None,
    )


def _bearer_token(authorization: str | None) -> str | None:
    if authorization is None or len(authorization) > 16_384:
        return None
    scheme, separator, token = authorization.partition(" ")
    if separator and scheme.casefold() == "bearer" and token.strip():
        return token.strip()
    return None


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


def _sync_supabase_identity(session: Session, identity: SupabaseIdentity) -> None:
    user = session.get(UserRecord, identity.user_id)
    if user is None:
        user = UserRecord(id=identity.user_id)
        session.add(user)

    if identity.name is not None:
        user.name = identity.name
    if identity.email is not None:
        user.email = identity.email
        user.email_verified = identity.email_verified
    session.commit()


def get_current_user_id(
    session: DatabaseSession,
    authorization: Annotated[str | None, Header()] = None,
    x_backend_proxy_secret: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_name: Annotated[str | None, Header()] = None,
    x_user_email: Annotated[str | None, Header()] = None,
    x_user_email_verified: Annotated[bool, Header()] = False,
    x_auth_provider: Annotated[str | None, Header()] = None,
    x_auth_provider_account_id: Annotated[str | None, Header()] = None,
) -> UUID:
    """Verify a Supabase session and return its application user identifier.

    Local tests and development without Supabase configured retain the previous
    header boundary. Production never accepts caller-provided user identifiers.
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

    if settings.supabase_url is not None:
        token = _bearer_token(authorization)
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        identity = _verify_supabase_access_token(token)
        _sync_supabase_identity(session, identity)
        return identity.user_id

    if settings.app_env == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not configured",
        )

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
