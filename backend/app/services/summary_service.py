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
        next_action = "תעד היום ארוחה אחת או אימון אחד." if not workouts and not meals else "תכנן את האימון הבא או ארוחה אחת עם דגש על חלבון."
        if pain_flags:
            next_action = "הימנע מתנועות כואבות ושקול פנייה לאיש מקצוע אם הכאב נמשך."
        return {
            "summary": f"היום הושלמו {completed} אימונים ותועדו {len(meals)} ארוחות.",
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
        summary_text = f"סיכום שבועי: {completed} אימונים הושלמו, {missed} אימונים פוספסו, {len(meals)} ארוחות תועדו."
        next_action = "קבע עכשיו את האימון הבא והמשך לתעד ארוחות עם דגש על חלבון."
        metrics = {
            "workouts_completed": completed,
            "missed_workouts": missed,
            "consistency_percentage": consistency,
            "meals_logged": len(meals),
        }
        records = self.db.scalars(
            select(WeeklySummary)
            .where(
                WeeklySummary.user_id == user_id,
                WeeklySummary.week_start == week_start,
                WeeklySummary.week_end == week_end,
            )
            .order_by(WeeklySummary.id)
        ).all()
        record = records[0] if records else None
        for duplicate in records[1:]:
            self.db.delete(duplicate)
        if record is None:
            record = WeeklySummary(user_id=user_id, week_start=week_start, week_end=week_end)
            self.db.add(record)
        record.summary_text = summary_text
        record.metrics_json = metrics
        record.next_action = next_action
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
