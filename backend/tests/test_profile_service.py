from sqlalchemy.orm import sessionmaker

from backend.app.db import init_db, make_engine
from backend.app.schemas import OnboardingPayload
from backend.app.services.profile_service import ProfileService


def make_session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'profile.db'}")
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def valid_payload(**overrides):
    data = {
        "name": "Lior",
        "age_range": "30-39",
        "gender": "prefer_not_to_say",
        "height_cm": 178,
        "weight_kg": 82,
        "main_goal": "build_muscle",
        "experience_level": "beginner",
        "training_location": "gym",
        "available_equipment": ["dumbbells", "barbell"],
        "weekly_availability": 3,
        "session_length_minutes": 45,
        "preferred_workout_days": ["Monday", "Wednesday", "Friday"],
        "injuries_limitations": "",
        "nutrition_preference": "high_protein",
        "foods_disliked": "running gels",
        "allergies": "",
        "typical_schedule": "after work",
        "coaching_style": "direct",
        "consent_disclaimer": True,
    }
    data.update(overrides)
    return OnboardingPayload(**data)


def test_profile_service_creates_default_user_and_profile(tmp_path):
    db = make_session(tmp_path)
    service = ProfileService(db)

    profile = service.upsert_onboarding(valid_payload())

    assert profile.user.name == "Lior"
    assert profile.main_goal == "build_muscle"
    assert profile.available_equipment == ["dumbbells", "barbell"]
    assert profile.consent_disclaimer is True


def test_profile_service_updates_existing_local_profile(tmp_path):
    db = make_session(tmp_path)
    service = ProfileService(db)

    first = service.upsert_onboarding(valid_payload(name="Lior", main_goal="build_muscle"))
    second = service.upsert_onboarding(valid_payload(name="Lee", main_goal="improve_strength"))

    assert first.id == second.id
    assert second.user.name == "Lee"
    assert second.main_goal == "improve_strength"

