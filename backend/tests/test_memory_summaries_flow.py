from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import MemorySummary, User, UserMemory
from backend.app.services.context_builder import ContextBuilder


def test_chat_flow_writes_and_reuses_long_term_memory_summary(tmp_path):
    client, db = make_client_and_db(tmp_path)

    first = client.post(
        "/api/chat",
        json={"message": "I prefer short workouts after work with dumbbells"},
    )
    assert first.status_code == 200

    user_id = db.scalar(select(User.id))
    assert user_id is not None
    assert db.scalar(select(func.count(UserMemory.id)).where(UserMemory.user_id == user_id)) == 3

    summary = db.scalar(select(MemorySummary).where(MemorySummary.user_id == user_id))
    assert summary is not None
    assert summary.summary_type == "long_term"
    assert "short workouts" in summary.content
    assert "after work" in summary.content
    assert "dumbbells" in summary.content
    assert summary.source_range_json["memory_count"] == 3

    second_session = client.post("/api/chat/sessions", json={"title": "Fresh context"}).json()
    context = ContextBuilder(db).build(user_id=user_id, session_id=second_session["id"], intent="general_chat")

    assert context["memory_summaries"] == [summary.content]
    assert "short workouts" in str(context)


def test_long_term_memory_summary_updates_existing_row_instead_of_duplicating(tmp_path):
    client, db = make_client_and_db(tmp_path)

    assert client.post("/api/chat", json={"message": "I prefer short workouts after work with dumbbells"}).status_code == 200
    assert client.post("/api/chat", json={"message": "I also avoid dairy and prefer direct coaching"}).status_code == 200

    user_id = db.scalar(select(User.id))
    summaries = db.scalars(select(MemorySummary).where(MemorySummary.user_id == user_id)).all()

    assert len(summaries) == 1
    assert "short workouts" in summaries[0].content
    assert "direct coaching" in summaries[0].content
    assert summaries[0].source_range_json["memory_count"] >= 4


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'memory-summary.db'}")
    init_db(engine)
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)
    db = testing_session_local()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
