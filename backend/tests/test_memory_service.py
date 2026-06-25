from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import MemoryFact
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.memory_service import MemoryService
from backend.app.services.profile_service import ProfileService


def test_memory_service_persists_hebrew_allergy_and_injects_safety_context(tmp_path):
    db = make_session(tmp_path)
    user = ProfileService(db).get_default_user()
    text = "אני אלרגי לבוטנים"

    saved = MemoryService(db).process_user_message(user_id=user.id, text=text)
    context = ContextBuilder(db).build(user_id=user.id, intent="workout_plan")

    assert len(saved) == 1
    assert saved[0].fact_type == "allergy"
    assert saved[0].salience == 1.0
    assert any("בוטנים" in fact["text_he"] for fact in context["memory_safety"])


def test_memory_service_ignores_hypothetical_allergy_trap(tmp_path):
    db = make_session(tmp_path)
    user = ProfileService(db).get_default_user()

    saved = MemoryService(db).process_user_message(user_id=user.id, text="אם הייתי אלרגי לבוטנים מה הייתי עושה?")

    assert saved == []
    assert db.scalars(select(MemoryFact)).all() == []


def test_memory_service_negated_allergy_does_not_suppress_real_injury(tmp_path):
    db = make_session(tmp_path)
    user = ProfileService(db).get_default_user()

    saved = MemoryService(db).process_user_message(user_id=user.id, text="אני לא אלרגי לבוטנים, אבל יש לי כאב ברך")

    assert [fact.fact_type for fact in saved] == ["injury"]
    facts = db.scalars(select(MemoryFact)).all()
    assert len(facts) == 1
    assert facts[0].fact_type == "injury"
    assert "כאב ברך" in facts[0].text_he


def test_memory_service_does_not_treat_hebrew_cannot_train_as_food_restriction(tmp_path):
    db = make_session(tmp_path)
    user = ProfileService(db).get_default_user()
    service = MemoryService(db)

    assert service.process_user_message(user_id=user.id, text="לא אוכל להתאמן השבוע") == []
    saved = service.process_user_message(user_id=user.id, text="אני לא אוכל גלוטן")

    assert [fact.fact_type for fact in saved] == ["restriction_nutrition"]
    facts = db.scalars(select(MemoryFact)).all()
    assert len(facts) == 1
    assert "גלוטן" in facts[0].text_he


def test_memory_service_does_not_store_low_protein_as_food_restriction(tmp_path):
    db = make_session(tmp_path)
    user = ProfileService(db).get_default_user()

    saved = MemoryService(db).process_user_message(user_id=user.id, text="אני לא אוכל מספיק חלבון")

    assert saved == []
    assert db.scalars(select(MemoryFact)).all() == []


def test_memory_service_does_not_store_negated_pain_as_injury(tmp_path):
    db = make_session(tmp_path)
    user = ProfileService(db).get_default_user()
    service = MemoryService(db)

    assert service.process_user_message(user_id=user.id, text="Log workout: RPE 7, no pain.") == []
    saved = service.process_user_message(user_id=user.id, text="No pain today after a knee injury last month.")

    assert [fact.fact_type for fact in saved] == ["injury"]
    facts = db.scalars(select(MemoryFact)).all()
    assert len(facts) == 1
    assert "knee injury" in facts[0].text_he


def test_memory_service_dedups_repeated_safety_fact(tmp_path):
    db = make_session(tmp_path)
    user = ProfileService(db).get_default_user()
    service = MemoryService(db)

    service.process_user_message(user_id=user.id, text="אני אלרגי לבוטנים")
    service.process_user_message(user_id=user.id, text="אני אלרגי לבוטנים")

    facts = db.scalars(select(MemoryFact)).all()
    assert len(facts) == 1
    assert facts[0].status == "active"


def test_chat_turn_stores_allergy_for_next_turn_context(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "אני אלרגי לבוטנים"})
    user = ProfileService(db).get_existing_default_user()
    assert user is not None
    context = ContextBuilder(db).build(user_id=user.id, intent="general_chat")

    assert response.status_code == 200
    assert any("בוטנים" in fact["text_he"] for fact in context["memory_safety"])


def make_session(tmp_path) -> Session:
    engine = make_engine(f"sqlite:///{tmp_path / 'memory.db'}")
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'memory-api.db'}")
    init_db(engine)
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)
    db = testing_session_local()

    def override_db() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
