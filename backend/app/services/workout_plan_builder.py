import re
from dataclasses import dataclass, field

from backend.app.schemas import StructuredExercise, StructuredWorkoutDay, StructuredWorkoutPlan


SOURCE_REFS = [
    "ACSM 2026 resistance training guidelines: https://acsm.org/resistance-training-guidelines-update-2026/",
    "CDC adult physical activity guidelines: https://www.cdc.gov/physical-activity-basics/guidelines/adults.html",
    "CDC physical activity intensity and talk test: https://www.cdc.gov/physical-activity-basics/measuring/index.html",
    "CDC older adult activity and balance guidance: https://www.cdc.gov/physical-activity-basics/guidelines/older-adults.html",
    "NSCA resistance training frequency: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/",
    "HPRC/NSCA exercise order: https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training",
    "NASM resistance training acute variables: https://blog.nasm.org/resistance-training",
    "Exercise is Medicine low back pain: https://exerciseismedicine.org/assets/page_documents/EIM%20Rx%20series_Exercising%20with%20Lower%20Back%20Pain.pdf",
    "Mayo Clinic exercise warning symptoms: https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/exercise-and-chronic-disease/art-20046049",
    "Wingate strength training and healthy longevity: https://wingate.org.il/%D7%90%D7%99%D7%9E%D7%95%D7%A0%D7%99-%D7%9B%D7%95%D7%97-%D7%95%D7%AA%D7%95%D7%97%D7%9C%D7%AA-%D7%97%D7%99%D7%99%D7%9D-%D7%90%D7%A8%D7%95%D7%9B%D7%94/",
    "Wingate muscle fatigue and training efficiency: https://wingate.org.il/%D7%A2%D7%99%D7%99%D7%A4%D7%95%D7%AA-%D7%94%D7%A9%D7%A8%D7%99%D7%A8-%D7%95%D7%99%D7%A2%D7%99%D7%9C%D7%95%D7%AA-%D7%94%D7%90%D7%99%D7%9E%D7%95%D7%9F/",
    "FitStreet Hebrew workout plan building: https://fitstreet.co.il/workout-plan/",
    "Fitnessophy Hebrew FBW and AB workout plans: https://www.fitnessophy.com/workout-plans/",
    "RP Strength training volume landmarks: https://rpstrength.com/blogs/articles/training-volume-landmarks-muscle-growth",
    "Stronger by Science complete strength training guide: https://www.strongerbyscience.com/complete-strength-training-guide/",
    "Barbell Medicine pain in training: https://www.barbellmedicine.com/blog/pain-in-training-what-do/",
    "Runner's World run/walk beginner endurance coaching: https://www.runnersworld.com/training/a69889317/starting-a-run-walk-program/",
    "Tom's Guide physical therapist mobility and balance exercises: https://www.tomsguide.com/wellness/workouts/no-sit-ups-or-planks-a-physical-therapist-shares-the-6-best-exercises-for-staying-independent-after-60",
]

CANONICAL_PLAN_TYPES = {"single_workout", "weekly_plan", "two_week_plan", "monthly_plan"}
SINGLE_WORKOUT_ALIASES = {"single_workout", "single_session"}
PERSISTENT_PLAN_TYPES = {"weekly_plan", "two_week_plan", "monthly_plan", "multi_week"}

PLAN_TYPE_DURATION_WEEKS = {
    "single_workout": 1,
    "weekly_plan": 1,
    "two_week_plan": 2,
    "monthly_plan": 4,
}

PLAN_TYPE_LABELS_HE = {
    "single_workout": "אימון יחיד",
    "weekly_plan": "תוכנית שבועית",
    "two_week_plan": "תוכנית לשבועיים",
    "monthly_plan": "תוכנית חודשית",
    "single_session": "אימון יחיד",
    "multi_week": "תוכנית רב-שבועית",
}

SINGLE_WORKOUT_TERMS = [
    "today",
    "single",
    "one workout",
    "one session",
    "single workout",
    "single session",
    "right now",
    "tonight",
    "quick workout",
    "short workout",
    "עכשיו",
    "היום",
    "אימון אחד",
    "אימון יחיד",
    "אימון בודד",
    "אימון זריז",
    "אימון קצר",
    "מיני אימון",
    "סשן",
    "סשן אחד",
]

WEEKLY_PLAN_TERMS = [
    "weekly",
    "one week",
    "1 week",
    "1-week",
    "this week",
    "for a week",
    "workout week",
    "training week",
    "שבוע אימונים",
    "שבוע של אימונים",
    "שבוע הקרוב",
    "השבוע",
    "שבוע הבא",
    "לשבוע הבא",
    "לשבוע",
    "שבועית",
]

TWO_WEEK_PLAN_TERMS = [
    "two week",
    "two-week",
    "2 week",
    "2-week",
    "fortnight",
    "שבועיים",
    "לשבועיים",
    "שני שבועות",
    "שתי שבועות",
    "שבועיים הקרובים",
    "השבועיים הקרובים",
    "שבועיים הבאים",
    "לשבועיים הקרובים",
    "2 שבועות",
]

MONTHLY_PLAN_TERMS = [
    "monthly",
    "month",
    "four week",
    "four-week",
    "4 week",
    "4-week",
    "חודש",
    "חודשי",
    "חודשית",
    "חודש הקרוב",
    "לחודש הקרוב",
    "ארבעה שבועות",
    "ארבע שבועות",
    "4 שבועות",
]


def infer_plan_type(plan_type: str | None, prompt: str) -> str:
    if plan_type in CANONICAL_PLAN_TYPES:
        return plan_type
    if plan_type in SINGLE_WORKOUT_ALIASES:
        return "single_workout"
    if plan_type == "multi_week":
        return _infer_plan_type_from_prompt(prompt) or "monthly_plan"
    return _infer_plan_type_from_prompt(prompt) or "monthly_plan"


def is_single_workout_plan(plan_type: str | None) -> bool:
    return plan_type in SINGLE_WORKOUT_ALIASES


def is_persistent_plan_type(plan_type: str | None) -> bool:
    return plan_type in PERSISTENT_PLAN_TYPES


def duration_weeks_for_plan_type(plan_type: str | None) -> int | None:
    return PLAN_TYPE_DURATION_WEEKS.get(plan_type or "")


def _infer_plan_type_from_prompt(prompt: str) -> str | None:
    text = prompt.lower()
    if any(term in text for term in TWO_WEEK_PLAN_TERMS):
        return "two_week_plan"
    if any(term in text for term in MONTHLY_PLAN_TERMS):
        return "monthly_plan"
    if any(term in text for term in WEEKLY_PLAN_TERMS):
        return "weekly_plan"
    if any(term in text for term in SINGLE_WORKOUT_TERMS):
        return "single_workout"
    return None


@dataclass(frozen=True)
class WorkoutPlanningInput:
    prompt: str
    goal: str
    experience_level: str
    days_per_week: int
    duration_weeks: int
    equipment: list[str] = field(default_factory=list)
    session_length_minutes: int = 45
    preferred_days: list[str] = field(default_factory=list)
    limitations: str | None = None
    plan_type: str = "monthly_plan"
    readiness: str | None = None
    training_status: dict | None = None
    assumptions: list[str] = field(default_factory=list)


class WorkoutPlanBuilder:
    def build(self, planning_input: WorkoutPlanningInput) -> StructuredWorkoutPlan:
        plan_type = self._normalize_plan_type(planning_input.plan_type, planning_input.prompt)
        days_per_week = 1 if is_single_workout_plan(plan_type) else max(1, min(7, planning_input.days_per_week))
        duration_weeks = duration_weeks_for_plan_type(plan_type) or max(1, min(4, planning_input.duration_weeks))
        session_length = max(10, min(120, planning_input.session_length_minutes))
        readiness = (
            planning_input.readiness
            or self._readiness_from_training_status(planning_input.training_status)
            or self._infer_readiness(planning_input.prompt)
        )
        split = self._select_split(
            plan_type=plan_type,
            days_per_week=days_per_week,
            experience_level=planning_input.experience_level,
        )
        variables = _experience_training_variables(
            _goal_training_variables(planning_input.goal),
            planning_input.experience_level,
        )
        variables = _prompt_training_variables(variables, planning_input.prompt)
        display_limitations = _display_limitations_he(planning_input.limitations)
        safety_notes = self._safety_notes(display_limitations, readiness, planning_input.training_status)
        day_specs = self._day_specs(split=split, days_per_week=days_per_week)
        weekly_spacing_guidance = _weekly_spacing_guidance(
            prompt=planning_input.prompt,
            plan_type=plan_type,
            split=split,
            days_per_week=days_per_week,
            experience_level=planning_input.experience_level,
            goal_focus=variables.get("goal_focus"),
        )
        days = [
            self._build_day(
                index=index,
                focus=focus,
                preferred_days=planning_input.preferred_days,
                equipment=planning_input.equipment,
                variables=variables,
                session_length_minutes=session_length,
                display_limitations=display_limitations,
                limitations_text=planning_input.limitations,
                readiness=readiness,
                plan_type=plan_type,
                experience_level=planning_input.experience_level,
                spacing_reduction=(
                    index >= 2
                    and split == "full_body"
                    and days_per_week >= 4
                    and planning_input.experience_level == "beginner"
                    and _has_consecutive_day_pressure(planning_input.prompt)
                ),
            )
            for index, focus in enumerate(day_specs)
        ]

        plan = StructuredWorkoutPlan(
            name=self._plan_name(
                plan_type=plan_type,
                days_per_week=days_per_week,
                goal=planning_input.goal,
                duration_weeks=duration_weeks,
                split=split,
            ),
            goal=planning_input.goal,
            plan_type=plan_type,
            training_split=split,
            experience_level=planning_input.experience_level,
            duration_weeks=duration_weeks,
            days_per_week=days_per_week,
            session_length_minutes=session_length,
            equipment_needed=planning_input.equipment or ["bodyweight"],
            days=days,
            progression_rule=variables["progression_rule"],
            progression_model=_progression_model(plan_type),
            progression_schedule=_progression_schedule(plan_type, variables, planning_input.experience_level),
            tracking_guidance=_tracking_guidance(
                plan_type,
                variables,
                display_limitations,
                readiness,
                weekly_spacing_guidance=weekly_spacing_guidance,
            ),
            recovery_note=self._recovery_note(variables, display_limitations, readiness, plan_type),
            safety_notes=safety_notes,
            decision_inputs={
                "plan_type": PLAN_TYPE_LABELS_HE.get(plan_type, "תוכנית אימון"),
                "goal": planning_input.goal,
                "experience_level": planning_input.experience_level,
                "days_per_week": days_per_week,
                "duration_weeks": duration_weeks,
                "session_length_minutes": session_length,
                "training_split": split,
                "equipment": planning_input.equipment or ["bodyweight"],
                "limitations": planning_input.limitations or "none provided",
                "readiness": readiness or "green",
                "training_status": planning_input.training_status or {},
                "assumptions": planning_input.assumptions,
                "weekly_spacing_guidance": weekly_spacing_guidance,
            },
            source_refs=SOURCE_REFS,
        )
        return _neutralize_plan_guidance_copy(plan)

    @staticmethod
    def _normalize_plan_type(plan_type: str | None, prompt: str) -> str:
        return infer_plan_type(plan_type, prompt)

    @staticmethod
    def _infer_readiness(prompt: str) -> str:
        text = prompt.lower()
        red_terms = ["sharp pain", "chest pain", "dizzy", "faint", "כאב חד", "סחרחורת", "כאב בחזה"]
        if any(term in text for term in red_terms):
            return "red"
        yellow_terms = ["slept badly", "low sleep", "tired", "sore", "stress", "עייף", "מעט שינה", "תפוס"]
        if any(term in text for term in yellow_terms):
            return "yellow"
        return "green"

    @staticmethod
    def _readiness_from_training_status(training_status: dict | None) -> str | None:
        if not training_status:
            return None
        signal = training_status.get("load_signal")
        if signal == "pain_caution":
            return "red"
        if signal in {"recovery_needed", "adherence_risk"}:
            return "yellow"
        return None

    @staticmethod
    def _select_split(plan_type: str, days_per_week: int, experience_level: str) -> str:
        if is_single_workout_plan(plan_type):
            return "single_workout"
        if days_per_week <= 3:
            return "full_body"
        if days_per_week == 4:
            return "full_body" if experience_level == "beginner" else "upper_lower"
        if experience_level == "advanced":
            return "push_pull_legs"
        return "upper_lower"

    @staticmethod
    def _day_specs(split: str, days_per_week: int) -> list[str]:
        if split == "single_workout":
            return ["single_workout"]
        if split == "upper_lower":
            return ["upper_body" if index % 2 == 0 else "lower_body" for index in range(days_per_week)]
        if split == "push_pull_legs":
            pattern = ["push", "pull", "legs"]
            return [pattern[index % len(pattern)] for index in range(days_per_week)]
        pattern = ["full_body", "full_body_lower", "full_body_upper"]
        return [pattern[index % len(pattern)] for index in range(days_per_week)]

    def _build_day(
        self,
        *,
        index: int,
        focus: str,
        preferred_days: list[str],
        equipment: list[str],
        variables: dict[str, str],
        session_length_minutes: int,
        display_limitations: str,
        limitations_text: str | None,
        readiness: str,
        plan_type: str,
        experience_level: str,
        spacing_reduction: bool = False,
    ) -> StructuredWorkoutDay:
        raw_day_label = preferred_days[index] if preferred_days and index < len(preferred_days) else f"יום {index + 1}"
        day_label = "היום" if is_single_workout_plan(plan_type) else _day_label_he(raw_day_label)
        exercises = self._exercises_for_focus(
            focus=focus,
            equipment=equipment,
            variables=variables,
            display_limitations=display_limitations,
            limitations_text=limitations_text,
            readiness=readiness,
            session_length_minutes=session_length_minutes,
            experience_level=experience_level,
        )
        max_exercises = 3 if session_length_minutes <= 20 else 4 if session_length_minutes <= 35 else 5
        exercises = exercises[:max_exercises]
        if spacing_reduction:
            exercises = [_reduce_exercise_for_spacing(exercise) for exercise in exercises]
        day_notes = [f"שמור על אימון של בערך {session_length_minutes} דקות."]
        if readiness == "yellow":
            day_notes.append("יום צהוב: הורד 20-40% נפח או עצימות והשאר 2-3 חזרות ברזרבה.")
        elif readiness == "red":
            day_notes.append("יום אדום: אל תעמיס; בחר תנועה קלה בלבד ופנה לאיש מקצוע אם יש סימן חריג.")
        elif spacing_reduction:
            day_notes.append("ימים צפופים: הורד סט אחד ושמור RPE 5-7 כדי לאפשר התאוששות.")
        else:
            day_notes.append(variables["day_note"])

        return StructuredWorkoutDay(
            name=f"{day_label} {_focus_label_he(focus)}",
            focus=focus,
            estimated_duration_minutes=session_length_minutes,
            warmup=self._warmup(readiness),
            exercises=exercises,
            difficulty="easy" if readiness == "red" else "moderate",
            notes=" ".join(day_notes),
        )

    def _exercises_for_focus(
        self,
        *,
        focus: str,
        equipment: list[str],
        variables: dict[str, str],
        display_limitations: str,
        limitations_text: str | None,
        readiness: str,
        session_length_minutes: int,
        experience_level: str,
    ) -> list[StructuredExercise]:
        catalog = _exercise_catalog(equipment, variables, display_limitations, limitations_text, experience_level)
        if variables.get("goal_focus") == "mobility":
            selected = ["mobility_flow", "balance_control", "squat", "hinge", "core"]
        elif variables.get("goal_focus") == "endurance":
            selected = ["cardio_base", "squat", "horizontal_pull", "hinge", "core"]
        elif focus == "upper_body":
            selected = ["horizontal_push", "horizontal_pull", "vertical_push", "vertical_pull", "core"]
        elif focus == "lower_body":
            selected = ["squat", "hinge", "lunge", "glute_bridge", "core"]
        elif focus == "push":
            selected = ["horizontal_push", "vertical_push", "squat", "core"]
        elif focus == "pull":
            selected = ["horizontal_pull", "vertical_pull", "hinge", "core"]
        elif focus == "legs":
            selected = ["squat", "hinge", "lunge", "glute_bridge", "core"]
        elif focus == "single_workout":
            selected = ["squat", "horizontal_push", "horizontal_pull", "hinge", "core"]
        elif focus == "full_body_lower":
            selected = ["squat", "hinge", "horizontal_push", "horizontal_pull", "core"]
        elif focus == "full_body_upper":
            selected = ["horizontal_push", "horizontal_pull", "squat", "hinge", "core"]
        else:
            selected = ["squat", "horizontal_push", "horizontal_pull", "hinge", "core"]
        selected = _adapt_selection_for_limitations(selected, display_limitations, limitations_text)

        exercise_set = [catalog[key] for key in selected if key in catalog]
        if readiness in {"yellow", "red"} or session_length_minutes <= 20:
            return [_reduce_exercise(exercise, readiness) for exercise in exercise_set]
        return exercise_set

    @staticmethod
    def _warmup(readiness: str) -> list[str]:
        if readiness == "red":
            return ["5 דקות הליכה קלה", "בדיקת טווח תנועה ללא כאב", "נשימה רגועה וברייסינג קל"]
        return ["5 דקות אירובי קל", "תרגול היפ הינג'", "סיבובי כתפיים", "סט הכנה קל לתרגיל הראשון"]

    @staticmethod
    def _safety_notes(display_limitations: str, readiness: str, training_status: dict | None = None) -> list[str]:
        notes = [
            "עצור אם מופיעים כאב חד, כאב בחזה, סחרחורת חריגה, עילפון או קוצר נשימה חריג.",
            "עבוד בטווח ללא כאב ושמור טכניקה יציבה לפני הוספת עומס.",
        ]
        if display_limitations:
            notes.append(f"התאם את האימון סביב המגבלה שתועדה: {display_limitations}.")
        if readiness == "yellow":
            notes.append("הורד היום נפח או עצימות כדי לאפשר התאוששות לפני התקדמות.")
        if readiness == "red":
            notes.append("אל תתאמן חזק היום; בחר תנועה קלה בלבד ופנה לעזרה מקצועית אם יש סימני אזהרה.")
        if training_status and training_status.get("next_adjustment"):
            notes.append(training_status["next_adjustment"])
        return notes

    @staticmethod
    def _recovery_note(
        variables: dict[str, str],
        display_limitations: str,
        readiness: str,
        plan_type: str,
    ) -> str:
        note = (
            "אם הכאב השרירי או העייפות גבוהים, הורד סט אחד מכל תרגיל או קח יום מנוחה נוסף. "
            f"{variables['recovery_note']}"
        )
        if is_single_workout_plan(plan_type):
            note += " זו תוכנית לאימון יחיד, לכן אין צורך להשלים נפח חסר היום."
        if readiness == "yellow":
            note += " היום עדיף לשמור התאוששות: הפחת עומס וחזור להתקדמות רק כשהביצוע יציב."
        if display_limitations:
            note += f" עבוד סביב {display_limitations}."
        return note

    @staticmethod
    def _plan_name(plan_type: str, days_per_week: int, goal: str, duration_weeks: int, split: str) -> str:
        if is_single_workout_plan(plan_type):
            return f"אימון יחיד ל{_goal_label_he(goal)}"
        horizon = {
            "weekly_plan": "תוכנית שבועית",
            "two_week_plan": "תוכנית שבועיים",
            "monthly_plan": "תוכנית חודשית",
        }.get(plan_type, f"תוכנית {duration_weeks} שבועות")
        return f"{horizon} - {days_per_week} ימים ל{_goal_label_he(goal)} ({_focus_label_he(split)})"


def infer_duration_weeks(prompt: str) -> int | None:
    text = prompt.lower()
    if "month" in text or "חודש" in text:
        return 4
    digit_match = re.search(r"(\d{1,2})\s*-?\s*(?:weeks?|שבועות|שבוע)", text)
    if digit_match:
        return max(1, min(4, int(digit_match.group(1))))
    words = {"one": 1, "two": 2, "three": 3, "four": 4}
    for word, value in words.items():
        if f"{word} week" in text:
            return value
    return None


def infer_experience(prompt: str) -> str | None:
    text = prompt.lower()
    if "advanced" in text or "מתקדם" in text:
        return "advanced"
    if "intermediate" in text or "בינוני" in text:
        return "intermediate"
    if "beginner" in text or "starter" in text or "מתחיל" in text:
        return "beginner"
    return None


def _exercise_catalog(
    equipment: list[str],
    variables: dict[str, str],
    display_limitations: str,
    limitations_text: str | None,
    experience_level: str,
) -> dict[str, StructuredExercise]:
    mode = _equipment_mode(equipment)
    limitation_note = f" כבד את {display_limitations}." if display_limitations else ""
    source_refs = SOURCE_REFS[:5]

    has_bench = _has_bench_equipment(equipment)
    catalog = {
        "cardio_base": StructuredExercise(
            name="אירובי בסיסי בקצב שיחה",
            sets="1",
            reps_or_duration="12-25 דקות",
            rest="RPE 5-6 / אפשר לדבר במשפטים קצרים",
            notes=(
                f"בחר {variables.get('cardio_options', 'הליכה מהירה, אופניים, אליפטיקל או חתירה קלה בקצב שיחה')}; "
                "העלה משך או תדירות לפני עצימות."
            ),
            difficulty="moderate",
            alternatives=["הליכה מהירה", "אופניים", "אליפטיקל", "מדרגות בקצב קל"],
            safety_notes=[
                "עצור אם מופיעים סחרחורת, כאב בחזה או קוצר נשימה חריג",
                "שמור קצב talk test במקום לרדוף אחרי מהירות",
            ],
            movement_pattern="cardiorespiratory",
            target_muscles=["heart_lungs", "legs"],
            progression="הוסף 5 דקות או יום קל לפני אינטרוולים.",
            regression="קצר ל-8-10 דקות או חלק לשני מקטעים.",
            source_refs=source_refs,
        ),
        "mobility_flow": StructuredExercise(
            name="זרימת מוביליטי ירך-גב-כתף",
            sets="1",
            reps_or_duration="5-8 דקות",
            rest="נשימה רגועה",
            notes="עבור בין טווחים נוחים בלי כאב חד; החזק שליטה ואל תדחוף בכוח.",
            difficulty="easy",
            alternatives=["cat-cow", "90/90 ירך", "פתיחת כתפיים בקיר"],
            safety_notes=["עצור בכאב חד", "שמור טווח נוח ולא כפוי"],
            movement_pattern="mobility",
            target_muscles=["hips", "thoracic_spine", "shoulders"],
            progression="הארך טווח או זמן רק אם אין כאב.",
            regression="הקטן טווח או בצע בתמיכת קיר/כיסא.",
            source_refs=source_refs,
        ),
        "balance_control": StructuredExercise(
            name="שיווי משקל והעברת משקל",
            sets="2",
            reps_or_duration="30-45 שניות לכל צד",
            rest="45-60 שניות",
            notes="עבוד ליד קיר/כיסא אם צריך; המטרה היא שליטה, לא עייפות.",
            difficulty="easy",
            alternatives=["הליכת עקב-אגודל", "עמידה על רגל אחת ליד קיר", "sit-to-stand איטי"],
            safety_notes=["השתמש בתמיכה אם יש חשש נפילה", "עצור בסחרחורת או איבוד שיווי משקל"],
            movement_pattern="balance",
            target_muscles=["feet", "hips", "trunk_stabilizers"],
            progression="הקטן תמיכה או הארך זמן רק כשהשליטה יציבה.",
            regression="הרחב בסיס עמידה, החזק קיר או בצע ישיבה-קימה איטית.",
            source_refs=source_refs,
        ),
        "squat": StructuredExercise(
            name=_squat_name(mode, experience_level),
            sets=variables["main_sets"],
            reps_or_duration=variables["main_reps"],
            rest=variables["main_rest"],
            notes=f"עבוד בטווח ללא כאב ובקצב נשלט.{limitation_note}",
            difficulty="moderate",
            alternatives=_movement_alternatives("squat", mode, experience_level),
            safety_notes=["עצור אם מופיע כאב חד", "שמור ברכיים בקו כף הרגל"],
            movement_pattern="squat",
            target_muscles=["quadriceps", "glutes", "core"],
            progression="הוסף חזרות נקיות בתוך טווח היעד לפני הוספת עומס.",
            regression="עבור לסקוואט לקופסה או הקטן עומק.",
            source_refs=source_refs,
        ),
        "horizontal_push": StructuredExercise(
            name=_horizontal_push_name(mode, experience_level),
            sets=variables["upper_sets"],
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes=variables["effort_note"],
            difficulty="moderate",
            alternatives=_movement_alternatives("horizontal_push", mode, experience_level),
            safety_notes=["שמור על כתפיים נוחות"],
            movement_pattern="horizontal_push",
            target_muscles=["chest", "triceps", "anterior shoulders"],
            progression="הוסף חזרות, ואז הורד שיפוע או הוסף עומס קל.",
            regression="עבור לשכיבת סמיכה בשיפוע.",
            source_refs=source_refs,
        ),
        "horizontal_pull": StructuredExercise(
            name=_horizontal_pull_name(mode, experience_level),
            sets=variables["upper_sets"],
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes="עצור רגע קצר בקצה התנועה.",
            difficulty="moderate",
            alternatives=_movement_alternatives("horizontal_pull", mode, experience_level),
            safety_notes=["שמור על עמוד שדרה ניטרלי"],
            movement_pattern="horizontal_pull",
            target_muscles=["upper back", "lats", "biceps"],
            progression=_horizontal_pull_progression(mode),
            regression=_horizontal_pull_regression(mode),
            source_refs=source_refs,
        ),
        "hinge": StructuredExercise(
            name=_hinge_name(mode, experience_level),
            sets=variables["hinge_sets"],
            reps_or_duration=variables["hinge_reps"],
            rest=variables["main_rest"],
            notes=f"התמקד בדחיפת אגן לאחור ושמור שתי חזרות ברזרבה.{limitation_note}",
            difficulty="moderate",
            alternatives=_movement_alternatives("hinge", mode, experience_level),
            safety_notes=["עצור אם מופיע כאב חד בגב או בירך"],
            movement_pattern="hip_hinge",
            target_muscles=["hamstrings", "glutes", "spinal stabilizers"],
            progression="הוסף טווח ושליטה לפני הוספת עומס.",
            regression="עבור לגשר ישבן או היפ הינג' עם מקל.",
            source_refs=source_refs,
        ),
        "core": StructuredExercise(
            name="פלאנק ליבה",
            sets=variables["core_sets"],
            reps_or_duration="20-40 שניות",
            rest="60 שניות",
            notes="שמור נשימה רגועה וצלעות נמוכות.",
            difficulty="easy",
            alternatives=["דד באג", "פלאנק ברכיים"],
            safety_notes=["עצור אם מופיע כאב חד"],
            movement_pattern="core_anti_extension",
            target_muscles=["abdominals", "trunk stabilizers"],
            progression="הוסף זמן בהדרגה כל עוד הנשימה נשארת בשליטה.",
            regression="עבור לדד באג או פלאנק ברכיים.",
            source_refs=source_refs,
        ),
        "vertical_push": StructuredExercise(
            name=_vertical_push_name(mode, experience_level),
            sets=variables["accessory_sets"],
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes="שמור צלעות נמוכות ואל תדחוף דרך כאב כתף.",
            difficulty="moderate",
            alternatives=_movement_alternatives("vertical_push", mode, experience_level),
            safety_notes=["עצור אם מופיע כאב חד בכתף"],
            movement_pattern="vertical_push",
            target_muscles=["shoulders", "triceps", "upper chest"],
            progression="הוסף חזרות לפני הוספת עומס.",
            regression="עבור לטווח קל יותר או לחיצה בחצי כריעה.",
            source_refs=source_refs,
        ),
        "vertical_pull": StructuredExercise(
            name=_vertical_pull_name(mode, experience_level),
            sets=variables["accessory_sets"],
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes="משוך שכמות למטה ואחורה בלי למשוך בצוואר.",
            difficulty="moderate",
            alternatives=_movement_alternatives("vertical_pull", mode, experience_level),
            safety_notes=["שמור צוואר וכתפיים נוחים"],
            movement_pattern="vertical_pull",
            target_muscles=["lats", "upper back", "biceps"],
            progression=_vertical_pull_progression(mode),
            regression=_vertical_pull_regression(mode),
            source_refs=source_refs,
        ),
        "lunge": StructuredExercise(
            name=_lunge_name(mode, experience_level),
            sets=variables["accessory_sets"],
            reps_or_duration="8-10 חזרות לכל צד",
            rest="75 שניות",
            notes=f"שמור צעד קצר ונוח וטווח ללא כאב.{limitation_note}",
            difficulty="moderate",
            alternatives=_movement_alternatives("single_leg", mode, experience_level),
            safety_notes=["הקטן טווח אם מופיע כאב ברך"],
            movement_pattern="single_leg",
            target_muscles=["quadriceps", "glutes", "adductors"],
            progression="הוסף חזרות לכל צד לפני הוספת עומס.",
            regression="השתמש בתמיכה או במדרגה נמוכה יותר.",
            source_refs=source_refs,
        ),
        "glute_bridge": StructuredExercise(
            name="גשר ישבן",
            sets=variables["accessory_sets"],
            reps_or_duration="10-15 חזרות",
            rest="60 שניות",
            notes="עצור רגע למעלה בלי להקשית גב.",
            difficulty="easy",
            alternatives=_glute_bridge_alternatives(mode),
            safety_notes=["עצור אם מופיע כאב חד בגב"],
            movement_pattern="glute_bridge",
            target_muscles=["glutes", "hamstrings"],
            progression="הוסף זמן עצירה, ואז עבור לרגל אחת או עומס.",
            regression="עבוד בטווח קצר יותר.",
            source_refs=source_refs,
        ),
    }
    if mode == "dumbbells" and has_bench:
        push = catalog["horizontal_push"]
        catalog["horizontal_push"] = push.model_copy(
            update={
                "name": "לחיצת חזה עם משקולות על ספסל",
                "alternatives": [
                    "לחיצת חזה בשיפוע עם משקולות",
                    "לחיצת רצפה עם משקולות",
                ],
                "regression": "עבור ללחיצת רצפה עם משקולות או הורד עומס.",
            }
        )
    return _adapt_catalog_for_limitations(catalog, mode, display_limitations, limitations_text)


def _equipment_mode(equipment: list[str]) -> str:
    joined = " ".join(item.lower() for item in equipment)
    if any(term in joined for term in ["gym", "machine", "cable", "חדר כושר", "מכון", "מכונה", "מכונות", "כבל"]):
        return "gym"
    if any(term in joined for term in ["dumbbell", "משקול"]):
        return "dumbbells"
    if any(term in joined for term in ["band", "גומי", "גומייה", "גומיות"]):
        return "bands"
    return "bodyweight"


def _has_bench_equipment(equipment: list[str]) -> bool:
    joined = " ".join(item.lower() for item in equipment)
    return "bench" in joined or "ספסל" in joined


def _squat_name(mode: str, experience_level: str) -> str:
    if mode == "gym":
        return "לחיצת רגליים במכונה"
    if mode == "dumbbells":
        return "סקוואט גביע עם משקולת"
    if mode == "bands":
        return "סקוואט לקופסה עם גומייה קלה" if experience_level == "beginner" else "סקוואט עם גומייה"
    if experience_level == "advanced":
        return "סקוואט מפוצל משקל גוף"
    if experience_level == "beginner":
        return "סקוואט לקופסה"
    return "סקוואט משקל גוף"


def _horizontal_push_name(mode: str, experience_level: str) -> str:
    if mode == "gym":
        return "לחיצת חזה במכונה"
    if mode == "dumbbells":
        return "לחיצת רצפה עם משקולות"
    if mode == "bands":
        return "לחיצת חזה עם גומייה"
    return "שכיבת סמיכה איטית" if experience_level == "advanced" else "שכיבת סמיכה בשיפוע"


def _horizontal_pull_name(mode: str, experience_level: str) -> str:
    if mode == "gym":
        return "חתירה במכונה"
    if mode == "dumbbells":
        return "חתירה ביד אחת עם משקולת"
    if mode == "bands":
        return "חתירה עם גומייה"
    return "חתירה מתחת לשולחן יציב" if experience_level == "advanced" else "משיכת מגבת איזומטרית"


def _hinge_name(mode: str, experience_level: str) -> str:
    if mode in {"gym", "dumbbells"}:
        return "דדליפט רומני עם משקולות"
    if mode == "bands":
        return "היפ הינג' עם גומייה"
    return "דדליפט רומני רגל אחת ללא משקל" if experience_level == "advanced" else "היפ הינג' עם מקל"


def _vertical_push_name(mode: str, experience_level: str) -> str:
    if mode == "gym":
        return "לחיצת כתפיים במכונה"
    if mode == "dumbbells":
        return "לחיצת כתפיים עם משקולות"
    if mode == "bands":
        return "לחיצת כתפיים עם גומייה"
    return "שכיבת סמיכה פייק מוגבהת" if experience_level == "advanced" else "הרחקת כתף בשכיבה על הצד"


def _vertical_pull_name(mode: str, experience_level: str) -> str:
    if mode == "gym":
        return "פולי עליון"
    if mode == "dumbbells":
        return "פולאובר עם משקולת"
    if mode == "bands":
        return "משיכת גומייה מלמעלה"
    return "משיכת מגבת איזומטרית"


def _lunge_name(mode: str, experience_level: str) -> str:
    if mode == "gym" and experience_level == "beginner":
        return "עלייה נמוכה למדרגה"
    if mode == "dumbbells":
        return "סקוואט מפוצל עם משקולות"
    if mode == "bands":
        return "לאנג' אחורי נתמך עם גומייה קלה" if experience_level == "beginner" else "סקוואט מפוצל עם גומייה"
    if experience_level == "advanced":
        return "סקוואט מפוצל בולגרי"
    return "סקוואט מפוצל נתמך"


def _horizontal_pull_progression(mode: str) -> str:
    if mode == "bodyweight":
        return "הוסף חזרות, זמן עצירה או זווית קשה יותר בשליטה."
    if mode == "bands":
        return "הוסף חזרות בשליטה, ואז מתח גומייה."
    return "הוסף חזרות בשליטה, ואז עומס קטן."


def _horizontal_pull_regression(mode: str) -> str:
    if mode == "bodyweight":
        return "השתמש בזווית קלה יותר, טווח קצר יותר או עצירה איזומטרית קצרה."
    if mode == "bands":
        return "השתמש בגומייה קלה יותר או בטווח קצר יותר."
    return "הורד עומס או קצר טווח בלי לאבד גב ניטרלי."


def _vertical_pull_progression(mode: str) -> str:
    if mode == "bodyweight":
        return "הוסף זמן עצירה, חזרות או זווית משיכה קשה יותר בשליטה."
    if mode == "bands":
        return "הוסף מתח גומייה או חזרות אחרי שליטה נקייה."
    return "הוסף חזרות בשליטה, ואז עומס קטן."


def _vertical_pull_regression(mode: str) -> str:
    if mode == "bodyweight":
        return "קצר טווח, עבור למשיכה איזומטרית קלה יותר או לחתירה אופקית."
    if mode == "bands":
        return "עבור לגומייה קלה יותר או חתירה אופקית."
    return "הורד עומס או עבור לחתירה אופקית קלה יותר."


def _glute_bridge_alternatives(mode: str) -> list[str]:
    if mode == "gym":
        return ["מכונת היפ תראסט אם זמינה", "גשר ישבן"]
    if mode == "dumbbells":
        return ["גשר ישבן עם משקולת", "דחיפת אגן מהרצפה עם משקולת"]
    if mode == "bands":
        return ["גשר ישבן עם גומייה", "גשר ישבן"]
    return ["גשר ישבן", "גשר ישבן רגל אחת", "עצירת גשר ישבן"]


def _movement_alternatives(pattern: str, mode: str, experience_level: str) -> list[str]:
    alternatives = {
        "squat": {
            "gym": ["סקוואט לקופסה", "לחיצת רגליים בטווח קצר", "עלייה נמוכה למדרגה"],
            "dumbbells": ["סקוואט לקופסה עם משקולת", "סקוואט מפוצל עם משקולות"],
            "bands": ["סקוואט עם גומייה", "סקוואט לקופסה"],
            "bodyweight": ["ישיבה-קימה מכיסא", "סקוואט לקופסה", "סקוואט משקל גוף"],
        },
        "horizontal_push": {
            "gym": ["לחיצת חזה במכונה", "לחיצת כבלים בעמידה"],
            "dumbbells": ["לחיצת רצפה עם משקולות", "לחיצת רצפה באחיזה ניטרלית"],
            "bands": ["לחיצת חזה עם גומייה", "שכיבת סמיכה בשיפוע"],
            "bodyweight": ["שכיבת סמיכה בשיפוע", "שכיבת סמיכה ברכיים"],
        },
        "horizontal_pull": {
            "gym": ["חתירה במכונה", "חתירה בכבל"],
            "dumbbells": ["חתירה ביד אחת עם משקולת", "חתירה בהטיית גו עם שתי משקולות"],
            "bands": ["חתירה עם גומייה", "פייס פול עם גומייה"],
            "bodyweight": ["משיכת מגבת איזומטרית", "חתירה מתחת לשולחן יציב"],
        },
        "hinge": {
            "gym": ["דדליפט רומני עם משקולות", "משיכת כבל בין הרגליים", "גשר ישבן"],
            "dumbbells": ["דדליפט רומני עם משקולות", "גשר ישבן עם משקולת"],
            "bands": ["היפ הינג' עם גומייה", "גשר ישבן עם גומייה"],
            "bodyweight": ["היפ הינג' עם מקל", "גשר ישבן", "דדליפט רומני רגל אחת ללא משקל"],
        },
        "vertical_push": {
            "gym": ["לחיצת כתפיים במכונה", "לחיצת לנדמיין אם זמינה"],
            "dumbbells": ["לחיצת כתפיים עם משקולות", "לחיצה חצי כריעה"],
            "bands": ["לחיצת כתפיים עם גומייה", "הרחקת כתף עם גומייה"],
            "bodyweight": ["הרחקת כתף בשכיבה על הצד", "שכיבת סמיכה פייק מוגבהת"],
        },
        "vertical_pull": {
            "gym": ["פולי עליון", "משיכה בכבל בידיים ישרות"],
            "dumbbells": ["פולאובר עם משקולת", "חתירה ביד אחת עם מרפק צמוד"],
            "bands": ["משיכת גומייה מלמעלה", "חתירה גבוהה עם גומייה"],
            "bodyweight": ["משיכת מגבת איזומטרית", "חתירה מתחת לשולחן יציב"],
        },
        "single_leg": {
            "gym": ["עלייה נמוכה למדרגה", "סקוואט מפוצל נתמך"],
            "dumbbells": ["סקוואט מפוצל עם משקולות", "עלייה למדרגה עם משקולות"],
            "bands": ["לאנג' אחורי נתמך", "עלייה נמוכה למדרגה"],
            "bodyweight": ["עלייה נמוכה למדרגה", "לאנג' אחורי נתמך"],
        },
    }[pattern][mode]
    if experience_level == "advanced" and mode == "bodyweight":
        return [*alternatives, "וריאציה איטית עם עצירה"]
    return alternatives


def _adapt_selection_for_limitations(
    selected: list[str],
    display_limitations: str,
    limitations_text: str | None,
) -> list[str]:
    if not _has_knee_limitation(display_limitations, limitations_text):
        return selected
    return [key for key in selected if key != "lunge"]


def _adapt_catalog_for_limitations(
    catalog: dict[str, StructuredExercise],
    mode: str,
    display_limitations: str,
    limitations_text: str | None,
) -> dict[str, StructuredExercise]:
    if _has_knee_limitation(display_limitations, limitations_text):
        squat = catalog["squat"]
        catalog["squat"] = squat.model_copy(
            update={
                "alternatives": _knee_sensitive_squat_alternatives(mode),
                "safety_notes": list(
                    dict.fromkeys(
                        [
                            *squat.safety_notes,
                            "ברך רגישה: להקטין עומק ולשמור ברך במסלול כף הרגל.",
                        ]
                    )
                ),
                "regression": "לעבור לסקוואט לקופסה, ישיבה-קימה מכיסא או טווח קצר ללא כאב.",
            }
        )
    if _has_low_back_limitation(display_limitations, limitations_text):
        hinge = catalog["hinge"]
        catalog["hinge"] = hinge.model_copy(
            update={
                "name": "היפ הינג' לקיר",
                "alternatives": _low_back_sensitive_hinge_alternatives(mode),
                "notes": f"{hinge.notes} גב רגיש: טווח קצר, עומס קל, וללא הקרנה או נימול.".strip(),
                "safety_notes": list(
                    dict.fromkeys(
                        [
                            *hinge.safety_notes,
                            "גב רגיש: לעצור בהקרנה לרגל, נימול, חולשה, כאב חד או החמרה אחרי האימון.",
                        ]
                    )
                ),
                "progression": "להגדיל טווח או עומס רק אם התגובה נשארת יציבה ב-24-48 שעות אחרי האימון.",
                "regression": "לעבור לגשר ישבן, דד באג או תרגול הינג' עם מקל בטווח קצר.",
            }
        )
    return catalog


def _knee_sensitive_squat_alternatives(mode: str) -> list[str]:
    if mode == "gym":
        return ["סקוואט לקופסה", "לחיצת רגליים בטווח קצר", "ישיבה-קימה מכיסא"]
    if mode == "dumbbells":
        return ["סקוואט לקופסה עם משקולת קלה", "ישיבה-קימה מכיסא"]
    if mode == "bands":
        return ["סקוואט לקופסה עם גומייה", "ישיבה-קימה מכיסא"]
    return ["ישיבה-קימה מכיסא", "סקוואט לקופסה"]


def _has_knee_limitation(display_limitations: str, limitations_text: str | None) -> bool:
    text = f"{display_limitations} {limitations_text or ''}".lower()
    return "ברך" in text or "knee" in text


def _has_low_back_limitation(display_limitations: str, limitations_text: str | None) -> bool:
    text = f"{display_limitations} {limitations_text or ''}".lower()
    return any(term in text for term in ["גב תחתון", "הגב", "גב", "מותן", "מותניים", "low back", "lower back", "back"])


def _low_back_sensitive_hinge_alternatives(mode: str) -> list[str]:
    if mode == "gym":
        return ["גשר ישבן", "משיכת כבל בין הרגליים קלה", "היפ הינג' עם מקל"]
    if mode == "dumbbells":
        return ["גשר ישבן", "דדליפט רומני עם משקולות קלות בטווח קצר", "היפ הינג' עם מקל"]
    if mode == "bands":
        return ["גשר ישבן עם גומייה", "היפ הינג' עם גומייה קלה בטווח קצר", "דד באג"]
    return ["גשר ישבן", "היפ הינג' עם מקל", "דד באג"]


def _reduce_exercise(exercise: StructuredExercise, readiness: str) -> StructuredExercise:
    data = exercise.model_dump()
    data["sets"] = "1" if readiness == "red" else "2"
    data["difficulty"] = "easy" if readiness == "red" else data["difficulty"]
    data["notes"] = f"{data.get('notes') or ''} הורד מאמץ היום ועצור הרבה לפני שהטכניקה מתפרקת.".strip()
    data["safety_notes"] = list(dict.fromkeys([*data.get("safety_notes", []), "אל תעלה עומס ביום מוכנות נמוכה."]))
    return StructuredExercise(**data)


def _reduce_exercise_for_spacing(exercise: StructuredExercise) -> StructuredExercise:
    data = exercise.model_dump()
    data["sets"] = _reduce_set_text_once(str(data.get("sets") or "1"))
    data["notes"] = f"{data.get('notes') or ''} ימים צפופים: להפחית סט אחד ולשמור RPE 5-7.".strip()
    data["safety_notes"] = list(dict.fromkeys([*data.get("safety_notes", []), "בימים צפופים אל תוסיף נפח או עומס."]))
    return StructuredExercise(**data)


def _reduce_set_text_once(value: str) -> str:
    numbers = [int(number) for number in re.findall(r"\d+", value)]
    if not numbers:
        return value
    if len(numbers) >= 2 and "-" in value:
        low = max(1, numbers[0] - 1)
        high = max(low, numbers[1] - 1)
        return str(low) if low == high else f"{low}-{high}"
    return str(max(1, numbers[0] - 1))


def _neutralize_plan_guidance_copy(plan: StructuredWorkoutPlan) -> StructuredWorkoutPlan:
    days = []
    for day in plan.days:
        exercises = []
        for exercise in day.exercises:
            exercises.append(
                exercise.model_copy(
                    update={
                        "notes": _neutralize_hebrew_guidance(exercise.notes),
                        "progression": _neutralize_hebrew_guidance(exercise.progression),
                        "regression": _neutralize_hebrew_guidance(exercise.regression),
                        "safety_notes": [_neutralize_hebrew_guidance(note) for note in exercise.safety_notes],
                    }
                )
            )
        days.append(
            day.model_copy(
                update={
                    "warmup": [_neutralize_hebrew_guidance(note) for note in day.warmup],
                    "notes": _neutralize_hebrew_guidance(day.notes),
                    "exercises": exercises,
                }
            )
        )

    return plan.model_copy(
        update={
            "days": days,
            "progression_rule": _neutralize_hebrew_guidance(plan.progression_rule),
            "progression_model": _neutralize_hebrew_guidance(plan.progression_model),
            "progression_schedule": [_neutralize_hebrew_guidance(note) for note in plan.progression_schedule],
            "tracking_guidance": [_neutralize_hebrew_guidance(note) for note in plan.tracking_guidance],
            "recovery_note": _neutralize_hebrew_guidance(plan.recovery_note),
            "safety_notes": [_neutralize_hebrew_guidance(note) for note in plan.safety_notes],
        }
    )


def _neutralize_hebrew_guidance(text: str | None) -> str | None:
    if not text:
        return text

    phrase_replacements = [
        ("לפני שאתה מוסיף", "לפני הוספת"),
        ("כשאתה רענן", "כשהגוף רענן"),
        ("להעניש את עצמך בעומס קיצוני", "ענישה בעומס קיצוני"),
        ("להעניש את עצמך", "ענישה"),
        ("ואל תנסה", "ולא לנסות"),
        ("ואל תרדוף", "ולא לרדוף"),
        ("ואל תדחוף", "ולא לדחוף"),
        ("ואל תעמיס", "ולא להעמיס"),
        ("ואל תתאמן", "ולא להתאמן"),
        ("ואל תעלה", "ולא להעלות"),
        ("אל תנסה", "לא לנסות"),
        ("אל תרדוף", "לא לרדוף"),
        ("אל תדחוף", "לא לדחוף"),
        ("אל תעמיס", "לא להעמיס"),
        ("אל תתאמן", "לא להתאמן"),
        ("אל תעלה", "לא להעלות"),
    ]
    token_replacements = [
        ("הוסף", "להוסיף"),
        ("העלה", "להעלות"),
        ("שמור", "לשמור"),
        ("עצור", "לעצור"),
        ("עבוד", "לעבוד"),
        ("בחר", "לבחור"),
        ("בצע", "לבצע"),
        ("הורד", "להוריד"),
        ("הפחת", "להפחית"),
        ("קח", "לקחת"),
        ("חזור", "לחזור"),
        ("התקדם", "להתקדם"),
        ("עבור", "לעבור"),
        ("השתמש", "להשתמש"),
        ("הקטן", "להקטין"),
        ("התמקד", "להתמקד"),
        ("משוך", "למשוך"),
        ("התאם", "להתאים"),
        ("אסוף", "לאסוף"),
        ("כבד", "לכבד"),
        ("השאר", "להשאיר"),
    ]

    neutral = text
    for source, target in phrase_replacements:
        neutral = neutral.replace(source, target)
    for source, target in token_replacements:
        neutral = re.sub(rf"(?<![\u0590-\u05ff])ו{re.escape(source)}(?![\u0590-\u05ff])", f"ו{target}", neutral)
        neutral = re.sub(rf"(?<![\u0590-\u05ff]){re.escape(source)}(?![\u0590-\u05ff])", target, neutral)
    neutral = neutral.replace("לכבד מדי", "כבד מדי")
    return neutral


def _goal_label_he(goal: str) -> str:
    return {
        "build_muscle": "בניית שריר",
        "lose_fat": "ירידה בשומן",
        "improve_fitness": "שיפור כושר",
        "maintain_health": "שמירה על בריאות",
        "improve_consistency": "שיפור עקביות",
        "improve_strength": "שיפור כוח",
        "improve_endurance": "שיפור סיבולת",
        "improve_mobility": "שיפור מוביליטי",
    }.get(goal, goal.replace("_", " "))


def _focus_label_he(focus: str) -> str:
    return {
        "single_workout": "אימון יחיד",
        "full_body": "גוף מלא",
        "full_body_lower": "גוף מלא - דגש רגליים",
        "full_body_upper": "גוף מלא - דגש פלג עליון",
        "upper_body": "פלג גוף עליון",
        "lower_body": "פלג גוף תחתון",
        "push": "דחיפה",
        "pull": "משיכה",
        "legs": "רגליים",
    }.get(focus, focus.replace("_", " "))


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
        "goal_focus": "strength",
        "cardio_options": "הליכה מהירה, אופניים, אליפטיקל או חתירה קלה בקצב שיחה",
        "main_sets": "3",
        "upper_sets": "3",
        "hinge_sets": "2",
        "accessory_sets": "2",
        "core_sets": "2",
        "main_reps": "8-12 חזרות",
        "upper_reps": "8-12 חזרות",
        "hinge_reps": "8-10 חזרות",
        "main_rest": "90 שניות",
        "upper_rest": "75 שניות",
        "effort": "RPE 6-8, לרוב 1-3 חזרות ברזרבה.",
        "effort_note": "להשאיר 1-3 חזרות ברזרבה ולשמור טכניקה נקייה.",
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
            "main_rest": "120-180 שניות",
            "upper_rest": "120 שניות",
            "effort": "RPE 7-8 ברוב הסטים; בלי כשל טכני.",
            "effort_note": "להשאיר 1-2 חזרות ברזרבה, בלי כשל טכני.",
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
            "goal_focus": "fat_loss",
            "main_rest": "60-90 שניות",
            "upper_rest": "60 שניות",
            "effort": "RPE 6-8; המטרה היא עקביות ושימור כוח.",
            "effort_note": "לעבוד קשה אבל בשליטה; לשמור איכות תנועה ושימור כוח.",
            "day_note": "שמור כוח כעוגן. אם נשאר זמן ואנרגיה, הוסף 10-20 דקות הליכה או אירובי קל בקצב דיבור.",
            "progression_rule": "שמור על כוח וטכניקה; הוסף 5-10 דקות הליכה/אירובי קל או 500-1,000 צעדים בהדרגה לפני העלאת עצימות.",
            "recovery_note": "ירידה בשומן לא דורשת דיאטת קיצון; שמור על אוכל מספיק, חלבון, שינה והרגל אחד יציב בכל פעם.",
        }
    if goal == "improve_endurance":
        return {
            **defaults,
            "goal_focus": "endurance",
            "main_reps": "10-15 חזרות",
            "upper_reps": "10-15 חזרות",
            "hinge_reps": "10-12 חזרות",
            "main_rest": "45-60 שניות",
            "upper_rest": "45-60 שניות",
            "effort": "RPE 5-7 עם נשימה שנשארת בשליטה.",
            "effort_note": "לשמור קצב נשימה נשלט וטכניקה נקייה.",
            "day_note": "שמור קצב נשימה נשלט והוסף הליכה או אירובי קל בימים נפרדים.",
            "progression_rule": "העלה קודם משך או תדירות קלה, ורק אחר כך עצימות.",
            "recovery_note": "רוב העבודה האירובית צריכה להרגיש ניתנת לשיחה, עם מעט עבודה עצימה רק אחרי בסיס עקבי.",
        }
    if goal == "improve_mobility":
        return _mobility_training_variables(defaults)
    return defaults


def _experience_training_variables(variables: dict[str, str], experience_level: str) -> dict[str, str]:
    goal_focus = variables.get("goal_focus")
    if experience_level == "beginner":
        updates = {
            "main_sets": "2",
            "upper_sets": "2",
            "hinge_sets": "2",
            "accessory_sets": "1-2",
            "core_sets": "2",
            "effort": "RPE 5-7, להשאיר 2-4 חזרות ברזרבה.",
            "effort_note": "להשאיר 2-4 חזרות ברזרבה וללמוד טכניקה נקייה.",
        }
        if goal_focus == "endurance":
            updates.update(
                {
                    "effort": "RPE 5-6 או talk test: אפשר לדבר במשפטים קצרים.",
                    "effort_note": "לבנות בסיס אירובי בקצב שיחה לפני עבודה עצימה.",
                }
            )
        elif goal_focus == "mobility":
            updates.update(
                {
                    "effort": "RPE 4-6; טווח נוח, שליטה ונשימה חשובים יותר מעומס.",
                    "effort_note": "לא לדחוף לכאב חד; להגדיל טווח רק כשהשליטה נשארת רגועה.",
                }
            )
        elif goal_focus == "fat_loss":
            updates.update(
                {
                    "effort": "RPE 5-7; לשמור כוח ועקביות בלי להפוך את האימון לעונש.",
                    "effort_note": "לשמור טכניקה וכוח כעוגן, ולהוסיף צעדים בהדרגה רק אם ההתאוששות טובה.",
                }
            )
        return {**variables, **updates}
    if experience_level == "advanced":
        updates = {
            "main_sets": "4",
            "upper_sets": "3",
            "hinge_sets": "3",
            "accessory_sets": "2-3",
            "core_sets": "3",
            "effort": "RPE 7-9 לפי תרגיל; רוב העבודה עדיין לא עד כשל.",
            "effort_note": "לעבוד קרוב יותר למאמץ גבוה, אבל להשאיר מרווח טכני נקי.",
        }
        if goal_focus == "endurance":
            updates.update(
                {
                    "effort": "RPE 6-8 לפי מקטע; רוב העבודה עדיין בקצב talk test.",
                    "effort_note": "להעלות קודם משך או תדירות, ולהוסיף עצימות רק כשבסיס אירובי יציב.",
                }
            )
        elif goal_focus == "mobility":
            updates.update(
                {
                    "effort": "RPE 5-7; טווח, שליטה ושיווי משקל לפני התנגדות.",
                    "effort_note": "להעמיק טווח או מורכבות רק כשהתנועה נשלטת וללא כאב חד.",
                }
            )
        elif goal_focus == "fat_loss":
            updates.update(
                {
                    "effort": "RPE 6-8; לשמור ביצועי כוח ולהימנע מנפח ענישה.",
                    "effort_note": "להתקדם רק אם שינה, רעב וביצועים לא נפגעים.",
                }
            )
        return {**variables, **updates}
    return variables


def _prompt_training_variables(variables: dict[str, str], prompt: str) -> dict[str, str]:
    text = prompt.lower()
    if any(term in text for term in ["no running", "without running", "בלי ריצה", "ללא ריצה"]):
        variables = {
            **variables,
            "cardio_options": "הליכה מהירה, אופניים, אליפטיקל או מדרגות בקצב שיחה",
        }
    if not any(term in text for term in ["mobility", "flexibility", "מוביליטי", "גמישות", "תנועתיות"]):
        return variables
    return _mobility_training_variables(variables)


def _mobility_training_variables(variables: dict[str, str]) -> dict[str, str]:
    return {
        **variables,
        "goal_focus": "mobility",
        "main_sets": "2",
        "upper_sets": "2",
        "hinge_sets": "2",
        "accessory_sets": "1-2",
        "core_sets": "1-2",
        "main_reps": "8-12 חזרות איטיות",
        "upper_reps": "8-12 חזרות איטיות",
        "hinge_reps": "8-10 חזרות איטיות",
        "main_rest": "60-90 שניות",
        "upper_rest": "60 שניות",
        "effort": "RPE 4-6; טווח, שליטה ונשימה חשובים יותר מעומס.",
        "effort_note": "לשמור מאמץ קל-בינוני, טווח נוח ונשימה רגועה.",
        "day_note": "מטרת האימון היא טווח תנועה, שליטה ונשימה לפני עומס.",
        "progression_rule": "התקדם דרך טווח תנועה נוח, שליטה ונשימה; הוסף עומס רק אחרי תנועה יציבה וללא כאב.",
        "recovery_note": "מוביליטי לא אמור להיות כאב חד; שמור על תחושת מתיחה או מאמץ קל-בינוני בלבד.",
    }


def _progression_schedule(plan_type: str, variables: dict[str, str], experience_level: str) -> list[str]:
    if is_single_workout_plan(plan_type):
        return ["אימון יחיד: לבצע, לתעד RPE או מאמץ מילולי, כאב ומה הושלם, ולא להשלים נפח בכוח."]
    if plan_type == "weekly_plan":
        return ["שבוע 1: לבצע את הימים ככתוב, לתעד RPE או מאמץ מילולי, כאב ופספוסים, ולא להוסיף נפח לפני שיש לוג."]
    if plan_type == "two_week_plan":
        if experience_level == "beginner":
            return [
                "שבוע 1: ללמוד את התנועות עם RPE 5-7 או RIR 2-4, ולתעד כאב, מאמץ מילולי ומה הושלם.",
                "שבוע 2: אם שבוע 1 הושלם בלי כאב ועם RPE 7 ומטה או RIR 2-4, להוסיף חזרה נקייה אחת; אם לא, או אם יש רק מאמץ מילולי, לשמור ולא להתקדם ולא להוסיף סטים עדיין.",
            ]
        if experience_level == "advanced":
            return [
                "שבוע 1: לכייל עומס עבודה לפי RPE 7-9 בלי כשל חוזר.",
                f"שבוע 2: אם לוגי RPE/RIR, כאב וביצועים יציבים, {variables['progression_rule']} או להוסיף סט עזר אחד בלבד; אם יש רק מאמץ מילולי או חוסר יציבות, לשמר או להוריד 20-30% נפח.",
            ]
        return [
            "שבוע 1: לכייל עומס שמאפשר טכניקה נקייה ו-1-3 חזרות ברזרבה.",
            f"שבוע 2: אם לוגי RPE/RIR, כאב והשלמות יציבים, {variables['progression_rule']}; אם לא, או אם יש רק מאמץ מילולי, לשמור עומס או להוריד מעט נפח לפני שמתקדמים.",
        ]
    if plan_type == "monthly_plan":
        if experience_level == "beginner":
            return [
                "שבוע 1: לימוד בסיס - 2 סטים, RPE 5-7, טכניקה נקייה ולוג מלא.",
                "שבוע 2: להוסיף חזרה נקייה אחת רק אם אין כאב ויש RPE 7 ומטה או RIR 2-4; אם יש רק מאמץ מילולי, לשמור ולתעד מספר, ולא להוסיף סטים עדיין.",
                "שבוע 3: לחזור על שבוע 2 או להוסיף סט אחד רק לתרגיל מרכזי אחד אם ההתאוששות טובה.",
                "שבוע 4: שבוע שימור ובדיקה - אם יש כאב, פספוסים או RPE חריג, להוריד 20-30% נפח ולא להעלות עומס.",
            ]
        if experience_level == "advanced":
            return [
                "שבוע 1: כיול עומס ונפח לפי RPE 7-9 בלי כשל חוזר.",
                f"שבוע 2: התקדמות קטנה אחת רק עם לוג RPE/RIR יציב - {variables['progression_rule']}",
                "שבוע 3: להוסיף עומס קטן או סט עזר אחד בלבד אם RPE/RIR, ביצועים, שינה וכאב יציבים.",
                "שבוע 4: בדיקה/שימור - אם RPE או מאמץ מילולי עולים, ביצועים יורדים או כאב מצטבר, להוריד 20-40% נפח לפני בלוק נוסף.",
            ]
        return [
            "שבוע 1: כיול בסיס - עומס בינוני, טכניקה נקייה ולוג מלא.",
            f"שבוע 2: התקדמות קטנה אחת רק עם לוג RPE/RIR יציב - {variables['progression_rule']}",
            "שבוע 3: להחזיק או להעלות רק אם RPE/RIR, שינה וכאב יציבים; אם יש רק מאמץ מילולי, לשמור ולתעד RPE/RIR.",
            "שבוע 4: שבוע בדיקה/שימור - להוריד 20-40% נפח אם מאמץ, עייפות, כאב או פספוסים עולים, ואז לתכנן את החודש הבא.",
        ]
    return []


def _progression_model(plan_type: str) -> str:
    if is_single_workout_plan(plan_type):
        return "אימון יחיד: לבצע היום, לתעד מה הושלם, RPE או מאמץ מילולי וכאב, ולא להעלות עומס עתידי בלי לוג נוסף."
    base = (
        "התקדמות כפולה: קודם להוסיף חזרות נקיות בתוך טווח היעד, ורק אחר כך עומס קטן "
        "או סט אחד אם ההתאוששות והטכניקה יציבות."
    )
    if plan_type == "monthly_plan":
        return (
            f"{base} שבוע 4 הוא שבוע בדיקה/דילואד: אם RPE עולה, ביצועים יורדים, כאב מצטבר או יש פספוסים, "
            "להוריד 20-40% נפח לפני בלוק נוסף."
        )
    return base


def _weekly_spacing_guidance(
    *,
    prompt: str,
    plan_type: str,
    split: str,
    days_per_week: int,
    experience_level: str,
    goal_focus: str | None = None,
) -> str | None:
    if is_single_workout_plan(plan_type) or days_per_week <= 1:
        return None

    consecutive = _has_consecutive_day_pressure(prompt)
    if goal_focus == "endurance":
        guidance = (
            "פיזור שבועי: פזר ימי אירובי כך שיהיה יום קל או מנוחה בין מקטעים עצימים; "
            "רוב העבודה נשארת בקצב שיחה."
        )
        if consecutive:
            guidance += " ציינת ימים צפופים, לכן היום האחרון צריך להיות אירובי קל או הליכה קצרה."
        return guidance
    if goal_focus == "mobility":
        guidance = "פיזור שבועי: פזר ימי מוביליטי ושיווי משקל כך שהטווח והשליטה ישתפרו בלי כאב חד או עייפות מצטברת."
        if consecutive:
            guidance += " ציינת ימים צפופים, לכן היום האחרון צריך להיות מוביליטי קל ונשימה, לא עומס נוסף."
        return guidance
    if split == "full_body":
        if days_per_week >= 4 and experience_level == "beginner":
            guidance = (
                "פיזור שבועי: 4 ימי full-body למתחיל/ה עדיף לפזר עם יום מנוחה או יום קל בין עומסים דומים; "
                "אם חייבים רצף, הורד סט אחד בימים 3-4 ושמור RPE 5-7."
            )
        elif days_per_week >= 3:
            guidance = "פיזור שבועי: פזר אימוני full-body כך שיהיה יום התאוששות או יום קל בין עומסים דומים."
        else:
            guidance = "פיזור שבועי: השאר לפחות יום התאוששות בין שני אימוני כוח דומים."
    elif split == "upper_lower":
        guidance = "פיזור שבועי: ב-upper/lower עדיף עליון/תחתון/מנוחה/עליון/תחתון, ולא שני ימי רגליים קשים רצוף."
    elif split == "push_pull_legs":
        guidance = "פיזור שבועי: ב-push/pull/legs שמור יום קל או מנוחה אחרי 3 ימי עומס רצופים."
    else:
        guidance = "פיזור שבועי: אל תצמיד שני ימים קשים לאותו אזור אם הביצועים, הכאב או השינה לא יציבים."

    if consecutive:
        guidance += " ציינת ימים צפופים, לכן עדיף להפוך את היום האחרון לגרסת מינימום אם העייפות עולה."
    return guidance


def _has_consecutive_day_pressure(prompt: str) -> bool:
    text = prompt.lower()
    return any(
        term in text
        for term in [
            "consecutive",
            "back to back",
            "in a row",
            "ברצף",
            "רצוף",
            "רצופים",
            "ראשון עד רביעי",
            "שני עד חמישי",
            "monday to thursday",
            "sunday to wednesday",
        ]
    )


def _tracking_guidance(
    plan_type: str,
    variables: dict[str, str],
    display_limitations: str | None,
    readiness: str | None,
    *,
    weekly_spacing_guidance: str | None = None,
) -> list[str]:
    goal_focus = variables.get("goal_focus")
    guidance = [
        "לתעד אחרי כל אימון: הושלם/חלקי/פוספס, RPE כללי או מאמץ מילולי כמו קל מדי/כבד מדי/בשליטה, כאב או מגבלה, והערה קצרה על הביצוע.",
        "לא לנחש מה היה באימון הקודם: לתעד את התרגיל המרכזי - חזרות, משקל אם יש, ו-RIR או כמה חזרות נשארו ברזרבה.",
    ]
    if goal_focus == "endurance":
        guidance[1] = "לא לנחש מה היה באימון הקודם: לתעד משך, מרחק או קצב אם יש, talk test או RPE, כאב, נשימה ומה הושלם."
    elif goal_focus == "mobility":
        guidance[1] = "לא לנחש מה היה באימון הקודם: לתעד תנועה מרכזית, טווח נוח, שליטה, נשימה, כאב ומה הושלם."
    if is_single_workout_plan(plan_type):
        guidance.append("אימון יחיד: לרשום מה בוצע ומה כדאי להחליף או להוריד בפעם הבאה.")
    elif plan_type == "weekly_plan":
        guidance.append("בסוף השבוע לבדוק כמה אימונים הושלמו ומה הפעולה הבאה המציאותית ביותר.")
    elif plan_type == "two_week_plan":
        if goal_focus == "endurance":
            guidance.append(
                "אחרי שבוע 1 להתקדם בשבוע 2 במשך או בתדירות רק אם talk test/RPE, כאב והשלמות יציבים; "
                "מאמץ מילולי לבד אומר לשמור. בסוף שבוע 2 לסכם מה הושלם ומה לשנות לפני בלוק נוסף."
            )
        elif goal_focus == "mobility":
            guidance.append(
                "אחרי שבוע 1 להתקדם בשבוע 2 בטווח, זמן או שליטה רק אם RPE, כאב ותנועה יציבים; "
                "מאמץ מילולי לבד אומר לשמור. בסוף שבוע 2 לסכם מה השתפר ומה עדיין מוגבל."
            )
        else:
            guidance.append(
                "אחרי שבוע 1 להתקדם בשבוע 2 רק אם RPE/RIR, כאב והשלמות אימון יציבים; מאמץ מילולי לבד אומר לשמור. "
                "בסוף שבוע 2 לסכם מה הושלם, מה כאב, ומה לשמר או לשנות לפני בלוק נוסף."
            )
    elif plan_type == "monthly_plan":
        if goal_focus == "endurance":
            guidance.append("בסוף כל שבוע לבדוק משך/תדירות, talk test/RPE, כאב ושינה לפני שינוי עצימות; מאמץ מילולי לבד אומר לשמור.")
        elif goal_focus == "mobility":
            guidance.append("בסוף כל שבוע לבדוק טווח נוח, שליטה, RPE, כאב ושינה לפני שינוי זמן או מורכבות; מאמץ מילולי לבד אומר לשמור.")
        else:
            guidance.append("בסוף כל שבוע לבדוק השלמות, RPE/RIR, כאב ושינה לפני שינוי נפח או עומס; מאמץ מילולי לבד אומר לשמור.")

    if weekly_spacing_guidance:
        guidance.append(weekly_spacing_guidance)
    if variables.get("effort"):
        guidance.append(f"עצימות עבודה: {variables['effort']}")
    if display_limitations or readiness in {"yellow", "red"}:
        guidance.append("אם כאב עולה או הטכניקה מתפרקת, לרשום את זה ולהחליף לגרסה קלה במקום להוסיף עומס.")
    return guidance[:6]
