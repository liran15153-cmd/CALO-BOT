from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import ChatSession, User


def test_chat_session_and_message_persistence(tmp_path):
    client = make_client(tmp_path)

    session_response = client.post("/api/chat/sessions", json={"title": "Plan chat"})
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]

    message_response = client.post(
        "/api/chat/messages",
        json={"session_id": session_id, "role": "user", "content": "Build me a 3-day plan"},
    )
    assert message_response.status_code == 200
    assert message_response.json()["content"] == "Build me a 3-day plan"

    messages = client.get(f"/api/chat/messages?session_id={session_id}")
    assert messages.status_code == 200
    assert messages.json()[0]["role"] == "user"


def test_chat_reset_deactivates_current_session(tmp_path):
    client = make_client(tmp_path)
    session_id = client.post("/api/chat/sessions", json={"title": "Reset me"}).json()["id"]

    response = client.post(f"/api/chat/sessions/{session_id}/reset")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_chat_session_model_default_title_is_hebrew(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'chat-default.db'}")
    init_db(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    user = User(name="משתמש בדיקה")
    db.add(user)
    db.flush()

    session = ChatSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    assert session.title == "צ'אט מאמן"


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'chat.db'}")
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
