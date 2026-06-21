from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    return DashboardService(db).build_dashboard(user_id=user.id)
