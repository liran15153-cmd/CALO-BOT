from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.schemas import MealTextRequest
from backend.app.services.file_storage_service import FileStorageService
from backend.app.services.meal_service import MealService
from backend.app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.post("/upload")
async def upload_meal_image(
    request: Request,
    note: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    user = ProfileService(db).get_default_user()
    upload_root = Path(getattr(request.app.state, "upload_root", Path("data/uploads")))
    try:
        stored_path = await FileStorageService(upload_root).store_meal_image(user_id=user.id, file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    meal = MealService(db).create_uploaded_meal(user_id=user.id, image_path=str(stored_path), note=note)
    return MealService.serialize_meal(meal)


@router.post("/{meal_id}/analyze")
def analyze_meal_image(meal_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        analysis = MealService(db).analyze_image(meal_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MealService.serialize_analysis(analysis)


@router.post("/manual")
def log_manual_meal(payload: MealTextRequest, db: Session = Depends(get_db)) -> dict:
    user = ProfileService(db).get_default_user()
    meal = MealService(db).log_manual_meal(user_id=user.id, request=payload)
    return MealService.serialize_meal(meal)
