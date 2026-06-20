from collections.abc import Generator
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import WeeklySummary


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


def test_weekly_summary_reuses_current_week_record(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/workout-logs", json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"})

    first = client.get("/api/summaries/weekly")
    second = client.get("/api/summaries/weekly")

    assert first.status_code == 200
    assert second.status_code == 200
    saved = db.scalars(select(WeeklySummary)).all()
    assert len(saved) == 1


def test_weekly_summary_consolidates_existing_duplicate_week_records(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.get("/api/summaries/daily")
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    db.add_all(
        [
            WeeklySummary(
                user_id=1,
                week_start=week_start,
                week_end=week_end,
                summary_text="old summary",
                metrics_json={},
            ),
            WeeklySummary(
                user_id=1,
                week_start=week_start,
                week_end=week_end,
                summary_text="duplicate summary",
                metrics_json={},
            ),
        ]
    )
    db.commit()

    response = client.get("/api/summaries/weekly")

    assert response.status_code == 200
    saved = db.scalars(select(WeeklySummary)).all()
    assert len(saved) == 1
    assert saved[0].summary_text.startswith("סיכום שבועי")


def make_client(tmp_path) -> TestClient:
    client, _db = make_client_and_db(tmp_path)
    return client


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'summaries.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
