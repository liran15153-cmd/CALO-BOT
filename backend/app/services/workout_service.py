from datetime import UTC, date, datetime
import re
from typing import Any

from sqlalchemy import delete, desc, select, update
from sqlalchemy.orm import Session

from backend.app.models import PendingAction, UserProfile, Workout, WorkoutExercise, WorkoutLog, WorkoutPlan
from backend.app.schemas import StructuredWorkoutPlan, WorkoutLogRequest, WorkoutPlanRequest
from backend.app.services.pain_text import extract_pain_area, has_pain_or_injury_signal
from backend.app.services.training_adaptation_service import TrainingAdaptationService
from backend.app.services.workout_plan_builder import (
    WorkoutPlanBuilder,
    WorkoutPlanningInput,
    duration_weeks_for_plan_type,
    infer_duration_weeks,
    infer_experience,
    infer_plan_type,
    is_persistent_plan_type,
    is_single_workout_plan,
)


class WorkoutService:
    def __init__(self, db: Session):
        self.db = db

    def generate_plan(self, user_id: int, request: WorkoutPlanRequest) -> WorkoutPlan:
        profile = self.db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        plan_type = infer_plan_type(request.plan_type, request.prompt)
        if request.plan_type is None and not is_single_workout_plan(plan_type) and request.duration_weeks in {1, 2, 4}:
            plan_type = {1: "weekly_plan", 2: "two_week_plan", 4: "monthly_plan"}[request.duration_weeks]
        inferred_days = self._infer_days(request.prompt)
        profile_days = self._profile_days(profile)
        days_per_week = (
            1
            if is_single_workout_plan(plan_type)
            else request.days_per_week or inferred_days or profile_days or 3
        )
        inferred_duration_weeks = infer_duration_weeks(request.prompt)
        duration_weeks = duration_weeks_for_plan_type(plan_type) or request.duration_weeks or inferred_duration_weeks or 4
        inferred_equipment = self._infer_equipment(request.prompt)
        profile_equipment = self._profile_equipment(profile)
        equipment = request.equipment or inferred_equipment or profile_equipment or ["bodyweight"]
        inferred_goal = self._infer_goal(request.prompt)
        profile_goal = profile.main_goal if profile else None
        goal = inferred_goal or request.goal or profile_goal or "improve_fitness"
        inferred_experience = infer_experience(request.prompt)
        profile_experience = profile.experience_level if profile else None
        experience_level = request.experience_level or inferred_experience or profile_experience or "beginner"
        inferred_session_length = self._infer_session_length(request.prompt)
        profile_session_length = profile.session_length_minutes if profile else None
        default_session_length = 30 if is_single_workout_plan(plan_type) else 45
        session_length_minutes = (
            request.session_length_minutes
            or inferred_session_length
            or profile_session_length
            or default_session_length
        )
        limitations = request.limitations or (profile.injuries_limitations if profile else None)
        assumptions = self._planning_assumptions(
            request=request,
            profile=profile,
            plan_type=plan_type,
            inferred_days=inferred_days,
            profile_days=profile_days,
            inferred_duration_weeks=inferred_duration_weeks,
            inferred_equipment=inferred_equipment,
            profile_equipment=profile_equipment,
            inferred_goal=inferred_goal,
            profile_goal=profile_goal,
            inferred_experience=inferred_experience,
            profile_experience=profile_experience,
            inferred_session_length=inferred_session_length,
            profile_session_length=profile_session_length,
        )
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
                assumptions=assumptions,
            )
        )

        current_plans = list(
            self.db.scalars(
                select(WorkoutPlan)
                .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_current.is_(True))
                .order_by(desc(WorkoutPlan.created_at), desc(WorkoutPlan.id))
            ).all()
        )
        if is_persistent_plan_type(plan_type):
            for current in current_plans:
                if is_single_workout_plan((current.plan_json or {}).get("plan_type")):
                    current.is_current = False
            current_plans = [
                current
                for current in current_plans
                if not is_single_workout_plan((current.plan_json or {}).get("plan_type"))
            ]
        is_current = is_persistent_plan_type(plan_type) and not current_plans

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
        current_plans = self.db.scalars(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_current.is_(True))
            .order_by(desc(WorkoutPlan.created_at), desc(WorkoutPlan.id))
        ).all()
        return next(
            (
                plan
                for plan in current_plans
                if not is_single_workout_plan((plan.plan_json or {}).get("plan_type"))
            ),
            None,
        )

    def activate_plan(self, user_id: int, plan_id: int, *, delete_previous: bool = True) -> WorkoutPlan:
        plan = self.db.get(WorkoutPlan, plan_id)
        if plan is None or plan.user_id != user_id:
            raise ValueError("Workout plan not found")
        if is_single_workout_plan((plan.plan_json or {}).get("plan_type")):
            raise ValueError("Cannot activate a single workout as the current plan")

        current_plans = list(
            self.db.scalars(
                select(WorkoutPlan)
                .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_current.is_(True), WorkoutPlan.id != plan_id)
                .order_by(desc(WorkoutPlan.created_at), desc(WorkoutPlan.id))
            ).all()
        )
        for current in current_plans:
            if delete_previous:
                self._delete_plan_record(current)
            else:
                current.is_current = False

        plan.is_current = True
        self.db.execute(
            update(PendingAction)
            .where(
                PendingAction.subject_type == "workout_plan",
                PendingAction.subject_id == plan.id,
                PendingAction.status == "pending",
            )
            .values(status="resolved", resolution="confirmed", resolved_at=datetime.now(UTC))
        )
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def delete_plan(self, user_id: int, plan_id: int, *, allow_current: bool = False) -> None:
        plan = self.db.get(WorkoutPlan, plan_id)
        if plan is None or plan.user_id != user_id:
            raise ValueError("Workout plan not found")
        if plan.is_current and not allow_current:
            raise ValueError("Cannot delete the active workout plan")
        self._delete_plan_record(plan)
        self.db.commit()

    def apply_scoped_plan_edit(self, user_id: int, text: str) -> dict[str, Any]:
        plan = self.current_plan(user_id=user_id)
        if plan is None:
            return {
                "status": "no_current_plan",
                "edit_type": "none",
                "changed_exercises": 0,
                "message": "אין תוכנית פעילה לעריכה. הפעולה הבאה: לבקש תוכנית שבועית, לשבועיים או חודשית ואז אוכל לשנות אותה נקודתית.",
            }

        edit_type = _scoped_plan_edit_type(text)
        if edit_type is None:
            return {
                "status": "needs_clarification",
                "edit_type": "unclear",
                "changed_exercises": 0,
                "message": "איזה שינוי נקודתי לעשות בתוכנית: להחליף תרגיל בגלל ציוד/כאב, להוריד נפח, או לשנות יום מסוים?",
            }

        plan_json = dict(plan.plan_json or {})
        days = [
            {
                **dict(day),
                "exercises": [dict(exercise) for exercise in (day.get("exercises") or [])],
            }
            for day in plan_json.get("days", [])
        ]
        if edit_type == "pain_clarification":
            return {
                "status": "needs_clarification",
                "edit_type": "pain_unclear",
                "changed_exercises": 0,
                "message": "חסר פרט בטיחותי אחד לפני שינוי התוכנית: איפה הכאב, והאם הוא חד/מחמיר או רק רגישות קלה? עד אז אל תדחוף דרך הכאב.",
            }
        if edit_type == "exercise_clarification":
            return {
                "status": "needs_clarification",
                "edit_type": "exercise_unclear",
                "changed_exercises": 0,
                "message": "לפני שאחליף תרגיל בתוכנית חסרה סיבה אחת: ציוד לא זמין, קשה מדי, כאב, או העדפה? עד אז אני לא משנה את התוכנית הפעילה.",
            }

        if edit_type == "pain_substitution":
            pain_area = extract_pain_area(text) or "אזור הכאב"
            changed_exercises = _apply_pain_substitution_to_days(days, text=text, pain_area=pain_area)
            status = "updated" if changed_exercises else "needs_clarification"
            message = (
                f"עדכנתי רק את התרגילים הרלוונטיים סביב כאב ב{pain_area} בלי לבנות תוכנית חדשה: "
                f"החלפתי/צמצמתי {changed_exercises} תרגילים. הפעולה הבאה: לבצע בטווח ללא כאב, RPE 5-7, ולעצור אם הכאב חד או מחמיר."
            )
            if not changed_exercises:
                return {
                    "status": status,
                    "edit_type": edit_type,
                    "changed_exercises": 0,
                    "message": "לא מצאתי בתוכנית תרגיל שמתאים לכאב שתיארת. איזה תרגיל בדיוק מכאיב: סקוואט, מכרע, מדרגה או משהו אחר?",
                }
        elif edit_type == "replace_row_machine":
            changed_exercises = _replace_row_machine_from_days(days)
            status = "updated" if changed_exercises else "needs_clarification"
            message = (
                f"עדכנתי רק את תרגילי החתירה שדרשו מכונה בלי לבנות תוכנית חדשה: החלפתי {changed_exercises} תרגילים/חלופות. "
                "הפעולה הבאה: לבצע חתירה חופשית/כבל בטכניקה נשלטת ולתעד RPE או מאמץ מילולי."
            )
            if not changed_exercises:
                return {
                    "status": status,
                    "edit_type": edit_type,
                    "changed_exercises": 0,
                    "message": "לא מצאתי בתוכנית חתירה במכונה. איזה תרגיל או ציוד חסר בדיוק?",
                }
        elif edit_type == "regress_pushup":
            changed_exercises = _regress_pushups_in_days(days)
            status = "updated" if changed_exercises else "needs_clarification"
            message = (
                f"החלפתי רק את שכיבות הסמיכה שקשות מדי בלי לבנות תוכנית חדשה: עדכנתי {changed_exercises} תרגילים לגרסה קלה יותר. "
                "הפעולה הבאה: לסיים את כל החזרות בטכניקה נקייה לפני שמורידים את השיפוע."
            )
            if not changed_exercises:
                return {
                    "status": status,
                    "edit_type": edit_type,
                    "changed_exercises": 0,
                    "message": "לא מצאתי בתוכנית שכיבות סמיכה. איזה תרגיל בדיוק קשה מדי?",
                }
        elif edit_type == "remove_bench":
            changed_exercises = _remove_bench_from_days(days)
            plan.equipment_needed = _without_bench(plan.equipment_needed or [])
            plan_json["equipment_needed"] = _without_bench(plan_json.get("equipment_needed") or [])
            decision_inputs = dict(plan_json.get("decision_inputs") or {})
            decision_inputs["equipment"] = _without_bench(decision_inputs.get("equipment") or [])
            plan_json["decision_inputs"] = decision_inputs
            status = "updated"
            message = (
                f"עדכנתי את התוכנית הפעילה בלי לבנות חדשה: הסרתי שימוש בספסל ועדכנתי {changed_exercises} תרגילים/חלופות. "
                "הפעולה הבאה: באימון הקרוב לבצע את הגרסאות בלי ספסל ולתעד RPE או מאמץ מילולי וכאב."
            )
        elif edit_type == "remove_cable":
            changed_exercises = _remove_cable_from_days(days)
            current_equipment = list(plan.equipment_needed or [])
            plan_equipment = list(plan_json.get("equipment_needed") or [])
            decision_inputs = dict(plan_json.get("decision_inputs") or {})
            decision_equipment = list(decision_inputs.get("equipment") or [])
            next_current_equipment = _without_cable(current_equipment)
            next_plan_equipment = _without_cable(plan_equipment)
            next_decision_equipment = _without_cable(decision_equipment)
            equipment_changed = (
                next_current_equipment != current_equipment
                or next_plan_equipment != plan_equipment
                or next_decision_equipment != decision_equipment
            )
            plan.equipment_needed = next_current_equipment
            plan_json["equipment_needed"] = next_plan_equipment
            decision_inputs["equipment"] = next_decision_equipment
            plan_json["decision_inputs"] = decision_inputs
            status = "updated" if changed_exercises or equipment_changed else "needs_clarification"
            message = (
                f"עדכנתי את התוכנית הפעילה בלי לבנות תוכנית חדשה: הסרתי שימוש בכבל/פולי ועדכנתי {changed_exercises} תרגילים/חלופות. "
                "הפעולה הבאה: לבצע את הגרסאות בלי כבל, לשמור אותו דפוס תנועה, ולתעד RPE או מאמץ מילולי וכאב."
            )
            if not changed_exercises and not equipment_changed:
                return {
                    "status": status,
                    "edit_type": edit_type,
                    "changed_exercises": 0,
                    "message": "לא מצאתי בתוכנית תרגיל או חלופה עם כבל. איזה תרגיל בדיוק דורש כבל או פולי?",
                }
        else:
            changed_exercises = _reduce_volume_in_days(days)
            status = "updated" if changed_exercises else "unchanged"
            message = (
                f"הורדתי נפח בתוכנית הפעילה בלי לבנות חדשה: סט אחד פחות ב-{changed_exercises} תרגילים, בלי לשנות תרגילים. "
                "הפעולה הבאה: לבצע שבוע קל יותר ולתעד אם העייפות או הכאב ירדו."
            )

        if not changed_exercises and edit_type == "reduce_volume":
            message = "לא מצאתי סטים שאפשר להוריד בלי להפוך את האימון לריק. הפעולה הבאה: לבצע גרסת מינימום של 2-3 תרגילים ולתעד RPE או מאמץ מילולי וכאב."

        plan_json["days"] = days
        edit_history = list(plan_json.get("plan_edit_history") or [])
        edit_history.append(
            {
                "date": date.today().isoformat(),
                "edit_type": edit_type,
                "changed_exercises": changed_exercises,
                "source": "chat_scoped_plan_edit",
            }
        )
        plan_json["plan_edit_history"] = edit_history[-10:]
        plan.plan_json = plan_json
        self._sync_plan_rows_from_json(plan)
        self.db.commit()
        self.db.refresh(plan)
        return {
            "status": status,
            "edit_type": edit_type,
            "changed_exercises": changed_exercises,
            "message": message,
        }

    def _delete_plan_record(self, plan: WorkoutPlan) -> None:
        self.db.execute(
            update(PendingAction)
            .where(
                PendingAction.subject_type == "workout_plan",
                PendingAction.subject_id == plan.id,
                PendingAction.status == "pending",
            )
            .values(status="cancelled", resolution="candidate_deleted", resolved_at=datetime.now(UTC))
        )
        workouts = self._workouts_for_plan(plan.id)
        workout_ids = [workout.id for workout in workouts]
        if workout_ids:
            self.db.execute(update(WorkoutLog).where(WorkoutLog.workout_id.in_(workout_ids)).values(workout_id=None))
            self.db.execute(delete(WorkoutExercise).where(WorkoutExercise.workout_id.in_(workout_ids)))
            self.db.execute(delete(Workout).where(Workout.id.in_(workout_ids)))
        self.db.delete(plan)

    def _sync_plan_rows_from_json(self, plan: WorkoutPlan) -> None:
        days = plan.plan_json.get("days") or []
        workouts = self._workouts_for_plan(plan.id)
        for day_index, day_payload in enumerate(days):
            day = dict(day_payload)
            day_name = day.get("name") or f"Workout {day_index + 1}"
            scheduled_day = day_name.split(" ", 1)[0] if day_name else None
            if day_index < len(workouts):
                workout = workouts[day_index]
            else:
                workout = Workout(
                    user_id=plan.user_id,
                    plan_id=plan.id,
                    name=day_name,
                    scheduled_day=scheduled_day,
                    difficulty=day.get("difficulty") or "beginner",
                    workout_json=day,
                )
                self.db.add(workout)
                self.db.flush()
            workout.name = day_name
            workout.scheduled_day = scheduled_day or workout.scheduled_day
            workout.difficulty = day.get("difficulty") or workout.difficulty or "beginner"
            workout.workout_json = day
            self._sync_workout_exercise_rows(workout=workout, exercises=day.get("exercises") or [])

        for workout in workouts[len(days) :]:
            self.db.execute(update(WorkoutLog).where(WorkoutLog.workout_id == workout.id).values(workout_id=None))
            self.db.execute(delete(WorkoutExercise).where(WorkoutExercise.workout_id == workout.id))
            self.db.delete(workout)

    def _sync_workout_exercise_rows(self, *, workout: Workout, exercises: list[dict[str, Any]]) -> None:
        exercise_rows = self._exercises_for_workout(workout.id)
        for exercise_index, exercise_payload in enumerate(exercises):
            exercise = dict(exercise_payload)
            exercise_name = exercise.get("name") or f"Exercise {exercise_index + 1}"
            if exercise_index < len(exercise_rows):
                exercise_row = exercise_rows[exercise_index]
                exercise_row.name = exercise_name
            else:
                exercise_row = WorkoutExercise(
                    workout_id=workout.id,
                    name=exercise_name,
                    sets=exercise.get("sets"),
                    reps_or_duration=exercise.get("reps_or_duration"),
                    rest=exercise.get("rest"),
                    notes=exercise.get("notes"),
                    alternatives=exercise.get("alternatives") or [],
                )
                self.db.add(exercise_row)
                continue
            exercise_row.sets = exercise.get("sets") or exercise_row.sets
            exercise_row.reps_or_duration = exercise.get("reps_or_duration") or exercise_row.reps_or_duration
            exercise_row.rest = exercise.get("rest") or exercise_row.rest
            exercise_row.notes = exercise.get("notes")
            exercise_row.alternatives = exercise.get("alternatives") or []

        for exercise_row in exercise_rows[len(exercises) :]:
            self.db.delete(exercise_row)

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
        exercise_adjustments = [self._matching_exercise_adjustment(exercise, adaptation) for exercise in exercises]
        allow_first_progression = adaptation.get("progress_evidence") != "exercise_log" or not any(exercise_adjustments)
        return {
            "source": "derived_from_base_workout",
            "base_workout_id": workout.get("id"),
            "workout_name": workout.get("name"),
            "load_signal": load_signal,
            "summary": _execution_summary(load_signal),
            "plan_adjustment": adaptation.get("plan_adjustment"),
            "adjusted_exercises": [
                self._execution_exercise(
                    exercise=exercise,
                    load_signal=load_signal,
                    is_first_exercise=index == 0,
                    exercise_adjustment=exercise_adjustments[index],
                    adaptation=adaptation,
                    allow_first_progression=allow_first_progression,
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
        adaptation: dict[str, Any],
        allow_first_progression: bool,
    ) -> dict[str, Any]:
        base_sets = str(exercise.get("sets") or "")
        prescribed_sets = base_sets
        adjustment = exercise_adjustment.get("adjustment") if exercise_adjustment else "maintain"
        next_action = exercise_adjustment.get("next_action") if exercise_adjustment else "לבצע לפי התוכנית ולתעד איך זה הרגיש."
        notes = exercise.get("notes") or ""
        alternatives = list(exercise.get("alternatives") or [])
        progression_next_step = (
            _progression_next_step(exercise.get("name"), alternatives)
            if _can_name_progression_next_step(notes)
            else None
        )

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
            if adaptation.get("pain_area") == "knee":
                alternatives = _knee_pain_execution_alternatives(exercise, alternatives)
        elif load_signal == "recovery_needed":
            prescribed_sets = _reduced_sets(base_sets)
            adjustment = "reduce_or_hold"
            next_action = "המאמץ האחרון היה גבוה לפי RPE/RIR; להוריד מעט נפח או עומס ולהשאיר 2-3 RIR."
            notes = _append_note(notes, "זה אימון התאוששות יחסי, לא ניסיון לשבור שיא.")
        elif load_signal == "progress_candidate" and (
            (is_first_exercise and allow_first_progression)
            or adjustment == "small_progression"
            or _contains_any(notes, ["הוחלף", "קשות מדי", "לא זמינה", "לא זמין"])
        ):
            if _contains_any(notes, ["הוחלף", "קשות מדי", "לא זמינה", "לא זמין"]):
                adjustment = "substitution_progression_gate"
                next_action = (
                    f"אם הלוג האחרון היה נקי, ללא כאב ועם RPE 8 ומטה, להתקדם שלב אחד בלבד: רק ל{progression_next_step}; "
                    "אחרת לשמור את הגרסה הנוכחית. לתעד RPE וכאב אחרי הסטים - לא לנחש."
                    if progression_next_step
                    else "אם הלוג האחרון היה נקי, ללא כאב ועם RPE 8 ומטה, להתקדם שלב אחד בלבד; אחרת לשמור את הגרסה הנוכחית. לתעד RPE וכאב אחרי הסטים - לא לנחש."
                )
                notes = _append_note(
                    notes,
                    "שער התקדמות אחרי החלפה: השלמה נקייה, RPE 8 ומטה וללא כאב לפני חזרה לגרסה קשה יותר.",
                )
                if adaptation.get("progress_evidence") == "session_rpe_no_pain":
                    next_action = (
                        "הלוג האחרון היה כללי: RPE 8 ומטה ובלי כאב. להתקדם שלב אחד בלבד, "
                        "ולתעד חזרות/RPE לתרגיל הזה - לא לנחש מה היה בסטים; אם מופיע כאב או RPE מעל 8, לשמור."
                    )
                    notes = _append_note(
                        notes,
                        "מבוסס על לוג אימון כללי; באימון הבא עדיף לתעד גם חזרות/RPE לתרגיל.",
                    )
            else:
                adjustment = "small_progression"
                reason = exercise_adjustment.get("reason") if exercise_adjustment else None
                if reason == "qualitative_underload":
                    next_action = exercise_adjustment.get("next_action") or "להעלות עומס קטן או להאט קצב כי הלוג תיאר שקל מדי."
                    notes = _append_note(notes, "הלוג האחרון תיאר מאמץ קל מדי; לתקן במשתנה אחד קטן בלי קפיצה גדולה.")
                elif reason == "high_rir_underload":
                    next_action = exercise_adjustment.get("next_action") or "להעלות עומס קטן כדי לכוון ל-RIR 1-3."
                    notes = _append_note(notes, "הלוג האחרון השאיר יותר מדי חזרות ברזרבה; לכוון ל-RIR 1-3 בלי קפיצה גדולה.")
                elif reason == "qualitative_controlled_effort":
                    next_action = exercise_adjustment.get("next_action") or "אפשר להוסיף חזרה אחת או עומס קטן אחד בלבד אם הטכניקה נשארת נקייה."
                    notes = _append_note(notes, "הלוג האחרון תיאר מאמץ בשליטה; להתקדם רק במשתנה אחד ולתעד שוב.")
                else:
                    next_action = "אפשר להוסיף חזרה אחת או עומס קטן אחד בלבד אם הטכניקה נשארת נקייה; הלוג האחרון הראה RPE/RIR בשליטה."
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
            "progression_next_step": progression_next_step,
            "notes": notes,
            "alternatives": alternatives,
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
        text = prompt.lower()
        match = re.search(r"(\d{1,2})\s*-?\s*(?:days?|ימים|יום)", text)
        if match:
            return max(1, min(7, int(match.group(1))))
        hebrew_day_counts = {
            1: ["יום אחד", "פעם אחת בשבוע", "אימון אחד בשבוע"],
            2: ["יומיים", "שני ימים", "שתי פעמים בשבוע", "פעמיים בשבוע", "שני אימונים"],
            3: ["שלושה ימים", "שלוש פעמים בשבוע", "שלושה אימונים", "שלוש אימונים"],
            4: ["ארבעה ימים", "ארבע פעמים בשבוע", "ארבעה אימונים", "ארבע אימונים"],
            5: ["חמישה ימים", "חמש פעמים בשבוע", "חמישה אימונים", "חמש אימונים"],
            6: ["שישה ימים", "שש פעמים בשבוע", "שישה אימונים", "שש אימונים"],
            7: ["שבעה ימים", "שבע פעמים בשבוע", "שבעה אימונים", "שבע אימונים"],
        }
        for days, phrases in hebrew_day_counts.items():
            if any(phrase in text for phrase in phrases):
                return days
        return None

    @staticmethod
    def _infer_goal(prompt: str) -> str | None:
        text = prompt.lower()
        if any(term in text for term in ["muscle", "hypertrophy"]):
            return "build_muscle"
        if any(term in text for term in ["strength", "get stronger"]):
            return "improve_strength"
        if any(term in text for term in ["endurance", "cardio"]):
            return "improve_endurance"
        if any(term in text for term in ["fat", "cutting"]):
            return "lose_fat"
        if any(term in text for term in ["mobility", "flexibility", "מוביליטי", "גמישות", "תנועתיות"]):
            return "improve_mobility"
        if "שריר" in text or "מסה" in text or "היפרטרופיה" in text:
            return "build_muscle"
        if WorkoutService._has_strength_goal_signal(text):
            return "improve_strength"
        if "כוח" in text or "להתחזק" in text:
            return "improve_strength"
        if "סיבולת" in text or "לב ריאה" in text:
            return "improve_endurance"
        if "שומן" in text or "ירידה במשקל" in text or "חיטוב" in text or "להתחטב" in text:
            return "lose_fat"
        return None

    @staticmethod
    def _has_hypertrophy_goal_signal(prompt: str) -> bool:
        text = prompt.lower()
        return any(term in text for term in ["muscle", "hypertrophy", "שריר", "מסה", "היפרטרופיה"])

    @staticmethod
    def _has_strength_goal_signal(prompt: str) -> bool:
        text = prompt.lower()
        return any(term in text for term in ["strength", "get stronger", "כוח", "להתחזק", "לחיזוק"])

    @staticmethod
    def _infer_session_length(prompt: str) -> int | None:
        text = prompt.lower()
        if "שעה וחצי" in text:
            return 90
        if "חצי שעה" in text:
            return 30
        if "רבע שעה" in text:
            return 15
        if "שעה" in text:
            return 60
        match = re.search(r"(\d{2,3})\s*(?:minutes?|mins?|min|דקות|דקה|דק׳|דק')", text)
        if not match:
            return None
        return max(10, min(120, int(match.group(1))))

    @staticmethod
    def _infer_equipment(prompt: str) -> list[str]:
        text = prompt.lower()
        if any(
            term in text
            for term in ["בלי ציוד", "ללא ציוד", "משקל גוף", "משקל-גוף", "bodyweight", "body weight", "body-weight", "no equipment"]
        ):
            return ["bodyweight"]
        if any(term in text for term in ["חדר כושר", "gym", "מכון", "מכונה", "מכונות", "כבל", "cable", "machine"]):
            return ["חדר כושר", "משקולות יד", "מכונות"]
        if any(term in text for term in ["משקולת", "משקולות", "dumbbell", "dumbbells"]):
            return ["dumbbells"]
        if any(term in text for term in ["גומייה", "גומיות", "band", "bands"]):
            return ["resistance bands"]
        if any(term in text for term in ["בית", "בבית", "ביתית", "home"]):
            return ["bodyweight"]
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

    @staticmethod
    def _planning_assumptions(
        *,
        request: WorkoutPlanRequest,
        profile: UserProfile | None,
        plan_type: str,
        inferred_days: int | None,
        profile_days: int | None,
        inferred_duration_weeks: int | None,
        inferred_equipment: list[str],
        profile_equipment: list[str],
        inferred_goal: str | None,
        profile_goal: str | None,
        inferred_experience: str | None,
        profile_experience: str | None,
        inferred_session_length: int | None,
        profile_session_length: int | None,
    ) -> list[str]:
        assumptions: list[str] = []
        if (
            request.plan_type is None
            and request.duration_weeks is None
            and inferred_duration_weeks is None
            and plan_type == "monthly_plan"
        ):
            assumptions.append("לא צוין אופק תוכנית, הנחתי תוכנית חודשית.")
        if plan_type == "monthly_plan" and (request.duration_weeks == 3 or inferred_duration_weeks == 3):
            assumptions.append("צוין אופק של 3 שבועות; המערכת מפרידה כרגע בין שבוע, שבועיים וחודש, לכן בניתי תוכנית חודשית שמרנית.")
        if request.goal is None and inferred_goal is None and profile_goal is None:
            assumptions.append("לא צוינה מטרה, הנחתי שיפור כושר כללי.")
        if request.goal is not None and inferred_goal is not None and request.goal != inferred_goal:
            assumptions.append("הטקסט ציין מטרה שונה משדה goal, השתמשתי במטרה מתוך הבקשה.")
        if (
            inferred_goal == "build_muscle"
            and WorkoutService._has_hypertrophy_goal_signal(request.prompt)
            and WorkoutService._has_strength_goal_signal(request.prompt)
        ):
            assumptions.append(
                "הבקשה שילבה כוח ומסת שריר; הנחתי שבניית שריר היא המוקד הראשי והכוח יתקדם דרך התרגילים המרכזיים."
            )
        if (
            not is_single_workout_plan(plan_type)
            and request.days_per_week is None
            and inferred_days is None
            and profile_days is None
        ):
            assumptions.append("לא צוינו ימי אימון, הנחתי 3 אימונים בשבוע.")
        if request.session_length_minutes is None and inferred_session_length is None and profile_session_length is None:
            if is_single_workout_plan(plan_type):
                assumptions.append("לא צוין משך אימון, הנחתי 30 דקות לאימון יחיד.")
            else:
                assumptions.append("לא צוין משך אימון, הנחתי 45 דקות.")
        if not request.equipment and not inferred_equipment and not profile_equipment:
            assumptions.append("לא צוין ציוד, הנחתי משקל גוף.")
        if request.experience_level is None and inferred_experience is None and profile_experience is None:
            assumptions.append("לא צוינה רמת ניסיון, הנחתי מתחיל/ה.")
        if profile is None:
            assumptions.append("לא נמצא פרופיל אימון, השתמשתי בברירות מחדל שמרניות.")
        return assumptions[:6]

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
            if any(
                term in text
                for term in [
                    "skipped",
                    "פספסתי",
                    "פספס",
                    "דילגתי",
                    "לא עשיתי",
                    "לא התאמנתי",
                    "did not workout",
                    "did not work out",
                    "didn't workout",
                    "didn't work out",
                    "didnt workout",
                    "didnt work out",
                ]
            )
            else "completed"
        )
        results = self._parse_exercise_results(request.text)
        rpe = self._parse_rpe(request.text)
        rir = self._parse_rir(request.text)
        effort_signal = self._parse_qualitative_effort(request.text)
        if rir is not None:
            for result in results:
                result.setdefault("rir", rir)
        if effort_signal:
            for result in results:
                result.setdefault("effort_signal", effort_signal)
        parse_confidence = (
            "high" if results and (rpe is not None or rir is not None or effort_signal) else "medium" if results or rpe is not None else "low"
        )
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
        exercise_results = []
        for exercise in request.exercises:
            exercise_text = " ".join(part for part in [exercise.notes, request.notes, request.text] if part)
            result = {
                "exercise_id": exercise.exercise_id,
                "exercise_name": exercise.exercise_name,
                "status": exercise.status,
                "sets": [logged_set.model_dump(exclude_none=True) for logged_set in exercise.sets],
                "rpe": exercise.rpe,
                "rir": exercise.rir,
                "notes": exercise.notes,
            }
            effort_signal = self._parse_qualitative_effort(exercise_text)
            if effort_signal:
                result["effort_signal"] = effort_signal
            if (
                self._exercise_requires_numeric_progression_gate(exercise.exercise_id)
                and exercise.rpe is None
                and request.rpe is None
            ):
                result["progression_gate_missing_rpe"] = True
            exercise_results.append(result)
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

    def _exercise_requires_numeric_progression_gate(self, exercise_id: int | None) -> bool:
        if exercise_id is None:
            return False
        exercise = self.db.get(WorkoutExercise, exercise_id)
        if exercise is None:
            return False
        text = " ".join(
            [
                exercise.name or "",
                exercise.notes or "",
                " ".join(exercise.alternatives or []),
            ]
        ).lower()
        return _contains_any(text, ["שער התקדמות אחרי החלפה", "הוחלף", "קשות מדי", "לא זמינה", "לא זמין"])

    @staticmethod
    def _parse_exercise_results(text: str) -> list[dict]:
        patterns = [
            r"(?P<sets>\d+)\s+sets?\s+of\s+(?P<exercise>[a-zA-Z ]+?)\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s+with\s+(?P<weight>\d+\s?kg))?",
            r"(?:i\s+did\s+)?(?P<exercise>[a-zA-Z][a-zA-Z ]+?)\s+(?P<sets>\d+)\s+sets?\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s+(?:with|at)\s+(?P<weight>\d+\s?kg))?",
            r"(?:עשיתי\s+)?(?P<exercise>[\u0590-\u05ffa-zA-Z \"'/-]+?)\s+(?P<sets>\d+)\s*[xX×]\s*(?P<rep_single>\d+)(?:\s*חזרות)?(?:\s*(?:עם|ב)?\s*(?P<weight>\d+\s?(?:kg|קג|ק\"ג|ק״ג|קילו)))?",
            r"(?:עשיתי\s+)?(?P<exercise>[\u0590-\u05ffa-zA-Z \"'/-]+?)\s+(?P<sets>\d+)\s+סט(?:ים)?\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s*חזרות)?(?:\s*(?:עם)?\s*(?P<weight>\d+\s?(?:kg|קג|ק\"ג|ק״ג|קילו)))?",
            r"(?P<sets>\d+)\s+סט(?:ים)?\s+של\s+(?P<exercise>[\u0590-\u05ffa-zA-Z \"'/-]+?)\s+(?P<reps>\d+(?:,\s*\d+)*)(?:\s*חזרות)?(?:\s*(?:עם)?\s*(?P<weight>\d+\s?(?:kg|קג|ק\"ג|ק״ג)))?",
        ]
        match = next((match for pattern in patterns if (match := re.search(pattern, text, flags=re.IGNORECASE))), None)
        if not match:
            return []
        result = {
            "exercise": match.group("exercise").strip(" :-"),
            "sets": int(match.group("sets")),
        }
        reps_text = match.groupdict().get("reps")
        if reps_text:
            result["reps"] = [int(rep.strip()) for rep in reps_text.split(",")]
        else:
            result["reps"] = [int(match.group("rep_single"))] * int(match.group("sets"))
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
        match = re.search(r"(?:מאמץ|קושי|דרגת מאמץ)\D{0,10}(10|[1-9])(?:\s*(?:/|מתוך)\s*10)?", text)
        if match:
            return int(match.group(1))
        match = re.search(r"\b(10|[1-9])\s*(?:/|מתוך)\s*10\s*(?:מאמץ|קושי|דרגת מאמץ)\b", text)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _parse_rir(text: str) -> int | None:
        hebrew_rep = r"\u05d7\u05d6\u05e8(?:\u05d4|\u05d5\u05ea)"
        patterns = [
            r"\brir\s*[:=-]?\s*(10|[0-9])\b",
            r"\b(10|[0-9])\s*(?:rir|reps?\s+in\s+reserve)\b",
            rf"(?<!\d)(10|[0-9])(?!\d)\s*(?:{hebrew_rep}\s+\u05d1\u05e8\u05d6\u05e8\u05d1\u05d4|\u05e8\u05d6\u05e8\u05d1\u05d4)",
            rf"(?:\u05e0\u05e9\u05d0\u05e8(?:\u05d5|\u05d4)?|\u05e0\u05d5\u05ea\u05e8\u05d5|\u05d4\u05e9\u05d0\u05e8\u05ea\u05d9)\s*(?:\u05dc\u05d9\s*)?(10|[0-9])\s*{hebrew_rep}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _parse_qualitative_effort(text: str) -> str | None:
        normalized = text.lower()
        controlled_terms = [
            "בשליטה",
            "מאתגר אבל סבבה",
            "מאתגר אבל טוב",
            "לא קשה מדי",
            "לא כבד מדי",
        ]
        if any(term in normalized for term in controlled_terms):
            return "controlled"
        too_hard_terms = [
            "קשה מדי",
            "קשות מדי",
            "קשים מדי",
            "קשה רצח",
            "כבד מדי",
            "כבד רצח",
            "בקושי סיימתי",
            "הרג אותי",
            "too hard",
            "too heavy",
            "barely finished",
        ]
        if any(term in normalized for term in too_hard_terms):
            return "too_hard"
        underloaded_terms = [
            "קל מדי",
            "קלה מדי",
            "קלים מדי",
            "קל רצח",
            "קליל מדי",
            "לא היה מאתגר",
            "לא מאתגר",
            "נשאר לי מלא כוח",
            "נשאר מלא כוח",
            "נשארו מלא חזרות",
            "יכולתי עוד הרבה",
            "too easy",
            "felt easy",
        ]
        if any(term in normalized for term in underloaded_terms):
            return "underloaded"
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


def _scoped_plan_edit_type(text: str) -> str | None:
    normalized = text.lower()
    if has_pain_or_injury_signal(normalized):
        return "pain_substitution" if extract_pain_area(normalized) else "pain_clarification"
    if (
        _contains_any(normalized, ["חתירה", "row"])
        and _contains_any(normalized, ["מכונה", "machine"])
        and _contains_any(normalized, ["אין לי", "בלי", "ללא", "לא זמינה", "not available", "no machine"])
    ):
        return "replace_row_machine"
    if _contains_any(normalized, ["שכיבת סמיכה", "שכיבות סמיכה", "push-up", "pushup"]) and _contains_any(
        normalized,
        ["קשה מדי", "קשות מדי", "קשים מדי", "too hard", "too difficult"],
    ):
        return "regress_pushup"
    has_bench = "bench" in normalized or "ספסל" in normalized
    removes_bench = has_bench and any(
        phrase in normalized
        for phrase in ["אין לי", "בלי", "ללא", "no bench", "without bench", "remove bench", "לא זמין"]
    )
    if removes_bench:
        return "remove_bench"
    has_cable = any(term in normalized for term in ["cable", "cables", "כבל", "כבלים", "פולי"])
    removes_cable = has_cable and any(
        phrase in normalized
        for phrase in ["אין לי", "בלי", "ללא", "no cable", "without cable", "remove cable", "לא זמין", "לא זמינים"]
    )
    if removes_cable:
        return "remove_cable"
    if any(
        phrase in normalized
        for phrase in ["תוריד נפח", "תורידי נפח", "להוריד נפח", "פחות נפח", "פחות סטים", "reduce volume", "less volume"]
    ):
        return "reduce_volume"
    if _contains_any(normalized, ["דדליפט", "deadlift", "rdl"]) and _contains_any(
        normalized,
        ["תחליף", "תחליפי", "להחליף", "replace", "swap"],
    ):
        return "exercise_clarification"
    return None


def _apply_pain_substitution_to_days(days: list[dict[str, Any]], *, text: str, pain_area: str) -> int:
    normalized_area = pain_area.lower()
    normalized_text = text.lower()

    if _contains_any(normalized_area, ["ברך", "knee"]) and _contains_any(normalized_text, ["סקוואט", "squat"]):
        make_friendly = _make_squat_knee_friendly
    elif _contains_any(normalized_area, ["כתף", "shoulder"]) and _contains_any(
        normalized_text,
        ["לחיצ", "כתפ", "חזה", "שכיבת סמיכה", "press", "push"],
    ):
        target_patterns = {"vertical_push", "horizontal_push"}
        target_terms = ["לחיצ", "כתפ", "חזה", "שכיבת סמיכה", "press", "push"]
        if _contains_any(normalized_text, ["חזה", "שכיבת סמיכה", "push-up", "push up", "chest press", "bench press"]):
            target_patterns = {"horizontal_push"}
            target_terms = ["חזה", "שכיבת סמיכה", "push-up", "push up", "chest press", "bench press", "floor press"]
        elif _contains_any(normalized_text, ["כתפ", "overhead", "shoulder press", "military press"]):
            target_patterns = {"vertical_push"}
            target_terms = ["כתפ", "overhead", "shoulder press", "military press", "לנדמיין", "landmine"]
        make_friendly = lambda exercise: _make_press_shoulder_friendly(
            exercise,
            target_patterns=target_patterns,
            target_terms=target_terms,
        )
    elif _contains_any(normalized_area, ["גב תחתון", "גב", "מותן", "low back", "lower back", "back"]) and _contains_any(
        normalized_text,
        ["דדליפט", "הינג", "hinge", "deadlift", "rdl"],
    ):
        make_friendly = _make_hinge_low_back_friendly
    else:
        return 0

    changed = 0
    for day in days:
        for exercise in day.get("exercises") or []:
            if make_friendly(exercise):
                changed += 1
    return changed


def _replace_row_machine_from_days(days: list[dict[str, Any]]) -> int:
    changed = 0
    for day in days:
        for exercise in day.get("exercises") or []:
            if _make_row_machine_free(exercise):
                changed += 1
    return changed


def _make_row_machine_free(exercise: dict[str, Any]) -> bool:
    if not _exercise_matches(exercise, movement_patterns={"horizontal_pull"}, terms=["חתירה", "row"]):
        return False
    if not _exercise_text_contains(exercise, ["מכונה", "machine"]):
        return False
    original = dict(exercise)
    exercise["name"] = "חתירת משקולת יד בתמיכה"
    exercise["alternatives"] = ["חתירה בכבל", "חתירה עם גומייה", "חתירה מתחת לשולחן יציב"]
    exercise["notes"] = _append_note(
        exercise.get("notes") or "",
        "הוחלף כי מכונת חתירה לא זמינה; שמור דפוס משיכה אופקית, גב ניטרלי ועצירה קצרה בסוף התנועה.",
    )
    return exercise != original


def _regress_pushups_in_days(days: list[dict[str, Any]]) -> int:
    changed = 0
    for day in days:
        for exercise in day.get("exercises") or []:
            if _make_pushup_easier(exercise):
                changed += 1
    return changed


def _make_pushup_easier(exercise: dict[str, Any]) -> bool:
    if not _exercise_matches(exercise, movement_patterns={"horizontal_push"}, terms=["שכיבת סמיכה", "שכיבות סמיכה", "push-up", "pushup"]):
        return False
    if not _exercise_text_contains(exercise, ["שכיבת סמיכה", "שכיבות סמיכה", "push-up", "pushup"]):
        return False
    original = dict(exercise)
    exercise["name"] = "שכיבת סמיכה על קיר"
    exercise["sets"] = _reduced_sets(str(exercise.get("sets") or ""))
    exercise["alternatives"] = ["שכיבת סמיכה בשיפוע גבוה", "שכיבת סמיכה ברכיים", "החזקת פלאנק בשיפוע"]
    exercise["notes"] = _append_note(
        exercise.get("notes") or "",
        "הוחלף כי שכיבות הסמיכה קשות מדי כרגע; שמור גוף ישר וטווח נקי לפני שמורידים שיפוע.",
    )
    return exercise != original


def _make_squat_knee_friendly(exercise: dict[str, Any]) -> bool:
    if str(exercise.get("movement_pattern") or "").lower() != "squat" and not _exercise_text_contains(
        exercise,
        ["סקוואט", "squat"],
    ):
        return False
    original = dict(exercise)
    exercise["name"] = "סקוואט לקופסה בטווח קצר"
    exercise["sets"] = _reduced_sets(str(exercise.get("sets") or ""))
    exercise["alternatives"] = _knee_pain_execution_alternatives(exercise, list(exercise.get("alternatives") or []))
    if "ישיבה-קימה מכיסא" not in exercise["alternatives"]:
        exercise["alternatives"].append("ישיבה-קימה מכיסא")
    safety_notes = list(exercise.get("safety_notes") or [])
    pain_note = "ברך רגישה: לעבוד בטווח ללא כאב, בלי מכרע עמוק או מדרגה גבוהה, ולעצור אם הכאב חד או מחמיר."
    if pain_note not in safety_notes:
        safety_notes.append(pain_note)
    exercise["safety_notes"] = safety_notes
    exercise["notes"] = _append_note(
        exercise.get("notes") or "",
        "הוחלף בגלל כאב ברך בסקוואט; שמור דפוס squat בטווח קצר ו-RPE 5-7.",
    )
    return exercise != original


def _make_press_shoulder_friendly(
    exercise: dict[str, Any],
    *,
    target_patterns: set[str],
    target_terms: list[str],
) -> bool:
    if not _exercise_matches(
        exercise,
        movement_patterns=target_patterns,
        terms=target_terms,
    ):
        return False
    original = dict(exercise)
    if exercise.get("movement_pattern") == "vertical_push":
        exercise["name"] = "לחיצת לנדמיין חצי כריעה"
        exercise["alternatives"] = ["לחיצה בזווית שיפוע בטווח נוח", "הרחקת כתף עם גומייה קלה"]
    else:
        exercise["name"] = "שכיבת סמיכה בשיפוע"
        exercise["alternatives"] = ["לחיצת רצפה באחיזה ניטרלית", "לחיצת כבלים קלה בטווח נוח"]
    exercise["sets"] = _reduced_sets(str(exercise.get("sets") or ""))
    safety_notes = list(exercise.get("safety_notes") or [])
    pain_note = "כתף רגישה: לעבוד בטווח נוח ללא כאב חד, להעדיף אחיזה ניטרלית/זווית שיפוע, ולעצור אם יש הקרנה, חולשה או החמרה."
    if pain_note not in safety_notes:
        safety_notes.append(pain_note)
    exercise["safety_notes"] = safety_notes
    exercise["notes"] = _append_note(
        exercise.get("notes") or "",
        "הוחלף בגלל כאב כתף בלחיצה; שמור דפוס push בזווית נוחה ו-RPE 5-7.",
    )
    return exercise != original


def _make_hinge_low_back_friendly(exercise: dict[str, Any]) -> bool:
    if not _exercise_matches(
        exercise,
        movement_patterns={"hip_hinge", "hinge"},
        terms=["דדליפט", "הינג", "hinge", "deadlift", "rdl"],
    ):
        return False
    original = dict(exercise)
    exercise["name"] = "היפ הינג' לקיר"
    exercise["sets"] = _reduced_sets(str(exercise.get("sets") or ""))
    exercise["alternatives"] = ["גשר ישבן", "משיכת כבל בין הרגליים קלה", "היפ הינג' עם מקל"]
    safety_notes = list(exercise.get("safety_notes") or [])
    pain_note = "גב תחתון רגיש: לשמור עמוד שדרה ניטרלי, טווח קצר ועומס קל; לעצור בהקרנה לרגל, נימול, חולשה או כאב חד."
    if pain_note not in safety_notes:
        safety_notes.append(pain_note)
    exercise["safety_notes"] = safety_notes
    exercise["notes"] = _append_note(
        exercise.get("notes") or "",
        "הוחלף בגלל כאב גב תחתון בדדליפט/הינג'; תרגל שליטה לפני חזרה לעומס.",
    )
    return exercise != original


def _exercise_matches(exercise: dict[str, Any], *, movement_patterns: set[str], terms: list[str]) -> bool:
    movement_pattern = str(exercise.get("movement_pattern") or "").lower()
    if movement_pattern:
        return movement_pattern in movement_patterns
    return _exercise_text_contains(exercise, terms)


def _exercise_text_contains(exercise: dict[str, Any], terms: list[str]) -> bool:
    text = " ".join(
        [
            str(exercise.get("name") or ""),
            " ".join(str(alternative) for alternative in (exercise.get("alternatives") or [])),
        ]
    ).lower()
    return _contains_any(text, terms)


def _contains_any(value: str, terms: list[str]) -> bool:
    return any(term in value for term in terms)


def _progression_next_step(name: str | None, alternatives: list[str]) -> str | None:
    current_name = str(name or "").strip()
    for alternative in alternatives:
        candidate = str(alternative or "").strip()
        if candidate and candidate != current_name:
            return candidate
    return None


def _can_name_progression_next_step(notes: str) -> bool:
    normalized = str(notes or "").lower()
    if _contains_any(normalized, ["כאב", "pain", "לא זמינה", "לא זמין", "ציוד", "מכונה", "ספסל", "bench"]):
        return False
    return _contains_any(normalized, ["קשות מדי", "קשה מדי", "too hard", "too difficult"])


def _remove_bench_from_days(days: list[dict[str, Any]]) -> int:
    changed = 0
    for day in days:
        for exercise in day.get("exercises") or []:
            if _remove_bench_from_exercise(exercise):
                changed += 1
    return changed


def _remove_bench_from_exercise(exercise: dict[str, Any]) -> bool:
    original = dict(exercise)
    name = str(exercise.get("name") or "")
    replacement = _no_bench_replacement(exercise)
    if replacement and _requires_bench(name):
        exercise["name"] = replacement

    alternatives = [str(alternative) for alternative in (exercise.get("alternatives") or [])]
    filtered_alternatives = [alternative for alternative in alternatives if not _requires_bench(alternative)]
    current_name = str(exercise.get("name") or "")
    if replacement and replacement != current_name and replacement not in filtered_alternatives:
        filtered_alternatives.insert(0, replacement)
    exercise["alternatives"] = filtered_alternatives

    if exercise != original:
        exercise["notes"] = _append_note(
            exercise.get("notes") or "",
            "הוחלף בגלל ציוד חסר; שמור אותו דפוס תנועה ועבוד ב-RPE 6-8.",
        )
    return exercise != original


def _no_bench_replacement(exercise: dict[str, Any]) -> str | None:
    text = " ".join(
        [
            str(exercise.get("name") or ""),
            str(exercise.get("movement_pattern") or ""),
            " ".join(str(alternative) for alternative in (exercise.get("alternatives") or [])),
        ]
    ).lower()
    if any(term in text for term in ["חתירה", "row", "horizontal_pull"]):
        return "חתירה ביד אחת עם משקולת"
    if any(term in text for term in ["דחיפת אגן", "היפ", "hip", "glute_bridge"]):
        return "גשר ישבן"
    if any(term in text for term in ["לחיצ", "press", "horizontal_push", "חזה"]):
        return "לחיצת רצפה עם משקולות"
    return None


def _requires_bench(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in ["bench", "ספסל", "בשיפוע עם משקולות"])


def _without_bench(items: list[str]) -> list[str]:
    return [item for item in items if not _requires_bench(str(item))]


def _remove_cable_from_days(days: list[dict[str, Any]]) -> int:
    changed = 0
    for day in days:
        for exercise in day.get("exercises") or []:
            if _remove_cable_from_exercise(exercise):
                changed += 1
    return changed


def _remove_cable_from_exercise(exercise: dict[str, Any]) -> bool:
    original = dict(exercise)
    name = str(exercise.get("name") or "")
    alternatives = [str(alternative) for alternative in (exercise.get("alternatives") or [])]
    if not _requires_cable(name) and not any(_requires_cable(alternative) for alternative in alternatives):
        return False

    replacement = _no_cable_replacement(exercise)
    if replacement and _requires_cable(name):
        exercise["name"] = replacement

    filtered_alternatives = [alternative for alternative in alternatives if not _requires_cable(alternative)]
    current_name = str(exercise.get("name") or "")
    if replacement and replacement != current_name and replacement not in filtered_alternatives:
        filtered_alternatives.insert(0, replacement)
    exercise["alternatives"] = filtered_alternatives

    if exercise != original:
        exercise["notes"] = _append_note(
            exercise.get("notes") or "",
            "הוחלף בגלל כבל/פולי חסר; שמור אותו דפוס תנועה ועבוד ב-RPE 6-8 לפני הוספת עומס.",
        )
    return exercise != original


def _no_cable_replacement(exercise: dict[str, Any]) -> str | None:
    text = " ".join(
        [
            str(exercise.get("name") or ""),
            str(exercise.get("movement_pattern") or ""),
            " ".join(str(alternative) for alternative in (exercise.get("alternatives") or [])),
        ]
    ).lower()
    if any(term in text for term in ["חתירה", "row", "horizontal_pull"]):
        return "חתירת משקולת יד בתמיכה"
    if any(term in text for term in ["לחיצ", "press", "horizontal_push", "חזה"]):
        return "לחיצת חזה במכונה"
    if any(term in text for term in ["דדליפט", "היפ", "hinge", "hip", "glute_bridge"]):
        return "גשר ישבן"
    if any(term in text for term in ["פולי", "vertical_pull", "משיכה", "pulldown"]):
        return "פולאובר עם משקולת"
    return None


def _requires_cable(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in ["cable", "כבל", "כבלים", "פולי"])


def _without_cable(items: list[str]) -> list[str]:
    return [item for item in items if not _requires_cable(str(item))]


def _reduce_volume_in_days(days: list[dict[str, Any]]) -> int:
    changed = 0
    for day in days:
        for exercise in day.get("exercises") or []:
            sets = str(exercise.get("sets") or "")
            reduced = _reduced_sets(sets)
            if reduced == sets:
                continue
            exercise["sets"] = reduced
            exercise["notes"] = _append_note(
                exercise.get("notes") or "",
                "נפח הופחת זמנית לשבוע קל יותר; אל תנסה להשלים את הסטים החסרים באותו אימון.",
            )
            changed += 1
    return changed


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


def _knee_pain_execution_alternatives(exercise: dict[str, Any], alternatives: list[str]) -> list[str]:
    text = " ".join([str(exercise.get("name") or ""), *alternatives]).lower()
    knee_loaded_terms = ["סקוואט", "squat", "לאנג", "lunge", "מדרגה", "step", "לחיצת רגליים", "leg press"]
    if not any(term in text for term in knee_loaded_terms):
        return alternatives

    risky_terms = ["מדרגה", "step", "מפוצל", "לאנג", "lunge"]
    filtered = [alternative for alternative in alternatives if not any(term in alternative.lower() for term in risky_terms)]
    if any("קופסה" in alternative or "ישיבה-קימה" in alternative or "טווח קצר" in alternative for alternative in filtered):
        return filtered
    return ["סקוואט לקופסה", "ישיבה-קימה מכיסא"]


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
