from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import ChatMessage, Meal, SafetyEvent, UsageEvent, WorkoutPlan


def test_chat_endpoint_persists_user_and_no_key_coach_messages(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "Build me a beginner workout"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "not_configured"
    assert "not configured" in body["response"]
    messages = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert [message.role for message in messages] == ["user", "coach"]


def test_chat_endpoint_uses_safety_response_for_pain(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "My knee hurts when I squat"})

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is True
    assert "Stop" in body["response"]
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "pain_or_injury"
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "safety_override"))
    assert usage is not None


def test_chat_endpoint_dispatches_workout_plan_intent_to_module(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "Create a 2-day dumbbell workout plan"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "workout plan" in body["response"].lower()
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.days_per_week == 2
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None


def test_chat_endpoint_dispatches_manual_meal_log_intent_to_module(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "Log meal: protein shake with 25g protein"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "meal" in body["response"].lower()
    saved = db.scalar(select(Meal))
    assert saved is not None
    assert saved.calories_min is not None


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'coach.db'}")
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
