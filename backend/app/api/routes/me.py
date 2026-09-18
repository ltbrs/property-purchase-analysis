from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.auth import CurrentUserId
from app.core.database import DatabaseSession
from app.property.models import UserRecord

router = APIRouter(prefix="/me", tags=["account"])


class UserPreferencesRead(BaseModel):
    show_demo_case: bool


class UserPreferencesUpdate(BaseModel):
    show_demo_case: bool


@router.get("/preferences", response_model=UserPreferencesRead)
def get_user_preferences(
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> UserPreferencesRead:
    user = session.get(UserRecord, current_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserPreferencesRead(show_demo_case=user.show_demo_case)


@router.patch("/preferences", response_model=UserPreferencesRead)
def update_user_preferences(
    payload: UserPreferencesUpdate,
    current_user_id: CurrentUserId,
    session: DatabaseSession,
) -> UserPreferencesRead:
    user = session.get(UserRecord, current_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.show_demo_case = payload.show_demo_case
    session.commit()
    return UserPreferencesRead(show_demo_case=user.show_demo_case)
