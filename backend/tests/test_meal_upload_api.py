from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Meal, MealImageAnalysis, MealItem
from backend.app.services.ai_provider import AIResult


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


def test_meal_upload_rejects_jpeg_content_type_with_invalid_magic_bytes(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/meals/upload",
        files={"file": ("lunch.jpg", b"not-actually-a-jpeg", "image/jpeg")},
    )

    assert response.status_code == 400
    assert "image bytes" in response.json()["detail"].lower()
    assert db.scalar(select(Meal)) is None
    assert list((tmp_path / "uploads").glob("**/*")) == []


def test_meal_upload_rejects_images_over_5mb(tmp_path):
    client, db = make_client_and_db(tmp_path)
    too_large_jpeg = b"\xff\xd8\xff\xe0" + (b"x" * ((5 * 1024 * 1024) + 1))

    response = client.post(
        "/api/meals/upload",
        files={"file": ("lunch.jpg", too_large_jpeg, "image/jpeg")},
    )

    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()
    assert db.scalar(select(Meal)) is None
    assert list((tmp_path / "uploads").glob("**/*")) == []


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


def test_meal_image_analysis_updates_meal_ranges_and_items(tmp_path, monkeypatch):
    client, db = make_client_and_db(tmp_path)
    upload = client.post(
        "/api/meals/upload",
        data={"note": "Chicken bowl"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()
    monkeypatch.setattr(
        "backend.app.services.meal_service.build_ai_provider",
        lambda _api_key, _model: FakeImageProvider(),
    )

    response = client.post(f"/api/meals/{upload['id']}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    meal = db.get(Meal, upload["id"])
    assert meal is not None
    assert meal.calories_min == 520
    assert meal.calories_max == 760
    assert meal.protein_min == 35
    assert meal.protein_max == 52
    item = db.scalar(select(MealItem))
    assert item is not None
    assert item.name == "chicken rice bowl"


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


class FakeImageProvider:
    def analyze_image(self, _image_path, note=None):
        return AIResult(
            text=(
                '{"detected_items":[{"name":"chicken rice bowl","quantity":"1 bowl",'
                '"calories_min":520,"calories_max":760,"protein_min":35,"protein_max":52}],'
                '"calorie_range":[520,760],'
                '"macro_ranges":{"protein":[35,52],"carbs":[55,90],"fat":[12,24]},'
                '"confidence":"medium","follow_up_questions":["How much rice was in the bowl?"]}'
            ),
            provider_status="configured",
            used_model="fake-vision",
            estimated_tokens_in=10,
            estimated_tokens_out=20,
        )
