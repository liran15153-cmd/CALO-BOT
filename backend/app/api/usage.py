from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import UsageResponse
from backend.app.services.usage_service import UsageService

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("", response_model=UsageResponse)
def usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return UsageService(db).daily_totals(user_id=user.id)
