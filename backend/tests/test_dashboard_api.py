from collections.abc import Generator

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

