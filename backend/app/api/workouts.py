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
workouts_router = APIRouter(prefix="/api/workouts", tags=["workouts"])


@router.post("")
def create_workout_plan(payload: WorkoutPlanRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    service = WorkoutService(db)
    plan = service.generate_plan(user_id=user.id, request=payload)
    return service.serialize_plan_with_rows(plan)


@router.get("/current")
def get_current_workout_plan(db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    service = WorkoutService(db)
    plan = service.current_plan(user_id=user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="אין תוכנית אימון פעילה")
    return service.serialize_plan_with_rows(plan)


@workouts_router.get("/next")
def get_next_workout(db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    next_workout = WorkoutService(db).next_workout(user_id=user.id)
    if next_workout is None:
        raise HTTPException(status_code=404, detail="אין אימון הבא כי אין תוכנית פעילה")
    return next_workout


@logs_router.get("/recent")
def recent_workout_logs(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    user = ProfileService(db).get_default_user()
    logs = WorkoutService(db).recent_logs(user_id=user.id)
    return [WorkoutService.serialize_log(log) for log in logs]


@logs_router.post("")
def create_workout_log(payload: WorkoutLogRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    workout_service = WorkoutService(db)
    try:
        log = workout_service.log_workout(user_id=user.id, request=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    source_text = _workout_log_safety_source(payload, pain_flag=log.pain_flag)
    if source_text:
        safety_result = SafetyService(db).classify(source_text)
        # Record both hard-blocked events and soft pain signals so a logged workout that
        # mentions pain leaves an audit trail, matching the coach chat path.
        if safety_result.flagged or safety_result.event_type == "pain_signal":
            SafetyService(db).record_event(user_id=user.id, source_text=source_text, result=safety_result)
    workout_ids = [log.workout_id] if log.workout_id else None
    adaptation = workout_service.training_status(user_id=user.id, workout_ids=workout_ids)
    return WorkoutService.serialize_log(log, adaptation=adaptation)


def _workout_log_safety_source(payload: WorkoutLogRequest, *, pain_flag: bool) -> str:
    parts = [
        payload.text,
        payload.notes,
        " ".join(exercise.notes or "" for exercise in payload.exercises),
    ]
    source_text = " ".join(part.strip() for part in parts if part and part.strip()).strip()
    if source_text:
        return source_text
    return "כאב דווח בתיעוד אימון מובנה" if pain_flag else ""
