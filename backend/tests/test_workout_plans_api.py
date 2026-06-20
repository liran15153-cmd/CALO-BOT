from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import Workout, WorkoutExercise, WorkoutLog, WorkoutPlan


def test_workout_plan_api_generates_and_saves_structured_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 3-day gym plan for muscle", "days_per_week": 3, "equipment": ["dumbbells"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["days_per_week"] == 3
    assert body["days"][0]["exercises"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["days"][0]["exercises"][0]["name"]
    saved_workout = db.scalar(select(Workout))
    assert saved_workout is not None
    assert saved_workout.plan_id == saved.id
    saved_exercise = db.scalar(select(WorkoutExercise))
    assert saved_exercise is not None
    assert saved_exercise.workout_id == saved_workout.id


def test_workout_plan_api_returns_current_plan(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/workout-plans", json={"prompt": "Create a home dumbbell plan", "days_per_week": 2})

    response = client.get("/api/workout-plans/current")

    assert response.status_code == 200
    assert response.json()["is_current"] is True


def test_workout_plan_uses_saved_profile_when_request_is_open_ended(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/workout-plans", json={"prompt": "Create a safe starter plan"})

    assert response.status_code == 200
    body = response.json()
    assert body["days_per_week"] == 2
    assert body["equipment_needed"] == ["resistance bands"]
    assert body["days"][0]["name"].startswith("יום שלישי")
    assert "המגבלה שתועדה בפרופיל" in body["recovery_note"]


def test_workout_plan_uses_coaching_principles_for_full_body_structure(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית אימון של 2 ימים לשיפור כוח", "days_per_week": 2, "equipment": ["dumbbells"]},
    )

    assert response.status_code == 200
    body = response.json()
    first_day = body["days"][0]
    exercise_names = " ".join(exercise["name"] for exercise in first_day["exercises"])
    exercise_notes = " ".join(exercise["notes"] for exercise in first_day["exercises"])

    assert len(first_day["exercises"]) >= 4
    assert "לחיצ" in exercise_names or "שכיבת סמיכה" in exercise_names
    assert "חתירה" in exercise_names
    assert "ליבה" in exercise_names or "פלאנק" in exercise_names
    assert "שתי חזרות ברזרבה" in exercise_notes
    assert "עומס" in body["progression_rule"]
    assert any("כאב חד" in note for note in first_day["exercises"][0]["safety_notes"])


def test_workout_plan_adjusts_training_variables_by_goal(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    strength_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 2-day strength plan", "days_per_week": 2, "equipment": ["dumbbells"]},
    )
    muscle_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 2-day muscle plan", "days_per_week": 2, "equipment": ["dumbbells"]},
    )
    fat_loss_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 2-day fat loss plan", "days_per_week": 2, "equipment": ["dumbbells"]},
    )

    assert strength_response.status_code == 200
    assert muscle_response.status_code == 200
    assert fat_loss_response.status_code == 200

    strength = strength_response.json()
    muscle = muscle_response.json()
    fat_loss = fat_loss_response.json()

    assert strength["days"][0]["exercises"][0]["reps_or_duration"] == "4-6 חזרות"
    assert strength["days"][0]["exercises"][0]["rest"] == "120 שניות"
    assert muscle["days"][0]["exercises"][0]["reps_or_duration"] == "8-12 חזרות"
    assert "נפח" in muscle["progression_rule"]
    assert "אירובי קל" in fat_loss["days"][0]["notes"]
    assert "דיאטת קיצון" in fat_loss["recovery_note"]


def test_workout_plan_api_builds_source_backed_four_week_upper_lower_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post(
        "/api/onboarding",
        json={
            **valid_payload(),
            "experience_level": "intermediate",
            "weekly_availability": 4,
            "session_length_minutes": 50,
        },
    )

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four week intermediate strength plan",
            "days_per_week": 4,
            "duration_weeks": 4,
            "session_length_minutes": 50,
            "equipment": ["dumbbells", "bench"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan_type"] == "multi_week"
    assert body["duration_weeks"] == 4
    assert body["training_split"] == "upper_lower"
    assert body["experience_level"] == "intermediate"
    assert body["decision_inputs"]["duration_weeks"] == 4
    assert any("ACSM 2026 resistance training guidelines" in source for source in body["source_refs"])
    assert {day["focus"] for day in body["days"]} == {"upper_body", "lower_body"}
    assert all(day["estimated_duration_minutes"] <= 50 for day in body["days"])

    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["training_split"] == "upper_lower"
    assert saved.plan_json["source_refs"]
    assert len(db.scalars(select(Workout)).all()) == 4


def test_single_session_plan_is_saved_without_replacing_current_multi_week_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day month plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "I only have 20 minutes today and slept badly. Build one workout for today.",
            "plan_type": "single_session",
            "session_length_minutes": 20,
            "equipment": ["bodyweight"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan_type"] == "single_session"
    assert body["duration_weeks"] == 1
    assert body["days_per_week"] == 1
    assert len(body["days"]) == 1
    assert body["days"][0]["estimated_duration_minutes"] <= 20
    assert "single session" in body["decision_inputs"]["plan_type"]
    assert any("recovery" in note.lower() or "reduce" in note.lower() for note in body["safety_notes"])

    current_after = db.get(WorkoutPlan, current_id)
    assert current_after is not None
    assert current_after.is_current is True
    one_off = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert one_off is not None
    assert one_off.is_current is False


def test_single_session_plan_uses_recent_training_status_to_reduce_load(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    user_plan_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    db.add(
        WorkoutLog(
            user_id=1,
            workout_id=None,
            logged_on=__import__("datetime").date.today(),
            status="completed",
            exercise_results=[],
            rpe=9,
            notes="Very hard session",
            pain_flag=False,
            parse_confidence="medium",
        )
    )
    db.commit()

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build one workout for today",
            "plan_type": "single_session",
            "session_length_minutes": 30,
            "equipment": ["bodyweight"],
        },
    )

    assert user_plan_response.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["decision_inputs"]["training_status"]["load_signal"] == "recovery_needed"
    assert any("Reduce" in note or "recovery" in note.lower() for note in body["safety_notes"])
    assert body["days"][0]["exercises"][0]["sets"] == "2"


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'plans.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db


def valid_payload():
    return {
        "name": "Lior",
        "main_goal": "improve_strength",
        "experience_level": "beginner",
        "training_location": "home",
        "available_equipment": ["resistance bands"],
        "weekly_availability": 2,
        "session_length_minutes": 30,
        "preferred_workout_days": ["Tuesday", "Friday"],
        "injuries_limitations": "Avoid deep knee flexion",
        "coaching_style": "direct",
        "consent_disclaimer": True,
    }
