from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import ChatMessage, Meal, UserMemory, UserProfile, WorkoutLog, WorkoutPlan


class ContextBuilder:
    def __init__(self, db: Session):
        self.db = db

    def build(self, user_id: int, session_id: int | None = None, intent: str | None = None) -> dict:
        profile = self.db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        plan = self.db.scalar(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_current.is_(True))
            .order_by(desc(WorkoutPlan.created_at))
        )
        workout_logs = self.db.scalars(
            select(WorkoutLog).where(WorkoutLog.user_id == user_id).order_by(desc(WorkoutLog.logged_on)).limit(5)
        ).all()
        meals = self.db.scalars(
            select(Meal).where(Meal.user_id == user_id).order_by(desc(Meal.eaten_on)).limit(5)
        ).all()
        memory_query = select(UserMemory).where(UserMemory.user_id == user_id, UserMemory.is_sensitive.is_(False))
        relevant_types = self._memory_types_for_intent(intent)
        if relevant_types:
            memory_query = memory_query.where(UserMemory.memory_type.in_(relevant_types))
        memories = self.db.scalars(memory_query.order_by(desc(UserMemory.created_at)).limit(6)).all()

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
            "current_workout_plan": self._plan(plan),
            "recent_workouts": [
                {
                    "date": log.logged_on.isoformat(),
                    "status": log.status,
                    "notes": log.notes,
                    "pain_flag": log.pain_flag,
                }
                for log in workout_logs
            ],
            "recent_meals": [
                {
                    "date": meal.eaten_on.isoformat(),
                    "note": meal.note,
                    "calories_range": [meal.calories_min, meal.calories_max],
                    "confidence": meal.confidence,
                }
                for meal in meals
            ],
            "memories": [memory.content for memory in memories],
            "recent_chat": recent_chat,
        }

    @staticmethod
    def _memory_types_for_intent(intent: str | None) -> set[str]:
        if intent in {"meal_log", "meal_image"}:
            return {"nutrition", "allergy", "preference"}
        if intent in {"workout_plan", "workout_log"}:
            return {"equipment", "schedule", "preference"}
        return set()

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
    def _plan(plan: WorkoutPlan | None) -> dict:
        if plan is None:
            return {}
        return {
            "name": plan.name,
            "goal": plan.goal,
            "days_per_week": plan.days_per_week,
            "equipment_needed": plan.equipment_needed or [],
            "progression_rule": plan.progression_rule,
        }
