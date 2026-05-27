from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.schemas.profile import ProfileOut, ProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(user: CurrentUser, session: SessionDep) -> ProfileOut:
    profile = ProfileService(session).get(user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileOut.model_validate(profile)


@router.put("", response_model=ProfileOut)
def update_profile(payload: ProfileUpdate, user: CurrentUser, session: SessionDep) -> ProfileOut:
    profile = ProfileService(session).update(user.id, payload)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileOut.model_validate(profile)
