from collections.abc import Generator
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Meal, MealItem, UsageEvent
from backend.app.services.ai_provider import AIResult


def test_manual_meal_logging_estimates_protein_shake(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/meals/manual", json={"text": "Log protein shake 25g protein", "meal_type": "snack"})

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "medium"
    assert body["protein_min"] == 25
    assert body["calories_min"] < body["calories_max"]
    assert db.scalar(select(Meal)) is not None
    assert db.scalar(select(MealItem)).name == "שייק חלבון"


def test_manual_meal_logging_sums_multiple_recognized_items(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/meals/manual",
        json={"text": "Greek yogurt, banana and protein shake after training"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "medium"
    assert body["calories_min"] >= 280
    assert body["protein_min"] >= 35
    items = db.scalars(select(MealItem).order_by(MealItem.id)).all()
    assert len(items) == 3


def test_manual_meal_logging_estimates_shakshuka_bread_and_salad_as_itemized_ranges(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/meals/manual",
        json={"text": "אכלתי שקשוקה עם לחם וסלט"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "medium"
    assert body["calories_min"] >= 370
    assert body["calories_max"] <= 920
    assert body["protein_min"] >= 16
    items = db.scalars(select(MealItem).order_by(MealItem.id)).all()
    assert [item.name for item in items] == ["שקשוקה", "לחם", "סלט ירקות"]


def test_manual_meal_logging_estimates_pizza_as_low_confidence(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/meals/manual", json={"text": "I ate pizza"})

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "low"
    assert body["calories_min"] == 500
    assert body["calories_max"] == 1000


def test_recent_meals_returns_saved_history_with_items(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    older = client.post(
        "/api/meals/manual",
        json={"text": "I ate pizza", "meal_type": "dinner", "eaten_on": "2026-06-18"},
    )
    newer = client.post(
        "/api/meals/manual",
        json={"text": "Greek yogurt, banana and protein shake", "meal_type": "snack", "eaten_on": "2026-06-20"},
    )
    assert older.status_code == 200
    assert newer.status_code == 200

    response = client.get("/api/meals/recent")

    assert response.status_code == 200
    body = response.json()
    assert [meal["id"] for meal in body] == [newer.json()["id"], older.json()["id"]]
    assert body[0]["eaten_on"] == "2026-06-20"
    assert body[0]["meal_type"] == "snack"
    assert body[0]["calories_min"] >= 280
    assert len(body[0]["items"]) == 3
    assert body[0]["items"][0]["name"]


def test_manual_meal_logging_uses_ai_for_food_outside_the_hardcoded_table(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.meal_service.build_ai_provider",
        lambda _api_key, _model: FakeMealTextProvider(),
    )

    response = client.post("/api/meals/manual", json={"text": "אכלתי סטייק ופסטה ברוטב עגבניות"})

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "medium"
    assert body["calories_min"] == 650
    assert body["calories_max"] == 1150
    assert body["protein_min"] == 50
    items = db.scalars(select(MealItem).order_by(MealItem.id)).all()
    assert [item.name for item in items] == ["סטייק", "פסטה ברוטב עגבניות"]
    assert items[0].calories_min == 350
    usage = db.scalar(select(UsageEvent).where(UsageEvent.task == "meal_text"))
    assert usage is not None
    assert usage.provider == "configured"


def test_manual_meal_logging_replaces_non_hebrew_ai_item_names(tmp_path, monkeypatch):
    monkeypatch.setenv("LANGUAGE_GUARD_ENABLED", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.meal_service.build_ai_provider",
        lambda _api_key, _model: EnglishMealTextProvider(),
    )

    response = client.post("/api/meals/manual", json={"text": "I ate a grilled steak"})

    assert response.status_code == 200
    item = db.scalar(select(MealItem))
    assert item is not None
    assert item.name == "פריט מזון שזוהה"
    assert item.calories_min == 350
    assert "steak" not in str([row.name for row in db.scalars(select(MealItem)).all()])


def test_manual_meal_logging_falls_back_to_table_when_budget_spent(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("DAILY_AI_TOKEN_LIMIT", "1")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    db.add(
        UsageEvent(
            user_id=None,
            usage_date=date.today(),
            task="chat",
            provider="configured",
            model="fake-model",
            estimated_tokens_in=5,
            estimated_tokens_out=0,
        )
    )
    db.commit()

    def fail_if_called(_api_key, _model):
        raise AssertionError("provider should not be built after budget is spent")

    monkeypatch.setattr("backend.app.services.meal_service.build_ai_provider", fail_if_called)

    response = client.post("/api/meals/manual", json={"text": "I ate pizza"})

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "low"
    assert body["calories_min"] == 500
    assert body["calories_max"] == 1000
    usage = db.scalar(select(UsageEvent).where(UsageEvent.task == "meal_text"))
    assert usage is not None
    assert usage.provider == "budget_exceeded"


def test_manual_meal_logging_without_key_uses_deterministic_table(tmp_path):
    # No API key (autouse fixture leaves it empty): steak is outside the hardcoded table,
    # so it falls through to the generic estimate and records no AI usage.
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/meals/manual", json={"text": "אכלתי סטייק"})

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "low"
    assert body["calories_min"] == 300
    assert body["calories_max"] == 700
    assert db.scalar(select(MealItem)).name == "ארוחה לא ברורה"
    assert db.scalar(select(UsageEvent).where(UsageEvent.task == "meal_text")) is None


class FakeMealTextProvider:
    def structured(self, _request):
        return AIResult(
            text=(
                '{"message":"הערכה בטווחים לסטייק ופסטה.",'
                '"detected_items":['
                '{"name":"סטייק","quantity":"מנה בינונית","calories_range":[350,600],"protein_range":[40,60]},'
                '{"name":"פסטה ברוטב עגבניות","quantity":"צלחת","calories_range":[300,550],"protein_range":[10,18]}],'
                '"calorie_range":[650,1150],'
                '"macro_ranges":{"protein":[50,78],"carbs":[60,120],"fat":[20,45]},'
                '"confidence":"medium","follow_up_questions":["מה היה גודל מנת הסטייק?"]}'
            ),
            provider_status="configured",
            used_model="fake-haiku",
            estimated_tokens_in=12,
            estimated_tokens_out=24,
            token_breakdown={"message": 12, "output": 24, "input_total": 12, "total": 36, "source": "fake_meal_text"},
        )


class EnglishMealTextProvider:
    def structured(self, _request):
        return AIResult(
            text=(
                '{"message":"English estimate",'
                '"detected_items":[{"name":"grilled steak","quantity":"1 plate",'
                '"calories_range":[350,600],"protein_range":[40,60]}],'
                '"calorie_range":[350,600],"macro_ranges":{"protein":[40,60]},'
                '"confidence":"medium","follow_up_questions":["How big was the steak?"]}'
            ),
            provider_status="configured",
            used_model="fake-haiku",
            estimated_tokens_in=10,
            estimated_tokens_out=20,
        )


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'manual_meals.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
