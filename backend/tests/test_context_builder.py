from sqlalchemy.orm import sessionmaker

from backend.app.db import init_db, make_engine
from backend.app.models import ChatMessage, ChatSession, UserMemory
from backend.app.schemas import OnboardingPayload
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.profile_service import ProfileService


def test_context_builder_uses_compact_context_not_full_chat_history(tmp_path):
    db = make_session(tmp_path)
    profile_service = ProfileService(db)
    profile = profile_service.upsert_onboarding(valid_payload())
    session = ChatSession(user_id=profile.user_id, title="test")
    db.add(session)
    db.commit()
    db.refresh(session)

    for index in range(8):
      db.add(ChatMessage(session_id=session.id, user_id=profile.user_id, role="user", content=f"turn {index}"))
    db.add(UserMemory(user_id=profile.user_id, memory_type="preference", content="User prefers short workouts"))
    db.commit()

    context = ContextBuilder(db).build(user_id=profile.user_id, session_id=session.id)

    assert context["profile"]["main_goal"] == "build_muscle"
    assert context["memories"] == ["User prefers short workouts"]
    assert len(context["recent_chat"]) == 4
    assert "turn 0" not in str(context)
    assert "turn 7" in str(context)


def test_context_builder_filters_memories_for_intent(tmp_path):
    db = make_session(tmp_path)
    profile_service = ProfileService(db)
    profile = profile_service.upsert_onboarding(valid_payload())
    db.add_all(
        [
            UserMemory(user_id=profile.user_id, memory_type="equipment", content="User has access to dumbbells"),
            UserMemory(user_id=profile.user_id, memory_type="nutrition", content="User avoids dairy"),
            UserMemory(user_id=profile.user_id, memory_type="schedule", content="User trains after work"),
        ]
    )
    db.commit()

    context = ContextBuilder(db).build(user_id=profile.user_id, intent="meal_log")

    assert "User avoids dairy" in context["memories"]
    assert "User has access to dumbbells" not in context["memories"]


def make_session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'context.db'}")
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def valid_payload():
    return OnboardingPayload(
        name="Lior",
        main_goal="build_muscle",
        experience_level="beginner",
        training_location="gym",
        available_equipment=["dumbbells"],
        weekly_availability=3,
        session_length_minutes=45,
        preferred_workout_days=["Monday"],
        coaching_style="direct",
        consent_disclaimer=True,
    )
