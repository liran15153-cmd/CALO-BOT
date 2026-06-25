from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import ActivateWorkoutPlanRequest, WorkoutPlanRequest
from backend.app.services.pending_action_service import PendingActionService
from backend.app.services.pain_text import extract_pain_area, vague_pain_plan_clarification_response
from backend.app.schemas import WorkoutLogRequest
from backend.app.services.safety_service import SafetyService
from backend.app.services.workout_plan_builder import is_persistent_plan_type, is_single_workout_plan
from backend.app.services.workout_service import WorkoutService

router = APIRouter(prefix="/api/workout-plans", tags=["workout-plans"])
logs_router = APIRouter(prefix="/api/workout-logs", tags=["workout-logs"])
workouts_router = APIRouter(prefix="/api/workouts", tags=["workouts"])


@router.post("")
def create_workout_plan(
    payload: WorkoutPlanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    safety_source = _workout_plan_safety_source(payload)
    safety_result = SafetyService(db).classify(safety_source)
    if safety_result.event_type:
        SafetyService(db).record_event(user_id=user.id, source_text=safety_source, result=safety_result)
    if safety_result.flagged:
        raise HTTPException(status_code=400, detail=safety_result.response)
    planning_payload = payload
    if safety_result.event_type == "pain_signal" and not payload.limitations:
        pain_area = extract_pain_area(safety_source)
        if pain_area is None:
            raise HTTPException(status_code=400, detail=vague_pain_plan_clarification_response())
        planning_payload = payload.model_copy(update={"limitations": f"רגישות ב{pain_area}"})

    service = WorkoutService(db)
    current_before = service.current_plan(user_id=user.id)
    plan = service.generate_plan(user_id=user.id, request=planning_payload)
    response = service.serialize_plan_with_rows(plan)
    if (
        current_before is not None
        and not is_single_workout_plan((current_before.plan_json or {}).get("plan_type"))
        and current_before.id != plan.id
        and not plan.is_current
        and is_persistent_plan_type(response.get("plan_type"))
    ):
        pending = PendingActionService(db).create_workout_plan_replacement(
            user_id=user.id,
            candidate_plan_id=plan.id,
            current_plan_id=current_before.id,
        )
        response["pending_action"] = PendingActionService(db).serialize(pending)
    return response


@router.get("/current")
def get_current_workout_plan(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    service = WorkoutService(db)
    plan = service.current_plan(user_id=user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="אין תוכנית אימון פעילה")
    return service.serialize_plan_with_rows(plan)


@router.post("/{plan_id}/activate")
def activate_workout_plan(
    plan_id: int,
    payload: ActivateWorkoutPlanRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    service = WorkoutService(db)
    try:
        plan = service.activate_plan(
            user_id=user.id,
            plan_id=plan_id,
            delete_previous=True if payload is None else payload.delete_previous,
        )
    except ValueError as exc:
        status_code = 400 if "single workout" in str(exc).lower() else 404
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return service.serialize_plan_with_rows(plan)


@router.delete("/{plan_id}", status_code=204)
def delete_workout_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    service = WorkoutService(db)
    try:
        service.delete_plan(user_id=user.id, plan_id=plan_id)
    except ValueError as exc:
        status_code = 400 if "active" in str(exc).lower() else 404
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return Response(status_code=204)


@workouts_router.get("/next")
def get_next_workout(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    next_workout = WorkoutService(db).next_workout(user_id=user.id)
    if next_workout is None:
        raise HTTPException(status_code=404, detail="אין אימון הבא כי אין תוכנית פעילה")
    return next_workout


@logs_router.get("/recent")
def recent_workout_logs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    logs = WorkoutService(db).recent_logs(user_id=user.id)
    return [WorkoutService.serialize_log(log) for log in logs]


@logs_router.post("")
def create_workout_log(
    payload: WorkoutLogRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
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
        if safety_result.flagged or safety_result.event_type:
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


def _workout_plan_safety_source(payload: WorkoutPlanRequest) -> str:
    parts = [payload.prompt, payload.limitations]
    return " ".join(part.strip() for part in parts if part and part.strip()).strip()
