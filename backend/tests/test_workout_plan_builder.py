import re

from backend.app.services.workout_plan_builder import (
    WorkoutPlanBuilder,
    WorkoutPlanningInput,
    infer_duration_weeks,
    infer_plan_type,
    is_persistent_plan_type,
)


def test_infer_plan_type_uses_explicit_values_when_valid():
    assert infer_plan_type("monthly_plan", "Build any plan today") == "monthly_plan"
    assert infer_plan_type("weekly_plan", "Build any plan today") == "weekly_plan"
    assert infer_plan_type("two_week_plan", "Build any plan today") == "two_week_plan"
    assert infer_plan_type("single_workout", "Build a long training plan") == "single_workout"


def test_infer_plan_type_keeps_old_aliases_compatible():
    assert infer_plan_type("multi_week", "Build a four week strength plan") == "monthly_plan"
    assert infer_plan_type("single_session", "Build a long training plan") == "single_workout"


def test_infer_plan_type_infers_single_workout_from_prompt():
    assert infer_plan_type(None, "I only have 20 minutes today") == "single_workout"
    assert infer_plan_type("weird value", "one workout for tonight") == "single_workout"
    assert infer_plan_type(None, "תן לי אימון זריז להיום במכון") == "single_workout"
    assert infer_plan_type(None, "תן לי סשן אחד קצר עכשיו") == "single_workout"
    assert infer_plan_type(None, "מיני אימון בודד לבית") == "single_workout"


def test_infer_plan_type_splits_weekly_two_week_and_monthly_plans():
    assert infer_plan_type(None, "Build me a strength plan for this week") == "weekly_plan"
    assert infer_plan_type(None, "תבנה לי תוכנית קצרה לשבוע הקרוב") == "weekly_plan"
    assert infer_plan_type(None, "בנה לי שבוע אימונים לשבוע הבא") == "weekly_plan"
    assert infer_plan_type(None, "תבנה לי תוכנית לשבועיים עם משקולות") == "two_week_plan"
    assert infer_plan_type(None, "תוכנית לשבועיים שמתחילה היום") == "two_week_plan"
    assert infer_plan_type(None, "תוכנית לשבועיים הקרובים עם משקל גוף") == "two_week_plan"
    assert infer_plan_type(None, "בנה לי בלוק להשבועיים הקרובים") == "two_week_plan"
    assert infer_plan_type(None, "Build a monthly gym plan") == "monthly_plan"
    assert infer_plan_type(None, "תבנה לי תוכנית חודשית שמתחילה היום") == "monthly_plan"
    assert infer_plan_type(None, "Build a four-week plan starting today") == "monthly_plan"
    assert infer_plan_type(None, "תבני לי תוכנית חודשית לבית") == "monthly_plan"
    assert infer_plan_type(None, "תוכנית לחודש הקרוב במכון") == "monthly_plan"


def test_infer_plan_type_defaults_to_monthly_plan_without_horizon_signal():
    assert infer_plan_type(None, "Build me a strength plan") == "monthly_plan"


def test_infer_duration_weeks_clamps_two_digit_week_counts():
    assert infer_duration_weeks("Build a plan for 10 weeks") == 4
    assert infer_duration_weeks("תוכנית ל-12 שבועות") == 4


def test_is_persistent_plan_type_rejects_unknown_legacy_values():
    assert is_persistent_plan_type("weekly_plan") is True
    assert is_persistent_plan_type("two_week_plan") is True
    assert is_persistent_plan_type("monthly_plan") is True
    assert is_persistent_plan_type("multi_week") is True
    assert is_persistent_plan_type("single_workout") is False
    assert is_persistent_plan_type("custom_plan") is False
    assert is_persistent_plan_type(None) is False


def test_generated_plan_copy_uses_neutral_hebrew_without_regex_rewrite():
    blocked_words = [
        "הוסף",
        "שמור",
        "עצור",
        "הורד",
        "העלה",
        "בחר",
        "עבוד",
        "קח",
        "השתמש",
        "התאם",
        "בצע",
        "הפחת",
        "חזור",
        "התקדם",
        "עבור",
    ]
    hebrew = r"\u0590-\u05ff"
    imperative_pattern = re.compile(rf"(?<![{hebrew}])ו?(?:{'|'.join(blocked_words)})(?![{hebrew}])")
    direct_prohibition_pattern = re.compile(rf"(?<![{hebrew}])ו?אל ת")
    builder = WorkoutPlanBuilder()
    goals = ["build_muscle", "improve_strength", "lose_fat", "improve_endurance", "improve_mobility"]
    experience_levels = ["beginner", "intermediate", "advanced"]
    equipment_modes = [["bodyweight"], ["home"], ["dumbbells"], ["gym"]]

    for goal in goals:
        for experience_level in experience_levels:
            for equipment in equipment_modes:
                plan = builder.build(
                    WorkoutPlanningInput(
                        prompt="תוכנית חודשית",
                        goal=goal,
                        experience_level=experience_level,
                        days_per_week=3,
                        duration_weeks=4,
                        equipment=equipment,
                        plan_type="monthly_plan",
                    )
                )
                text = str(plan.model_dump())
                leaked = [
                    *imperative_pattern.findall(text),
                    *direct_prohibition_pattern.findall(text),
                ]
                assert leaked == []
                if goal == "build_muscle":
                    assert "בניית שריר" in plan.name


def test_generated_plan_copy_keeps_key_neutral_phrases_readable():
    builder = WorkoutPlanBuilder()
    plan = builder.build(
        WorkoutPlanningInput(
            prompt="תוכנית חודשית",
            goal="build_muscle",
            experience_level="beginner",
            days_per_week=3,
            duration_weeks=4,
            equipment=["bodyweight"],
            plan_type="monthly_plan",
        )
    )

    text = str(plan.model_dump())
    assert "מסגרת אימון של בערך" in text
    assert "לעצור אם מופיעים כאב חד" in text
    assert "להוסיף חזרות" in text
    assert "בניית שריר" in plan.name


def test_low_back_limitation_ignores_background_and_upper_back_mentions():
    builder = WorkoutPlanBuilder()

    for limitation in ["background noise", "תרגיל גב עליון"]:
        plan = builder.build(
            WorkoutPlanningInput(
                prompt="תוכנית חודשית",
                goal="build_muscle",
                experience_level="beginner",
                days_per_week=3,
                duration_weeks=4,
                equipment=["bodyweight"],
                limitations=limitation,
                plan_type="monthly_plan",
            )
        )
        text = str(plan.model_dump())
        hinge_names = [
            exercise.name
            for day in plan.days
            for exercise in day.exercises
            if exercise.movement_pattern == "hip_hinge"
        ]

        assert "היפ הינג' לקיר" not in hinge_names
        assert "גב רגיש" not in text


def test_low_back_limitation_detects_specific_low_back_markers():
    builder = WorkoutPlanBuilder()

    for limitation in ["כאב בגב התחתון", "מותניים"]:
        plan = builder.build(
            WorkoutPlanningInput(
                prompt="תוכנית חודשית",
                goal="build_muscle",
                experience_level="beginner",
                days_per_week=3,
                duration_weeks=4,
                equipment=["bodyweight"],
                limitations=limitation,
                plan_type="monthly_plan",
            )
        )
        hinge_names = [
            exercise.name
            for day in plan.days
            for exercise in day.exercises
            if exercise.movement_pattern == "hip_hinge"
        ]

        assert "היפ הינג' לקיר" in hinge_names
