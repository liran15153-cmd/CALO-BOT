from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models import Meal, UserMemory, WorkoutLog
from backend.app.services.profile_service import ProfileService
from backend.app.services.workout_service import WorkoutService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    profile = ProfileService(db).get_profile()
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=6)
    workouts = db.scalars(
        select(WorkoutLog).where(
            WorkoutLog.user_id == user.id,
            WorkoutLog.logged_on >= week_start,
            WorkoutLog.logged_on <= week_end,
        )
    ).all()
    meals = db.scalars(
        select(Meal).where(Meal.user_id == user.id, Meal.eaten_on >= week_start, Meal.eaten_on <= week_end)
    ).all()
    memories = db.scalars(select(UserMemory).where(UserMemory.user_id == user.id).limit(4)).all()
    plan = WorkoutService(db).current_plan(user_id=user.id)
    calories_min = sum(meal.calories_min or 0 for meal in meals) or None
    calories_max = sum(meal.calories_max or 0 for meal in meals) or None
    completed = sum(1 for log in workouts if log.status == "completed")
    missed = sum(1 for log in workouts if log.status == "skipped")
    return {
        "current_goal": profile.main_goal if profile else None,
        "current_workout_plan": WorkoutService.serialize_plan(plan) if plan else None,
        "completed_workouts_this_week": completed,
        "meals_logged_this_week": len(meals),
        "estimated_nutrition_range": [calories_min, calories_max],
        "recent_coach_notes": [memory.content for memory in memories],
        "current_streak": completed,
        "missed_workouts": missed,
        "next_recommended_action": "Complete the next planned workout and log one protein-focused meal.",
    }

