from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.config import Settings
from backend.app.models import (
    ChatMessage,
    ChatSession,
    Meal,
    MealImageAnalysis,
    MealItem,
    SafetyEvent,
    UsageEvent,
    User,
    UserMemory,
    UserProfile,
    WeeklySummary,
    Workout,
    WorkoutExercise,
    WorkoutLog,
    WorkoutPlan,
)
from backend.app.services.meal_service import MealService
from backend.app.services.profile_service import ProfileService
from backend.app.services.workout_service import WorkoutService


DISCLAIMER = (
    "מאמן הכושר המקומי הזה מיועד לתמיכה כללית בכושר ותזונה בלבד. "
    "זו אינה עצה רפואית והוא לא מחליף רופא, דיאטן, פיזיותרפיסט או איש מקצוע מוסמך."
)


class SettingsService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def provider_status(settings: Settings) -> dict[str, Any]:
        return {
            "ai_provider": settings.ai_provider_status,
            "model": settings.anthropic_model,
            "database": "configured" if settings.database_url else "not_configured",
            "api_key_present": bool(settings.anthropic_api_key),
            "disclaimer": DISCLAIMER,
        }

    def export_local_data(self) -> dict[str, Any]:
        user = ProfileService(self.db).get_default_user()
        profile = ProfileService(self.db).get_profile()
        plans = self.db.scalars(select(WorkoutPlan).where(WorkoutPlan.user_id == user.id)).all()
        workouts = self.db.scalars(select(Workout).where(Workout.user_id == user.id)).all()
        logs = self.db.scalars(select(WorkoutLog).where(WorkoutLog.user_id == user.id)).all()
        meals = self.db.scalars(select(Meal).where(Meal.user_id == user.id)).all()
        memories = self.db.scalars(select(UserMemory).where(UserMemory.user_id == user.id)).all()
        summaries = self.db.scalars(select(WeeklySummary).where(WeeklySummary.user_id == user.id)).all()
        safety_events = self.db.scalars(select(SafetyEvent).where(SafetyEvent.user_id == user.id)).all()

        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "user": {"id": user.id, "name": user.name},
            "profile": ProfileService.to_response(profile).model_dump() if profile else None,
            "workout_plans": [WorkoutService.serialize_plan(plan) for plan in plans],
            "workouts": [
                {
                    "id": workout.id,
                    "name": workout.name,
                    "scheduled_day": workout.scheduled_day,
                    "difficulty": workout.difficulty,
                    "workout": workout.workout_json,
                }
                for workout in workouts
            ],
            "workout_logs": [
                {
                    "id": log.id,
                    "logged_on": log.logged_on.isoformat(),
                    "status": log.status,
                    "exercise_results": log.exercise_results or [],
                    "rpe": log.rpe,
                    "notes": log.notes,
                    "pain_flag": log.pain_flag,
                    "parse_confidence": log.parse_confidence,
                }
                for log in logs
            ],
            "meals": [MealService.serialize_meal(meal) for meal in meals],
            "memories": [
                {
                    "id": memory.id,
                    "type": memory.memory_type,
                    "content": memory.content,
                    "source": memory.source,
                    "confidence": memory.confidence,
                    "is_sensitive": memory.is_sensitive,
                }
                for memory in memories
            ],
            "weekly_summaries": [
                {
                    "id": summary.id,
                    "week_start": summary.week_start.isoformat(),
                    "week_end": summary.week_end.isoformat(),
                    "summary": summary.summary_text,
                    "metrics": summary.metrics_json or {},
                    "next_action": summary.next_action,
                }
                for summary in summaries
            ],
            "safety_events": [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "source_text": event.source_text,
                    "response_text": event.response_text,
                }
                for event in safety_events
            ],
        }

    def reset_local_data(self, upload_root: Path | None = None) -> int:
        image_paths = [
            meal.image_path
            for meal in self.db.scalars(select(Meal).where(Meal.image_path.is_not(None))).all()
            if meal.image_path
        ]
        deleted = 0
        for model in (
            UsageEvent,
            SafetyEvent,
            WeeklySummary,
            UserMemory,
            MealImageAnalysis,
            MealItem,
            Meal,
            WorkoutLog,
            WorkoutExercise,
            Workout,
            WorkoutPlan,
            ChatMessage,
            ChatSession,
            UserProfile,
            User,
        ):
            result = self.db.execute(delete(model))
            deleted += result.rowcount or 0
        self.db.commit()
        self._delete_meal_image_files(image_paths=image_paths, upload_root=upload_root or Path("data/uploads"))
        return deleted

    @staticmethod
    def _delete_meal_image_files(*, image_paths: list[str], upload_root: Path) -> None:
        root = upload_root.resolve()
        for raw_path in image_paths:
            path = Path(raw_path)
            try:
                resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
                resolved.relative_to(root)
            except (OSError, ValueError):
                continue
            if resolved.is_file():
                resolved.unlink()
