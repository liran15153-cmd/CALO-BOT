from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.auth import AuthContext, get_auth_context, get_current_user
from backend.app.config import get_settings
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import ResetResponse, SettingsResponse
from backend.app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def settings() -> dict:
    return SettingsService.provider_status(get_settings())


@router.get("/export")
def export_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    return SettingsService(db).export_local_data(user_id=user.id)


@router.post("/reset", response_model=ResetResponse)
def reset_data(
    request: Request,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    upload_root = Path(getattr(request.app.state, "upload_root", Path("data/uploads")))
    try:
        deleted_records = SettingsService(db).reset_local_data(
            upload_root=upload_root,
            user_id=context.user.id,
            access_token=context.access_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"deleted_records": deleted_records, "message": "הנתונים המקומיים של המאמן אופסו."}
