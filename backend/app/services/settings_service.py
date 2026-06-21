from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.config import Settings
from backend.app.models import (
    ChatMessage,
    ChatSession,
    BodyMetric,
    Meal,
    MealImageAnalysis,
    MealItem,
    MemorySummary,
    PendingAction,
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
            "chat_model": settings.chat_model,
            "database": "configured" if settings.database_url else "not_configured",
            "api_key_present": bool(settings.anthropic_api_key),
            "supabase": settings.supabase_auth_status,
            "supabase_storage": settings.supabase_storage_status,
            "disclaimer": DISCLAIMER,
        }

    def export_local_data(self, user_id: int | None = None) -> dict[str, Any]:
        user = ProfileService(self.db).get_default_user() if user_id is None else self.db.get(User, user_id)
        if user is None:
            raise ValueError("User not found")
        profile = ProfileService(self.db).get_profile_for_user(user.id)
        plans = self.db.scalars(select(WorkoutPlan).where(WorkoutPlan.user_id == user.id)).all()
        workouts = self.db.scalars(select(Workout).where(Workout.user_id == user.id)).all()
        logs = self.db.scalars(select(WorkoutLog).where(WorkoutLog.user_id == user.id)).all()
        meals = self.db.scalars(select(Meal).where(Meal.user_id == user.id)).all()
        memories = self.db.scalars(select(UserMemory).where(UserMemory.user_id == user.id)).all()
        memory_summaries = self.db.scalars(select(MemorySummary).where(MemorySummary.user_id == user.id)).all()
        body_metrics = self.db.scalars(select(BodyMetric).where(BodyMetric.user_id == user.id)).all()
        summaries = self.db.scalars(select(WeeklySummary).where(WeeklySummary.user_id == user.id)).all()
        safety_events = self.db.scalars(select(SafetyEvent).where(SafetyEvent.user_id == user.id)).all()
        pending_actions = self.db.scalars(select(PendingAction).where(PendingAction.user_id == user.id)).all()

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
            "memory_summaries": [
                {
                    "id": summary.id,
                    "summary_type": summary.summary_type,
                    "content": summary.content,
                    "source_range": summary.source_range_json or {},
                }
                for summary in memory_summaries
            ],
            "body_metrics": [
                {
                    "id": metric.id,
                    "measured_on": metric.measured_on.isoformat(),
                    "weight_kg": metric.weight_kg,
                    "body_fat_percent": metric.body_fat_percent,
                    "waist_cm": metric.waist_cm,
                    "measurements": metric.measurements_json or {},
                    "source": metric.source,
                    "note": metric.note,
                }
                for metric in body_metrics
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
            "pending_actions": [
                {
                    "id": action.id,
                    "action_type": action.action_type,
                    "status": action.status,
                    "subject_type": action.subject_type,
                    "subject_id": action.subject_id,
                    "payload": action.payload_json or {},
                    "resolution": action.resolution,
                }
                for action in pending_actions
            ],
        }

    def reset_local_data(self, upload_root: Path | None = None, user_id: int | None = None) -> int:
        user = ProfileService(self.db).get_default_user() if user_id is None else self.db.get(User, user_id)
        if user is None:
            return 0
        image_paths = [
            meal.image_path
            for meal in self.db.scalars(select(Meal).where(Meal.user_id == user.id, Meal.image_path.is_not(None))).all()
            if meal.image_path
        ]
        deleted = 0
        meal_ids = [meal.id for meal in self.db.scalars(select(Meal).where(Meal.user_id == user.id)).all()]
        workout_ids = [workout.id for workout in self.db.scalars(select(Workout).where(Workout.user_id == user.id)).all()]
        if meal_ids:
            for model in (MealImageAnalysis, MealItem):
                result = self.db.execute(delete(model).where(getattr(model, "meal_id").in_(meal_ids)))
                deleted += result.rowcount or 0
        if workout_ids:
            result = self.db.execute(delete(WorkoutExercise).where(WorkoutExercise.workout_id.in_(workout_ids)))
            deleted += result.rowcount or 0
        for model in (
            UsageEvent,
            SafetyEvent,
            WeeklySummary,
            MemorySummary,
            UserMemory,
            BodyMetric,
            Meal,
            WorkoutLog,
            PendingAction,
            Workout,
            WorkoutPlan,
            ChatMessage,
            ChatSession,
            UserProfile,
        ):
            result = self.db.execute(delete(model).where(model.user_id == user.id))
            deleted += result.rowcount or 0
        self.db.delete(user)
        deleted += 1
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
