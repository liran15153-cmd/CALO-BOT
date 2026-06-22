"""End-to-end conversation simulations (no API key configured).

These exercise short, realistic multi-message flows through /api/chat the way a real
Hebrew user would talk — mixing moods, slang, pain, plateaus and Hebrew-English — and
assert that routing, safety and natural Hebrew hold across the whole exchange, not just
on clean single sentences.
"""

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Meal, SafetyEvent, WorkoutLog


class Conversation:
    """Small helper that keeps a single chat session across turns."""

    def __init__(self, client: TestClient):
        self.client = client
        self.session_id: int | None = None

    def say(self, message: str) -> dict:
        payload: dict = {"message": message}
        if self.session_id is not None:
            payload["session_id"] = self.session_id
        response = self.client.post("/api/chat", json=payload)
        assert response.status_code == 200, message
        body = response.json()
        self.session_id = body["session_id"]
        # Every coach reply is Hebrew and never the bare not-configured notice for a
        # message we know how to answer locally.
        assert any("֐" <= ch <= "׿" for ch in body["response"]), message
        return body


def test_simulation_tired_then_debating_then_partial_log(tmp_path):
    client, db = make_client_and_db(tmp_path)
    chat = Conversation(client)

    first = chat.say("אין לי מוטיבציה היום, בא לי לוותר")
    assert first["provider_status"] == "local_tool"
    assert "מוטיבציה" in first["response"]

    second = chat.say("בסוף הלכתי, עשיתי רק 2 סטים חזה")
    # A reported partial workout is logged, not treated as a question.
    assert second["provider_status"] == "local_tool"
    assert "רשמתי את האימון" in second["response"]
    assert db.scalar(select(WorkoutLog)) is not None


def test_simulation_creatine_question_then_meal_log(tmp_path):
    client, db = make_client_and_db(tmp_path)
    chat = Conversation(client)

    creatine = chat.say("קריאטין בטוח?")
    assert creatine["provider_status"] == "local_tool"
    assert "קריאטין" in creatine["response"]

    meal = chat.say("אכלתי ארוחת ערב: אורז, עוף וסלט")
    assert meal["provider_status"] == "local_tool"
    assert "רשמתי את הארוחה" in meal["response"]
    assert db.scalar(select(Meal)) is not None


def test_simulation_knee_pain_then_squat_question(tmp_path):
    client, db = make_client_and_db(tmp_path)
    chat = Conversation(client)

    pain = chat.say("כואבת לי הברך")
    # Soft pain is advisory, not a hard block, and is recorded for audit.
    assert pain["safety_flagged"] is False
    assert db.scalar(select(SafetyEvent)) is not None

    swap = chat.say("הברך רגישה בסקוואט, במה להחליף?")
    assert swap["provider_status"] == "local_tool"
    assert "סקוואט לקופסה" in swap["response"]
    assert "דדליפט רומני" in swap["response"]


def test_simulation_weight_plateau_then_what_to_change(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    chat = Conversation(client)

    stuck = chat.say("המשקל תקוע כבר שבועיים")
    assert stuck["provider_status"] == "local_tool"
    assert "ממוצע שבועי" in stuck["response"]

    change = chat.say("עליתי 2 קילו, זה שריר או שומן?")
    assert change["provider_status"] == "local_tool"
    assert "שריר" in change["response"]
    # No medical body-composition verdict.
    assert "אבחון" not in change["response"]


def test_simulation_broken_slang_mixed_hebrew_english(tmp_path):
    client, db = make_client_and_db(tmp_path)
    chat = Conversation(client)

    log = chat.say("עשיתי chest day היום")
    assert log["provider_status"] == "local_tool"
    assert "רשמתי את האימון" in log["response"]
    assert db.scalar(select(WorkoutLog)) is not None

    judgment = chat.say("אכלתי המבורגר, זה דופק לי את החיטוב?")
    # Mixed log-looking + question → answered as nutrition guidance, not silently logged.
    assert judgment["provider_status"] == "local_tool"
    assert "מגמה" in judgment["response"] or "טווח" in judgment["response"] or "שבועי" in judgment["response"]
    # Only the workout was logged, the burger question was not stored as a meal.
    assert db.scalar(select(Meal)) is None


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'sim.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
