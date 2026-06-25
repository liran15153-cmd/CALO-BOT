from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app


def test_onboarding_api_returns_empty_state_then_saves_profile(tmp_path):
    client = make_client(tmp_path)

    empty = client.get("/api/onboarding")
    assert empty.status_code == 200
    assert empty.json() == {"completed": False, "profile": None}

    payload = valid_payload()
    saved = client.post("/api/onboarding", json=payload)

    assert saved.status_code == 200
    body = saved.json()
    assert body["completed"] is True
    assert body["profile"]["name"] == "Lior"
    assert body["profile"]["main_goal"] == "build_muscle"

    reloaded = client.get("/api/onboarding")
    assert reloaded.json()["profile"]["name"] == "Lior"


def test_onboarding_api_rejects_missing_consent(tmp_path):
    client = make_client(tmp_path)
    payload = valid_payload(consent_disclaimer=False)

    response = client.post("/api/onboarding", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == ["יש לאשר שהאפליקציה מספקת הכוונת כושר ותזונה כללית בלבד"]


def test_onboarding_api_validation_errors_are_hebrew(tmp_path):
    client = make_client(tmp_path)
    payload = valid_payload(main_goal="invalid_goal")

    response = client.post("/api/onboarding", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"] == ["בקשת API לא תקינה. יש לבדוק את השדות והערכים שנשלחו."]
    assert "Input should be" not in str(response.json())


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'api.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def valid_payload(**overrides):
    payload = {
        "name": "Lior",
        "age_range": "30-39",
        "gender": "prefer_not_to_say",
        "height_cm": 178,
        "weight_kg": 82,
        "main_goal": "build_muscle",
        "experience_level": "beginner",
        "training_location": "gym",
        "available_equipment": ["dumbbells"],
        "weekly_availability": 3,
        "session_length_minutes": 45,
        "preferred_workout_days": ["Monday"],
        "injuries_limitations": "",
        "nutrition_preference": "high_protein",
        "foods_disliked": "",
        "allergies": "",
        "typical_schedule": "after work",
        "coaching_style": "direct",
        "consent_disclaimer": True,
    }
    payload.update(overrides)
    return payload

