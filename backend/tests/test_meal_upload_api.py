from collections.abc import Generator
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Meal, MealImageAnalysis, MealItem, UsageEvent
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
    assert not Path(body["image_path"]).is_absolute()
    assert ".." not in body["image_path"]
    assert (tmp_path / "uploads" / body["image_path"]).exists()
    saved = db.scalar(select(Meal))
    assert saved is not None
    assert saved.image_path == body["image_path"]


def test_meal_upload_rejects_local_file_fallback_in_production(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/meals/upload",
        data={"note": "Production upload"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    )

    assert response.status_code == 400
    assert "Supabase Storage is required" in response.json()["detail"]
    assert db.scalar(select(Meal)) is None
    get_settings.cache_clear()


def test_meal_upload_rejects_jpeg_content_type_with_invalid_magic_bytes(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/meals/upload",
        files={"file": ("lunch.jpg", b"not-actually-a-jpeg", "image/jpeg")},
    )

    assert response.status_code == 400
    assert "קובץ התמונה" in response.json()["detail"]
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
    assert "גדולה מדי" in response.json()["detail"]
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
    assert "לא זמין" in body["message"]
    saved = db.scalar(select(MealImageAnalysis))
    assert saved is not None
    assert saved.provider_status == "not_configured"


def test_meal_image_analysis_returns_404_when_uploaded_file_is_missing(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    upload = client.post(
        "/api/meals/upload",
        data={"note": "This is lunch"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()
    (tmp_path / "uploads" / upload["image_path"]).unlink()

    response = client.post(f"/api/meals/{upload['id']}/analyze")

    assert response.status_code == 404
    assert "תמונת הארוחה לא נמצאה" in response.json()["detail"]


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
    assert item.name == "קערת עוף ואורז"
    usage = db.scalar(select(UsageEvent).where(UsageEvent.task == "image_analysis"))
    assert usage is not None
    assert usage.token_breakdown_json["message"] == 10
    assert usage.token_breakdown_json["output"] == 20
    assert usage.token_breakdown_json["total"] == 30


def test_meal_image_analysis_replaces_non_hebrew_provider_text(tmp_path, monkeypatch):
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    upload = client.post(
        "/api/meals/upload",
        data={"note": "Lunch"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()
    monkeypatch.setattr(
        "backend.app.services.meal_service.build_ai_provider",
        lambda _api_key, _model: EnglishImageProvider(),
    )

    response = client.post(f"/api/meals/{upload['id']}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["detected_items"][0]["name"] == "פריט מזון שזוהה"
    assert body["follow_up_questions"] == ["מה הכמות המשוערת ומה שיטת ההכנה?"]
    assert "English" not in str(body)


def test_meal_image_analysis_replaces_generic_english_terms_in_hebrew_message(tmp_path, monkeypatch):
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    upload = client.post(
        "/api/meals/upload",
        data={"note": "Lunch"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()
    monkeypatch.setattr(
        "backend.app.services.meal_service.build_ai_provider",
        lambda _api_key, _model: HebrewWithEnglishTermImageProvider(),
    )

    response = client.post(f"/api/meals/{upload['id']}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert "protein timing" not in body["message"]
    assert "טקסט שרובו לא בעברית" in body["message"]


def test_meal_image_analysis_replaces_mixed_english_user_visible_text(tmp_path, monkeypatch):
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    upload = client.post(
        "/api/meals/upload",
        data={"note": "Lunch"},
        files={"file": ("lunch.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()
    monkeypatch.setattr(
        "backend.app.services.meal_service.build_ai_provider",
        lambda _api_key, _model: MixedEnglishImageProvider(),
    )

    response = client.post(f"/api/meals/{upload['id']}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["detected_items"][0]["name"] == "פריט מזון שזוהה"
    assert body["follow_up_questions"] == ["מה הכמות המשוערת ומה שיטת ההכנה?"]
    assert "English" not in str(body)
    assert "chicken" not in str(body)
    assert "rice" not in str(body)
    assert "bowl" not in str(body)


def test_meal_image_analysis_blocks_provider_when_daily_token_budget_is_spent(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("DAILY_AI_TOKEN_LIMIT", "1")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    upload = client.post(
        "/api/meals/upload",
        data={"note": "Dinner"},
        files={"file": ("dinner.jpg", b"\xff\xd8\xff\xe0fake-jpeg", "image/jpeg")},
    ).json()
    db.add(
        UsageEvent(
            user_id=None,
            usage_date=date.today(),
            task="chat",
            provider="configured",
            model="fake-model",
            estimated_tokens_in=2,
            estimated_tokens_out=0,
        )
    )
    db.commit()

    def fail_if_called(_api_key, _model):
        raise AssertionError("provider should not be built after budget is spent")

    monkeypatch.setattr("backend.app.services.meal_service.build_ai_provider", fail_if_called)

    response = client.post(f"/api/meals/{upload['id']}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "budget_exceeded"
    assert "תקציב" in body["message"]
    assert body["detected_items"] == []
    saved = db.scalar(select(MealImageAnalysis))
    assert saved is not None
    assert saved.provider_status == "budget_exceeded"


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


def enable_language_guard(monkeypatch) -> None:
    monkeypatch.setenv("LANGUAGE_GUARD_ENABLED", "true")


class FakeImageProvider:
    def analyze_image(self, _image_path, note=None):
        return AIResult(
            text=(
                '{"detected_items":[{"name":"קערת עוף ואורז","quantity":"קערה אחת",'
                '"calories_min":520,"calories_max":760,"protein_min":35,"protein_max":52}],'
                '"calorie_range":[520,760],'
                '"macro_ranges":{"protein":[35,52],"carbs":[55,90],"fat":[12,24]},'
                '"confidence":"medium","follow_up_questions":["כמה אורז היה בקערה?"]}'
            ),
            provider_status="configured",
            used_model="fake-vision",
            estimated_tokens_in=10,
            estimated_tokens_out=20,
            token_breakdown={
                "message": 10,
                "output": 20,
                "input_total": 10,
                "total": 30,
                "source": "fake_image_provider",
            },
        )


class EnglishImageProvider:
    def analyze_image(self, _image_path, note=None):
        return AIResult(
            text=(
                '{"detected_items":[{"name":"chicken rice bowl","quantity":"1 bowl"}],'
                '"calorie_range":[520,760],'
                '"macro_ranges":{"protein":[35,52]},'
                '"message":"English estimate","confidence":"medium",'
                '"follow_up_questions":["How much rice was in the bowl?"]}'
            ),
            provider_status="configured",
            used_model="fake-vision",
            estimated_tokens_in=10,
            estimated_tokens_out=20,
        )


class HebrewWithEnglishTermImageProvider:
    def analyze_image(self, _image_path, note=None):
        return AIResult(
            text=(
                '{"detected_items":[{"name":"קערת עוף ואורז","quantity":"קערה אחת"}],'
                '"calorie_range":[520,760],'
                '"macro_ranges":{"protein":[35,52]},'
                '"message":"הערכה שמרנית: protein timing לא קריטי כאן, אבל יש כנראה חלבון בכמות בינונית-גבוהה.","confidence":"medium",'
                '"follow_up_questions":["כמה אורז היה בקערה?"]}'
            ),
            provider_status="configured",
            used_model="fake-vision",
            estimated_tokens_in=10,
            estimated_tokens_out=20,
        )


class MixedEnglishImageProvider:
    def analyze_image(self, _image_path, note=None):
        return AIResult(
            text=(
                '{"detected_items":[{"name":"chicken rice bowl","quantity":"1 bowl"}],'
                '"calorie_range":[520,760],'
                '"macro_ranges":{"protein":[35,52]},'
                '"message":"כן. This is a chicken rice bowl with protein and calories estimate.","confidence":"medium",'
                '"follow_up_questions":["How much rice was in the bowl?"]}'
            ),
            provider_status="configured",
            used_model="fake-vision",
            estimated_tokens_in=10,
            estimated_tokens_out=20,
        )
