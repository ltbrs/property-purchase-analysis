from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status


def get_current_user_id(x_user_id: Annotated[str | None, Header()] = None) -> UUID:
    """Read the identity asserted by the trusted authentication boundary.

    The MVP does not own sign-in yet. Deployments must have their authentication
    layer replace and protect this header; clients must never be allowed to assert
    arbitrary identities at the public edge.
    """

    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        return UUID(x_user_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user",
        ) from error


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
