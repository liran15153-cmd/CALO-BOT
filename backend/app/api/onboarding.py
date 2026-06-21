from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import OnboardingPayload
from backend.app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("")
def get_onboarding(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    service = ProfileService(db)
    profile = service.get_profile_for_user(user.id)
    if profile is None:
        return {"completed": False, "profile": None}
    return {"completed": True, "profile": service.to_response(profile).model_dump()}


@router.post("")
def save_onboarding(
    payload: OnboardingPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    service = ProfileService(db)
    profile = service.upsert_onboarding(payload, user_id=user.id)
    return {"completed": True, "profile": service.to_response(profile).model_dump()}
