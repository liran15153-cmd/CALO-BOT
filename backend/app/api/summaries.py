from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.services.summary_service import SummaryService

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.get("/daily")
def daily_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return SummaryService(db).daily_summary(user_id=user.id)


@router.get("/weekly/current")
def current_weekly_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return SummaryService(db).current_weekly_summary(user_id=user.id)


@router.get("/weekly")
def weekly_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    summary = SummaryService(db).weekly_summary(user_id=user.id)
    return {
        "summary": summary.summary_text,
        "metrics": summary.metrics_json,
        "next_action": summary.next_action,
        "week_start": summary.week_start.isoformat(),
        "week_end": summary.week_end.isoformat(),
    }
