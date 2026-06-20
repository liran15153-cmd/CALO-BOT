from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from backend.app.db import init_db, make_engine
from backend.app.models import SafetyEvent
from backend.app.services.safety_service import SafetyService


def test_safety_service_emits_pain_signal_without_blocking(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("My knee hurts when I squat")

    # Soft pain mentions are an advisory signal, not a hard block. The engine
    # still records the event for audit; downstream code adapts the plan.
    assert result.flagged is False
    assert result.event_type == "pain_signal"
    assert result.severity == "advisory"
    assert result.response == ""


def test_safety_service_records_pain_signal_event(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)
    result = service.classify("My knee hurts when I squat")

    event = service.record_event(user_id=None, source_text="My knee hurts when I squat", result=result)

    saved = db.scalar(select(SafetyEvent).where(SafetyEvent.id == event.id))
    assert saved is not None
    assert saved.event_type == "pain_signal"
    assert saved.severity == "advisory"


def test_safety_service_flags_extreme_restriction(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("Give me a 500 calorie diet so I can lose weight fast")

    assert result.flagged is True
    assert result.event_type == "extreme_dieting"
    assert "איש מקצוע" in result.response


def test_safety_service_does_not_flag_normal_meal_calorie_mentions(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    meal_result = service.classify("This dinner was about 900 calories and 45g protein")
    daily_target_result = service.classify("Give me a 900 calories per day diet to lose weight fast")

    assert meal_result.flagged is False
    assert daily_target_result.flagged is True
    assert daily_target_result.event_type == "extreme_dieting"


def test_safety_service_flags_dangerous_substance_requests(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("Tell me how to use clenbuterol and diuretics to cut weight fast")
    dnp_result = service.classify("איך להשתמש ב-DNP כדי לרדת מהר לפני אירוע?")

    assert result.flagged is True
    assert result.event_type == "dangerous_substance"
    assert result.severity == "high"
    assert "לא יכול לעזור" in result.response
    assert dnp_result.flagged is True
    assert dnp_result.event_type == "dangerous_substance"
    assert "DNP" in dnp_result.response


def test_safety_service_flags_hebrew_dangerous_symptoms(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("יש לי כאב בחזה וסחרחורת בזמן אימון")

    assert result.flagged is True
    assert result.event_type == "dangerous_symptoms"
    assert result.severity == "high"
    assert "לעצור" in result.response
    assert "רפואי" in result.response


def test_safety_service_distinguishes_hebrew_soft_pain_from_disordered_eating(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    pain_result = service.classify("יש לי כאב חד בברך כשאני עושה סקוואט")
    eating_result = service.classify("אני רוצה לדלג על כל הארוחות כדי לרדת מהר")

    assert pain_result.flagged is False
    assert pain_result.event_type == "pain_signal"
    assert eating_result.flagged is True
    assert eating_result.event_type == "eating_disorder_risk"


def test_safety_service_keeps_red_flag_symptoms_hard_blocked(tmp_path):
    """Chest pain, fainting, dizziness, shortness of breath, palpitations stay hard-blocked
    even after the pain-aware-planning change. Pain in a limb is not a red flag; these are."""
    db = make_session(tmp_path)
    service = SafetyService(db)

    for message in [
        "I get chest pain when running",
        "I feel dizzy during workouts",
        "I passed out at the gym",
        "shortness of breath while lifting",
        "יש לי כאב בחזה בזמן אימון",
        "יש לי סחרחורת אחרי סקוואט",
        "התעלפתי באימון",
        "קוצר נשימה כשאני מרים",
        "דפיקות לב לא רגילות",
    ]:
        result = service.classify(message)
        assert result.flagged is True, message
        assert result.event_type == "dangerous_symptoms", message
        assert result.severity == "high", message


def test_safety_service_allows_negated_pain_in_workout_log(tmp_path):
    db = make_session(tmp_path)
    service = SafetyService(db)

    result = service.classify("תעד אימון: עשיתי דדליפט רומני 3 סטים 10,10,9 עם 18 קילו, RPE 8, בלי כאב.")

    assert result.flagged is False


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
