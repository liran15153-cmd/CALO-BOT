import json
import re
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import PendingAction, SafetyEvent, Workout, WorkoutExercise, WorkoutLog, WorkoutPlan
from backend.app.services.profile_service import ProfileService
from backend.app.services.workout_service import WorkoutService


def test_workout_plan_api_generates_and_saves_structured_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 3-day gym plan for muscle", "days_per_week": 3, "equipment": ["dumbbells"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["days_per_week"] == 3
    assert "full_body" not in body["name"]
    assert "גוף מלא" in body["name"]
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


def test_workout_plan_api_persists_workout_rows_matching_plan_json(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית לשבועיים עם משקולות יד בלבד", "days_per_week": 3},
    )

    assert response.status_code == 200
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    workouts = db.scalars(select(Workout).where(Workout.plan_id == saved.id).order_by(Workout.id)).all()
    days = saved.plan_json["days"]

    assert len(workouts) == len(days)
    for workout, day in zip(workouts, days, strict=True):
        assert workout.name == day["name"]
        assert workout.difficulty == day["difficulty"]
        assert workout.workout_json["name"] == day["name"]
        rows = db.scalars(
            select(WorkoutExercise).where(WorkoutExercise.workout_id == workout.id).order_by(WorkoutExercise.id)
        ).all()
        assert len(rows) == len(day["exercises"])
        for row, exercise in zip(rows, day["exercises"], strict=True):
            assert row.name == exercise["name"]
            assert row.sets == exercise["sets"]
            assert row.reps_or_duration == exercise["reps_or_duration"]
            assert row.rest == exercise["rest"]
            assert row.notes == exercise["notes"]
            assert row.alternatives == exercise["alternatives"]


def test_workout_service_sync_plan_rows_adds_and_removes_exercise_rows(tmp_path):
    client, db = make_client_and_db(tmp_path)
    response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day gym plan", "days_per_week": 2})
    assert response.status_code == 200
    plan = db.get(WorkoutPlan, response.json()["id"])
    assert plan is not None
    first_workout = db.scalars(select(Workout).where(Workout.plan_id == plan.id).order_by(Workout.id)).first()
    assert first_workout is not None
    original_exercises = list(plan.plan_json["days"][0]["exercises"])
    assert len(original_exercises) > 1
    removed_name = original_exercises[-1]["name"]

    plan_json = dict(plan.plan_json)
    days = [dict(day) for day in plan_json["days"]]
    days[0]["exercises"] = [dict(exercise) for exercise in original_exercises[:-1]]
    plan_json["days"] = days
    plan.plan_json = plan_json
    WorkoutService(db)._sync_plan_rows_from_json(plan)
    db.commit()

    rows_after_removal = db.scalars(
        select(WorkoutExercise).where(WorkoutExercise.workout_id == first_workout.id).order_by(WorkoutExercise.id)
    ).all()
    assert len(rows_after_removal) == len(original_exercises) - 1
    assert removed_name not in {row.name for row in rows_after_removal}

    added_exercise = {
        "name": "Loop 128 row sync exercise",
        "sets": "2",
        "reps_or_duration": "8-10",
        "rest": "60 sec",
        "notes": "row sync test",
        "alternatives": ["Bodyweight squat"],
    }
    plan_json = dict(plan.plan_json)
    days = [dict(day) for day in plan_json["days"]]
    days[0]["exercises"] = [dict(exercise) for exercise in days[0]["exercises"]] + [added_exercise]
    plan_json["days"] = days
    plan.plan_json = plan_json
    WorkoutService(db)._sync_plan_rows_from_json(plan)
    db.commit()

    rows_after_addition = db.scalars(
        select(WorkoutExercise).where(WorkoutExercise.workout_id == first_workout.id).order_by(WorkoutExercise.id)
    ).all()
    assert len(rows_after_addition) == len(original_exercises)
    assert rows_after_addition[-1].name == "Loop 128 row sync exercise"
    serialized = WorkoutService(db).serialize_plan_with_rows(plan)
    assert serialized["days"][0]["exercises"][-1]["exercise_id"] == rows_after_addition[-1].id


def test_workout_service_sync_plan_rows_removes_extra_workouts_without_deleting_logs(tmp_path):
    client, db = make_client_and_db(tmp_path)
    response = client.post("/api/workout-plans", json={"prompt": "Create a 3-day gym plan", "days_per_week": 3})
    assert response.status_code == 200
    plan = db.get(WorkoutPlan, response.json()["id"])
    assert plan is not None
    workouts = db.scalars(select(Workout).where(Workout.plan_id == plan.id).order_by(Workout.id)).all()
    assert len(workouts) == 3
    removed_workout_id = workouts[-1].id
    log_response = client.post("/api/workout-logs", json={"workout_id": removed_workout_id, "status": "completed"})
    assert log_response.status_code == 200
    log_id = log_response.json()["id"]

    plan_json = dict(plan.plan_json)
    plan_json["days"] = [dict(day) for day in plan_json["days"][:-1]]
    plan.plan_json = plan_json
    WorkoutService(db)._sync_plan_rows_from_json(plan)
    db.commit()

    assert db.get(Workout, removed_workout_id) is None
    saved_log = db.get(WorkoutLog, log_id)
    assert saved_log is not None
    assert saved_log.workout_id is None
    remaining_workouts = db.scalars(select(Workout).where(Workout.plan_id == plan.id).order_by(Workout.id)).all()
    assert len(remaining_workouts) == len(plan_json["days"])
    serialized = WorkoutService(db).serialize_plan_with_rows(plan)
    assert len(serialized["days"]) == len(plan_json["days"])
    assert {day["workout_id"] for day in serialized["days"]} == {workout.id for workout in remaining_workouts}


def test_workout_plan_api_persists_conservative_assumptions_for_minimal_prompt(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/workout-plans", json={"prompt": "תבנה לי תוכנית אימונים"})

    assert response.status_code == 200
    body = response.json()
    assumptions = body["decision_inputs"]["assumptions"]
    assert body["plan_type"] == "monthly_plan"
    assert body["days_per_week"] == 3
    assert body["session_length_minutes"] == 45
    assert body["equipment_needed"] == ["bodyweight"]
    assert any("אופק תוכנית" in assumption for assumption in assumptions)
    assert any("שיפור כושר כללי" in assumption for assumption in assumptions)
    assert any("3 אימונים בשבוע" in assumption for assumption in assumptions)
    assert any("45 דקות" in assumption for assumption in assumptions)
    assert any("משקל גוף" in assumption for assumption in assumptions)
    assert any("מתחיל/ה" in assumption for assumption in assumptions)
    assert any("מאמץ מילולי" in item and "קל מדי" in item and "כבד מדי" in item for item in body["tracking_guidance"])
    assert all("לכבד מדי" not in item for item in body["tracking_guidance"])
    assert any("לא לנחש" in item and "התרגיל המרכזי" in item for item in body["tracking_guidance"])
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["decision_inputs"]["assumptions"] == assumptions


def test_workout_plan_api_states_assumption_for_three_week_request(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a three week workout plan", "duration_weeks": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assumptions = body["decision_inputs"]["assumptions"]
    assert body["plan_type"] == "monthly_plan"
    assert body["duration_weeks"] == 4
    assert any("3" in assumption and "חודשית" in assumption for assumption in assumptions)


def test_workout_plan_api_returns_current_plan(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/workout-plans", json={"prompt": "Create a home dumbbell plan", "days_per_week": 2})

    response = client.get("/api/workout-plans/current")

    assert response.status_code == 200
    body = response.json()
    assert body["is_current"] is True
    assert body["days"][0]["workout_id"] is not None
    assert body["days"][0]["exercises"][0]["exercise_id"] is not None


def test_current_plan_ignores_legacy_single_workout_marked_current(tmp_path):
    client, db = make_client_and_db(tmp_path)
    user = ProfileService(db).get_default_user()
    one_off = WorkoutPlan(
        user_id=user.id,
        name="Legacy one-off",
        goal="improve_fitness",
        duration_weeks=1,
        days_per_week=1,
        equipment_needed=["bodyweight"],
        plan_json={"plan_type": "single_workout", "days": []},
        progression_rule="One-off only.",
        is_current=True,
    )
    db.add(one_off)
    db.commit()

    assert client.get("/api/workout-plans/current").status_code == 404
    assert client.get("/api/workouts/next").status_code == 404

    created = client.post("/api/workout-plans", json={"prompt": "Build me a weekly plan", "days_per_week": 2})

    assert created.status_code == 200
    assert created.json()["is_current"] is True
    db.refresh(one_off)
    assert one_off.is_current is False


def test_workout_plan_api_creates_candidate_when_current_plan_exists(tmp_path):
    client, db = make_client_and_db(tmp_path)
    current_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    current_id = current_response.json()["id"]

    response = client.post("/api/workout-plans", json={"prompt": "Create a new 4-day muscle plan", "days_per_week": 4})

    assert response.status_code == 200
    body = response.json()
    assert body["is_current"] is False
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert pending is not None
    assert body["pending_action"]["id"] == pending.id
    assert pending.action_type == "activate_workout_plan"
    assert pending.subject_type == "workout_plan"
    assert pending.subject_id == body["id"]
    assert pending.payload_json["current_plan_id"] == current_id


def test_workout_plan_api_keeps_legacy_current_plan_without_type_as_active(tmp_path):
    client, db = make_client_and_db(tmp_path)
    user = ProfileService(db).get_default_user()
    legacy = WorkoutPlan(
        user_id=user.id,
        name="Legacy current plan",
        goal="improve_fitness",
        duration_weeks=4,
        days_per_week=3,
        equipment_needed=["bodyweight"],
        plan_json={"name": "Legacy current plan", "days": []},
        progression_rule="Keep effort controlled.",
        is_current=True,
    )
    db.add(legacy)
    db.commit()
    db.refresh(legacy)

    response = client.post("/api/workout-plans", json={"prompt": "Create a new monthly gym plan"})

    assert response.status_code == 200
    body = response.json()
    assert body["plan_type"] == "monthly_plan"
    assert body["is_current"] is False
    assert db.get(WorkoutPlan, legacy.id).is_current is True
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert pending is not None
    assert pending.payload_json["current_plan_id"] == legacy.id


def test_pending_action_api_returns_and_resolves_current_plan_candidate(tmp_path):
    client, db = make_client_and_db(tmp_path)
    current_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    current_id = current_response.json()["id"]
    candidate_response = client.post("/api/workout-plans", json={"prompt": "Create a new 4-day muscle plan", "days_per_week": 4})
    candidate_id = candidate_response.json()["id"]

    current_pending = client.get("/api/pending-actions/current", params={"action_type": "activate_workout_plan"})

    assert current_pending.status_code == 200
    pending_body = current_pending.json()
    assert pending_body["status"] == "pending"
    assert pending_body["subject_id"] == candidate_id
    assert pending_body["candidate_plan"]["id"] == candidate_id
    assert pending_body["candidate_plan"]["is_current"] is False

    resolve = client.post(f"/api/pending-actions/{pending_body['id']}/resolve", json={"decision": "confirm"})

    assert resolve.status_code == 200
    body = resolve.json()
    assert body["pending_action"]["status"] == "resolved"
    assert body["pending_action"]["resolution"] == "confirmed"
    assert body["workout_plan"]["id"] == candidate_id
    assert body["workout_plan"]["is_current"] is True
    assert db.get(WorkoutPlan, current_id) is None
    assert db.get(PendingAction, pending_body["id"]).status == "resolved"


def test_pending_action_api_declines_candidate_and_keeps_current_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    current_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    current_id = current_response.json()["id"]
    candidate_response = client.post("/api/workout-plans", json={"prompt": "Create a new 4-day muscle plan", "days_per_week": 4})
    candidate_id = candidate_response.json()["id"]
    pending_id = candidate_response.json()["pending_action"]["id"]

    resolve = client.post(f"/api/pending-actions/{pending_id}/resolve", json={"decision": "decline"})

    assert resolve.status_code == 200
    body = resolve.json()
    assert body["pending_action"]["status"] == "resolved"
    assert body["pending_action"]["resolution"] == "declined"
    assert body["workout_plan"]["id"] == current_id
    assert db.get(WorkoutPlan, current_id).is_current is True
    assert db.get(WorkoutPlan, candidate_id) is None


def test_new_candidate_replaces_existing_pending_action_and_removes_old_candidate(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    first_candidate = client.post("/api/workout-plans", json={"prompt": "Create a new 4-day muscle plan", "days_per_week": 4})
    first_candidate_id = first_candidate.json()["id"]
    first_pending_id = first_candidate.json()["pending_action"]["id"]

    second_candidate = client.post("/api/workout-plans", json={"prompt": "Create a new 5-day strength plan", "days_per_week": 5})

    second_body = second_candidate.json()
    assert db.get(WorkoutPlan, first_candidate_id) is None
    replaced = db.get(PendingAction, first_pending_id)
    assert replaced.status == "cancelled"
    assert replaced.resolution == "replaced"
    current_pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert current_pending is not None
    assert current_pending.id == second_body["pending_action"]["id"]
    assert current_pending.subject_id == second_body["id"]


def test_pending_action_api_returns_404_when_no_pending_action(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.get("/api/pending-actions/current", params={"action_type": "activate_workout_plan"})

    assert response.status_code == 404


def test_pending_action_api_rejects_resolving_non_pending_action(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    candidate = client.post("/api/workout-plans", json={"prompt": "Create a new 4-day muscle plan", "days_per_week": 4})
    pending_id = candidate.json()["pending_action"]["id"]
    assert client.post(f"/api/pending-actions/{pending_id}/resolve", json={"decision": "decline"}).status_code == 200

    response = client.post(f"/api/pending-actions/{pending_id}/resolve", json={"decision": "confirm"})

    assert response.status_code == 400


def test_activate_workout_plan_deletes_previous_plan_and_preserves_log_history(tmp_path):
    client, db = make_client_and_db(tmp_path)
    current_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    current_body = current_response.json()
    current_id = current_body["id"]
    workout_id = current_body["days"][0]["workout_id"]
    log_response = client.post("/api/workout-logs", json={"workout_id": workout_id, "status": "completed"})
    log_id = log_response.json()["id"]
    candidate_response = client.post("/api/workout-plans", json={"prompt": "Create a new 4-day muscle plan", "days_per_week": 4})
    candidate_id = candidate_response.json()["id"]
    pending_id = candidate_response.json()["pending_action"]["id"]

    response = client.post(f"/api/workout-plans/{candidate_id}/activate", json={"delete_previous": True})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == candidate_id
    assert body["is_current"] is True
    assert db.get(WorkoutPlan, current_id) is None
    assert db.get(Workout, workout_id) is None
    saved_log = db.get(WorkoutLog, log_id)
    assert saved_log is not None
    assert saved_log.workout_id is None
    pending = db.get(PendingAction, pending_id)
    assert pending.status == "resolved"
    assert pending.resolution == "confirmed"


def test_activate_workout_plan_rejects_single_workout_and_keeps_current_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    current_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    current_id = current_response.json()["id"]
    one_off_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build one workout for today", "plan_type": "single_workout", "session_length_minutes": 20},
    )
    one_off_id = one_off_response.json()["id"]

    response = client.post(f"/api/workout-plans/{one_off_id}/activate")

    assert response.status_code == 400
    assert "single workout" in response.json()["detail"]
    assert db.get(WorkoutPlan, current_id).is_current is True
    assert db.get(WorkoutPlan, one_off_id).is_current is False


def test_delete_workout_plan_removes_inactive_candidate_only(tmp_path):
    client, db = make_client_and_db(tmp_path)
    current_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day plan", "days_per_week": 2})
    current_id = current_response.json()["id"]
    candidate_response = client.post("/api/workout-plans", json={"prompt": "Create a new 4-day muscle plan", "days_per_week": 4})
    candidate_id = candidate_response.json()["id"]
    pending_id = candidate_response.json()["pending_action"]["id"]

    response = client.delete(f"/api/workout-plans/{candidate_id}")

    assert response.status_code == 204
    assert db.get(WorkoutPlan, candidate_id) is None
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    pending = db.get(PendingAction, pending_id)
    assert pending is not None
    assert pending.status == "cancelled"
    assert pending.resolution == "candidate_deleted"
    assert client.get("/api/pending-actions/current", params={"action_type": "activate_workout_plan"}).status_code == 404


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


def test_workout_plan_hebrew_prompt_goal_overrides_saved_profile_goal(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/workout-plans", json={"prompt": "תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה"})

    assert response.status_code == 200
    body = response.json()
    assert body["goal"] == "improve_endurance"
    assert body["plan_type"] == "two_week_plan"
    assert body["days_per_week"] == 2
    assert body["equipment_needed"] == ["resistance bands"]
    assert body["days"][0]["exercises"][0]["name"] == "אירובי בסיסי בקצב שיחה"
    assert "ריצה" not in body["days"][0]["exercises"][0]["notes"]


def test_workout_plan_hebrew_prompt_goal_beats_conflicting_request_goal(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה",
            "goal": "build_muscle",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assumptions = body["decision_inputs"]["assumptions"]
    assert body["goal"] == "improve_endurance"
    assert body["plan_type"] == "two_week_plan"
    assert body["days"][0]["exercises"][0]["name"] == "אירובי בסיסי בקצב שיחה"
    assert any("שדה goal" in assumption and "מתוך הבקשה" in assumption for assumption in assumptions)


def test_workout_plan_request_goal_still_applies_when_prompt_has_no_goal(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית ביתית פשוטה לשבועיים",
            "goal": "lose_fat",
            "equipment": ["bodyweight"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assumptions = body["decision_inputs"]["assumptions"]
    assert body["goal"] == "lose_fat"
    assert body["plan_type"] == "two_week_plan"
    assert "אירובי קל" in body["days"][0]["notes"]
    assert not any("שדה goal" in assumption for assumption in assumptions)


def test_workout_plan_api_blocks_red_flag_symptoms_before_saving_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "כואב לי החזה וסחרחורת, תבנה לי תוכנית כוח של 3 ימים"},
    )

    assert response.status_code == 400
    assert "לעצור" in response.json()["detail"]
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "dangerous_symptoms"
    assert db.scalar(select(WorkoutPlan)) is None


def test_workout_plan_api_records_soft_pain_event_and_builds_adapted_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "יש לי כאב ברך קל, תבנה לי תוכנית כוח של 2 ימים בלי ציוד"},
    )

    assert response.status_code == 200
    body = response.json()
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "pain_signal"
    assert "ברך" in (body["decision_inputs"].get("limitations") or "")
    assert db.scalar(select(WorkoutPlan)) is not None


def test_workout_plan_api_treats_general_back_pain_as_hinge_constraint(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "יש לי כאב גב קל בדדליפט, תבנה לי תוכנית שבועית כוח של 2 ימים בלי ציוד"},
    )

    assert response.status_code == 200
    body = response.json()
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "pain_signal"
    assert body["plan_type"] == "weekly_plan"
    assert "גב" in (body["decision_inputs"].get("limitations") or "")

    hinges = [
        exercise
        for day in body["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "hip_hinge"
    ]
    assert hinges
    assert any("הינג" in exercise["name"] and "קיר" in exercise["name"] for exercise in hinges)
    assert any("24-48" in (exercise.get("progression") or "") for exercise in hinges)
    assert any(
        "גב רגיש" in note
        for exercise in hinges
        for note in exercise.get("safety_notes", [])
    )
    hinge_text = " ".join(
        " ".join([exercise["name"], *exercise.get("alternatives", [])])
        for exercise in hinges
    )
    assert "דדליפט" not in hinge_text
    assert db.scalar(select(WorkoutPlan)) is not None


def test_workout_plan_api_requires_pain_area_for_vague_soft_pain(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "יש לי כאב, תבנה לי תוכנית כוח של 2 ימים"},
    )

    assert response.status_code == 400
    assert "איפה הכאב" in response.json()["detail"]
    assert "חד" in response.json()["detail"]
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "pain_signal"
    assert db.scalar(select(WorkoutPlan)) is None


def test_knee_sensitive_plan_avoids_primary_lunge_work(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "יש לי כאב ברך קל, תבנה לי תוכנית חודשית לבינוני בחדר כושר",
            "days_per_week": 4,
            "equipment": ["gym"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    lower_days = [day for day in body["days"] if day["focus"] == "lower_body"]
    assert lower_days
    for day in lower_days:
        patterns = [exercise.get("movement_pattern") for exercise in day["exercises"]]
        assert "single_leg" not in patterns
        assert "squat" in patterns
        assert "hip_hinge" in patterns
        assert "glute_bridge" in patterns
        squat = next(exercise for exercise in day["exercises"] if exercise.get("movement_pattern") == "squat")
        alternatives_text = " ".join(squat.get("alternatives", []))
        assert "קופסה" in alternatives_text
        assert "מדרגה" not in alternatives_text
        assert "מפוצל" not in alternatives_text
        assert any("ברך רגישה" in note for note in squat.get("safety_notes", []))


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
    endurance_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 2-day endurance plan", "days_per_week": 2, "equipment": ["dumbbells"]},
    )
    mobility_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Build me a 2-day mobility plan", "days_per_week": 2, "equipment": ["dumbbells"]},
    )
    explicit_mobility_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build me a 2-day plan",
            "goal": "improve_mobility",
            "days_per_week": 2,
            "equipment": ["bodyweight"],
        },
    )

    assert strength_response.status_code == 200
    assert muscle_response.status_code == 200
    assert fat_loss_response.status_code == 200
    assert endurance_response.status_code == 200
    assert mobility_response.status_code == 200
    assert explicit_mobility_response.status_code == 200

    strength = strength_response.json()
    muscle = muscle_response.json()
    fat_loss = fat_loss_response.json()
    endurance = endurance_response.json()
    mobility = mobility_response.json()
    explicit_mobility = explicit_mobility_response.json()

    assert strength["days"][0]["exercises"][0]["reps_or_duration"] == "4-6 חזרות"
    assert strength["days"][0]["exercises"][0]["rest"] == "120-180 שניות"
    assert muscle["days"][0]["exercises"][0]["reps_or_duration"] == "8-12 חזרות"
    assert "נפח" in muscle["progression_rule"]
    assert fat_loss["days"][0]["exercises"][0]["rest"] == "60-90 שניות"
    assert "הליכה" in fat_loss["days"][0]["notes"]
    assert "אירובי קל" in fat_loss["days"][0]["notes"]
    assert "500-1,000 צעדים" in fat_loss["progression_rule"]
    assert "דיאטת קיצון" in fat_loss["recovery_note"]
    fat_loss_text = json.dumps(fat_loss, ensure_ascii=False)
    assert "ענישה" not in fat_loss_text
    assert "שורף" not in fat_loss_text
    assert "קלוריות" not in fat_loss["days"][0]["notes"]
    assert "קלוריות" not in fat_loss["progression_rule"]
    endurance_first = endurance["days"][0]["exercises"][0]
    assert "אירובי" in endurance_first["name"]
    assert "דקות" in endurance_first["reps_or_duration"]
    assert "RPE 5-6" in endurance_first["rest"]
    assert "להעלות משך או תדירות לפני עצימות" in endurance_first["notes"]
    assert "נשימה" in endurance["days"][0]["notes"]
    endurance_tracking = " ".join(endurance["tracking_guidance"])
    assert "talk test" in endurance_tracking
    assert "ברזרבה" not in endurance_tracking
    assert "משקל אם יש" not in endurance_tracking
    assert "RIR" not in endurance_tracking
    assert "full-body" not in endurance_tracking
    mobility_exercises = mobility["days"][0]["exercises"]
    assert "מוביליטי" in mobility_exercises[0]["name"]
    assert mobility_exercises[0]["reps_or_duration"] == "5-8 דקות"
    assert "שיווי משקל" in mobility_exercises[1]["name"]
    assert "חזרות איטיות" in mobility_exercises[2]["reps_or_duration"]
    assert "טווח" in mobility_exercises[2]["notes"]
    mobility_tracking = " ".join(mobility["tracking_guidance"])
    assert "RPE 4-6" in mobility_tracking
    assert "ברזרבה" not in mobility_tracking
    assert "משקל אם יש" not in mobility_tracking
    assert "RIR" not in mobility_tracking
    assert "טווח נוח" in mobility_tracking
    assert "full-body" not in mobility_tracking
    assert mobility["goal"] == "improve_mobility"
    assert explicit_mobility["goal"] == "improve_mobility"
    assert "מוביליטי" in explicit_mobility["days"][0]["exercises"][0]["name"]


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
    assert body["plan_type"] == "monthly_plan"
    assert body["duration_weeks"] == 4
    assert body["training_split"] == "upper_lower"
    assert body["experience_level"] == "intermediate"
    assert body["decision_inputs"]["duration_weeks"] == 4
    assert any("ACSM 2026 resistance training guidelines" in source for source in body["source_refs"])
    assert any("Wingate strength training" in source for source in body["source_refs"])
    assert any("RP Strength training volume landmarks" in source for source in body["source_refs"])
    assert any("Barbell Medicine pain in training" in source for source in body["source_refs"])
    assert {day["focus"] for day in body["days"]} == {"upper_body", "lower_body"}
    assert all(day["estimated_duration_minutes"] <= 50 for day in body["days"])

    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["training_split"] == "upper_lower"
    assert saved.plan_json["source_refs"]
    assert len(db.scalars(select(Workout)).all()) == 4


def test_single_session_alias_plan_is_saved_without_replacing_current_monthly_plan(tmp_path):
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
    assert body["plan_type"] == "single_workout"
    assert body["duration_weeks"] == 1
    assert body["days_per_week"] == 1
    assert len(body["progression_schedule"]) == 1
    assert "אימון יחיד" in body["progression_model"]
    assert "התקדמות כפולה" not in body["progression_model"]
    assert "שבוע" not in body["progression_model"]
    assert "חודש" not in body["progression_model"]
    assert "אימון יחיד" in body["progression_schedule"][0]
    assert "מאמץ מילולי" in body["progression_schedule"][0]
    assert any("מאמץ מילולי" in item for item in body["tracking_guidance"])
    assert len(body["days"]) == 1
    assert body["days"][0]["focus"] == "single_workout"
    assert body["days"][0]["estimated_duration_minutes"] <= 20
    assert body["decision_inputs"]["plan_type"] == "אימון יחיד"
    assert any("התאוששות" in note or "הורד" in note for note in body["safety_notes"])
    assert_no_english_workout_guidance(body)

    current_after = db.get(WorkoutPlan, current_id)
    assert current_after is not None
    assert current_after.is_current is True
    one_off = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert one_off is not None
    assert one_off.is_current is False


def test_single_workout_plan_infers_hebrew_gym_and_duration_from_prompt_before_profile_defaults(tmp_path):
    client, db = make_client_and_db(tmp_path)
    payload = valid_payload()
    payload["training_location"] = "home"
    payload["available_equipment"] = ["resistance bands"]
    payload["session_length_minutes"] = 45
    client.post("/api/onboarding", json=payload)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "תן לי אימון אחד להיום בחדר כושר, 30 דקות, בלי לפנות אליי בלשון זכר או נקבה."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan_type"] == "single_workout"
    assert body["session_length_minutes"] == 30
    assert body["days"][0]["focus"] == "single_workout"
    assert body["days"][0]["estimated_duration_minutes"] == 30
    assert "חדר כושר" in body["equipment_needed"]
    assert "bodyweight" not in body["equipment_needed"]
    assert body["decision_inputs"]["session_length_minutes"] == 30
    assert "חדר כושר" in body["decision_inputs"]["equipment"]
    exercise_names = [exercise["name"] for exercise in body["days"][0]["exercises"]]
    movement_patterns = [exercise["movement_pattern"] for exercise in body["days"][0]["exercises"]]
    assert any("מכונה" in name or "משקולות" in name for name in exercise_names)
    assert movement_patterns[:4] == ["squat", "horizontal_push", "horizontal_pull", "hip_hinge"]
    assert "core_anti_extension" not in movement_patterns[:4]
    assert_no_direct_gendered_hebrew_workout_guidance(body)
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["session_length_minutes"] == 30


def test_single_workout_without_duration_defaults_to_short_practical_session(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/workout-plans", json={"prompt": "תן לי אימון יחיד להיום"})

    assert response.status_code == 200
    body = response.json()
    assert body["plan_type"] == "single_workout"
    assert body["days_per_week"] == 1
    assert body["session_length_minutes"] == 30
    assert body["days"][0]["focus"] == "single_workout"
    assert body["days"][0]["estimated_duration_minutes"] == 30
    assumptions = body["decision_inputs"]["assumptions"]
    assert any("30 דקות לאימון יחיד" in assumption for assumption in assumptions)
    assert not any("45 דקות" in assumption for assumption in assumptions)
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.is_current is False


def test_single_workout_plan_uses_recent_training_status_to_reduce_load(tmp_path):
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
            "plan_type": "single_workout",
            "session_length_minutes": 30,
            "equipment": ["bodyweight"],
        },
    )

    assert user_plan_response.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["decision_inputs"]["training_status"]["load_signal"] == "recovery_needed"
    assert any("התאוששות" in note or "הורד" in note for note in body["safety_notes"])
    assert_no_english_workout_guidance(body)
    assert body["days"][0]["exercises"][0]["sets"] == "2"


def test_workout_plan_api_splits_weekly_two_week_and_monthly_horizons(tmp_path):
    client, _ = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    weekly = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית קצרה לשבוע הקרוב, 20 דקות ביום", "days_per_week": 3},
    ).json()
    two_week = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית לשבועיים עם משקולות", "days_per_week": 3},
    ).json()
    monthly = client.post(
        "/api/workout-plans",
        json={"prompt": "תבני לי תוכנית חודשית למכון", "days_per_week": 4},
    ).json()

    assert weekly["plan_type"] == "weekly_plan"
    assert weekly["duration_weeks"] == 1
    assert len(weekly["progression_schedule"]) == 1
    assert "שבוע 4" not in weekly["progression_model"]
    assert "דילואד" not in weekly["progression_model"]
    assert any("RPE" in item for item in weekly["tracking_guidance"])
    assert any("מאמץ מילולי" in item for item in weekly["tracking_guidance"])
    assert any("מאמץ מילולי" in item for item in weekly["progression_schedule"])
    assert weekly["decision_inputs"]["plan_type"] == "תוכנית שבועית"
    assert two_week["plan_type"] == "two_week_plan"
    assert two_week["duration_weeks"] == 2
    assert len(two_week["progression_schedule"]) == 2
    assert any("שבוע 2" in item for item in two_week["progression_schedule"])
    assert any("מאמץ מילולי" in item for item in two_week["progression_schedule"])
    assert any("אם לא" in item and ("לשמור" in item or "להוריד" in item) for item in two_week["progression_schedule"])
    assert any("RPE" in item and "RIR" in item for item in two_week["progression_schedule"])
    assert any("מאמץ מילולי" in item and "לשמור" in item for item in two_week["progression_schedule"])
    assert any("שבוע 1" in item and "שבוע 2" in item for item in two_week["tracking_guidance"])
    assert any("מאמץ מילולי" in item for item in two_week["tracking_guidance"])
    assert any("מאמץ מילולי לבד" in item and "לשמור" in item for item in two_week["tracking_guidance"])
    assert any("בסוף שבוע 2" in item and "בלוק נוסף" in item for item in two_week["tracking_guidance"])
    assert two_week["decision_inputs"]["plan_type"] == "תוכנית לשבועיים"
    assert monthly["plan_type"] == "monthly_plan"
    assert monthly["duration_weeks"] == 4
    assert len(monthly["progression_schedule"]) == 4
    assert "שבוע 4" in monthly["progression_model"]
    assert "דילואד" in monthly["progression_model"]
    assert "20-40%" in monthly["progression_model"]
    assert any("שבוע 4" in item for item in monthly["progression_schedule"])
    assert any("מאמץ" in item and "מילולי" in item for item in monthly["progression_schedule"])
    assert any("RPE" in item and "RIR" in item for item in monthly["progression_schedule"])
    assert any("מאמץ מילולי" in item and "לשמור" in item for item in monthly["progression_schedule"])
    assert any("%" in item and "נפח" in item for item in monthly["progression_schedule"])
    assert any("בסוף כל שבוע" in item for item in monthly["tracking_guidance"])
    assert any("מאמץ מילולי" in item for item in monthly["tracking_guidance"])
    assert any("מאמץ מילולי לבד" in item and "לשמור" in item for item in monthly["tracking_guidance"])
    assert monthly["decision_inputs"]["plan_type"] == "תוכנית חודשית"


def test_workout_plan_infers_hebrew_worded_day_counts(tmp_path):
    client, _ = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    monthly = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית חודשית ארבעה ימים במכון, חצי שעה לאימון"},
    ).json()
    weekly = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית שבועית שלושה אימונים בלי ציוד"},
    ).json()
    over_requested = client.post(
        "/api/workout-plans",
        json={"prompt": "Build a weekly plan for 10 days"},
    ).json()

    assert monthly["plan_type"] == "monthly_plan"
    assert monthly["days_per_week"] == 4
    assert monthly["session_length_minutes"] == 30
    assert len(monthly["days"]) == 4
    assert monthly["decision_inputs"]["days_per_week"] == 4
    assert monthly["decision_inputs"]["session_length_minutes"] == 30
    assert weekly["plan_type"] == "weekly_plan"
    assert weekly["days_per_week"] == 3
    assert len(weekly["days"]) == 3
    assert over_requested["days_per_week"] == 7
    assert len(over_requested["days"]) == 7


def test_full_body_plan_rotates_day_emphasis_without_losing_balance(tmp_path):
    client, _ = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד", "days_per_week": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["training_split"] == "full_body"
    assert [day["focus"] for day in body["days"]] == ["full_body", "full_body_lower", "full_body_upper"]
    assert any("דגש רגליים" in day["name"] for day in body["days"])
    assert any("דגש פלג עליון" in day["name"] for day in body["days"])

    first_three_patterns = [
        [exercise.get("movement_pattern") for exercise in day["exercises"][:3]]
        for day in body["days"]
    ]
    assert len({tuple(patterns) for patterns in first_three_patterns}) == 3
    for day in body["days"]:
        patterns = [exercise.get("movement_pattern") for exercise in day["exercises"]]
        assert "horizontal_push" in patterns
        assert "horizontal_pull" in patterns
        assert "squat" in patterns or "hip_hinge" in patterns


def test_four_day_beginner_full_body_includes_recovery_spacing_for_consecutive_hebrew_request(tmp_path):
    client, _ = make_client_and_db(tmp_path)

    response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית חודשית למתחיל בלי ציוד, 4 ימים בשבוע, ראשון עד רביעי ברצף",
            "days_per_week": 4,
        },
    )

    assert response.status_code == 200
    body = response.json()
    spacing = body["decision_inputs"]["weekly_spacing_guidance"]
    tracking_text = " ".join(body["tracking_guidance"])

    assert body["training_split"] == "full_body"
    assert body["days_per_week"] == 4
    assert body["days"][0]["exercises"][0]["sets"] == "2"
    assert body["days"][2]["exercises"][0]["sets"] == "1"
    assert body["days"][3]["exercises"][0]["sets"] == "1"
    assert "ימים צפופים" in body["days"][2]["notes"]
    assert any("ימים צפופים" in exercise["notes"] for exercise in body["days"][2]["exercises"])
    assert "4 ימי full-body" in spacing
    assert "ימים צפופים" in spacing
    assert "RPE 5-7" in spacing
    assert "4 ימי full-body" in tracking_text
    assert "ימים צפופים" in tracking_text
    assert "גרסת מינימום" in tracking_text


def test_workout_plan_infers_hebrew_goal_slang_and_mobility_focus(tmp_path):
    client, _ = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    fat_loss = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית חיטוב ביתית לשבוע", "days_per_week": 2},
    ).json()
    endurance = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה", "days_per_week": 2},
    ).json()
    mobility = client.post(
        "/api/workout-plans",
        json={"prompt": "תן לי תוכנית מוביליטי חודשית עם משקל גוף", "days_per_week": 3},
    ).json()

    assert fat_loss["goal"] == "lose_fat"
    assert "הליכה" in fat_loss["days"][0]["notes"]
    assert "500-1,000 צעדים" in fat_loss["progression_rule"]
    assert endurance["goal"] == "improve_endurance"
    endurance_text = " ".join(
        " ".join([exercise["name"], exercise.get("notes") or "", *exercise.get("alternatives", [])])
        for exercise in endurance["days"][0]["exercises"]
    )
    assert "הליכה" in endurance_text or "אופניים" in endurance_text
    assert "ריצה" not in endurance_text
    assert mobility["goal"] == "improve_mobility"
    mobility_names = [exercise["name"] for exercise in mobility["days"][0]["exercises"]]
    assert any("מוביליטי" in name for name in mobility_names)
    assert any("שיווי משקל" in name for name in mobility_names)
    assert "טווח תנועה" in mobility["progression_rule"]
    assert "מוביליטי" in mobility["recovery_note"]


def test_workout_plan_handles_mixed_hebrew_strength_and_muscle_goal(tmp_path):
    client, _ = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json={**valid_payload(), "experience_level": "intermediate"})

    mixed = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית חודשית לחדר כושר לחיזוק ועלייה במסת שריר",
            "days_per_week": 4,
        },
    ).json()
    strength_only = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית חודשית לחדר כושר לחיזוק", "days_per_week": 4},
    ).json()

    assumptions = mixed["decision_inputs"]["assumptions"]
    assert mixed["goal"] == "build_muscle"
    assert any("כוח" in assumption and "מסת שריר" in assumption and "המוקד הראשי" in assumption for assumption in assumptions)
    assert "נפח" in mixed["progression_rule"]
    assert mixed["days"][0]["exercises"][0]["reps_or_duration"] == "8-12 חזרות"

    assert strength_only["goal"] == "improve_strength"
    assert "עומס" in strength_only["progression_rule"]
    assert strength_only["days"][0]["exercises"][0]["rest"] == "120 שניות"
    assert "1-2 חזרות ברזרבה" in strength_only["days"][0]["exercises"][0]["notes"]


def test_workout_plan_tailors_exercises_by_equipment_and_experience(tmp_path):
    client, _ = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    beginner_bodyweight = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית למתחיל בלי ציוד לשבוע", "days_per_week": 2},
    ).json()
    dumbbells_only = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית לשבועיים עם משקולות יד בלבד", "days_per_week": 3},
    ).json()
    bands_only = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית שבועית עם גומייה בלבד", "days_per_week": 2},
    ).json()
    advanced_bodyweight = client.post(
        "/api/workout-plans",
        json={"prompt": "Build an advanced bodyweight weekly plan", "days_per_week": 3},
    ).json()

    beginner_names = [exercise["name"] for exercise in beginner_bodyweight["days"][0]["exercises"]]
    beginner_alternatives = [
        alternative
        for exercise in beginner_bodyweight["days"][0]["exercises"]
        for alternative in exercise.get("alternatives", [])
    ]
    dumbbell_names = [exercise["name"] for exercise in dumbbells_only["days"][0]["exercises"]]
    band_names = [exercise["name"] for exercise in bands_only["days"][0]["exercises"]]
    advanced_names = [exercise["name"] for exercise in advanced_bodyweight["days"][0]["exercises"]]

    assert "סקוואט לקופסה" in beginner_names
    assert any("שכיבת סמיכה בשיפוע" in name for name in beginner_names)
    assert beginner_bodyweight["days"][0]["exercises"][0]["sets"] == "2"
    assert "2-4 חזרות ברזרבה" in beginner_bodyweight["days"][0]["exercises"][1]["notes"]
    assert all("מכונה" not in name for name in beginner_names)
    assert any("ישיבה-קימה" in alternative for alternative in beginner_alternatives)
    assert any("משקולת" in name or "משקולות" in name for name in dumbbell_names)
    assert all("מכונה" not in name for name in dumbbell_names)
    assert bands_only["equipment_needed"] == ["resistance bands"]
    assert bands_only["decision_inputs"]["equipment"] == ["resistance bands"]
    assert any("גומייה" in name for name in band_names)
    assert any("מפוצל" in name or "איטית" in name for name in advanced_names)
    assert advanced_bodyweight["days"][0]["exercises"][0]["sets"] == "4"
    assert any("RPE 7-9" in item for item in advanced_bodyweight["tracking_guidance"])
    generated_text = " ".join(beginner_names + beginner_alternatives + dumbbell_names + advanced_names)
    assert "step-up" not in generated_text.lower()
    beginner_bodyweight_text = _exercise_equipment_text(beginner_bodyweight)
    dumbbells_only_text = _exercise_equipment_text(dumbbells_only)
    bands_only_text = _exercise_equipment_text(bands_only)
    for unavailable in ["גומייה", "ספסל", "כבל", "פולי", "מכונה"]:
        assert unavailable not in beginner_bodyweight_text
    for unavailable in ["גומייה", "ספסל", "כבל", "פולי", "מכונה"]:
        assert unavailable not in dumbbells_only_text
    for unavailable in ["ספסל", "כבל", "פולי", "מכונה", "משקולת", "משקולות"]:
        assert unavailable not in bands_only_text
    assert "חתירה בהטיית גו" in dumbbells_only_text
    assert "חתירה עם גומייה" in bands_only_text


def test_home_plan_prompt_overrides_saved_gym_equipment_when_equipment_missing(tmp_path):
    client, _ = make_client_and_db(tmp_path)
    payload = valid_payload()
    payload["training_location"] = "gym"
    payload["available_equipment"] = ["machines", "cables", "barbell"]
    client.post("/api/onboarding", json=payload)

    response = client.post("/api/workout-plans", json={"prompt": "תבנה לי תוכנית ביתית לשבוע"})

    assert response.status_code == 200
    body = response.json()
    assert body["equipment_needed"] == ["bodyweight"]
    text = " ".join(
        " ".join([exercise["name"], *exercise.get("alternatives", [])])
        for exercise in body["days"][0]["exercises"]
    )
    assert "מכונה" not in text
    assert "כבל" not in text


def test_monthly_progression_schedule_respects_experience_level(tmp_path):
    client, _ = make_client_and_db(tmp_path)

    beginner = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית חודשית למתחיל בלי ציוד", "days_per_week": 2},
    ).json()
    advanced = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית חודשית למתקדם עם משקל גוף", "days_per_week": 3},
    ).json()

    assert beginner["experience_level"] == "beginner"
    assert "2 סטים" in beginner["progression_schedule"][0]
    assert "לא להוסיף סטים" in " ".join(beginner["progression_schedule"])
    assert any("RPE 7" in item and "RIR 2-4" in item for item in beginner["progression_schedule"])
    assert any("מאמץ מילולי" in item and "לשמור" in item for item in beginner["progression_schedule"])
    assert any("20-30%" in item and "לא להעלות עומס" in item for item in beginner["progression_schedule"])
    assert "דילואד" in beginner["progression_model"]
    assert "ביצועים יורדים" in beginner["progression_model"]
    assert advanced["experience_level"] == "advanced"
    assert "RPE 7-9" in advanced["progression_schedule"][0]
    assert any("RPE/RIR" in item for item in advanced["progression_schedule"])
    assert any("סט עזר אחד בלבד" in item for item in advanced["progression_schedule"])
    assert any("20-40%" in item and "לפני בלוק נוסף" in item for item in advanced["progression_schedule"])
    assert "דילואד" in advanced["progression_model"]
    assert "20-40%" in advanced["progression_model"]


def test_two_week_progression_schedule_respects_experience_level(tmp_path):
    client, _ = make_client_and_db(tmp_path)

    beginner = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית לשבועיים למתחיל בלי ציוד", "days_per_week": 2},
    ).json()
    advanced = client.post(
        "/api/workout-plans",
        json={"prompt": "תבנה לי תוכנית לשבועיים למתקדם עם משקל גוף", "days_per_week": 3},
    ).json()

    assert beginner["plan_type"] == "two_week_plan"
    assert beginner["experience_level"] == "beginner"
    assert len(beginner["progression_schedule"]) == 2
    assert "RPE 5-7" in beginner["progression_schedule"][0]
    assert any("RPE 7" in item and "RIR 2-4" in item for item in beginner["progression_schedule"])
    assert any("מאמץ מילולי" in item and "לשמור" in item for item in beginner["progression_schedule"])
    assert any("לא להתקדם" in item and "לא להוסיף סטים עדיין" in item for item in beginner["progression_schedule"])
    assert advanced["plan_type"] == "two_week_plan"
    assert advanced["experience_level"] == "advanced"
    assert len(advanced["progression_schedule"]) == 2
    assert "RPE 7-9" in advanced["progression_schedule"][0]
    assert any("RPE/RIR" in item and "מאמץ מילולי" in item for item in advanced["progression_schedule"])
    assert any("סט עזר אחד בלבד" in item for item in advanced["progression_schedule"])
    assert any("20-30%" in item and "נפח" in item for item in advanced["progression_schedule"])


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'plans.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db


def assert_no_english_workout_guidance(plan: dict) -> None:
    guidance_texts = [
        plan.get("progression_model", ""),
        plan.get("recovery_note", ""),
        *plan.get("safety_notes", []),
    ]
    for day in plan.get("days", []):
        guidance_texts.extend(day.get("warmup", []))
        guidance_texts.extend(day.get("cooldown", []))
        guidance_texts.append(day.get("notes", ""))
        for exercise in day.get("exercises", []):
            guidance_texts.extend(
                [
                    exercise.get("notes", ""),
                    exercise.get("progression", ""),
                    exercise.get("regression", ""),
                    *exercise.get("alternatives", []),
                    *exercise.get("safety_notes", []),
                ]
            )

    text = "\n".join(str(item) for item in guidance_texts)
    forbidden = [
        "Stop ",
        "Use ",
        "Reduce ",
        "Do not ",
        "Add ",
        "single session",
        "multi week",
        "recovery",
        "hip hinge",
        "hip thrust",
        "pull-through",
        "step-up",
        "push-up",
        "RDL",
    ]
    for fragment in forbidden:
        assert fragment.lower() not in text.lower()


def assert_no_direct_gendered_hebrew_workout_guidance(plan: dict) -> None:
    guidance_texts = [
        plan.get("progression_rule", ""),
        plan.get("progression_model", ""),
        plan.get("recovery_note", ""),
        *plan.get("safety_notes", []),
    ]
    for day in plan.get("days", []):
        guidance_texts.extend(day.get("warmup", []))
        guidance_texts.append(day.get("notes", ""))
        for exercise in day.get("exercises", []):
            guidance_texts.extend(
                [
                    exercise.get("notes", ""),
                    exercise.get("progression", ""),
                    exercise.get("regression", ""),
                    *exercise.get("alternatives", []),
                    *exercise.get("safety_notes", []),
                ]
            )

    text = "\n".join(str(item) for item in guidance_texts)
    forbidden_tokens = [
        "הוסף",
        "העלה",
        "שמור",
        "עצור",
        "עבוד",
        "בחר",
        "בצע",
        "הורד",
        "הפחת",
        "קח",
        "חזור",
        "התקדם",
        "עבור",
        "השתמש",
        "התאם",
        "אסוף",
        "כבד",
        "השאר",
        "משוך",
        "הקטן",
    ]
    forbidden_fragments = [
        "אתה",
        "עצמך",
        "אל ת",
    ]
    for fragment in forbidden_tokens:
        assert not re.search(rf"(?<![\u0590-\u05ff])ו?{re.escape(fragment)}(?![\u0590-\u05ff])", text)
    for fragment in forbidden_fragments:
        assert fragment not in text


def _exercise_equipment_text(plan: dict) -> str:
    parts = []
    for day in plan.get("days", []):
        for exercise in day.get("exercises", []):
            parts.extend(
                [
                    exercise.get("name") or "",
                    exercise.get("notes") or "",
                    exercise.get("progression") or "",
                    exercise.get("regression") or "",
                    " ".join(exercise.get("alternatives") or []),
                ]
            )
    return " ".join(parts)


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
