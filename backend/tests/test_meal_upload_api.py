from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Meal, MealImageAnalysis


def test_meal_upload_stores_file_and_database_record(tmp_path):
    client, db = make_client_and_db(tmp_path)
    upload_bytes = b"\xff\xd8\xff\xe0fake-jpeg"

    response = client.post(
        "/api/meals/upload",
        data={"note": "This is lunch"},
        files={"file": ("../unsafe lunch.jpg", upload_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["note"] == "This is lunch"
    assert body["image_path"].endswith(".jpg")
    assert ".." not in body["image_path"]
    assert Path(body["image_path"]).exists()
    saved = db.scalar(select(Meal))
    assert saved is not None
    assert saved.image_path == body["image_path"]


def test_meal_image_analysis_no_key_does_not_fake_detection(tmp_path):
    client, db = make_client_and_db(tmp_path)
    upload = client.post(
        "/api/meals/upload",
        data={"note": "This is lunch"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()

    response = client.post(f"/api/meals/{upload['id']}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "not_configured"
    assert body["detected_items"] == []
    assert "unavailable" in body["message"].lower()
    saved = db.scalar(select(MealImageAnalysis))
    assert saved is not None
    assert saved.provider_status == "not_configured"


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'meals.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.state.upload_root = tmp_path / "uploads"
    return TestClient(app), db
