from collections.abc import Generator

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


def test_dashboard_next_recommended_action_reflects_available_state(tmp_path):
    client = make_client(tmp_path)

    empty_action = client.get("/api/dashboard").json()["next_recommended_action"]
    assert empty_action == "סיים את האונבורדינג כדי שהמאמן יוכל לבנות את התוכנית הראשונה."

    client.post("/api/onboarding", json=valid_payload())
    client.post("/api/workout-plans", json={"prompt": "Build me a 3-day plan", "days_per_week": 3})
    planned_action = client.get("/api/dashboard").json()["next_recommended_action"]
    assert planned_action == "בצע את האימון המתוכנן הבא ותעד ארוחה אחת עם דגש על חלבון."
    assert planned_action != empty_action

    client.post("/api/workout-logs", json={"text": "I skipped today's workout"})
    missed_action = client.get("/api/dashboard").json()["next_recommended_action"]
    assert missed_action == "קבע מחדש את האימון שפוספס לפני שאתה מוסיף עוד נפח."
    assert missed_action != planned_action


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
