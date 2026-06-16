from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from backend.app.db import init_db, make_engine
from backend.app.models import UserMemory
from backend.app.services.memory_service import MemoryService


def test_memory_service_extracts_durable_preferences(tmp_path):
    db = make_session(tmp_path)
    service = MemoryService(db)

    memories = service.extract_and_store(
        user_id=1,
        source_text="I prefer short workouts after work and I have dumbbells at home.",
    )

    assert len(memories) == 3
    saved = db.scalars(select(UserMemory)).all()
    assert any("short workouts" in memory.content for memory in saved)
    assert any("dumbbells" in memory.content for memory in saved)
    assert any("after work" in memory.content for memory in saved)


def test_memory_service_ignores_non_durable_chat(tmp_path):
    db = make_session(tmp_path)
    service = MemoryService(db)

    memories = service.extract_and_store(user_id=1, source_text="That sounds good, thanks")

    assert memories == []
    assert db.scalars(select(UserMemory)).all() == []


def make_session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'memory.db'}")
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()

