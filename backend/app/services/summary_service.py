from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Meal, WeeklySummary, WorkoutLog
from backend.app.services.usage_service import UsageService


class SummaryService:
    def __init__(self, db: Session):
        self.db = db

    def daily_summary(self, user_id: int, target_date: date | None = None) -> dict:
        day = target_date or date.today()
        workouts = self.db.scalars(
            select(WorkoutLog).where(WorkoutLog.user_id == user_id, WorkoutLog.logged_on == day)
        ).all()
        meals = self.db.scalars(select(Meal).where(Meal.user_id == user_id, Meal.eaten_on == day)).all()
        calories_min = sum(meal.calories_min or 0 for meal in meals) or None
        calories_max = sum(meal.calories_max or 0 for meal in meals) or None
        protein_min = sum(meal.protein_min or 0 for meal in meals) or None
        protein_max = sum(meal.protein_max or 0 for meal in meals) or None
        completed = sum(1 for log in workouts if log.status == "completed")
        pain_flags = sum(1 for log in workouts if log.pain_flag)
        next_action = "Log one meal or workout today." if not workouts and not meals else "Plan the next concrete workout or protein-focused meal."
        if pain_flags:
            next_action = "Avoid painful movements and consider qualified guidance if pain persists."
        return {
            "summary": f"{completed} workouts completed and {len(meals)} meals logged today.",
            "metrics": {
                "date": day.isoformat(),
                "workouts_completed": completed,
                "workouts_logged": len(workouts),
                "meals_logged": len(meals),
                "calories_range": [calories_min, calories_max],
                "protein_range": [protein_min, protein_max],
                "pain_flags": pain_flags,
            },
            "next_action": next_action,
        }

    def weekly_summary(self, user_id: int, target_date: date | None = None) -> WeeklySummary:
        today = target_date or date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        workouts = self.db.scalars(
            select(WorkoutLog).where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.logged_on >= week_start,
                WorkoutLog.logged_on <= week_end,
            )
        ).all()
        meals = self.db.scalars(
            select(Meal).where(Meal.user_id == user_id, Meal.eaten_on >= week_start, Meal.eaten_on <= week_end)
        ).all()
        completed = sum(1 for log in workouts if log.status == "completed")
        missed = sum(1 for log in workouts if log.status == "skipped")
        consistency = round((completed / max(1, completed + missed)) * 100)
        summary_text = f"Weekly review: {completed} completed workouts, {missed} missed workouts, {len(meals)} meals logged."
        next_action = "Schedule the next workout now and keep logging protein-focused meals."
        record = WeeklySummary(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            summary_text=summary_text,
            metrics_json={
                "workouts_completed": completed,
                "missed_workouts": missed,
                "consistency_percentage": consistency,
                "meals_logged": len(meals),
            },
            next_action=next_action,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        UsageService(self.db).record(
            user_id=user_id,
            task="summary",
            provider="local",
            model=None,
            estimated_tokens_in=0,
            estimated_tokens_out=0,
        )
        return record
