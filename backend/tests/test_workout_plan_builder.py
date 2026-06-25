from backend.app.services.workout_plan_builder import infer_duration_weeks, infer_plan_type, is_persistent_plan_type


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
