from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from backend.app.auth import AuthContext, get_auth_context, get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import MealTextRequest
from backend.app.services.file_storage_service import FileStorageService
from backend.app.services.meal_service import MealService

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.get("/recent")
def recent_meals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    service = MealService(db)
    return [service.serialize_meal_with_items(meal) for meal in service.recent_meals(user_id=user.id)]


@router.post("/upload")
async def upload_meal_image(
    request: Request,
    note: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    user = context.user
    upload_root = Path(getattr(request.app.state, "upload_root", Path("data/uploads")))
    try:
        stored_path = await FileStorageService(upload_root, access_token=context.access_token).store_meal_image(
            user_id=user.id,
            owner_key=user.auth_user_id,
            file=file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    meal = MealService(db).create_uploaded_meal(user_id=user.id, image_path=str(stored_path), note=note)
    return MealService.serialize_meal(meal)


@router.post("/{meal_id}/analyze")
def analyze_meal_image(
    meal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    upload_root = Path(getattr(request.app.state, "upload_root", Path("data/uploads")))
    try:
        analysis = MealService(db).analyze_image(
            meal_id,
            upload_root=upload_root,
            user_id=context.user.id,
            access_token=context.access_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MealService.serialize_analysis(analysis)


@router.post("/manual")
def log_manual_meal(
    payload: MealTextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    meal = MealService(db).log_manual_meal(user_id=user.id, request=payload)
    return MealService.serialize_meal(meal)
