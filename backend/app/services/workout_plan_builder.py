import re
from dataclasses import dataclass, field

from backend.app.schemas import StructuredExercise, StructuredWorkoutDay, StructuredWorkoutPlan


SOURCE_REFS = [
    "ACSM 2026 resistance training guidelines: https://acsm.org/resistance-training-guidelines-update-2026/",
    "CDC adult physical activity guidelines: https://www.cdc.gov/physical-activity-basics/guidelines/adults.html",
    "NSCA resistance training frequency: https://www.nsca.com/education/articles/kinetic-select/determination-of-resistance-training-frequency/",
    "HPRC/NSCA exercise order: https://www.hprc-online.org/physical-fitness/training-performance/choosing-right-exercises-optimize-your-resistance-training",
    "NASM resistance training acute variables: https://blog.nasm.org/resistance-training",
    "Exercise is Medicine low back pain: https://exerciseismedicine.org/assets/page_documents/EIM%20Rx%20series_Exercising%20with%20Lower%20Back%20Pain.pdf",
    "Mayo Clinic exercise warning symptoms: https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/exercise-and-chronic-disease/art-20046049",
]


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
    plan_type: str = "multi_week"
    readiness: str | None = None
    training_status: dict | None = None


class WorkoutPlanBuilder:
    def build(self, planning_input: WorkoutPlanningInput) -> StructuredWorkoutPlan:
        plan_type = self._normalize_plan_type(planning_input.plan_type, planning_input.prompt)
        days_per_week = 1 if plan_type == "single_session" else max(1, min(7, planning_input.days_per_week))
        duration_weeks = 1 if plan_type == "single_session" else max(1, min(4, planning_input.duration_weeks))
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
        variables = _goal_training_variables(planning_input.goal)
        display_limitations = _display_limitations_he(planning_input.limitations)
        safety_notes = self._safety_notes(display_limitations, readiness, planning_input.training_status)
        day_specs = self._day_specs(split=split, days_per_week=days_per_week)
        days = [
            self._build_day(
                index=index,
                focus=focus,
                preferred_days=planning_input.preferred_days,
                equipment=planning_input.equipment,
                variables=variables,
                session_length_minutes=session_length,
                display_limitations=display_limitations,
                readiness=readiness,
                plan_type=plan_type,
            )
            for index, focus in enumerate(day_specs)
        ]

        return StructuredWorkoutPlan(
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
            progression_model=(
                "Double progression: add clean reps inside the target range first, then add a small load "
                "or one set only when recovery and technique are stable."
            ),
            recovery_note=self._recovery_note(variables, display_limitations, readiness, plan_type),
            safety_notes=safety_notes,
            decision_inputs={
                "plan_type": "single session" if plan_type == "single_session" else "multi week",
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
            },
            source_refs=SOURCE_REFS,
        )

    @staticmethod
    def _normalize_plan_type(plan_type: str | None, prompt: str) -> str:
        if plan_type in {"multi_week", "single_session"}:
            return plan_type
        text = prompt.lower()
        single_terms = ["today", "single", "one workout", "one session", "right now", "tonight", "היום", "אימון אחד"]
        if any(term in text for term in single_terms):
            return "single_session"
        return "multi_week"

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
        if plan_type == "single_session":
            return "single_session"
        if days_per_week <= 3:
            return "full_body"
        if days_per_week == 4:
            return "full_body" if experience_level == "beginner" else "upper_lower"
        if experience_level == "advanced":
            return "push_pull_legs"
        return "upper_lower"

    @staticmethod
    def _day_specs(split: str, days_per_week: int) -> list[str]:
        if split == "single_session":
            return ["single_session"]
        if split == "upper_lower":
            return ["upper_body" if index % 2 == 0 else "lower_body" for index in range(days_per_week)]
        if split == "push_pull_legs":
            pattern = ["push", "pull", "legs"]
            return [pattern[index % len(pattern)] for index in range(days_per_week)]
        return ["full_body" for _ in range(days_per_week)]

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
        readiness: str,
        plan_type: str,
    ) -> StructuredWorkoutDay:
        raw_day_label = preferred_days[index] if preferred_days and index < len(preferred_days) else f"יום {index + 1}"
        day_label = "היום" if plan_type == "single_session" else _day_label_he(raw_day_label)
        exercises = self._exercises_for_focus(
            focus=focus,
            equipment=equipment,
            variables=variables,
            display_limitations=display_limitations,
            readiness=readiness,
            session_length_minutes=session_length_minutes,
        )
        max_exercises = 3 if session_length_minutes <= 20 else 4 if session_length_minutes <= 35 else 5
        exercises = exercises[:max_exercises]
        day_notes = [f"שמור על אימון של בערך {session_length_minutes} דקות."]
        if readiness == "yellow":
            day_notes.append("יום צהוב: הורד 20-40% נפח או עצימות והשאר 2-3 חזרות ברזרבה.")
        elif readiness == "red":
            day_notes.append("יום אדום: אל תעמיס; בחר תנועה קלה בלבד ופנה לאיש מקצוע אם יש סימן חריג.")
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
        readiness: str,
        session_length_minutes: int,
    ) -> list[StructuredExercise]:
        catalog = _exercise_catalog(equipment, variables, display_limitations)
        if focus == "upper_body":
            selected = ["horizontal_push", "horizontal_pull", "vertical_push", "vertical_pull", "core"]
        elif focus == "lower_body":
            selected = ["squat", "hinge", "lunge", "glute_bridge", "core"]
        elif focus == "push":
            selected = ["horizontal_push", "vertical_push", "squat", "core"]
        elif focus == "pull":
            selected = ["horizontal_pull", "vertical_pull", "hinge", "core"]
        elif focus == "legs":
            selected = ["squat", "hinge", "lunge", "glute_bridge", "core"]
        elif focus == "single_session":
            selected = ["squat", "horizontal_push", "horizontal_pull", "core"]
        else:
            selected = ["squat", "horizontal_push", "horizontal_pull", "hinge", "core"]

        exercise_set = [catalog[key] for key in selected if key in catalog]
        if readiness in {"yellow", "red"} or session_length_minutes <= 20:
            return [_reduce_exercise(exercise, readiness) for exercise in exercise_set]
        return exercise_set

    @staticmethod
    def _warmup(readiness: str) -> list[str]:
        if readiness == "red":
            return ["5 דקות הליכה קלה", "בדיקת טווח תנועה ללא כאב", "נשימה רגועה וברייסינג קל"]
        return ["5 דקות אירובי קל", "תרגול hip hinge", "סיבובי כתפיים", "סט הכנה קל לתרגיל הראשון"]

    @staticmethod
    def _safety_notes(display_limitations: str, readiness: str, training_status: dict | None = None) -> list[str]:
        notes = [
            "Stop for sharp pain, chest pain, unusual dizziness, fainting, or unusual shortness of breath.",
            "Use a pain-free range of motion and keep technique stable before adding load.",
        ]
        if display_limitations:
            notes.append(f"Adapt around the documented limitation: {display_limitations}.")
        if readiness == "yellow":
            notes.append("Reduce volume or intensity today for recovery before progressing.")
        if readiness == "red":
            notes.append("Do not train hard today; use only easy movement and seek qualified help for red flags.")
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
        if plan_type == "single_session":
            note += " זו תוכנית לאימון יחיד, לכן אין צורך להשלים נפח חסר היום."
        if readiness == "yellow":
            note += " היום עדיף לשמור התאוששות: הפחת עומס וחזור להתקדמות רק כשהביצוע יציב."
        if display_limitations:
            note += f" עבוד סביב {display_limitations}."
        return note

    @staticmethod
    def _plan_name(plan_type: str, days_per_week: int, goal: str, duration_weeks: int, split: str) -> str:
        if plan_type == "single_session":
            return f"אימון יחיד ל{_goal_label_he(goal)}"
        return f"תוכנית {duration_weeks} שבועות - {days_per_week} ימים ל{_goal_label_he(goal)} ({split})"


def infer_duration_weeks(prompt: str) -> int | None:
    text = prompt.lower()
    if "month" in text or "חודש" in text:
        return 4
    digit_match = re.search(r"(\d)\s*-?\s*(?:weeks?|שבועות|שבוע)", text)
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


def _exercise_catalog(equipment: list[str], variables: dict[str, str], display_limitations: str) -> dict[str, StructuredExercise]:
    has_dumbbells = any("dumbbell" in item.lower() or "משקול" in item for item in equipment)
    has_bands = any("band" in item.lower() or "גומי" in item for item in equipment)
    limitation_note = f" כבד את {display_limitations}." if display_limitations else ""
    source_refs = SOURCE_REFS[:5]

    return {
        "squat": StructuredExercise(
            name="סקוואט גביע" if has_dumbbells else "סקוואט משקל גוף",
            sets="3",
            reps_or_duration=variables["main_reps"],
            rest=variables["main_rest"],
            notes=f"עבוד בטווח ללא כאב ובקצב נשלט.{limitation_note}",
            difficulty="moderate",
            alternatives=["סקוואט לקופסה", "סקוואט מפוצל"],
            safety_notes=["עצור אם מופיע כאב חד", "שמור ברכיים בקו כף הרגל"],
            movement_pattern="squat",
            target_muscles=["quadriceps", "glutes", "core"],
            progression="Add clean reps inside the target range before adding load.",
            regression="Use a box squat or reduce depth.",
            source_refs=source_refs,
        ),
        "horizontal_push": StructuredExercise(
            name="לחיצת רצפה עם משקולות" if has_dumbbells else "שכיבת סמיכה",
            sets="3",
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes="השאר שתי חזרות ברזרבה.",
            difficulty="moderate",
            alternatives=["שכיבת סמיכה בשיפוע", "לחיצת חזה עם גומייה"],
            safety_notes=["שמור על כתפיים נוחות"],
            movement_pattern="horizontal_push",
            target_muscles=["chest", "triceps", "anterior shoulders"],
            progression="Add reps, then lower the incline or add light load.",
            regression="Use an incline push-up.",
            source_refs=source_refs,
        ),
        "horizontal_pull": StructuredExercise(
            name="חתירה ביד אחת עם משקולת" if has_dumbbells else "חתירה עם גומייה" if has_bands else "חתירה עם מגבת",
            sets="3",
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes="עצור רגע קצר בקצה התנועה.",
            difficulty="moderate",
            alternatives=["חתירה עם גומייה", "חתירה נתמכת על ספסל"],
            safety_notes=["שמור על עמוד שדרה ניטרלי"],
            movement_pattern="horizontal_pull",
            target_muscles=["upper back", "lats", "biceps"],
            progression="Add controlled reps, then load or band tension.",
            regression="Use chest support or lighter band tension.",
            source_refs=source_refs,
        ),
        "hinge": StructuredExercise(
            name="דדליפט רומני עם משקולות" if has_dumbbells else "היפ הינג' עם תיק",
            sets="2",
            reps_or_duration=variables["hinge_reps"],
            rest=variables["main_rest"],
            notes=f"התמקד בדחיפת אגן לאחור ושמור שתי חזרות ברזרבה.{limitation_note}",
            difficulty="moderate",
            alternatives=["גשר ישבן", "בוקר טוב ללא משקל"],
            safety_notes=["עצור אם מופיע כאב חד בגב או בירך"],
            movement_pattern="hip_hinge",
            target_muscles=["hamstrings", "glutes", "spinal stabilizers"],
            progression="Add range and control before load.",
            regression="Use glute bridge or dowel hip hinge.",
            source_refs=source_refs,
        ),
        "core": StructuredExercise(
            name="פלאנק ליבה",
            sets="2",
            reps_or_duration="20-40 שניות",
            rest="60 שניות",
            notes="שמור נשימה רגועה וצלעות נמוכות.",
            difficulty="easy",
            alternatives=["דד באג", "פלאנק ברכיים"],
            safety_notes=["עצור אם מופיע כאב חד"],
            movement_pattern="core_anti_extension",
            target_muscles=["abdominals", "trunk stabilizers"],
            progression="Add time in small steps while breathing stays controlled.",
            regression="Use dead bug or knee plank.",
            source_refs=source_refs,
        ),
        "vertical_push": StructuredExercise(
            name="לחיצת כתפיים עם משקולות" if has_dumbbells else "לחיצת כתפיים עם גומייה" if has_bands else "פייק פוש-אפ מוגבה",
            sets="2",
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes="שמור צלעות נמוכות ואל תדחוף דרך כאב כתף.",
            difficulty="moderate",
            alternatives=["לחיצה חצי כריעה", "הרחקת כתף קלה"],
            safety_notes=["עצור אם מופיע כאב חד בכתף"],
            movement_pattern="vertical_push",
            target_muscles=["shoulders", "triceps", "upper chest"],
            progression="Add reps before load.",
            regression="Use lighter range or half-kneeling press.",
            source_refs=source_refs,
        ),
        "vertical_pull": StructuredExercise(
            name="משיכת גומייה מלמעלה" if has_bands else "פולאובר עם משקולת" if has_dumbbells else "משיכת מגבת איזומטרית",
            sets="2",
            reps_or_duration=variables["upper_reps"],
            rest=variables["upper_rest"],
            notes="משוך שכמות למטה ואחורה בלי למשוך בצוואר.",
            difficulty="moderate",
            alternatives=["חתירה גבוהה עם גומייה", "פייס פול"],
            safety_notes=["שמור צוואר וכתפיים נוחים"],
            movement_pattern="vertical_pull",
            target_muscles=["lats", "upper back", "biceps"],
            progression="Increase band tension or reps after clean control.",
            regression="Use lower band tension or horizontal row.",
            source_refs=source_refs,
        ),
        "lunge": StructuredExercise(
            name="סקוואט מפוצל",
            sets="2",
            reps_or_duration="8-10 חזרות לכל צד",
            rest="75 שניות",
            notes=f"שמור צעד קצר ונוח וטווח ללא כאב.{limitation_note}",
            difficulty="moderate",
            alternatives=["step-up נמוך", "לאנג' אחורי נתמך"],
            safety_notes=["הקטן טווח אם מופיע כאב ברך"],
            movement_pattern="single_leg",
            target_muscles=["quadriceps", "glutes", "adductors"],
            progression="Add reps per side before load.",
            regression="Use support or lower step height.",
            source_refs=source_refs,
        ),
        "glute_bridge": StructuredExercise(
            name="גשר ישבן",
            sets="2",
            reps_or_duration="10-15 חזרות",
            rest="60 שניות",
            notes="עצור רגע למעלה בלי להקשית גב.",
            difficulty="easy",
            alternatives=["hip thrust לספסל", "גשר ישבן עם גומייה"],
            safety_notes=["עצור אם מופיע כאב חד בגב"],
            movement_pattern="glute_bridge",
            target_muscles=["glutes", "hamstrings"],
            progression="Add pause time, then single-leg or load.",
            regression="Use shorter range.",
            source_refs=source_refs,
        ),
    }


def _reduce_exercise(exercise: StructuredExercise, readiness: str) -> StructuredExercise:
    data = exercise.model_dump()
    data["sets"] = "1" if readiness == "red" else "2"
    data["difficulty"] = "easy" if readiness == "red" else data["difficulty"]
    data["notes"] = f"{data.get('notes') or ''} Reduce effort today; stop well before form breaks.".strip()
    data["safety_notes"] = list(dict.fromkeys([*data.get("safety_notes", []), "Do not progress load on a low-readiness day."]))
    return StructuredExercise(**data)


def _goal_label_he(goal: str) -> str:
    return {
        "build_muscle": "בניית שריר",
        "lose_fat": "ירידה בשומן",
        "improve_fitness": "שיפור כושר",
        "maintain_health": "שמירה על בריאות",
        "improve_consistency": "שיפור עקביות",
        "improve_strength": "שיפור כוח",
        "improve_endurance": "שיפור סיבולת",
    }.get(goal, goal.replace("_", " "))


def _focus_label_he(focus: str) -> str:
    return {
        "single_session": "אימון יחיד",
        "full_body": "גוף מלא",
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
            "recovery_note": "ירידה בשומן לא דורשת דיאטת קיצון; שמור על אוכל מספיק, חלבון והרגל אחד יציב בכל פעם.",
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
