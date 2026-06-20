from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app


def test_usage_tracks_chat_attempts_with_no_provider(tmp_path):
    client = make_client(tmp_path)

    chat = client.post("/api/chat", json={"message": "I only have 20 minutes today"})
    usage = client.get("/api/usage")

    assert chat.status_code == 200
    assert usage.status_code == 200
    body = usage.json()
    assert body["chat_requests_count"] == 1
    assert body["image_analysis_count"] == 0
    assert body["summary_requests_count"] == 0
    assert body["estimated_tokens_in"] >= 0
    assert body["estimated_tokens_out"] >= 0
    assert body["estimated_tokens_total"] == body["estimated_tokens_in"] + body["estimated_tokens_out"]
    assert body["daily_ai_token_limit"] == 50000
    assert body["tokens_remaining"] == body["daily_ai_token_limit"] - body["estimated_tokens_total"]


def test_usage_tracks_summary_generation(tmp_path):
    client = make_client(tmp_path)

    summary = client.get("/api/summaries/weekly")
    usage = client.get("/api/usage")

    assert summary.status_code == 200
    assert usage.json()["summary_requests_count"] == 1


def test_usage_tracks_image_analysis_attempts(tmp_path):
    client = make_client(tmp_path)
    app.state.upload_root = tmp_path / "uploads"
    upload = client.post(
        "/api/meals/upload",
        data={"note": "lunch"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()

    analysis = client.post(f"/api/meals/{upload['id']}/analyze")
    usage = client.get("/api/usage")

    assert analysis.status_code == 200
    assert usage.json()["image_analysis_count"] == 1


def test_usage_today_alias_is_not_exposed(tmp_path):
    client = make_client(tmp_path)

    response = client.get("/api/usage/today")

    assert response.status_code == 404


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'usage.db'}")
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
