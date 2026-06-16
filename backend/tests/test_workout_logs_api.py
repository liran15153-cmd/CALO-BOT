from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app


def test_workout_log_api_parses_sets_reps_and_weight(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["exercise_results"][0]["exercise"] == "bench press"
    assert body["exercise_results"][0]["reps"] == [10, 8, 7]
    assert body["exercise_results"][0]["weight"] == "50kg"


def test_workout_log_api_flags_skipped_and_pain(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/api/workout-logs", json={"text": "I skipped squats because my knee hurts"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "skipped"
    assert body["pain_flag"] is True


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'logs.db'}")
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

