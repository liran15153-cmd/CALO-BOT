from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.auth import AuthContext, get_auth_context
from backend.app.config import get_settings
from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import User
from backend.app.services.settings_service import SettingsService


def test_settings_returns_masked_provider_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-anthropic-key-that-must-not-leak")
    get_settings.cache_clear()
    client = make_client(tmp_path)

    response = client.get("/api/settings")

    assert response.status_code == 200
    body = response.json()
    serialized = str(body)
    assert body["ai_provider"] in {"configured", "not_configured"}
    assert body["api_key_present"] is True
    assert "fake-anthropic-key" not in serialized
    assert "עצה רפואית" in body["disclaimer"]
    get_settings.cache_clear()


def test_settings_export_and_reset_local_data(tmp_path):
    client = make_client(tmp_path)
    profile = valid_payload()
    assert client.post("/api/onboarding", json=profile).status_code == 200
    assert client.post("/api/chat", json={"message": "אני אלרגי לבוטנים"}).status_code == 200
    assert client.post("/api/meals/manual", json={"text": "2 eggs and toast"}).status_code == 200
    assert client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2}).status_code == 200
    pending_candidate = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a new 4-day plan", "days_per_week": 4},
    )
    assert pending_candidate.status_code == 200
    assert pending_candidate.json()["pending_action"]["status"] == "pending"
    upload = client.post(
        "/api/meals/upload",
        data={"note": "Lunch photo"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    )
    assert upload.status_code == 200
    uploaded_path = tmp_path / "uploads" / upload.json()["image_path"]
    assert uploaded_path.exists()

    exported = client.get("/api/settings/export")

    assert exported.status_code == 200
    body = exported.json()
    assert body["profile"]["name"] == "Lior"
    assert body["meals"][0]["note"] == "2 eggs and toast"
    assert body["memory_facts"][0]["type"] == "allergy"
    assert body["pending_actions"][0]["status"] == "pending"
    assert body["pending_actions"][0]["action_type"] == "activate_workout_plan"

    reset = client.post("/api/settings/reset")

    assert reset.status_code == 200
    assert reset.json()["deleted_records"] > 0
    assert not uploaded_path.exists()
    assert client.get("/api/onboarding").json() == {"completed": False, "profile": None}
    assert client.get("/api/settings/export").json()["meals"] == []
    assert client.get("/api/settings/export").json()["memory_facts"] == []
    assert client.get("/api/settings/export").json()["pending_actions"] == []


def test_settings_reset_passes_auth_access_token_to_storage_cleanup(tmp_path, monkeypatch):
    captured = {}

    def fake_reset(self, *, upload_root=None, user_id=None, access_token=None):
        captured.update({"upload_root": upload_root, "user_id": user_id, "access_token": access_token})
        return 0

    monkeypatch.setattr(SettingsService, "reset_local_data", fake_reset)
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(
        user=User(id=123, name="משתמש בדיקה"),
        access_token="user-jwt",
    )
    try:
        response = make_client(tmp_path).post("/api/settings/reset")
    finally:
        app.dependency_overrides.pop(get_auth_context, None)

    assert response.status_code == 200
    assert captured["user_id"] == 123
    assert captured["access_token"] == "user-jwt"


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'settings.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.state.upload_root = tmp_path / "uploads"
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
