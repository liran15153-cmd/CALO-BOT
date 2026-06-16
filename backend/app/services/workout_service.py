from datetime import date
import re

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import WorkoutLog, WorkoutPlan
from backend.app.schemas import StructuredWorkoutPlan, WorkoutLogRequest, WorkoutPlanRequest


class WorkoutService:
    def __init__(self, db: Session):
        self.db = db

    def generate_plan(self, user_id: int, request: WorkoutPlanRequest) -> WorkoutPlan:
        days_per_week = request.days_per_week or self._infer_days(request.prompt) or 3
        equipment = request.equipment or ["bodyweight"]
        goal = self._infer_goal(request.prompt)
        plan = self._build_plan(goal=goal, days_per_week=days_per_week, equipment=equipment)

        for current in self.db.scalars(
            select(WorkoutPlan).where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_current.is_(True))
        ):
            current.is_current = False

        record = WorkoutPlan(
            user_id=user_id,
            name=plan.name,
            goal=plan.goal,
            duration_weeks=plan.duration_weeks,
            days_per_week=plan.days_per_week,
            equipment_needed=plan.equipment_needed,
            plan_json=plan.model_dump(),
            progression_rule=plan.progression_rule,
            recovery_note=plan.recovery_note,
            is_current=True,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def current_plan(self, user_id: int) -> WorkoutPlan | None:
        return self.db.scalar(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_current.is_(True))
            .order_by(desc(WorkoutPlan.created_at))
        )

    @staticmethod
    def serialize_plan(record: WorkoutPlan) -> dict:
        return {
            "id": record.id,
            "is_current": record.is_current,
            **record.plan_json,
        }

    @staticmethod
    def _infer_days(prompt: str) -> int | None:
        match = re.search(r"(\d)[ -]?day", prompt.lower())
        if match:
            return max(1, min(7, int(match.group(1))))
        return None

    @staticmethod
    def _infer_goal(prompt: str) -> str:
        text = prompt.lower()
        if "muscle" in text:
            return "build_muscle"
        if "strength" in text:
            return "improve_strength"
        if "endurance" in text:
            return "improve_endurance"
        if "fat" in text:
            return "lose_fat"
        return "improve_fitness"

    @staticmethod
    def _build_plan(goal: str, days_per_week: int, equipment: list[str]) -> StructuredWorkoutPlan:
        has_dumbbells = any("dumbbell" in item.lower() for item in equipment)
        primary_lower = "Goblet squat" if has_dumbbells else "Bodyweight squat"
        push = "Dumbbell floor press" if has_dumbbells else "Push-up"
        pull = "One-arm dumbbell row" if has_dumbbells else "Towel row"
        days = []
        for index in range(days_per_week):
            days.append(
                {
                    "name": f"Day {index + 1} Full Body",
                    "warmup": ["5 minutes easy cardio", "Hip hinge drill", "Shoulder circles"],
                    "exercises": [
                        {
                            "name": primary_lower,
                            "sets": "3",
                            "reps_or_duration": "8-12 reps",
                            "rest": "90 sec",
                            "notes": "Use a pain-free range and controlled tempo.",
                            "difficulty": "moderate",
                            "alternatives": ["Box squat", "Split squat"],
                            "safety_notes": ["Stop if sharp pain appears"],
                        },
                        {
                            "name": push,
                            "sets": "3",
                            "reps_or_duration": "8-12 reps",
                            "rest": "75 sec",
                            "notes": "Keep two reps in reserve.",
                            "difficulty": "moderate",
                            "alternatives": ["Incline push-up"],
                            "safety_notes": ["Keep shoulders comfortable"],
                        },
                        {
                            "name": pull,
                            "sets": "3",
                            "reps_or_duration": "10-12 reps",
                            "rest": "75 sec",
                            "notes": "Pause briefly at the top.",
                            "difficulty": "moderate",
                            "alternatives": ["Band row"],
                            "safety_notes": ["Keep spine neutral"],
                        },
                    ],
                    "difficulty": "moderate",
                    "notes": "Finish feeling like you could do a little more.",
                }
            )
        return StructuredWorkoutPlan(
            name=f"{days_per_week}-Day {goal.replace('_', ' ').title()} Plan",
            goal=goal,
            duration_weeks=4,
            days_per_week=days_per_week,
            equipment_needed=equipment,
            days=days,
            progression_rule="When all sets reach the top of the rep range with good form, increase load slightly or add reps first.",
            recovery_note="If soreness or fatigue is high, reduce one set per exercise or take an extra rest day.",
        )

    def parse_log(self, user_id: int, request: WorkoutLogRequest) -> WorkoutLog:
        text = request.text.lower()
        pain_flag = any(term in text for term in ["pain", "hurts", "injury"])
        status = "skipped" if "skipped" in text else "completed"
        results = self._parse_exercise_results(request.text)
        log = WorkoutLog(
            user_id=user_id,
            workout_id=request.workout_id,
            logged_on=request.logged_on or date.today(),
            status=status,
            exercise_results=results,
            rpe=None,
            notes=request.text,
            pain_flag=pain_flag,
            parse_confidence="medium" if results else "low",
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    @staticmethod
    def _parse_exercise_results(text: str) -> list[dict]:
        match = re.search(
            r"(?P<sets>\d+)\s+sets?\s+of\s+(?P<exercise>[a-zA-Z ]+?)\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s+with\s+(?P<weight>\d+\s?kg))?",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return []
        result = {
            "exercise": match.group("exercise").strip(),
            "sets": int(match.group("sets")),
            "reps": [int(rep.strip()) for rep in match.group("reps").split(",")],
        }
        if match.group("weight"):
            result["weight"] = match.group("weight").replace(" ", "")
        return [result]

    @staticmethod
    def serialize_log(log: WorkoutLog) -> dict:
        return {
            "id": log.id,
            "logged_on": log.logged_on.isoformat(),
            "status": log.status,
            "exercise_results": log.exercise_results or [],
            "rpe": log.rpe,
            "notes": log.notes,
            "pain_flag": log.pain_flag,
            "parse_confidence": log.parse_confidence,
        }
