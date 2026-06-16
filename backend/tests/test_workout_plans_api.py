from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Workout, WorkoutExercise, WorkoutPlan


def test_workout_plan_api_generates_and_saves_structured_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 3-day gym plan for muscle", "days_per_week": 3, "equipment": ["dumbbells"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["days_per_week"] == 3
    assert body["days"][0]["exercises"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["days"][0]["exercises"][0]["name"]
    saved_workout = db.scalar(select(Workout))
    assert saved_workout is not None
    assert saved_workout.plan_id == saved.id
    saved_exercise = db.scalar(select(WorkoutExercise))
    assert saved_exercise is not None
    assert saved_exercise.workout_id == saved_workout.id


def test_workout_plan_api_returns_current_plan(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/workout-plans", json={"prompt": "Create a home dumbbell plan", "days_per_week": 2})

    response = client.get("/api/workout-plans/current")

    assert response.status_code == 200
    assert response.json()["is_current"] is True


def test_workout_plan_uses_saved_profile_when_request_is_open_ended(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/workout-plans", json={"prompt": "Create a safe starter plan"})

    assert response.status_code == 200
    body = response.json()
    assert body["days_per_week"] == 2
    assert body["equipment_needed"] == ["resistance bands"]
    assert body["days"][0]["name"].startswith("Tuesday")
    assert "knee" in body["recovery_note"].lower()


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'plans.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db


def valid_payload():
    return {
        "name": "Lior",
        "main_goal": "improve_strength",
        "experience_level": "beginner",
        "training_location": "home",
        "available_equipment": ["resistance bands"],
        "weekly_availability": 2,
        "session_length_minutes": 30,
        "preferred_workout_days": ["Tuesday", "Friday"],
        "injuries_limitations": "Avoid deep knee flexion",
        "coaching_style": "direct",
        "consent_disclaimer": True,
    }
