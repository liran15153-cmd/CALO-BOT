from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import SafetyEvent, WorkoutLog


def test_workout_log_api_parses_sets_reps_and_weight(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["exercise_results"][0]["exercise"] == "bench press"
    assert body["exercise_results"][0]["reps"] == [10, 8, 7]
    assert body["exercise_results"][0]["weight"] == "50kg"


def test_workout_log_api_parses_user_ordered_sets_reps_weight_and_rpe(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "I did goblet squat 3 sets 8,8,7 with 20kg. RPE 9."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["rpe"] == 9
    assert body["parse_confidence"] == "high"
    assert body["exercise_results"][0]["exercise"] == "goblet squat"
    assert body["exercise_results"][0]["reps"] == [8, 8, 7]
    assert body["exercise_results"][0]["weight"] == "20kg"


def test_workout_log_api_flags_skipped_and_pain(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/api/workout-logs", json={"text": "I skipped squats because my knee hurts"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "skipped"
    assert body["pain_flag"] is True


def test_workout_log_api_records_safety_event_for_dangerous_symptoms_without_pain(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "I felt dizzy during the workout and stopped."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["pain_flag"] is False
    safety_event = db.scalar(select(SafetyEvent))
    assert safety_event is not None
    assert safety_event.event_type == "dangerous_symptoms"
    assert "dizzy" in safety_event.source_text


def test_workout_log_api_does_not_flag_negated_pain(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "עשיתי דדליפט רומני 3 סטים 10,10,9 עם 18 קילו. RPE 8. בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["rpe"] == 8
    assert body["pain_flag"] is False


def test_workout_log_api_parses_hebrew_sets_reps_and_weight(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": 'עשיתי 3 סטים של לחיצת חזה 10, 8, 7 חזרות עם 50 ק"ג'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["exercise_results"][0]["exercise"] == "לחיצת חזה"
    assert body["exercise_results"][0]["reps"] == [10, 8, 7]
    assert body["exercise_results"][0]["weight"] == '50 ק"ג'


def test_next_workout_api_returns_first_workout_without_logs(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=2)

    response = client.get("/api/workouts/next")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == plan["days"][0]["workout_id"]
    assert body["exercises"][0]["exercise_id"] == plan["days"][0]["exercises"][0]["exercise_id"]
    assert body["adaptation"]["load_signal"] == "maintain"
    assert body["execution_plan"]["load_signal"] == "maintain"
    assert body["execution_plan"]["adjusted_exercises"][0]["source_exercise_id"] == plan["days"][0]["exercises"][0]["exercise_id"]
    assert body["execution_plan"]["adjusted_exercises"][0]["sets"] == plan["days"][0]["exercises"][0]["sets"]
    assert body["execution_plan"]["adjusted_exercises"][0]["adjustment"] == "maintain"


def test_next_workout_api_returns_single_session_when_no_current_plan_exists(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build one workout for today",
            "plan_type": "single_session",
            "session_length_minutes": 20,
            "equipment": ["bodyweight"],
        },
    )
    assert response.status_code == 200
    plan = response.json()

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["id"] == plan["days"][0]["workout_id"]
    assert body["plan"]["id"] == plan["id"]


def test_next_workout_api_advances_after_completed_log_without_pain(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=2)
    first_workout_id = plan["days"][0]["workout_id"]

    response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": first_workout_id,
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": plan["days"][0]["exercises"][0]["exercise_id"],
                    "exercise_name": plan["days"][0]["exercises"][0]["name"],
                    "status": "completed",
                    "sets": [
                        {"set_index": 1, "reps": 12, "weight": "20kg", "completed": True},
                        {"set_index": 2, "reps": 12, "weight": "20kg", "completed": True},
                        {"set_index": 3, "reps": 12, "weight": "20kg", "completed": True},
                    ],
                    "rpe": 8,
                    "rir": 2,
                }
            ],
            "rpe": 8,
            "pain_flag": False,
        },
    )
    assert response.status_code == 200

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["id"] == plan["days"][1]["workout_id"]
    assert body["execution_plan"]["load_signal"] == "progress_candidate"
    assert body["execution_plan"]["adjusted_exercises"][0]["adjustment"] == "small_progression"
    assert body["execution_plan"]["adjusted_exercises"][0]["sets"] == plan["days"][1]["exercises"][0]["sets"]
    assert "התקדמות קטנה" in body["execution_plan"]["summary"]


def test_next_workout_api_repeats_after_skipped_or_pain_log(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=2)
    first_workout_id = plan["days"][0]["workout_id"]

    skipped = client.post(
        "/api/workout-logs",
        json={"workout_id": first_workout_id, "status": "skipped", "notes": "No time today"},
    )
    assert skipped.status_code == 200

    skipped_next = client.get("/api/workouts/next")
    assert skipped_next.status_code == 200
    assert skipped_next.json()["id"] == first_workout_id
    assert skipped_next.json()["adaptation"]["load_signal"] == "adherence_risk"
    skipped_body = skipped_next.json()
    assert skipped_body["execution_plan"]["load_signal"] == "adherence_risk"
    assert skipped_body["execution_plan"]["adjusted_exercises"][0]["sets"] == "2"
    assert len(skipped_body["execution_plan"]["adjusted_exercises"]) <= 3
    assert "גרסת מינימום" in skipped_body["execution_plan"]["summary"]

    pain = client.post(
        "/api/workout-logs",
        json={
            "workout_id": first_workout_id,
            "status": "partial",
            "pain_flag": True,
            "notes": "Knee pain during squats",
        },
    )
    assert pain.status_code == 200

    pain_next = client.get("/api/workouts/next")
    assert pain_next.status_code == 200
    pain_body = pain_next.json()
    assert pain_body["id"] == first_workout_id
    assert pain_body["adaptation"]["load_signal"] == "pain_caution"
    assert pain_body["execution_plan"]["load_signal"] == "pain_caution"
    assert pain_body["execution_plan"]["adjusted_exercises"][0]["adjustment"] == "reduce_or_swap"
    assert "ללא כאב" in pain_body["execution_plan"]["adjusted_exercises"][0]["notes"]


def test_next_workout_api_repeats_after_partial_or_modified_log_without_pain(tmp_path):
    client = make_client(tmp_path)
    for status in ["partial", "modified"]:
        plan = create_plan(client, days_per_week=2)
        if not plan["is_current"]:
            activate_response = client.post(f"/api/workout-plans/{plan['id']}/activate", json={"delete_previous": True})
            assert activate_response.status_code == 200
            plan = activate_response.json()
        first_workout_id = plan["days"][0]["workout_id"]

        log_response = client.post(
            "/api/workout-logs",
            json={"workout_id": first_workout_id, "status": status, "notes": f"{status} session, no pain"},
        )
        assert log_response.status_code == 200

        next_response = client.get("/api/workouts/next")

        assert next_response.status_code == 200
        assert next_response.json()["id"] == first_workout_id
        assert next_response.json()["adaptation"]["load_signal"] == "adherence_risk"


def test_next_workout_execution_plan_reduces_after_high_rpe_log(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    workout_id = plan["days"][0]["workout_id"]
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": exercise["exercise_id"],
                    "exercise_name": exercise["name"],
                    "status": "completed",
                    "sets": [
                        {"set_index": 1, "reps": 8, "completed": True},
                        {"set_index": 2, "reps": 7, "completed": True},
                    ],
                    "rpe": 10,
                    "rir": 0,
                }
            ],
            "rpe": 10,
        },
    )
    assert log_response.status_code == 200

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    execution = next_response.json()["execution_plan"]
    assert execution["load_signal"] == "recovery_needed"
    assert execution["adjusted_exercises"][0]["sets"] == "2"
    assert execution["adjusted_exercises"][0]["adjustment"] == "reduce_or_hold"
    assert "התאוששות" in execution["summary"]


def test_structured_workout_log_api_persists_exercises_sets_rpe_rir_and_pain_safety(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan = create_plan(client, days_per_week=1)
    workout_id = plan["days"][0]["workout_id"]
    exercise = plan["days"][0]["exercises"][0]

    response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "status": "modified",
            "logged_on": "2026-06-20",
            "exercises": [
                {
                    "exercise_id": exercise["exercise_id"],
                    "exercise_name": exercise["name"],
                    "status": "partial",
                    "sets": [
                        {"set_index": 1, "reps": 10, "weight": "18kg", "completed": True},
                        {"set_index": 2, "reps": 6, "weight": "18kg", "completed": False},
                    ],
                    "rpe": 9,
                    "rir": 0,
                    "notes": "Stopped when knee pain started",
                }
            ],
            "rpe": 9,
            "rir": 0,
            "pain_flag": True,
            "notes": "Knee pain started in set 2",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["workout_id"] == workout_id
    assert body["status"] == "modified"
    assert body["rpe"] == 9
    assert body["pain_flag"] is True
    assert body["exercise_results"][0]["exercise_id"] == exercise["exercise_id"]
    assert body["exercise_results"][0]["exercise_name"] == exercise["name"]
    assert body["exercise_results"][0]["sets"][1]["completed"] is False
    assert body["exercise_results"][0]["rir"] == 0
    assert body["adaptation"]["load_signal"] == "pain_caution"

    saved = db.scalar(select(WorkoutLog).order_by(WorkoutLog.id.desc()))
    assert saved is not None
    assert saved.workout_id == workout_id
    assert saved.status == "modified"
    assert saved.exercise_results[0]["sets"][0]["weight"] == "18kg"

    safety_event = db.scalar(select(SafetyEvent))
    assert safety_event is not None


def test_structured_workout_log_uses_exercise_notes_as_safety_source(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan = create_plan(client, days_per_week=1)
    workout_id = plan["days"][0]["workout_id"]
    exercise = plan["days"][0]["exercises"][0]

    response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "status": "partial",
            "exercises": [
                {
                    "exercise_id": exercise["exercise_id"],
                    "exercise_name": exercise["name"],
                    "status": "partial",
                    "sets": [{"set_index": 1, "reps": 4, "completed": False}],
                    "notes": "Sharp knee pain on the first set",
                }
            ],
        },
    )

    assert response.status_code == 200
    safety_event = db.scalar(select(SafetyEvent))
    assert safety_event is not None
    assert "Sharp knee pain" in safety_event.source_text


def test_structured_workout_log_rejects_unknown_or_mismatched_workout_and_exercise_ids(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    workout_id = plan["days"][0]["workout_id"]
    exercise_id = plan["days"][0]["exercises"][0]["exercise_id"]

    unknown_workout = client.post(
        "/api/workout-logs",
        json={"workout_id": 999999, "status": "completed", "notes": "Done"},
    )
    assert unknown_workout.status_code == 400

    mismatched_exercise = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": exercise_id + 999999,
                    "exercise_name": "Unknown exercise",
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                }
            ],
        },
    )
    assert mismatched_exercise.status_code == 400


def test_recent_workout_logs_returns_saved_logs_ordered_newest_first(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    workout_id = plan["days"][0]["workout_id"]
    exercise = plan["days"][0]["exercises"][0]

    older = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "logged_on": "2026-06-18",
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": exercise["exercise_id"],
                    "exercise_name": exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "weight": "20kg", "completed": True}],
                    "rpe": 8,
                }
            ],
            "rpe": 8,
            "pain_flag": False,
        },
    )
    newer = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "logged_on": "2026-06-20",
            "status": "partial",
            "pain_flag": True,
            "notes": "Shoulder discomfort on presses",
        },
    )
    assert older.status_code == 200
    assert newer.status_code == 200

    response = client.get("/api/workout-logs/recent")

    assert response.status_code == 200
    body = response.json()
    assert [log["logged_on"] for log in body[:2]] == ["2026-06-20", "2026-06-18"]
    assert body[0]["status"] == "partial"
    assert body[0]["pain_flag"] is True
    assert body[0]["notes"] == "Shoulder discomfort on presses"
    assert body[1]["exercise_results"][0]["exercise_id"] == exercise["exercise_id"]
    assert body[1]["exercise_results"][0]["sets"][0]["reps"] == 10
    assert body[1]["rpe"] == 8


def create_plan(client: TestClient, days_per_week: int) -> dict:
    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a simple dumbbell plan",
            "days_per_week": days_per_week,
            "equipment": ["dumbbells"],
        },
    )
    assert response.status_code == 200
    return response.json()


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'logs.db'}")
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


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'structured_logs.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db
