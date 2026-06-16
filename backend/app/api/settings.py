from fastapi import APIRouter, Depends
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
def reset_data(db: Session = Depends(get_db)) -> dict:
    deleted_records = SettingsService(db).reset_local_data()
    return {"deleted_records": deleted_records, "message": "Local coaching data reset."}
