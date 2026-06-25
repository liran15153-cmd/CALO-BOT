from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import BodyMetricRequest, BodyMetricResponse
from backend.app.services.body_metric_service import BodyMetricService


router = APIRouter(prefix="/api/body-metrics", tags=["body-metrics"])


@router.post("", response_model=BodyMetricResponse)
def create_body_metric(
    payload: BodyMetricRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    metric = BodyMetricService(db).create(user_id=user.id, request=payload)
    return BodyMetricService.serialize(metric)


@router.get("/recent", response_model=list[BodyMetricResponse])
def recent_body_metrics(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    metrics = BodyMetricService(db).recent(user_id=user.id, limit=limit)
    return [BodyMetricService.serialize(metric) for metric in metrics]


@router.get("/latest", response_model=BodyMetricResponse)
def latest_body_metric(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    metric = BodyMetricService(db).latest(user_id=user.id)
    if metric is None:
        raise HTTPException(status_code=404, detail="מדד גוף לא נמצא")
    return BodyMetricService.serialize(metric)
