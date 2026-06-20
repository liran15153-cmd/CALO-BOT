from backend.app.services.workout_plan_builder import infer_plan_type


def test_infer_plan_type_uses_explicit_values_when_valid():
    assert infer_plan_type("multi_week", "Build any plan today") == "multi_week"
    assert infer_plan_type("single_session", "Build a long training plan") == "single_session"


def test_infer_plan_type_infers_single_session_from_prompt():
    assert infer_plan_type(None, "I only have 20 minutes today") == "single_session"
    assert infer_plan_type("weird value", "one workout for tonight") == "single_session"


def test_infer_plan_type_defaults_to_multi_week_without_single_signal():
    assert infer_plan_type(None, "Build me a strength plan for this week") == "multi_week"
