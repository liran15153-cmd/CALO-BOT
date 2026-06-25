from collections.abc import Generator
from datetime import date, timedelta
import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app


def test_dashboard_returns_live_user_state(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    client.post("/api/workout-plans", json={"prompt": "Build me a 3-day plan", "days_per_week": 3})
    client.post("/api/workout-logs", json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"})
    client.post("/api/meals/manual", json={"text": "Log protein shake 25g protein"})

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["current_goal"] == "build_muscle"
    assert body["current_workout_plan"]["days_per_week"] == 3
    assert body["completed_workouts_this_week"] == 1
    assert body["meals_logged_this_week"] == 1
    assert body["next_recommended_action"]


def test_dashboard_current_streak_counts_consecutive_active_dates_not_log_count(tmp_path):
    client = make_client(tmp_path)
    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    three_days_ago = today - timedelta(days=3)

    for note in ["First session today", "Second session today"]:
        client.post(
            "/api/workout-logs",
            json={"logged_on": today.isoformat(), "status": "completed", "notes": note},
        )
    client.post(
        "/api/workout-logs",
        json={"logged_on": yesterday.isoformat(), "status": "skipped", "notes": "No time"},
    )
    client.post("/api/meals/manual", json={"text": "I ate yogurt", "eaten_on": yesterday.isoformat()})
    client.post(
        "/api/workout-logs",
        json={"logged_on": two_days_ago.isoformat(), "status": "partial", "notes": "Short session"},
    )
    client.post(
        "/api/workout-logs",
        json={"logged_on": three_days_ago.isoformat(), "status": "completed", "notes": "Old session"},
    )

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["current_streak"] == 4


def test_dashboard_next_recommended_action_reflects_available_state(tmp_path):
    client = make_client(tmp_path)

    empty_action = client.get("/api/dashboard").json()["next_recommended_action"]
    assert empty_action == "להשלים את האונבורדינג כדי שהמאמן יוכל לבנות את התוכנית הראשונה."

    client.post("/api/onboarding", json=valid_payload())
    plan = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה", "days_per_week": 3},
    ).json()
    planned_dashboard = client.get("/api/dashboard").json()
    planned_action = planned_dashboard["next_recommended_action"]
    assert planned_dashboard["current_goal"] == plan["goal"] == "improve_endurance"
    assert planned_dashboard["next_workout"]["id"] == plan["days"][0]["workout_id"]
    assert planned_dashboard["next_workout"]["first_exercise"]["name"] == "אירובי בסיסי בקצב שיחה"
    assert planned_dashboard["next_workout"]["first_exercise"]["reps_or_duration"] == "12-25 דקות"
    assert plan["days"][0]["name"] in planned_action
    assert "שמור על התוכנית" in planned_action
    assert "לא לנחש" in planned_action
    assert planned_action != empty_action

    client.post("/api/workout-logs", json={"workout_id": plan["days"][0]["workout_id"], "status": "skipped"})
    missed_dashboard = client.get("/api/dashboard").json()
    missed_action = missed_dashboard["next_recommended_action"]
    assert missed_dashboard["next_workout"]["id"] == plan["days"][0]["workout_id"]
    assert "גרסת מינימום" in missed_action
    assert missed_action != planned_action

    client.post(
        "/api/workout-logs",
        json={"workout_id": plan["days"][1]["workout_id"], "status": "partial", "notes": "Stopped early, no pain"},
    )
    repeated_miss_dashboard = client.get("/api/dashboard").json()
    repeated_action = repeated_miss_dashboard["next_recommended_action"]
    assert "להוריד זמנית יום אימון אחד" in repeated_action
    assert "שאלה אחת" in repeated_action
    assert repeated_miss_dashboard["next_workout"]["plan_adjustment"]["type"] == "reduce_plan_before_rebuild"


def test_dashboard_current_plan_uses_edited_workout_rows_after_scoped_edit(tmp_path):
    client = make_client(tmp_path)
    plan = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Create a 2-day dumbbell plan with bench",
            "days_per_week": 2,
            "equipment": ["dumbbells", "bench"],
        },
    ).json()

    edit_response = client.post("/api/chat", json={"message": "no bench in my plan, replace only what needs it"})
    assert edit_response.status_code == 200
    assert edit_response.json()["provider_status"] == "local_tool"

    dashboard = client.get("/api/dashboard").json()
    current_plan = dashboard["current_workout_plan"]
    assert current_plan["id"] == plan["id"]
    assert dashboard["next_workout"]["id"] == current_plan["days"][0]["workout_id"]
    assert all(day.get("workout_id") for day in current_plan["days"])
    assert all(exercise.get("exercise_id") for day in current_plan["days"] for exercise in day["exercises"])
    assert dashboard["next_workout"]["first_exercise"]["name"] == current_plan["days"][0]["exercises"][0]["name"]
    exercise_text = json.dumps([day["exercises"] for day in current_plan["days"]], ensure_ascii=False).lower()
    equipment_text = json.dumps(current_plan.get("equipment_needed") or [], ensure_ascii=False).lower()
    assert "bench" not in exercise_text
    assert "bench" not in equipment_text


def test_dashboard_next_action_advances_with_completed_plan_log(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 2-day plan", "days_per_week": 2}).json()

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": plan["days"][0]["exercises"][0]["exercise_id"],
                    "exercise_name": plan["days"][0]["exercises"][0]["name"],
                    "status": "completed",
                    "sets": [
                        {"set_index": 1, "reps": 12, "completed": True},
                        {"set_index": 2, "reps": 12, "completed": True},
                    ],
                    "rpe": 8,
                    "rir": 2,
                }
            ],
            "rpe": 8,
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["id"] == plan["days"][1]["workout_id"]
    assert plan["days"][1]["name"] in dashboard["next_recommended_action"]
    assert dashboard["next_workout"]["load_signal"] == "progress_candidate"


def test_dashboard_surfaces_rir_based_progression_evidence(tmp_path):
    client = make_client(tmp_path)
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 1-day plan", "days_per_week": 1}).json()

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": (
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10. \u05e0\u05e9\u05d0\u05e8\u05d5 "
                "\u05dc\u05d9 2 \u05d7\u05d6\u05e8\u05d5\u05ea "
                "\u05d1\u05e8\u05d6\u05e8\u05d1\u05d4, \u05d1\u05dc\u05d9 "
                "\u05db\u05d0\u05d1."
            ),
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "progress_candidate"
    assert dashboard["next_workout"]["progress_evidence"] == "exercise_log"
    assert "RPE/RIR" in dashboard["next_recommended_action"]
    assert "\u05dc\u05d0 \u05dc\u05e0\u05d7\u05e9" in dashboard["next_recommended_action"]


def test_dashboard_surfaces_zero_rir_recovery_evidence(tmp_path):
    client = make_client(tmp_path)
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 1-day plan", "days_per_week": 1}).json()

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": (
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10. RIR 0, \u05d1\u05dc\u05d9 "
                "\u05db\u05d0\u05d1."
            ),
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "recovery_needed"
    assert any("RPE/RIR" in signal for signal in dashboard["next_workout"]["signals"])
    assert "RPE/RIR" in dashboard["next_recommended_action"]
    assert "\u05dc\u05d4\u05d5\u05e8\u05d9\u05d3" in dashboard["next_recommended_action"]
    assert "\u05dc\u05d0 \u05dc\u05e0\u05d7\u05e9" in dashboard["next_recommended_action"]


def test_dashboard_surfaces_high_rir_underload_guidance(tmp_path):
    client = make_client(tmp_path)
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 1-day plan", "days_per_week": 1}).json()
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": f"עשיתי {exercise['name']} 3x10. RIR 5, בלי כאב.",
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "progress_candidate"
    assert dashboard["next_workout"]["exercise_adjustments"][0]["reason"] == "high_rir_underload"
    assert "RIR 1-3" in dashboard["next_recommended_action"]
    assert "\u05e2\u05d5\u05de\u05e1 \u05e7\u05d8\u05df" in dashboard["next_recommended_action"]
    assert "\u05dc\u05d0 \u05dc\u05e0\u05d7\u05e9" in dashboard["next_recommended_action"]


def test_dashboard_surfaces_natural_hebrew_underload_guidance(tmp_path):
    client = make_client(tmp_path)
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 1-day plan", "days_per_week": 1}).json()
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": f"עשיתי {exercise['name']} 3x10. היה קל מדי ונשאר לי מלא כוח, בלי כאב.",
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "progress_candidate"
    assert dashboard["next_workout"]["exercise_adjustments"][0]["reason"] == "qualitative_underload"
    assert "קל מדי" in dashboard["next_recommended_action"]
    assert "RIR 1-3" not in dashboard["next_recommended_action"]
    assert "RPE/RIR" not in dashboard["next_recommended_action"]
    assert "\u05e2\u05d5\u05de\u05e1 \u05e7\u05d8\u05df" in dashboard["next_recommended_action"]
    assert "\u05dc\u05d0 \u05dc\u05e0\u05d7\u05e9" in dashboard["next_recommended_action"]


def test_dashboard_surfaces_natural_hebrew_too_hard_recovery_guidance(tmp_path):
    client = make_client(tmp_path)
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 1-day plan", "days_per_week": 1}).json()
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": f"עשיתי {exercise['name']} 3x10. היה כבד מדי ובקושי סיימתי, בלי כאב.",
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "recovery_needed"
    assert dashboard["next_workout"]["exercise_adjustments"][0]["reason"] == "qualitative_high_effort"
    assert "\u05db\u05d1\u05d3 \u05de\u05d3\u05d9" in dashboard["next_recommended_action"]
    assert "RPE/RIR" not in dashboard["next_recommended_action"]
    assert "\u05dc\u05d4\u05d5\u05e8\u05d9\u05d3" in dashboard["next_recommended_action"]
    assert "\u05dc\u05d0 \u05dc\u05e0\u05d7\u05e9" in dashboard["next_recommended_action"]


def test_dashboard_holds_progression_after_controlled_verbal_effort_without_rpe(tmp_path):
    client = make_client(tmp_path)
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 1-day plan", "days_per_week": 1}).json()
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": f"עשיתי {exercise['name']} 3x10. היה מאתגר אבל בשליטה, בלי כאב.",
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "maintain"
    assert dashboard["next_workout"]["exercise_adjustments"][0]["reason"] == "qualitative_controlled_effort"
    assert "בשליטה" in dashboard["next_recommended_action"]
    assert "RPE 1-10" in dashboard["next_recommended_action"]
    assert "להעלות עומס" in dashboard["next_recommended_action"]
    assert "אפשר התקדמות קטנה" not in dashboard["next_recommended_action"]


def test_dashboard_surfaces_progression_gate_after_regressed_exercise_clean_log(tmp_path):
    client = make_client(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["bodyweight"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    target_exercise = next(
        exercise
        for day in plan["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )

    edit_response = client.post(
        "/api/chat",
        json={"message": "שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["provider_status"] == "local_tool"

    edited_next = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_next["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )
    assert edited_exercise["name"] == "שכיבת סמיכה על קיר"

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": edited_next["id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": edited_exercise["exercise_id"],
                    "exercise_name": edited_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "rpe": 8,
                    "rir": 2,
                }
            ],
            "rpe": 8,
            "pain_flag": False,
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "progress_candidate"
    gate = dashboard["next_workout"]["progression_gate"]
    assert gate["exercise_name"] == "שכיבת סמיכה על קיר"
    assert "שלב אחד" in gate["action"]
    assert "RPE 8" in gate["action"]
    assert "לתעד RPE וכאב" in gate["action"]
    assert "לא לנחש" in gate["action"]
    assert "שלב אחד" in dashboard["next_recommended_action"]
    assert "לא לנחש" in dashboard["next_recommended_action"]
    assert "חזרה אחת" not in dashboard["next_recommended_action"]


def test_dashboard_no_cable_progression_gate_does_not_recommend_unavailable_equipment(tmp_path):
    client = make_client(tmp_path)
    cable = "\u05db\u05d1\u05dc"
    pulley = "\u05e4\u05d5\u05dc\u05d9"
    cable_missing_note = "\u05db\u05d1\u05dc/\u05e4\u05d5\u05dc\u05d9 \u05d7\u05e1\u05e8"

    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a one day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 1,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    assert plan_response.status_code == 200
    edit_response = client.post(
        "/api/chat",
        json={
            "message": (
                "\u05d0\u05d9\u05df \u05dc\u05d9 \u05db\u05d1\u05dc\u05d9\u05dd "
                "\u05d1\u05ea\u05d5\u05db\u05e0\u05d9\u05ea, \u05ea\u05d7\u05dc\u05d9\u05e3 "
                "\u05e8\u05e7 \u05d0\u05ea \u05de\u05d4 \u05e9\u05e6\u05e8\u05d9\u05da"
            )
        },
    )
    assert edit_response.status_code == 200

    edited_next = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_next["exercises"]
        if cable_missing_note in (exercise.get("notes") or "")
    )
    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": edited_next["id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": edited_exercise["exercise_id"],
                    "exercise_name": edited_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "rpe": 7,
                }
            ],
            "rpe": 7,
            "pain_flag": False,
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    gate = dashboard["next_workout"]["progression_gate"]
    assert gate["exercise_name"] == edited_exercise["name"]
    assert "\u05e9\u05dc\u05d1 \u05d0\u05d7\u05d3" in dashboard["next_recommended_action"]
    assert "\u05dc\u05d0 \u05dc\u05e0\u05d7\u05e9" in dashboard["next_recommended_action"]
    assert dashboard["next_workout"]["exercise_adjustments"][0]["reason"] == "completed_with_manageable_effort"
    assert "substitution_progression_gate" not in dashboard["next_recommended_action"]
    assert cable not in gate["action"]
    assert pulley not in gate["action"]
    assert cable not in dashboard["next_recommended_action"]
    assert pulley not in dashboard["next_recommended_action"]


def test_dashboard_holds_progression_gate_after_verbal_effort_without_rpe(tmp_path):
    client = make_client(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["bodyweight"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    target_exercise = next(
        exercise
        for day in plan["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )

    edit_response = client.post(
        "/api/chat",
        json={"message": "שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר"},
    )
    assert edit_response.status_code == 200

    edited_next = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_next["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": edited_next["id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": edited_exercise["exercise_id"],
                    "exercise_name": edited_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "notes": "היה בשליטה בלי כאב",
                }
            ],
            "pain_flag": False,
        },
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "maintain"
    adjusted = dashboard["next_workout"]["exercise_adjustments"][0]
    assert adjusted["reason"] == "progression_gate_missing_rpe"
    assert "מאמץ מילולי נשמר" in dashboard["next_recommended_action"]
    assert "RPE 1-10" in dashboard["next_recommended_action"]
    assert "הגרסה הנוכחית" in dashboard["next_recommended_action"]
    assert dashboard["next_workout"].get("progression_gate") is None


def test_dashboard_surfaces_session_level_progression_gate_note_after_chat_log(tmp_path):
    client = make_client(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["bodyweight"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    target_exercise = next(
        exercise
        for day in plan["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )

    edit_response = client.post(
        "/api/chat",
        json={"message": "שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["provider_status"] == "local_tool"

    edited_next = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_next["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )
    assert edited_exercise["name"] == "שכיבת סמיכה על קיר"

    log_response = client.post(
        "/api/chat",
        json={"message": "סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב"},
    )
    assert log_response.status_code == 200

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["next_workout"]["load_signal"] == "progress_candidate"
    gate = dashboard["next_workout"]["progression_gate"]
    assert gate["exercise_name"] == "שכיבת סמיכה על קיר"
    assert "לוג" in gate["action"]
    assert "כללי" in gate["action"]
    assert "חזרות/RPE" in gate["action"]
    assert "לא לנחש" in gate["action"]
    assert "שלב אחד" in dashboard["next_recommended_action"]
    assert "לא לנחש" in dashboard["next_recommended_action"]


def test_dashboard_prefers_existing_next_workout_over_onboarding_action(tmp_path):
    client = make_client(tmp_path)
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 2-day plan", "days_per_week": 2}).json()

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["current_goal"] == plan["goal"]
    assert dashboard["next_workout"]["id"] == plan["days"][0]["workout_id"]
    assert plan["days"][0]["name"] in dashboard["next_recommended_action"]
    assert "אונבורדינג" not in dashboard["next_recommended_action"]


def test_dashboard_nutrition_action_reflects_today_meals(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    empty_dashboard = client.get("/api/dashboard").json()
    assert empty_dashboard["meals_logged_today"] == 0
    assert "לתעד ארוחה אחת" in empty_dashboard["nutrition_action"]

    client.post("/api/meals/manual", json={"text": "Log protein shake 25g protein"})
    fed_dashboard = client.get("/api/dashboard").json()

    assert fed_dashboard["meals_logged_today"] == 1
    assert fed_dashboard["estimated_protein_range_today"] == [25, 35]
    assert "יש ארוחה מתועדת היום" in fed_dashboard["nutrition_action"]


def test_dashboard_uses_null_nutrition_range_when_no_estimates_exist(tmp_path):
    client = make_client(tmp_path)

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    assert response.json()["estimated_nutrition_range"] is None


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'dashboard.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def valid_payload():
    return {
        "name": "Lior",
        "main_goal": "build_muscle",
        "experience_level": "beginner",
        "training_location": "gym",
        "available_equipment": ["dumbbells"],
        "weekly_availability": 3,
        "session_length_minutes": 45,
        "preferred_workout_days": ["Monday"],
        "coaching_style": "direct",
        "consent_disclaimer": True,
    }
