from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import BodyMetric, ChatMessage, Meal, UserProfile, WorkoutLog, WorkoutPlan
from backend.app.services.coaching_knowledge import CoachingKnowledgeService
from backend.app.services.memory_service import MemoryService
from backend.app.services.training_adaptation_service import TrainingAdaptationService
from backend.app.services.workout_service import WorkoutService


_PLAN_EDIT_SUMMARIES = {
    "remove_bench": "removed bench-dependent exercises or substitutions",
    "remove_cable": "removed cable-dependent exercises or substitutions",
    "replace_row_machine": "replaced row-machine-dependent rowing work",
    "regress_pushup": "regressed push-up work to an easier variation",
    "pain_substitution": "changed exercises around reported pain without diagnosis",
    "reduce_volume": "reduced training volume",
}


class ContextBuilder:
    def __init__(self, db: Session):
        self.db = db

    def build(
        self,
        user_id: int,
        session_id: int | None = None,
        intent: str | None = None,
        user_message: str | None = None,
    ) -> dict:
        profile = self.db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        workout_service = WorkoutService(self.db)
        plan = workout_service.current_plan(user_id=user_id)
        workout_logs = self.db.scalars(
            select(WorkoutLog).where(WorkoutLog.user_id == user_id).order_by(desc(WorkoutLog.logged_on)).limit(5)
        ).all()
        meals = self.db.scalars(
            select(Meal).where(Meal.user_id == user_id).order_by(desc(Meal.eaten_on)).limit(5)
        ).all()
        body_metrics = self.db.scalars(
            select(BodyMetric)
            .where(BodyMetric.user_id == user_id)
            .order_by(desc(BodyMetric.measured_on), desc(BodyMetric.id))
            .limit(5)
        ).all()
        memory_context = MemoryService(self.db).for_context(user_id=user_id, intent=intent)

        recent_chat = []
        if session_id is not None:
            messages = self.db.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(desc(ChatMessage.created_at), desc(ChatMessage.id))
                .limit(4)
            ).all()
            recent_chat = [{"role": message.role, "content": message.content} for message in reversed(messages)]

        return {
            "profile": self._profile(profile),
            "current_workout_plan": self._plan(plan, workout_service=workout_service),
            "recent_workouts": [
                {
                    "date": log.logged_on.isoformat(),
                    "status": log.status,
                    "notes": log.notes,
                    "pain_flag": log.pain_flag,
                }
                for log in workout_logs
            ],
            "training_status": TrainingAdaptationService().summarize(workout_logs),
            "recent_meals": [
                {
                    "date": meal.eaten_on.isoformat(),
                    "note": meal.note,
                    "calories_range": [meal.calories_min, meal.calories_max],
                    "confidence": meal.confidence,
                }
                for meal in meals
            ],
            "body_metrics": [self._body_metric(metric) for metric in body_metrics],
            "memory_safety": memory_context["safety"],
            "recent_chat": recent_chat,
            "coaching_knowledge": CoachingKnowledgeService().for_provider_context(intent, query=user_message),
        }

    @staticmethod
    def _profile(profile: UserProfile | None) -> dict:
        if profile is None:
            return {}
        return {
            "main_goal": profile.main_goal,
            "experience_level": profile.experience_level,
            "training_location": profile.training_location,
            "available_equipment": profile.available_equipment or [],
            "weekly_availability": profile.weekly_availability,
            "session_length_minutes": profile.session_length_minutes,
            "limitations": profile.injuries_limitations,
            "nutrition_preference": profile.nutrition_preference,
            "coaching_style": profile.coaching_style,
        }

    @staticmethod
    def _plan(plan: WorkoutPlan | None, *, workout_service: WorkoutService) -> dict:
        if plan is None:
            return {}
        plan_json = plan.plan_json or {}
        serialized_plan = workout_service.serialize_plan_with_rows(plan)
        return {
            "name": plan.name,
            "goal": plan.goal,
            "plan_type": plan_json.get("plan_type", "monthly_plan"),
            "duration_weeks": plan.duration_weeks,
            "days_per_week": plan.days_per_week,
            "training_split": plan_json.get("training_split", "full_body"),
            "experience_level": plan_json.get("experience_level"),
            "session_length_minutes": plan_json.get("session_length_minutes"),
            "equipment_needed": plan.equipment_needed or [],
            "progression_rule": plan.progression_rule,
            "progression_schedule": plan_json.get("progression_schedule", []),
            "tracking_guidance": plan_json.get("tracking_guidance", []),
            "recovery_note": plan.recovery_note,
            "source_refs": plan_json.get("source_refs", []),
            "decision_inputs": plan_json.get("decision_inputs", {}),
            "workout_outline": ContextBuilder._workout_outline(serialized_plan.get("days") or []),
            "recent_plan_edits": ContextBuilder._plan_edit_summaries(plan_json.get("plan_edit_history") or []),
        }

    @staticmethod
    def _workout_outline(days: list[dict]) -> list[dict]:
        outline = []
        for day in days[:4]:
            exercises = day.get("exercises") or []
            first_exercise = exercises[0] if exercises else {}
            outline.append(
                {
                    "name": day.get("name"),
                    "workout_id": day.get("workout_id"),
                    "first_exercise": {
                        "exercise_id": first_exercise.get("exercise_id"),
                        "name": first_exercise.get("name"),
                        "sets": first_exercise.get("sets"),
                        "reps_or_duration": first_exercise.get("reps_or_duration"),
                    }
                    if first_exercise
                    else None,
                }
            )
        return outline

    @staticmethod
    def _plan_edit_summaries(edit_history: list[dict]) -> list[dict]:
        summaries = []
        for edit in edit_history[-3:]:
            edit_type = edit.get("edit_type")
            summaries.append(
                {
                    "date": edit.get("date"),
                    "edit_type": edit_type,
                    "summary": _PLAN_EDIT_SUMMARIES.get(str(edit_type), "scoped plan edit"),
                    "changed_exercises": edit.get("changed_exercises"),
                }
            )
        return summaries

    @staticmethod
    def _body_metric(metric: BodyMetric) -> dict:
        measurements = dict(metric.measurements_json or {})
        if metric.waist_cm is not None and "waist_cm" not in measurements:
            measurements["waist_cm"] = metric.waist_cm
        return {
            "measured_on": metric.measured_on.isoformat(),
            "weight_kg": metric.weight_kg,
            "body_fat_percent": metric.body_fat_percent,
            "measurements": measurements,
            "source": metric.source,
            "note": metric.note,
        }
