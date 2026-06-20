from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.schemas import WorkoutPlanRequest
from backend.app.services.profile_service import ProfileService
from backend.app.schemas import WorkoutLogRequest
from backend.app.services.safety_service import SafetyService
from backend.app.services.workout_service import WorkoutService

router = APIRouter(prefix="/api/workout-plans", tags=["workout-plans"])
logs_router = APIRouter(prefix="/api/workout-logs", tags=["workout-logs"])


@router.post("")
def create_workout_plan(payload: WorkoutPlanRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    plan = WorkoutService(db).generate_plan(user_id=user.id, request=payload)
    return WorkoutService.serialize_plan(plan)


@router.get("/current")
def get_current_workout_plan(db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    plan = WorkoutService(db).current_plan(user_id=user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="אין תוכנית אימון פעילה")
    return WorkoutService.serialize_plan(plan)


@logs_router.post("")
def create_workout_log(payload: WorkoutLogRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    log = WorkoutService(db).parse_log(user_id=user.id, request=payload)
    if log.pain_flag:
        safety_result = SafetyService(db).classify(payload.text)
        if safety_result.flagged:
            SafetyService(db).record_event(user_id=user.id, source_text=payload.text, result=safety_result)
    return WorkoutService.serialize_log(log)
