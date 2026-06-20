from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.schemas import UsageResponse
from backend.app.services.usage_service import UsageService

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("", response_model=UsageResponse)
def usage(db: Session = Depends(get_db)) -> dict:
    return UsageService(db).daily_totals()
