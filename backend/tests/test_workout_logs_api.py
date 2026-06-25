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


def test_workout_log_api_marks_negated_workout_as_skipped(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/api/workout-logs", json={"text": "Log workout: I did not work out yesterday"})

    assert response.status_code == 200
    assert response.json()["status"] == "skipped"


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


def test_workout_log_api_parses_natural_hebrew_effort_as_rpe(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "עשיתי לחיצת חזה 3 סטים 10,8,7 חזרות. מאמץ 8 מתוך 10, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["rpe"] == 8
    assert body["pain_flag"] is False


def test_workout_log_api_parses_hebrew_gym_shorthand_sets_reps_and_effort(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "עשיתי לחיצת חזה 3x10 עם 50 ק״ג. מאמץ 8 מתוך 10, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["parse_confidence"] == "high"
    assert body["rpe"] == 8
    assert body["pain_flag"] is False
    assert body["exercise_results"][0]["exercise"] == "לחיצת חזה"
    assert body["exercise_results"][0]["sets"] == 3
    assert body["exercise_results"][0]["reps"] == [10, 10, 10]
    assert body["exercise_results"][0]["weight"] == "50 ק״ג"


def test_workout_log_api_parses_natural_hebrew_controlled_effort(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={"text": "עשיתי לחיצת חזה 3x10 עם 50 ק״ג. היה מאתגר אבל בשליטה, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rpe"] is None
    assert "rir" not in body["exercise_results"][0]
    assert body["exercise_results"][0]["effort_signal"] == "controlled"
    assert body["parse_confidence"] == "high"


def test_workout_log_api_parses_hebrew_rir_as_exercise_level_evidence(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-logs",
        json={
            "text": (
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10 \u05e2\u05dd 50 \u05e7\u05f4\u05d2. "
                "\u05e0\u05e9\u05d0\u05e8\u05d5 \u05dc\u05d9 2 \u05d7\u05d6\u05e8\u05d5\u05ea "
                "\u05d1\u05e8\u05d6\u05e8\u05d1\u05d4, \u05d1\u05dc\u05d9 \u05db\u05d0\u05d1."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["parse_confidence"] == "high"
    assert body["rpe"] is None
    assert body["pain_flag"] is False
    result = body["exercise_results"][0]
    assert result["exercise"] == "\u05dc\u05d7\u05d9\u05e6\u05ea \u05d7\u05d6\u05d4"
    assert result["sets"] == 3
    assert result["reps"] == [10, 10, 10]
    assert result["weight"] == "50 \u05e7\u05f4\u05d2"
    assert result["rir"] == 2


def test_next_workout_uses_free_text_hebrew_rir_for_progression(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": (
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10 \u05e2\u05dd 50 \u05e7\u05f4\u05d2. "
                "\u05e0\u05e9\u05d0\u05e8\u05d5 \u05dc\u05d9 2 \u05d7\u05d6\u05e8\u05d5\u05ea "
                "\u05d1\u05e8\u05d6\u05e8\u05d1\u05d4, \u05d1\u05dc\u05d9 \u05db\u05d0\u05d1."
            ),
        },
    )
    assert log_response.status_code == 200
    assert log_response.json()["rpe"] is None
    assert log_response.json()["exercise_results"][0]["rir"] == 2

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["load_signal"] == "progress_candidate"
    assert body["adaptation"]["progress_evidence"] == "exercise_log"
    assert body["execution_plan"]["load_signal"] == "progress_candidate"
    assert "RPE/RIR" in body["execution_plan"]["adjusted_exercises"][0]["execution_note"]


def test_next_workout_treats_free_text_zero_rir_as_recovery_needed(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": (
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10. RIR 0, \u05d1\u05dc\u05d9 "
                "\u05db\u05d0\u05d1."
            ),
        },
    )
    assert log_response.status_code == 200
    assert log_response.json()["exercise_results"][0]["rir"] == 0

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["load_signal"] == "recovery_needed"
    assert body["adaptation"]["exercise_adjustments"][0]["reason"] == "near_failure_rir"
    assert body["execution_plan"]["load_signal"] == "recovery_needed"
    assert "RPE/RIR" in body["execution_plan"]["adjusted_exercises"][0]["execution_note"]
    assert "\u05dc\u05d4\u05d5\u05e1\u05d9\u05e3 \u05d7\u05d6\u05e8\u05d4" not in body["execution_plan"]["adjusted_exercises"][0]["execution_note"]


def test_next_workout_uses_free_text_high_rir_for_underload_progression(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": f"עשיתי {exercise['name']} 3x10. RIR 5, בלי כאב.",
        },
    )
    assert log_response.status_code == 200
    assert log_response.json()["exercise_results"][0]["rir"] == 5

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["load_signal"] == "progress_candidate"
    assert body["adaptation"]["exercise_adjustments"][0]["reason"] == "high_rir_underload"
    first = body["execution_plan"]["adjusted_exercises"][0]
    assert first["adjustment"] == "small_progression"
    assert "RIR 1-3" in first["execution_note"]
    assert "\u05dc\u05d0 \u05dc\u05e7\u05e4\u05d5\u05e5" in first["execution_note"]


def test_next_workout_uses_natural_hebrew_underload_without_fake_rir(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": f"עשיתי {exercise['name']} 3x10. היה קל מדי, נשאר לי מלא כוח, בלי כאב.",
        },
    )

    assert log_response.status_code == 200
    logged = log_response.json()
    assert logged["rpe"] is None
    assert "rir" not in logged["exercise_results"][0]
    assert logged["exercise_results"][0]["effort_signal"] == "underloaded"
    assert logged["parse_confidence"] == "high"

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["load_signal"] == "progress_candidate"
    assert body["adaptation"]["exercise_adjustments"][0]["reason"] == "qualitative_underload"
    first = body["execution_plan"]["adjusted_exercises"][0]
    assert "קל מדי" in first["execution_note"]
    assert "RIR" not in first["execution_note"]
    assert "RPE/RIR" not in first["notes"]


def test_next_workout_uses_controlled_verbal_effort_without_fake_metrics(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    exercise = plan["days"][0]["exercises"][0]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": plan["days"][0]["workout_id"],
            "text": f"עשיתי {exercise['name']} 3x10. היה מאתגר אבל בשליטה, בלי כאב.",
        },
    )

    assert log_response.status_code == 200
    logged = log_response.json()
    assert logged["rpe"] is None
    assert logged["exercise_results"][0].get("rir") is None
    assert logged["exercise_results"][0]["effort_signal"] == "controlled"

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["load_signal"] == "maintain"
    assert body["adaptation"]["exercise_adjustments"][0]["reason"] == "qualitative_controlled_effort"
    first = body["execution_plan"]["adjusted_exercises"][0]
    assert first["adjustment"] == "maintain"
    assert "בשליטה" in first["execution_note"]
    assert "RPE 1-10" in first["execution_note"]
    assert "מעלים עומס" in first["execution_note"]
    assert "RPE/RIR" not in first["notes"]


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


def test_next_workout_api_does_not_treat_single_workout_as_current_plan(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build one workout for today",
            "plan_type": "single_workout",
            "session_length_minutes": 20,
            "equipment": ["bodyweight"],
        },
    )
    assert response.status_code == 200
    plan = response.json()
    assert plan["is_current"] is False

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 404
    assert "אין תוכנית פעילה" in next_response.json()["detail"]


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


def test_next_workout_progresses_logged_exercise_not_first_by_default(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    workout_id = plan["days"][0]["workout_id"]
    first_exercise = plan["days"][0]["exercises"][0]
    second_exercise = plan["days"][0]["exercises"][1]

    response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": second_exercise["exercise_id"],
                    "exercise_name": second_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 12, "completed": True}],
                    "rpe": 8,
                    "rir": 2,
                }
            ],
            "pain_flag": False,
        },
    )
    assert response.status_code == 200

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["progress_evidence"] == "exercise_log"
    adjusted = body["execution_plan"]["adjusted_exercises"]
    first_adjusted = next(exercise for exercise in adjusted if exercise["source_exercise_id"] == first_exercise["exercise_id"])
    second_adjusted = next(exercise for exercise in adjusted if exercise["source_exercise_id"] == second_exercise["exercise_id"])
    assert first_adjusted["adjustment"] == "maintain"
    assert second_adjusted["adjustment"] == "small_progression"


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
    assert skipped_body["execution_plan"]["adjusted_exercises"][0]["sets"] == reduced_sets(plan["days"][0]["exercises"][0]["sets"])
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


def test_next_workout_api_surfaces_plan_adjustment_after_repeated_misses(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=3)

    first_workout_id = plan["days"][0]["workout_id"]
    second_workout_id = plan["days"][1]["workout_id"]

    first_log = client.post(
        "/api/workout-logs",
        json={"workout_id": first_workout_id, "status": "skipped", "notes": "No time"},
    )
    second_log = client.post(
        "/api/workout-logs",
        json={"workout_id": second_workout_id, "status": "partial", "notes": "Had to stop early, no pain"},
    )
    assert first_log.status_code == 200
    assert second_log.status_code == 200

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["load_signal"] == "adherence_risk"
    assert "שאלה אחת" in body["adaptation"]["next_adjustment"]
    plan_adjustment = body["adaptation"]["plan_adjustment"]
    assert plan_adjustment["type"] == "reduce_plan_before_rebuild"
    assert plan_adjustment["recommendation"] == "reduce_days_or_add_minimum_day"
    assert plan_adjustment["reduce_days_per_week_by"] == 1
    assert plan_adjustment["use_minimum_version_days"] is True
    assert "זמן" in plan_adjustment["critical_question"]
    assert body["execution_plan"]["plan_adjustment"] == plan_adjustment


def test_next_workout_after_knee_pain_narrows_lower_body_substitutions(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 4,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    assert response.status_code == 200
    plan = response.json()
    target_day = None
    target_exercise = None
    for day in plan["days"]:
        for exercise in day["exercises"]:
            alternatives = exercise.get("alternatives") or []
            if "סקוואט" in exercise["name"] and any("מדרגה" in alternative for alternative in alternatives):
                target_day = day
                target_exercise = exercise
                break
        if target_exercise:
            break
    assert target_day is not None
    assert target_exercise is not None

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": target_day["workout_id"],
            "status": "partial",
            "pain_flag": True,
            "notes": "Knee pain during squats",
            "exercises": [
                {
                    "exercise_id": target_exercise["exercise_id"],
                    "exercise_name": target_exercise["name"],
                    "status": "partial",
                    "sets": [{"set_index": 1, "reps": 6, "completed": False}],
                    "notes": "Knee pain on the first set",
                }
            ],
        },
    )
    assert log_response.status_code == 200

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["id"] == target_day["workout_id"]
    assert body["adaptation"]["load_signal"] == "pain_caution"
    assert body["adaptation"]["pain_area"] == "knee"
    adjusted = next(
        exercise
        for exercise in body["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == target_exercise["exercise_id"]
    )
    assert any("קופסה" in alternative or "טווח קצר" in alternative for alternative in adjusted["alternatives"])
    assert not any("מדרגה" in alternative or "מפוצל" in alternative for alternative in adjusted["alternatives"])


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
    assert execution["adjusted_exercises"][0]["sets"] == reduced_sets(exercise["sets"])
    assert execution["adjusted_exercises"][0]["adjustment"] == "reduce_or_hold"
    assert "התאוששות" in execution["summary"]


def test_next_workout_uses_progression_gate_after_clean_log_for_regressed_pushup(tmp_path):
    client = make_client(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["bodyweight"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    target_exercise = next(
        exercise
        for day in plan["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )

    edit_response = client.post(
        "/api/chat",
        json={"message": "שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["provider_status"] == "local_tool"

    edited_next = client.get("/api/workouts/next")
    assert edited_next.status_code == 200
    edited_workout = edited_next.json()
    edited_exercise = next(
        exercise
        for exercise in edited_workout["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )
    assert edited_exercise["name"] == "שכיבת סמיכה על קיר"
    assert "קשות מדי" in edited_exercise["notes"]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": edited_workout["id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": edited_exercise["exercise_id"],
                    "exercise_name": edited_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "rpe": 8,
                    "rir": 2,
                }
            ],
            "rpe": 8,
            "pain_flag": False,
        },
    )
    assert log_response.status_code == 200

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    execution = next_response.json()["execution_plan"]
    adjusted = next(
        exercise
        for exercise in execution["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert execution["load_signal"] == "progress_candidate"
    assert adjusted["adjustment"] == "substitution_progression_gate"
    assert "RPE 8" in adjusted["execution_note"]
    assert "שלב אחד" in adjusted["execution_note"]
    assert "שיפוע גבוה" in adjusted["execution_note"]
    assert "לא לנחש" in adjusted["execution_note"]
    assert adjusted["progression_next_step"] == "שכיבת סמיכה בשיפוע גבוה"
    assert "שער התקדמות אחרי החלפה" in adjusted["notes"]
    assert "חזרה אחת" not in adjusted["execution_note"]


def test_next_workout_holds_progression_gate_after_verbal_effort_without_rpe(tmp_path):
    client = make_client(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["bodyweight"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    target_exercise = next(
        exercise
        for day in plan["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )

    edit_response = client.post(
        "/api/chat",
        json={"message": "שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר"},
    )
    assert edit_response.status_code == 200

    edited_workout = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_workout["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": edited_workout["id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": edited_exercise["exercise_id"],
                    "exercise_name": edited_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "notes": "היה בשליטה בלי כאב",
                }
            ],
            "pain_flag": False,
        },
    )
    assert log_response.status_code == 200
    logged = log_response.json()["exercise_results"][0]
    assert logged["rpe"] is None
    assert logged["effort_signal"] == "controlled"
    assert logged["progression_gate_missing_rpe"] is True

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    execution = next_response.json()["execution_plan"]
    adjusted = next(
        exercise
        for exercise in execution["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )

    assert execution["load_signal"] == "maintain"
    assert adjusted["adjustment"] == "maintain"
    assert adjusted["reason"] == "progression_gate_missing_rpe"
    assert "מאמץ מילולי נשמר" in adjusted["execution_note"]
    assert "RPE 1-10" in adjusted["execution_note"]
    assert "הגרסה הנוכחית" in adjusted["execution_note"]


def test_next_workout_keeps_pain_substitution_progression_generic_after_clean_log(tmp_path):
    client = make_client(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["bodyweight"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    target_exercise = next(
        exercise
        for day in plan["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "squat"
    )

    edit_response = client.post(
        "/api/chat",
        json={"message": "כואבת לי הברך בסקוואט שבתוכנית, תחליף רק את זה"},
    )
    assert edit_response.status_code == 200

    edited_workout = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_workout["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )
    assert "קופסה" in edited_exercise["name"]
    assert "כאב ברך" in edited_exercise["notes"]

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": edited_workout["id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": edited_exercise["exercise_id"],
                    "exercise_name": edited_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "rpe": 7,
                    "rir": 3,
                }
            ],
            "rpe": 7,
            "pain_flag": False,
        },
    )
    assert log_response.status_code == 200

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    adjusted = next(
        exercise
        for exercise in next_response.json()["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert adjusted["adjustment"] == "substitution_progression_gate"
    assert adjusted["progression_next_step"] is None
    assert "שלב אחד" in adjusted["execution_note"]
    assert "לא לנחש" in adjusted["execution_note"]
    assert "רק ל" not in adjusted["execution_note"]


def test_direct_log_after_cable_substitution_keeps_progression_generic(tmp_path):
    client = make_client(tmp_path)
    cable = "\u05db\u05d1\u05dc"
    pulley = "\u05e4\u05d5\u05dc\u05d9"
    cable_missing_note = "\u05db\u05d1\u05dc/\u05e4\u05d5\u05dc\u05d9 \u05d7\u05e1\u05e8"

    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a one day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 1,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    assert plan_response.status_code == 200
    edit_response = client.post(
        "/api/chat",
        json={
            "message": (
                "\u05d0\u05d9\u05df \u05dc\u05d9 \u05db\u05d1\u05dc\u05d9\u05dd "
                "\u05d1\u05ea\u05d5\u05db\u05e0\u05d9\u05ea, \u05ea\u05d7\u05dc\u05d9\u05e3 "
                "\u05e8\u05e7 \u05d0\u05ea \u05de\u05d4 \u05e9\u05e6\u05e8\u05d9\u05da"
            )
        },
    )
    assert edit_response.status_code == 200

    edited_workout = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_workout["exercises"]
        if cable_missing_note in (exercise.get("notes") or "")
    )

    log_response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": edited_workout["id"],
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": edited_exercise["exercise_id"],
                    "exercise_name": edited_exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "rpe": 7,
                }
            ],
            "rpe": 7,
            "pain_flag": False,
        },
    )
    assert log_response.status_code == 200

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    adjusted = next(
        exercise
        for exercise in next_response.json()["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert adjusted["adjustment"] == "substitution_progression_gate"
    assert adjusted["progression_next_step"] is None
    actionable_text = " ".join(
        [
            adjusted["name"],
            adjusted["execution_note"],
            " ".join(adjusted["alternatives"]),
        ]
    )
    assert cable not in actionable_text
    assert pulley not in actionable_text


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


def test_structured_workout_log_parses_qualitative_effort_from_exercise_notes(tmp_path):
    client = make_client(tmp_path)
    plan = create_plan(client, days_per_week=1)
    workout_id = plan["days"][0]["workout_id"]
    exercise = plan["days"][0]["exercises"][0]

    response = client.post(
        "/api/workout-logs",
        json={
            "workout_id": workout_id,
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": exercise["exercise_id"],
                    "exercise_name": exercise["name"],
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                    "notes": "היה קל מדי ונשאר לי מלא כוח",
                }
            ],
            "pain_flag": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["exercise_results"][0]["effort_signal"] == "underloaded"
    assert body["exercise_results"][0]["rir"] is None
    assert body["adaptation"]["load_signal"] == "progress_candidate"
    assert body["adaptation"]["exercise_adjustments"][0]["reason"] == "qualitative_underload"


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
    assert unknown_workout.json()["detail"] == "האימון שביקשת לתעד לא נמצא."

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
    assert mismatched_exercise.json()["detail"] == "התרגיל שביקשת לתעד לא שייך לאימון הזה."

    exercise_without_workout = client.post(
        "/api/workout-logs",
        json={
            "status": "completed",
            "exercises": [
                {
                    "exercise_id": exercise_id,
                    "exercise_name": "Known exercise",
                    "status": "completed",
                    "sets": [{"set_index": 1, "reps": 10, "completed": True}],
                }
            ],
        },
    )
    assert exercise_without_workout.status_code == 400
    assert exercise_without_workout.json()["detail"] == "כדי לתעד תרגיל מתוך תוכנית, צריך לציין גם את האימון המתאים."


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


def reduced_sets(value: str) -> str:
    return str(max(1, int(value.split("-", 1)[0]) - 1))


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
