from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from backend.app.db import init_db, make_engine
from backend.app.models import SafetyEvent
from backend.app.services.safety_service import SafetyService


def test_safety_service_flags_pain_and_responds_conservatively(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("My knee hurts when I squat")

    assert result.flagged is True
    assert result.event_type == "pain_or_injury"
    assert "stop" in result.response.lower()


def test_safety_service_flags_extreme_restriction(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("Give me a 500 calorie diet so I can lose weight fast")

    assert result.flagged is True
    assert result.event_type == "extreme_dieting"
    assert "qualified" in result.response.lower()


def test_safety_service_records_safety_event(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)
    result = service.classify("I feel dizzy and faint during workouts")

    event = service.record_event(user_id=None, source_text="I feel dizzy and faint during workouts", result=result)

    saved = db.scalar(select(SafetyEvent).where(SafetyEvent.id == event.id))
    assert saved is not None
    assert saved.event_type == "dangerous_symptoms"
    assert saved.severity == "high"


def test_safety_service_allows_normal_training_question(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("Can you build a beginner dumbbell workout?")

    assert result.flagged is False
    assert result.event_type is None


def make_session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'safety.db'}")
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()

