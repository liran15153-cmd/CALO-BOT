from datetime import date
import re

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
)


class WorkoutService:
    def __init__(self, db: Session):
        self.db = db

    def generate_plan(self, user_id: int, request: WorkoutPlanRequest) -> WorkoutPlan:
        profile = self.db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        plan_type = request.plan_type or self._infer_plan_type(request.prompt)
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
        equipment = request.equipment or self._profile_equipment(profile) or ["bodyweight"]
        goal = request.goal or self._infer_goal(request.prompt) or (profile.main_goal if profile else None) or "improve_fitness"
        experience_level = (
            request.experience_level
            or infer_experience(request.prompt)
            or (profile.experience_level if profile else None)
            or "beginner"
        )
        session_length_minutes = (
            request.session_length_minutes or (profile.session_length_minutes if profile else None) or 45
        )
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

        is_current = plan.plan_type == "multi_week"
        if is_current:
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
    def _infer_plan_type(prompt: str) -> str:
        text = prompt.lower()
        single_terms = ["today", "tonight", "right now", "single session", "one workout", "one session", "היום", "אימון אחד"]
        if any(term in text for term in single_terms):
            return "single_session"
        return "multi_week"

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
    def _profile_days(profile: UserProfile | None) -> int | None:
        if profile is None:
            return None
        return max(1, min(7, profile.weekly_availability))

    @staticmethod
    def _profile_equipment(profile: UserProfile | None) -> list[str]:
        if profile is None:
            return []
        return profile.available_equipment or []

    @staticmethod
    def _build_plan(
        goal: str,
        days_per_week: int,
        equipment: list[str],
        session_length_minutes: int = 45,
        preferred_days: list[str] | None = None,
        limitations: str | None = None,
    ) -> StructuredWorkoutPlan:
        has_dumbbells = any("dumbbell" in item.lower() for item in equipment)
        has_bands = any("band" in item.lower() for item in equipment)
        primary_lower = "סקוואט גביע" if has_dumbbells else "סקוואט משקל גוף"
        push = "לחיצת רצפה עם משקולות" if has_dumbbells else "שכיבת סמיכה"
        pull = "חתירה ביד אחת עם משקולת" if has_dumbbells else "חתירה עם גומייה" if has_bands else "חתירה עם מגבת"
        hinge = "דדליפט רומני עם משקולות" if has_dumbbells else "היפ הינג' עם תיק"
        variables = _goal_training_variables(goal)
        display_limitations = _display_limitations_he(limitations)
        limitation_note = f" כבד את {display_limitations}." if display_limitations else ""
        safety_notes = ["עצור אם מופיע כאב חד"]
        if display_limitations:
            safety_notes.append(f"התאם סביב {display_limitations}")
        days = []
        for index in range(days_per_week):
            raw_day_label = preferred_days[index] if preferred_days and index < len(preferred_days) else f"יום {index + 1}"
            day_label = _day_label_he(raw_day_label)
            days.append(
                {
                    "name": f"{day_label} גוף מלא",
                    "warmup": ["5 דקות אירובי קל", "תרגול היפ הינג'", "סיבובי כתפיים"],
                    "exercises": [
                        {
                            "name": primary_lower,
                            "sets": "3",
                            "reps_or_duration": variables["main_reps"],
                            "rest": variables["main_rest"],
                            "notes": f"עבוד בטווח ללא כאב ובקצב נשלט.{limitation_note}",
                            "difficulty": "moderate",
                            "alternatives": ["סקוואט לקופסה", "סקוואט מפוצל"],
                            "safety_notes": safety_notes,
                        },
                        {
                            "name": push,
                            "sets": "3",
                            "reps_or_duration": variables["upper_reps"],
                            "rest": variables["upper_rest"],
                            "notes": "השאר שתי חזרות ברזרבה.",
                            "difficulty": "moderate",
                            "alternatives": ["שכיבת סמיכה בשיפוע"],
                            "safety_notes": ["שמור על כתפיים נוחות"],
                        },
                        {
                            "name": pull,
                            "sets": "3",
                            "reps_or_duration": variables["upper_reps"],
                            "rest": variables["upper_rest"],
                            "notes": "עצור רגע קצר בקצה התנועה.",
                            "difficulty": "moderate",
                            "alternatives": ["חתירה עם גומייה"],
                            "safety_notes": ["שמור על עמוד שדרה ניטרלי"],
                        },
                        {
                            "name": hinge,
                            "sets": "2",
                            "reps_or_duration": variables["hinge_reps"],
                            "rest": variables["main_rest"],
                            "notes": f"התמקד בדחיפת אגן לאחור ושמור שתי חזרות ברזרבה.{limitation_note}",
                            "difficulty": "moderate",
                            "alternatives": ["גשר ישבן", "בוקר טוב ללא משקל"],
                            "safety_notes": ["עצור אם מופיע כאב חד בגב או בירך"],
                        },
                        {
                            "name": "פלאנק ליבה",
                            "sets": "2",
                            "reps_or_duration": "20-40 שניות",
                            "rest": "60 שניות",
                            "notes": "שמור נשימה רגועה וצלעות נמוכות.",
                            "difficulty": "easy",
                            "alternatives": ["דד באג", "פלאנק ברכיים"],
                            "safety_notes": ["עצור אם מופיע כאב חד"],
                        },
                    ],
                    "difficulty": "moderate",
                    "notes": f"שמור על אימון של בערך {session_length_minutes} דקות וסיים עם אנרגיה להמשך. {variables['day_note']}",
                }
            )
        recovery_note = (
            "אם הכאב השרירי או העייפות גבוהים, הורד סט אחד מכל תרגיל או קח יום מנוחה נוסף. "
            f"{variables['recovery_note']}"
        )
        if display_limitations:
            recovery_note = f"{recovery_note} עבוד סביב {display_limitations}."
        return StructuredWorkoutPlan(
            name=f"תוכנית {days_per_week} ימים ל{_goal_label_he(goal)}",
            goal=goal,
            duration_weeks=4,
            days_per_week=days_per_week,
            equipment_needed=equipment,
            days=days,
            progression_rule=variables["progression_rule"],
            recovery_note=recovery_note,
        )

    def parse_log(self, user_id: int, request: WorkoutLogRequest) -> WorkoutLog:
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


def _goal_label_he(goal: str) -> str:
    return {
        "build_muscle": "בניית שריר",
        "lose_fat": "ירידה בשומן",
        "improve_fitness": "שיפור כושר",
        "maintain_health": "שמירה על בריאות",
        "improve_consistency": "שיפור עקביות",
        "improve_strength": "שיפור כוח",
        "improve_endurance": "שיפור סבולת",
    }.get(goal, goal.replace("_", " "))


def _day_label_he(day_label: str) -> str:
    return {
        "monday": "יום שני",
        "tuesday": "יום שלישי",
        "wednesday": "יום רביעי",
        "thursday": "יום חמישי",
        "friday": "יום שישי",
        "saturday": "שבת",
        "sunday": "יום ראשון",
    }.get(day_label.strip().lower(), day_label)


def _display_limitations_he(limitations: str | None) -> str:
    if not limitations:
        return ""
    stripped = limitations.strip()
    if any("\u0590" <= character <= "\u05ff" for character in stripped):
        return f"המגבלה שתועדה בפרופיל: {stripped}"
    return "המגבלה שתועדה בפרופיל"


def _goal_training_variables(goal: str) -> dict[str, str]:
    defaults = {
        "main_reps": "8-12 חזרות",
        "upper_reps": "8-12 חזרות",
        "hinge_reps": "8-10 חזרות",
        "main_rest": "90 שניות",
        "upper_rest": "75 שניות",
        "day_note": "המטרה היא עקביות וטכניקה לפני עומס.",
        "progression_rule": "כאשר כל הסטים מגיעים לקצה העליון של טווח החזרות בטכניקה טובה, הוסף קודם חזרות או העלה עומס מעט.",
        "recovery_note": "שמור לפחות יום התאוששות בין אימוני כוח דומים.",
    }
    if goal == "improve_strength":
        return {
            **defaults,
            "main_reps": "4-6 חזרות",
            "upper_reps": "5-8 חזרות",
            "hinge_reps": "5-8 חזרות",
            "main_rest": "120 שניות",
            "upper_rest": "90 שניות",
            "day_note": "בצע את התרגילים המרכזיים בתחילת האימון כשאתה רענן.",
            "progression_rule": "כאשר הטכניקה יציבה וכל הסטים הושלמו בלי כאב, הוסף עומס קטן לפני שאתה מוסיף נפח.",
            "recovery_note": "אל תנסה לשבור שיא כששינה או התאוששות חלשות.",
        }
    if goal == "build_muscle":
        return {
            **defaults,
            "progression_rule": "התקדם דרך נפח: הוסף קודם חזרות בטווח, אחר כך סט נוסף או עומס קטן אם ההתאוששות טובה.",
            "recovery_note": "שמור 1-3 חזרות ברזרבה ברוב הסטים ואל תרדוף אחרי כשל בכל אימון.",
        }
    if goal == "lose_fat":
        return {
            **defaults,
            "upper_rest": "60 שניות",
            "day_note": "אם נשאר זמן ואנרגיה, הוסף 10-20 דקות אירובי קל או הליכה.",
            "progression_rule": "שמור על כוח וטכניקה, והוסף צעדים או אירובי קל בהדרגה במקום להעניש את עצמך בעומס קיצוני.",
            "recovery_note": "ירידה בשומן לא דורשת דיאטת קיצון; שמור על אוכל מספק, חלבון והרגל אחד יציב בכל פעם.",
        }
    if goal == "improve_endurance":
        return {
            **defaults,
            "main_reps": "10-15 חזרות",
            "upper_reps": "10-15 חזרות",
            "hinge_reps": "10-12 חזרות",
            "upper_rest": "60 שניות",
            "day_note": "שמור קצב נשימה נשלט והוסף הליכה או אירובי קל בימים נפרדים.",
            "progression_rule": "העלה קודם משך או תדירות קלה, ורק אחר כך עצימות.",
            "recovery_note": "רוב העבודה האירובית צריכה להרגיש ניתנת לשיחה, עם מעט עבודה עצימה רק אחרי בסיס עקבי.",
        }
    return defaults
