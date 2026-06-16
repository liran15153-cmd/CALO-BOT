from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app


def test_daily_summary_uses_stored_workouts_and_meals(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/workout-logs", json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"})
    client.post("/api/meals/manual", json={"text": "Log protein shake 25g protein"})

    response = client.get("/api/summaries/daily")

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["workouts_completed"] == 1
    assert body["metrics"]["meals_logged"] == 1
    assert body["metrics"]["calories_range"] == [120, 220]
    assert body["next_action"]


def test_weekly_summary_tracks_consistency_and_persists_summary(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/workout-logs", json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"})
    client.post("/api/workout-logs", json={"text": "I skipped squats because my knee hurts"})
    client.post("/api/meals/manual", json={"text": "I ate pizza"})

    response = client.get("/api/summaries/weekly")

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["workouts_completed"] == 1
    assert body["metrics"]["missed_workouts"] == 1
    assert body["metrics"]["consistency_percentage"] == 50
    assert body["next_action"]


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'summaries.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)
