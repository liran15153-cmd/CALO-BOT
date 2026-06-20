from datetime import date
import re
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import UserProfile, Workout, WorkoutExercise, WorkoutLog, WorkoutPlan
from backend.app.schemas import StructuredWorkoutPlan, WorkoutLogRequest, WorkoutPlanRequest
from backend.app.services.pain_text import has_pain_or_injury_signal
from backend.app.services.training_adaptation_service import TrainingAdaptationService
from backend.app.services.workout_plan_builder import (
    WorkoutPlanBuilder,
    WorkoutPlanningInput,
    infer_duration_weeks,
    infer_experience,
    infer_plan_type,
)


class WorkoutService:
    def __init__(self, db: Session):
        self.db = db

    def generate_plan(self, user_id: int, request: WorkoutPlanRequest) -> WorkoutPlan:
        profile = self.db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        plan_type = infer_plan_type(request.plan_type, request.prompt)
        days_per_week = (
            1
            if plan_type == "single_session"
            else request.days_per_week or self._infer_days(request.prompt) or self._profile_days(profile) or 3
        )
        duration_weeks = (
            1
            if plan_type == "single_session"
            else request.duration_weeks or infer_duration_weeks(request.prompt) or 4
        )
        equipment = request.equipment or self._infer_equipment(request.prompt) or self._profile_equipment(profile) or ["bodyweight"]
        goal = request.goal or self._infer_goal(request.prompt) or (profile.main_goal if profile else None) or "improve_fitness"
        experience_level = (
            request.experience_level
            or infer_experience(request.prompt)
            or (profile.experience_level if profile else None)
            or "beginner"
        )
        session_length_minutes = request.session_length_minutes or self._infer_session_length(request.prompt) or (profile.session_length_minutes if profile else None) or 45
        limitations = request.limitations or (profile.injuries_limitations if profile else None)
        recent_logs = self.db.scalars(
            select(WorkoutLog).where(WorkoutLog.user_id == user_id).order_by(desc(WorkoutLog.logged_on)).limit(5)
        ).all()
        training_status = TrainingAdaptationService().summarize(recent_logs)
        plan = WorkoutPlanBuilder().build(
            WorkoutPlanningInput(
                prompt=request.prompt,
                goal=goal,
                experience_level=experience_level,
                days_per_week=days_per_week,
                duration_weeks=duration_weeks,
                equipment=equipment,
                session_length_minutes=session_length_minutes,
                preferred_days=profile.preferred_workout_days if profile else [],
                limitations=limitations,
                plan_type=plan_type,
                readiness=request.readiness,
                training_status=training_status,
            )
        )

        current_plans = list(
            self.db.scalars(
                select(WorkoutPlan)
                .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_current.is_(True))
                .order_by(desc(WorkoutPlan.created_at), desc(WorkoutPlan.id))
            ).all()
        )
        current_plan_type = (current_plans[0].plan_json or {}).get("plan_type") if current_plans else None
        is_current = plan.plan_type == "multi_week" or not current_plans or current_plan_type == "single_session"
        if is_current:
            for current in current_plans:
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
            is_current=is_current,
        )
        self.db.add(record)
        self.db.flush()
        self._create_workout_rows(user_id=user_id, plan_id=record.id, plan=plan)
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

    def serialize_plan_with_rows(self, record: WorkoutPlan) -> dict:
        serialized = self.serialize_plan(record)
        days = [dict(day) for day in serialized.get("days", [])]
        workouts = self._workouts_for_plan(record.id)
        for index, workout in enumerate(workouts):
            if index >= len(days):
                break
            days[index]["workout_id"] = workout.id
            day_exercises = [dict(exercise) for exercise in days[index].get("exercises", [])]
            row_exercises = self._exercises_for_workout(workout.id)
            for exercise_index, exercise in enumerate(row_exercises):
                if exercise_index >= len(day_exercises):
                    break
                day_exercises[exercise_index]["exercise_id"] = exercise.id
            days[index]["exercises"] = day_exercises
        serialized["days"] = days
        return serialized

    def next_workout(self, user_id: int) -> dict[str, Any] | None:
        plan = self.current_plan(user_id=user_id)
        if plan is None:
            return None

        workouts = self._workouts_for_plan(plan.id)
        if not workouts:
            return None

        workout_ids = [workout.id for workout in workouts]
        latest_log = self.db.scalar(
            select(WorkoutLog)
            .where(WorkoutLog.user_id == user_id, WorkoutLog.workout_id.in_(workout_ids))
            .order_by(desc(WorkoutLog.logged_on), desc(WorkoutLog.id))
        )
        selected = workouts[0]
        if latest_log and latest_log.workout_id in workout_ids:
            latest_index = workout_ids.index(latest_log.workout_id)
            if latest_log.status == "completed" and not latest_log.pain_flag:
                selected = workouts[(latest_index + 1) % len(workouts)]
            else:
                selected = workouts[latest_index]

        adaptation = self.training_status(user_id=user_id, workout_ids=workout_ids)
        workout_payload = self._serialize_workout(selected)
        return {
            **workout_payload,
            "plan": {"id": plan.id, "name": plan.name},
            "adaptation": adaptation,
            "execution_plan": self._build_execution_plan(workout_payload, adaptation),
        }

    def training_status(self, user_id: int, workout_ids: list[int] | None = None) -> dict:
        logs = self._recent_logs_for_user(user_id=user_id, workout_ids=workout_ids)
        return TrainingAdaptationService().summarize(logs)

    def _workouts_for_plan(self, plan_id: int) -> list[Workout]:
        return list(self.db.scalars(select(Workout).where(Workout.plan_id == plan_id).order_by(Workout.id)).all())

    def _exercises_for_workout(self, workout_id: int) -> list[WorkoutExercise]:
        return list(
            self.db.scalars(select(WorkoutExercise).where(WorkoutExercise.workout_id == workout_id).order_by(WorkoutExercise.id)).all()
        )

    def _recent_logs_for_user(self, user_id: int, workout_ids: list[int] | None = None) -> list[WorkoutLog]:
        statement = select(WorkoutLog).where(WorkoutLog.user_id == user_id)
        if workout_ids:
            statement = statement.where(WorkoutLog.workout_id.in_(workout_ids))
        return list(self.db.scalars(statement.order_by(desc(WorkoutLog.logged_on), desc(WorkoutLog.id)).limit(5)).all())

    def recent_logs(self, user_id: int, limit: int = 10) -> list[WorkoutLog]:
        return list(
            self.db.scalars(
                select(WorkoutLog)
                .where(WorkoutLog.user_id == user_id)
                .order_by(desc(WorkoutLog.logged_on), desc(WorkoutLog.id))
                .limit(limit)
            ).all()
        )

    def _serialize_workout(self, workout: Workout) -> dict[str, Any]:
        workout_json = dict(workout.workout_json or {})
        return {
            "id": workout.id,
            "plan_id": workout.plan_id,
            "name": workout.name,
            "scheduled_day": workout.scheduled_day,
            "difficulty": workout.difficulty,
            "warmup": workout_json.get("warmup", []),
            "notes": workout_json.get("notes"),
            "exercises": [
                {
                    "exercise_id": exercise.id,
                    "name": exercise.name,
                    "sets": exercise.sets,
                    "reps_or_duration": exercise.reps_or_duration,
                    "rest": exercise.rest,
                    "notes": exercise.notes,
                    "alternatives": exercise.alternatives or [],
                }
                for exercise in self._exercises_for_workout(workout.id)
            ],
        }

    def _build_execution_plan(self, workout: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any]:
        load_signal = adaptation.get("load_signal", "maintain")
        base_exercises = workout.get("exercises") or []
        if load_signal == "adherence_risk":
            exercises = base_exercises[:3]
        else:
            exercises = base_exercises
        return {
            "source": "derived_from_base_workout",
            "base_workout_id": workout.get("id"),
            "workout_name": workout.get("name"),
            "load_signal": load_signal,
            "summary": _execution_summary(load_signal),
            "adjusted_exercises": [
                self._execution_exercise(
                    exercise=exercise,
                    load_signal=load_signal,
                    is_first_exercise=index == 0,
                    exercise_adjustment=self._matching_exercise_adjustment(exercise, adaptation),
                )
                for index, exercise in enumerate(exercises)
            ],
        }

    @staticmethod
    def _matching_exercise_adjustment(exercise: dict[str, Any], adaptation: dict[str, Any]) -> dict[str, Any] | None:
        exercise_id = exercise.get("exercise_id")
        exercise_name = (exercise.get("name") or "").strip().lower()
        for adjustment in adaptation.get("exercise_adjustments") or []:
            if adjustment.get("exercise_id") and adjustment.get("exercise_id") == exercise_id:
                return adjustment
            adjusted_name = (adjustment.get("exercise_name") or "").strip().lower()
            if adjusted_name and adjusted_name == exercise_name:
                return adjustment
        return None

    def _execution_exercise(
        self,
        *,
        exercise: dict[str, Any],
        load_signal: str,
        is_first_exercise: bool,
        exercise_adjustment: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base_sets = str(exercise.get("sets") or "")
        prescribed_sets = base_sets
        adjustment = exercise_adjustment.get("adjustment") if exercise_adjustment else "maintain"
        next_action = exercise_adjustment.get("next_action") if exercise_adjustment else "לבצע לפי התוכנית ולתעד איך זה הרגיש."
        notes = exercise.get("notes") or ""

        if load_signal == "adherence_risk":
            prescribed_sets = _reduced_sets(base_sets)
            adjustment = "minimum_version"
            next_action = "לבצע גרסת מינימום נקייה, לא להשלים את כל מה שפוספס."
            notes = _append_note(notes, "עדיף לסיים קצר ונקי מאשר לדחוס אימון מלא.")
        elif load_signal == "pain_caution":
            prescribed_sets = _reduced_sets(base_sets)
            adjustment = "reduce_or_swap"
            next_action = "לבחור וריאציה קלה יותר או לעצור אם הכאב חוזר."
            notes = _append_note(notes, "לעבוד רק בטווח ללא כאב, עם עומס נמוך יותר ובלי לדחוף דרך כאב.")
        elif load_signal == "recovery_needed":
            prescribed_sets = _reduced_sets(base_sets)
            adjustment = "reduce_or_hold"
            next_action = "להוריד מעט נפח או עומס ולהשאיר 2-3 RIR."
            notes = _append_note(notes, "זה אימון התאוששות יחסי, לא ניסיון לשבור שיא.")
        elif load_signal == "progress_candidate" and (is_first_exercise or adjustment == "small_progression"):
            adjustment = "small_progression"
            next_action = "אפשר להוסיף חזרה אחת או עומס קטן אחד בלבד אם הטכניקה נשארת נקייה."
            notes = _append_note(notes, "התקדמות קטנה רק במשתנה אחד; אם זה מרגיש כבד, לשמור על התוכנית.")
        elif not exercise_adjustment:
            adjustment = "maintain"

        return {
            "exercise_id": exercise.get("exercise_id"),
            "source_exercise_id": exercise.get("exercise_id"),
            "name": exercise.get("name"),
            "sets": prescribed_sets,
            "reps_or_duration": exercise.get("reps_or_duration"),
            "rest": exercise.get("rest"),
            "adjustment": adjustment,
            "reason": exercise_adjustment.get("reason") if exercise_adjustment else _execution_reason(load_signal),
            "execution_note": next_action,
            "notes": notes,
            "alternatives": exercise.get("alternatives") or [],
        }

    def _create_workout_rows(self, user_id: int, plan_id: int, plan: StructuredWorkoutPlan) -> None:
        for day in plan.days:
            workout = Workout(
                user_id=user_id,
                plan_id=plan_id,
                name=day.name,
                scheduled_day=day.name.split(" ", 1)[0],
                difficulty=day.difficulty,
                workout_json=day.model_dump(),
            )
            self.db.add(workout)
            self.db.flush()
            for exercise in day.exercises:
                self.db.add(
                    WorkoutExercise(
                        workout_id=workout.id,
                        name=exercise.name,
                        sets=exercise.sets,
                        reps_or_duration=exercise.reps_or_duration,
                        rest=exercise.rest,
                        notes=exercise.notes,
                        alternatives=exercise.alternatives,
                    )
                )

    @staticmethod
    def _infer_days(prompt: str) -> int | None:
        match = re.search(r"(\d)\s*-?\s*(?:days?|ימים|יום)", prompt.lower())
        if match:
            return max(1, min(7, int(match.group(1))))
        return None

    @staticmethod
    def _infer_goal(prompt: str) -> str | None:
        text = prompt.lower()
        if "muscle" in text:
            return "build_muscle"
        if "strength" in text:
            return "improve_strength"
        if "endurance" in text:
            return "improve_endurance"
        if "fat" in text:
            return "lose_fat"
        if "שריר" in text or "מסה" in text:
            return "build_muscle"
        if "כוח" in text:
            return "improve_strength"
        if "סיבולת" in text:
            return "improve_endurance"
        if "שומן" in text or "ירידה במשקל" in text:
            return "lose_fat"
        return None

    @staticmethod
    def _infer_session_length(prompt: str) -> int | None:
        text = prompt.lower()
        match = re.search(r"(\d{2,3})\s*(?:minutes?|mins?|min|דקות|דקה|דק׳|דק')", text)
        if not match:
            return None
        return max(10, min(120, int(match.group(1))))

    @staticmethod
    def _infer_equipment(prompt: str) -> list[str]:
        text = prompt.lower()
        if any(term in text for term in ["בלי ציוד", "ללא ציוד", "bodyweight", "no equipment"]):
            return ["bodyweight"]
        if any(term in text for term in ["חדר כושר", "gym", "מכון", "מכונה", "מכונות", "כבל", "cable", "machine"]):
            return ["חדר כושר", "משקולות יד", "מכונות"]
        if any(term in text for term in ["משקולת", "משקולות", "dumbbell", "dumbbells"]):
            return ["dumbbells"]
        if any(term in text for term in ["גומייה", "גומיות", "band", "bands"]):
            return ["resistance bands"]
        return []

    @staticmethod
    def _profile_days(profile: UserProfile | None) -> int | None:
        if profile is None:
            return None
        return max(1, min(7, profile.weekly_availability))

    @staticmethod
    def _profile_equipment(profile: UserProfile | None) -> list[str]:
        if profile is None:
            return []
        return profile.available_equipment or []

    def log_workout(self, user_id: int, request: WorkoutLogRequest) -> WorkoutLog:
        self._validate_workout_log_references(user_id=user_id, request=request)
        if self._is_structured_log(request):
            return self._log_structured_workout(user_id=user_id, request=request)
        return self.parse_log(user_id=user_id, request=request)

    def _validate_workout_log_references(self, user_id: int, request: WorkoutLogRequest) -> None:
        if request.workout_id is None:
            if any(exercise.exercise_id is not None for exercise in request.exercises):
                raise ValueError("exercise_id requires workout_id")
            return

        workout = self.db.get(Workout, request.workout_id)
        if workout is None or workout.user_id != user_id:
            raise ValueError("Unknown workout_id")

        for exercise in request.exercises:
            if exercise.exercise_id is None:
                continue
            workout_exercise = self.db.get(WorkoutExercise, exercise.exercise_id)
            if workout_exercise is None or workout_exercise.workout_id != request.workout_id:
                raise ValueError("exercise_id does not belong to workout_id")

    def parse_log(self, user_id: int, request: WorkoutLogRequest) -> WorkoutLog:
        if request.text is None:
            raise ValueError("Text workout log requires text")
        text = request.text.lower()
        pain_flag = has_pain_or_injury_signal(text)
        status = (
            "skipped"
            if any(term in text for term in ["skipped", "פספסתי", "פספס", "דילגתי", "לא עשיתי"])
            else "completed"
        )
        results = self._parse_exercise_results(request.text)
        rpe = self._parse_rpe(request.text)
        parse_confidence = "high" if results and rpe is not None else "medium" if results or rpe is not None else "low"
        log = WorkoutLog(
            user_id=user_id,
            workout_id=request.workout_id,
            logged_on=request.logged_on or date.today(),
            status=status,
            exercise_results=results,
            rpe=rpe,
            notes=request.text,
            pain_flag=pain_flag,
            parse_confidence=parse_confidence,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    @staticmethod
    def _is_structured_log(request: WorkoutLogRequest) -> bool:
        return bool(
            request.status
            or request.exercises
            or request.rpe is not None
            or request.rir is not None
            or request.pain_flag
            or request.notes
        )

    def _log_structured_workout(self, user_id: int, request: WorkoutLogRequest) -> WorkoutLog:
        text_for_pain = " ".join(
            part
            for part in [
                request.text,
                request.notes,
                " ".join(exercise.notes or "" for exercise in request.exercises),
            ]
            if part
        )
        pain_flag = request.pain_flag or has_pain_or_injury_signal(text_for_pain.lower())
        exercise_results = [
            {
                "exercise_id": exercise.exercise_id,
                "exercise_name": exercise.exercise_name,
                "status": exercise.status,
                "sets": [logged_set.model_dump(exclude_none=True) for logged_set in exercise.sets],
                "rpe": exercise.rpe,
                "rir": exercise.rir,
                "notes": exercise.notes,
            }
            for exercise in request.exercises
        ]
        rpe = request.rpe or self._max_exercise_rpe(request)
        log = WorkoutLog(
            user_id=user_id,
            workout_id=request.workout_id,
            logged_on=request.logged_on or date.today(),
            status=request.status or self._infer_structured_status(request),
            exercise_results=exercise_results,
            rpe=rpe,
            notes=request.notes or request.text,
            pain_flag=pain_flag,
            parse_confidence="high" if request.exercises else "medium",
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    @staticmethod
    def _infer_structured_status(request: WorkoutLogRequest) -> str:
        if not request.exercises:
            return "completed"
        statuses = {exercise.status for exercise in request.exercises}
        if "modified" in statuses:
            return "modified"
        if "partial" in statuses or "skipped" in statuses:
            return "partial"
        return "completed"

    @staticmethod
    def _max_exercise_rpe(request: WorkoutLogRequest) -> int | None:
        values = [exercise.rpe for exercise in request.exercises if exercise.rpe is not None]
        return max(values) if values else None

    @staticmethod
    def _parse_exercise_results(text: str) -> list[dict]:
        patterns = [
            r"(?P<sets>\d+)\s+sets?\s+of\s+(?P<exercise>[a-zA-Z ]+?)\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s+with\s+(?P<weight>\d+\s?kg))?",
            r"(?:i\s+did\s+)?(?P<exercise>[a-zA-Z][a-zA-Z ]+?)\s+(?P<sets>\d+)\s+sets?\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s+(?:with|at)\s+(?P<weight>\d+\s?kg))?",
            r"(?:עשיתי\s+)?(?P<exercise>[\u0590-\u05ffa-zA-Z \"'/-]+?)\s+(?P<sets>\d+)\s+סטים\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s*(?:חזרות)?\s*(?:עם)?\s*(?P<weight>\d+\s?(?:kg|קג|ק\"ג|קילו)))?",
            r"(?P<sets>\d+)\s+סטים\s+של\s+(?P<exercise>[\u0590-\u05ffa-zA-Z \"'/-]+?)\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s*(?:חזרות)?\s*(?:עם)?\s*(?P<weight>\d+\s?(?:kg|קג|ק\"ג)))?",
        ]
        match = next((match for pattern in patterns if (match := re.search(pattern, text, flags=re.IGNORECASE))), None)
        if not match:
            return []
        result = {
            "exercise": match.group("exercise").strip(" :-"),
            "sets": int(match.group("sets")),
            "reps": [int(rep.strip()) for rep in match.group("reps").split(",")],
        }
        if match.group("weight"):
            weight = match.group("weight").strip()
            result["weight"] = weight.replace(" ", "") if "kg" in weight.lower() else re.sub(r"\s+", " ", weight)
        return [result]

    @staticmethod
    def _parse_rpe(text: str) -> int | None:
        match = re.search(r"\brpe\s*[:=-]?\s*(10|[1-9])\b", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r"\b(10|[1-9])\s*/\s*10\s*rpe\b", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def serialize_log(log: WorkoutLog, adaptation: dict | None = None) -> dict:
        payload = {
            "id": log.id,
            "workout_id": log.workout_id,
            "logged_on": log.logged_on.isoformat(),
            "status": log.status,
            "exercise_results": log.exercise_results or [],
            "rpe": log.rpe,
            "notes": log.notes,
            "pain_flag": log.pain_flag,
            "parse_confidence": log.parse_confidence,
        }
        if adaptation is not None:
            payload["adaptation"] = adaptation
        return payload


def _execution_summary(load_signal: str) -> str:
    return {
        "adherence_risk": "לבצע גרסת מינימום: פחות תרגילים, פחות סטים, ולסיים נקי במקום להשלים בכוח את מה שפוספס.",
        "pain_caution": "לבצע בזהירות סביב הכאב: וריאציה קלה יותר, טווח ללא כאב, ועצירה אם הסימן חוזר.",
        "recovery_needed": "לבצע אימון התאוששות יחסי: לשמור על הטכניקה, להוריד מעט נפח או עומס, ולא לרדוף אחרי כשל.",
        "progress_candidate": "אפשר התקדמות קטנה: לבחור משתנה אחד בלבד, כמו חזרה אחת או עומס קטן בתרגיל הראשון.",
        "maintain": "לבצע את התוכנית כמו שהיא ולתעד ביצוע כדי לצבור דפוס ברור.",
    }.get(load_signal, "לבצע את האימון בצורה שמרנית ולתעד איך זה הרגיש.")


def _execution_reason(load_signal: str) -> str:
    return {
        "adherence_risk": "missed_or_partial_recently",
        "pain_caution": "pain_reported",
        "recovery_needed": "high_rpe_recently",
        "progress_candidate": "recent_workout_supported_progression",
        "maintain": "base_plan",
    }.get(load_signal, "load_signal")


def _reduced_sets(value: str) -> str:
    match = re.search(r"\d+", value)
    if not match:
        return "1-2"
    reduced = max(1, int(match.group(0)) - 1)
    return str(reduced)


def _append_note(existing: str, addition: str) -> str:
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing} {addition}"
