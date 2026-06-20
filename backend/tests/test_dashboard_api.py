from collections.abc import Generator
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import UserMemory


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
    plan = client.post("/api/workout-plans", json={"prompt": "Build me a 3-day plan", "days_per_week": 3}).json()
    planned_dashboard = client.get("/api/dashboard").json()
    planned_action = planned_dashboard["next_recommended_action"]
    assert planned_dashboard["next_workout"]["id"] == plan["days"][0]["workout_id"]
    assert plan["days"][0]["name"] in planned_action
    assert "שמור על התוכנית" in planned_action
    assert planned_action != empty_action

    client.post("/api/workout-logs", json={"workout_id": plan["days"][0]["workout_id"], "status": "skipped"})
    missed_dashboard = client.get("/api/dashboard").json()
    missed_action = missed_dashboard["next_recommended_action"]
    assert missed_dashboard["next_workout"]["id"] == plan["days"][0]["workout_id"]
    assert "גרסת מינימום" in missed_action
    assert missed_action != planned_action


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


def test_dashboard_does_not_show_sensitive_memories_as_recent_notes(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    db = next(app.dependency_overrides[get_db]())
    db.add_all(
        [
            UserMemory(
                user_id=1,
                memory_type="preference",
                content="המשתמש מעדיף אימונים קצרים",
                is_sensitive=False,
            ),
            UserMemory(
                user_id=1,
                memory_type="safety_limitation",
                content="המשתמש דיווח על רגישות ברך בסקוואט",
                is_sensitive=True,
            ),
        ]
    )
    db.commit()

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    notes = response.json()["recent_coach_notes"]
    assert "המשתמש מעדיף אימונים קצרים" in notes
    assert "המשתמש דיווח על רגישות ברך בסקוואט" not in notes


def test_dashboard_localizes_known_legacy_english_memory_notes(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    db = next(app.dependency_overrides[get_db]())
    db.add(
        UserMemory(
            user_id=1,
            memory_type="equipment",
            content="User has access to dumbbells",
            is_sensitive=False,
        )
    )
    db.commit()

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    notes = response.json()["recent_coach_notes"]
    assert "למשתמש יש גישה למשקולות יד" in notes
    assert "User has access to dumbbells" not in notes


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
