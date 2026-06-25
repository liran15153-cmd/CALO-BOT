from datetime import date, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import Meal, User, UserProfile, WorkoutLog, WorkoutPlan
from backend.app.services.profile_service import ProfileService
from backend.app.services.workout_service import WorkoutService


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def build_dashboard(self, user_id: int | None = None) -> dict[str, Any]:
        profile_service = ProfileService(self.db)
        workout_service = WorkoutService(self.db)
        user = profile_service.get_default_user() if user_id is None else self.db.get(User, user_id)
        if user is None:
            raise ValueError("User not found")
        profile = profile_service.get_profile_for_user(user.id)
        week_start, week_end = self._current_week_range()
        workouts = self._workouts_for_week(user.id, week_start, week_end)
        meals = self._meals_for_week(user.id, week_start, week_end)
        today = date.today()
        today_meals = [meal for meal in meals if meal.eaten_on == today]
        today_workouts = [workout for workout in workouts if workout.logged_on == today]
        active_dates = self._activity_dates(user.id, today=today)
        plan = workout_service.current_plan(user_id=user.id)
        calories_min, calories_max = self._nutrition_range(meals)
        nutrition_range = None if calories_min is None or calories_max is None else [calories_min, calories_max]
        protein_min, protein_max = self._protein_range(today_meals)
        protein_range_today = None if protein_min is None or protein_max is None else [protein_min, protein_max]
        completed = sum(1 for log in workouts if log.status == "completed")
        missed = sum(1 for log in workouts if log.status == "skipped")
        next_workout = workout_service.next_workout(user_id=user.id) if plan else None
        next_workout_summary = self._next_workout_summary(next_workout)
        current_goal = plan.goal if plan else (profile.main_goal if profile else None)

        return {
            "current_goal": current_goal,
            "current_workout_plan": workout_service.serialize_plan_with_rows(plan) if plan else None,
            "next_workout": next_workout_summary,
            "completed_workouts_this_week": completed,
            "meals_logged_this_week": len(meals),
            "meals_logged_today": len(today_meals),
            "estimated_nutrition_range": nutrition_range,
            "estimated_protein_range_today": protein_range_today,
            "nutrition_action": self._nutrition_action(today_meals=today_meals, today_workouts=today_workouts),
            "current_streak": self._current_streak(active_dates=active_dates, today=today),
            "missed_workouts": missed,
            "next_recommended_action": self._next_recommended_action(
                profile=profile,
                plan=plan,
                next_workout=next_workout_summary,
            ),
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

    def _activity_dates(self, user_id: int, *, today: date, lookback_days: int = 30) -> set[date]:
        start = today - timedelta(days=lookback_days)
        workout_dates = self.db.scalars(
            select(WorkoutLog.logged_on).where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.logged_on >= start,
                WorkoutLog.logged_on <= today,
                WorkoutLog.status.in_(["completed", "partial", "modified"]),
            )
        ).all()
        meal_dates = self.db.scalars(
            select(Meal.eaten_on).where(Meal.user_id == user_id, Meal.eaten_on >= start, Meal.eaten_on <= today)
        ).all()
        return {activity_date for activity_date in [*workout_dates, *meal_dates] if activity_date is not None}

    @staticmethod
    def _current_streak(*, active_dates: set[date], today: date) -> int:
        streak = 0
        cursor = today
        while cursor in active_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

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
    def _protein_range(meals: list[Meal]) -> tuple[int, int] | tuple[None, None]:
        meals_with_estimates = [meal for meal in meals if meal.protein_min is not None and meal.protein_max is not None]
        if not meals_with_estimates:
            return None, None
        return (
            sum(meal.protein_min or 0 for meal in meals_with_estimates),
            sum(meal.protein_max or 0 for meal in meals_with_estimates),
        )

    @staticmethod
    def _nutrition_action(*, today_meals: list[Meal], today_workouts: list[WorkoutLog]) -> str:
        if not today_meals:
            if any(log.status == "completed" for log in today_workouts):
                return "לתעד ארוחה אחת היום עם עוגן חלבון אחרי האימון, כטווח משוער ולא כמספר מדויק."
            return "לתעד ארוחה אחת היום עם טווח משוער, בלי לרדוף אחרי דיוק קלורי."
        if any(meal.protein_min is not None and meal.protein_max is not None for meal in today_meals):
            return "יש ארוחה מתועדת היום. לשמור על תיעוד פשוט, ואם צריך עוד ארוחה - להתחיל מעוגן חלבון."
        return "יש ארוחה מתועדת היום. בארוחה הבאה כדאי להוסיף כמות משוערת או מקור חלבון כדי לשפר את ההערכה."

    @staticmethod
    def _next_workout_summary(next_workout: dict[str, Any] | None) -> dict[str, Any] | None:
        if not next_workout:
            return None
        adaptation = next_workout.get("adaptation") or {}
        plan = next_workout.get("plan") or {}
        execution_plan = next_workout.get("execution_plan") or {}
        return {
            "id": next_workout.get("id"),
            "name": next_workout.get("name"),
            "plan_id": next_workout.get("plan_id"),
            "plan_name": plan.get("name"),
            "load_signal": adaptation.get("load_signal", "maintain"),
            "signals": adaptation.get("signals", []),
            "exercise_adjustments": adaptation.get("exercise_adjustments", []),
            "next_adjustment": adaptation.get("next_adjustment", "שמור על התוכנית הנוכחית."),
            "plan_adjustment": adaptation.get("plan_adjustment"),
            "progress_evidence": adaptation.get("progress_evidence"),
            "first_exercise": DashboardService._first_exercise_summary(execution_plan),
            "progression_gate": DashboardService._progression_gate_summary(execution_plan),
        }

    @staticmethod
    def _first_exercise_summary(execution_plan: dict[str, Any]) -> dict[str, Any] | None:
        exercises = execution_plan.get("adjusted_exercises") or []
        if not exercises:
            return None
        first = exercises[0]
        return {
            "name": first.get("name"),
            "sets": first.get("sets"),
            "reps_or_duration": first.get("reps_or_duration"),
            "rest": first.get("rest"),
        }

    @staticmethod
    def _progression_gate_summary(execution_plan: dict[str, Any]) -> dict[str, Any] | None:
        for exercise in execution_plan.get("adjusted_exercises") or []:
            if exercise.get("adjustment") != "substitution_progression_gate":
                continue
            exercise_name = exercise.get("name") or "תרגיל שהוחלף"
            execution_note = exercise.get("execution_note")
            if execution_note:
                action = f"ב{exercise_name}: {execution_note}"
            else:
                action = (
                    f"ב{exercise_name}: להתקדם שלב אחד בלבד רק אם אין כאב והמאמץ נשאר עד RPE 8; "
                    "לתעד RPE וכאב אחרי הסטים - לא לנחש."
                )
            return {
                "exercise_name": exercise_name,
                "action": action,
            }
        return None

    @staticmethod
    def _next_recommended_action(
        *,
        profile: UserProfile | None,
        plan: WorkoutPlan | None,
        next_workout: dict[str, Any] | None,
    ) -> str:
        if plan is None:
            if profile is None:
                return "להשלים את האונבורדינג כדי שהמאמן יוכל לבנות את התוכנית הראשונה."
            return "ליצור תוכנית אימון שמתאימה לזמינות השבועית."
        if not next_workout:
            return "לבדוק את תוכנית האימון הפעילה לפני תיעוד נוסף."
        workout_name = next_workout.get("name") or "האימון הבא"
        progression_gate = next_workout.get("progression_gate")
        if progression_gate:
            return f"לבצע את {workout_name}. {progression_gate['action']}"
        if next_workout.get("load_signal") == "progress_candidate" and any(
            adjustment.get("reason") == "qualitative_underload"
            for adjustment in next_workout.get("exercise_adjustments") or []
            if isinstance(adjustment, dict)
        ):
            return (
                f"לבצע את {workout_name}. הלוג האחרון תיאר שהמאמץ היה קל מדי, אז להעלות עומס קטן או להאט קצב בלי קפיצה גדולה. "
                "לתעד מאמץ/כאב ומה הושלם - לא לנחש."
            )
        if next_workout.get("load_signal") == "progress_candidate" and any(
            adjustment.get("reason") == "high_rir_underload"
            for adjustment in next_workout.get("exercise_adjustments") or []
            if isinstance(adjustment, dict)
        ):
            return (
                f"לבצע את {workout_name}. הלוג האחרון השאיר יותר מדי חזרות ברזרבה, אז להעלות עומס קטן או להאט קצב כדי לכוון ל-RIR 1-3. "
                "לתעד RPE/RIR או מאמץ מילולי, כאב ומה הושלם - לא לנחש."
            )
        if next_workout.get("load_signal") == "progress_candidate" and next_workout.get("progress_evidence") == "exercise_log":
            return (
                f"לבצע את {workout_name}. אפשר התקדמות קטנה במשתנה אחד בלבד כי הלוג האחרון כלל חזרות ו-RPE/RIR בשליטה. "
                "לתעד RPE/RIR או מאמץ מילולי, כאב ומה הושלם - לא לנחש."
            )
        if next_workout.get("load_signal") == "recovery_needed" and any(
            adjustment.get("reason") == "qualitative_high_effort"
            for adjustment in next_workout.get("exercise_adjustments") or []
            if isinstance(adjustment, dict)
        ):
            return (
                f"לבצע את {workout_name}. הלוג האחרון תיאר מאמץ כבד מדי, אז להוריד מעט נפח או עומס. "
                "לתעד מאמץ מילולי, כאב ומה הושלם - לא לנחש."
            )
        if next_workout.get("load_signal") == "recovery_needed" and any(
            "RPE/RIR" in str(signal) for signal in next_workout.get("signals") or []
        ):
            return (
                f"לבצע את {workout_name}. הלוג האחרון היה קרוב לכשל לפי RPE/RIR, אז להוריד מעט נפח או עומס. "
                "לתעד RPE/RIR או מאמץ מילולי, כאב ומה הושלם - לא לנחש."
            )
        adjustment = next_workout.get("next_adjustment") or "שמור על התוכנית הנוכחית."
        return f"לבצע את {workout_name}. {adjustment} לתעד RPE או מאמץ מילולי, כאב ומה הושלם - לא לנחש."
