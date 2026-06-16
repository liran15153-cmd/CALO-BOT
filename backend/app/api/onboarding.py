from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.schemas import OnboardingPayload
from backend.app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("")
def get_onboarding(db: Session = Depends(get_db)) -> dict[str, Any]:
    service = ProfileService(db)
    profile = service.get_profile()
    if profile is None:
        return {"completed": False, "profile": None}
    return {"completed": True, "profile": service.to_response(profile).model_dump()}


@router.post("")
def save_onboarding(payload: OnboardingPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    service = ProfileService(db)
    profile = service.upsert_onboarding(payload)
    return {"completed": True, "profile": service.to_response(profile).model_dump()}

