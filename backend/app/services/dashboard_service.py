from datetime import date, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import Meal, UserMemory, UserProfile, WorkoutLog, WorkoutPlan
from backend.app.services.profile_service import ProfileService
from backend.app.services.workout_service import WorkoutService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def build_dashboard(self) -> dict[str, Any]:
        profile_service = ProfileService(self.db)
        workout_service = WorkoutService(self.db)
        user = profile_service.get_default_user()
        profile = profile_service.get_profile()
        week_start, week_end = self._current_week_range()
        workouts = self._workouts_for_week(user.id, week_start, week_end)
        meals = self._meals_for_week(user.id, week_start, week_end)
        memories = self._recent_memories(user.id)
        plan = workout_service.current_plan(user_id=user.id)
        calories_min, calories_max = self._nutrition_range(meals)
        nutrition_range = None if calories_min is None or calories_max is None else [calories_min, calories_max]
        completed = sum(1 for log in workouts if log.status == "completed")
        missed = sum(1 for log in workouts if log.status == "skipped")

        return {
            "current_goal": profile.main_goal if profile else None,
            "current_workout_plan": WorkoutService.serialize_plan(plan) if plan else None,
            "completed_workouts_this_week": completed,
            "meals_logged_this_week": len(meals),
            "estimated_nutrition_range": nutrition_range,
            "recent_coach_notes": [memory.content for memory in memories],
            "current_streak": completed,
            "missed_workouts": missed,
            "next_recommended_action": self._next_recommended_action(profile=profile, plan=plan, missed=missed),
        }

    @staticmethod
    def _current_week_range() -> tuple[date, date]:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        return week_start, week_start + timedelta(days=6)

    def _workouts_for_week(self, user_id: int, week_start: date, week_end: date) -> list[WorkoutLog]:
        return list(
            self.db.scalars(
                select(WorkoutLog).where(
                    WorkoutLog.user_id == user_id,
                    WorkoutLog.logged_on >= week_start,
                    WorkoutLog.logged_on <= week_end,
                )
            ).all()
        )

    def _meals_for_week(self, user_id: int, week_start: date, week_end: date) -> list[Meal]:
        return list(
            self.db.scalars(
                select(Meal).where(Meal.user_id == user_id, Meal.eaten_on >= week_start, Meal.eaten_on <= week_end)
            ).all()
        )

    def _recent_memories(self, user_id: int) -> list[UserMemory]:
        return list(
            self.db.scalars(
                select(UserMemory)
                .where(UserMemory.user_id == user_id, UserMemory.is_sensitive.is_(False))
                .order_by(desc(UserMemory.created_at))
                .limit(4)
            ).all()
        )

    @staticmethod
    def _nutrition_range(meals: list[Meal]) -> tuple[int, int] | tuple[None, None]:
        meals_with_estimates = [
            meal for meal in meals if meal.calories_min is not None and meal.calories_max is not None
        ]
        if not meals_with_estimates:
            return None, None
        return (
            sum(meal.calories_min or 0 for meal in meals_with_estimates),
            sum(meal.calories_max or 0 for meal in meals_with_estimates),
        )

    @staticmethod
    def _next_recommended_action(profile: UserProfile | None, plan: WorkoutPlan | None, missed: int) -> str:
        if profile is None:
            return "סיים את האונבורדינג כדי שהמאמן יוכל לבנות את התוכנית הראשונה."
        if missed > 0:
            return "קבע מחדש את האימון שפוספס לפני שאתה מוסיף עוד נפח."
        if plan is None:
            return "צור תוכנית אימון שמתאימה לזמינות השבועית שלך."
        return "בצע את האימון המתוכנן הבא ותעד ארוחה אחת עם דגש על חלבון."
