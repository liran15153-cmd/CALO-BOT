from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Meal, MealItem


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


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'manual_meals.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
