from pathlib import Path

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db import get_db
from backend.app.schemas import ResetResponse, SettingsResponse
from backend.app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def settings() -> dict:
    return SettingsService.provider_status(get_settings())


@router.get("/export")
def export_data(db: Session = Depends(get_db)) -> dict:
    return SettingsService(db).export_local_data()


@router.post("/reset", response_model=ResetResponse)
def reset_data(request: Request, db: Session = Depends(get_db)) -> dict:
    upload_root = Path(getattr(request.app.state, "upload_root", Path("data/uploads")))
    deleted_records = SettingsService(db).reset_local_data(upload_root=upload_root)
    return {"deleted_records": deleted_records, "message": "הנתונים המקומיים של המאמן אופסו."}
