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
    assert any("אימונים קצרים" in memory.content for memory in saved)
    assert any("משקולות יד" in memory.content for memory in saved)
    assert any("אחרי העבודה" in memory.content for memory in saved)


def test_memory_service_extracts_hebrew_preferences_and_limitations(tmp_path):
    db = make_session(tmp_path)
    service = MemoryService(db)

    memories = service.extract_and_store(
        user_id=1,
        source_text=(
            "תזכור שאני מעדיף אימונים קצרים אחרי העבודה, יש לי משקולות יד "
            "וגומיות התנגדות, אני לא אוהב ריצה, בלי קפיצות ויש רגישות ברך בסקוואט."
        ),
    )

    saved = db.scalars(select(UserMemory)).all()
    contents = [memory.content for memory in saved]
    types = [memory.memory_type for memory in saved]

    assert len(memories) >= 6
    assert "preference" in types
    assert "schedule" in types
    assert "equipment" in types
    assert "safety_limitation" in types
    assert any("אימונים קצרים" in content for content in contents)
    assert any("אחרי העבודה" in content for content in contents)
    assert any("משקולות יד" in content for content in contents)
    assert any("גומיות התנגדות" in content for content in contents)
    assert any("לא אוהב ריצה" in content for content in contents)
    assert any("בלי קפיצות" in content for content in contents)
    knee_memory = next(memory for memory in saved if memory.memory_type == "safety_limitation")
    assert knee_memory.is_sensitive is True
    assert "ברך" in knee_memory.content


def test_memory_service_extracts_feminine_lactose_sensitivity(tmp_path):
    db = make_session(tmp_path)
    service = MemoryService(db)

    memories = service.extract_and_store(user_id=1, source_text="אני רגישה ללקטוז, תתייחסי לזה.")

    assert len(memories) == 1
    saved = db.scalars(select(UserMemory)).all()
    assert saved[0].memory_type == "nutrition"
    assert "לקטוז" in saved[0].content


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
