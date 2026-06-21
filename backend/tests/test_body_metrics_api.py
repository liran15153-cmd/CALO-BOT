from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import User
from backend.app.services.context_builder import ContextBuilder


def test_body_metrics_api_writes_reads_and_context_uses_recent_metrics(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/body-metrics",
        json={
            "measured_on": "2026-06-20",
            "weight_kg": 82.5,
            "body_fat_percent": 20.2,
            "measurements": {"waist_cm": 88.0, "chest_cm": 103.0},
            "source": "manual",
            "note": "morning check-in",
        },
    )

    assert response.status_code == 200
    created = response.json()
    assert created["weight_kg"] == 82.5
    assert created["body_fat_percent"] == 20.2
    assert created["measurements"]["waist_cm"] == 88.0
    assert created["source"] == "manual"

    recent = client.get("/api/body-metrics/recent")

    assert recent.status_code == 200
    assert recent.json()[0]["id"] == created["id"]
    assert recent.json()[0]["measured_on"] == "2026-06-20"

    latest = client.get("/api/body-metrics/latest")

    assert latest.status_code == 200
    assert latest.json()["id"] == created["id"]

    user_id = db.query(User.id).scalar()
    context = ContextBuilder(db).build(user_id=user_id, intent="general_chat")

    assert context["body_metrics"][0]["weight_kg"] == 82.5
    assert context["body_metrics"][0]["body_fat_percent"] == 20.2
    assert context["body_metrics"][0]["measurements"]["waist_cm"] == 88.0


def test_body_metrics_recent_returns_newest_first_and_scopes_to_current_user(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    older = client.post(
        "/api/body-metrics",
        json={"measured_on": "2026-06-18", "weight_kg": 83.0, "measurements": {"waist_cm": 89.0}},
    )
    newer = client.post(
        "/api/body-metrics",
        json={"measured_on": "2026-06-21", "weight_kg": 82.0, "measurements": {"waist_cm": 87.5}},
    )
    assert older.status_code == 200
    assert newer.status_code == 200

    recent = client.get("/api/body-metrics/recent")

    assert recent.status_code == 200
    assert [metric["id"] for metric in recent.json()] == [newer.json()["id"], older.json()["id"]]


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'body-metrics.db'}")
    init_db(engine)
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)
    db = testing_session_local()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
