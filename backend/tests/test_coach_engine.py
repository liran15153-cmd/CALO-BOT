from collections.abc import Generator
from datetime import date
import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import ChatMessage, Meal, PendingAction, SafetyEvent, UsageEvent, Workout, WorkoutExercise, WorkoutLog, WorkoutPlan
from backend.app.services.workout_service import WorkoutService


def test_chat_endpoint_generates_beginner_workout_without_provider_key(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "Build me a beginner workout"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית" in body["response"] or "אימון" in body["response"]
    messages = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert [message.role for message in messages] == ["user", "coach"]
    saved_plan = db.scalar(select(WorkoutPlan))
    assert saved_plan is not None
    assert saved_plan.is_current is True


def test_chat_endpoint_does_not_block_soft_pain_messages(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "My knee hurts when I squat"})

    assert response.status_code == 200
    body = response.json()
    # Soft pain is no longer a hard block: the engine acknowledges/adapts instead.
    assert body["safety_flagged"] is False
    assert body["provider_status"] != "safety_override"
    # The audit event is still recorded.
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "pain_signal"
    assert event.severity == "advisory"
    # No safety_override usage event for soft pain.
    assert db.scalar(select(UsageEvent).where(UsageEvent.provider == "safety_override")) is None


def test_chat_endpoint_does_not_save_non_food_i_had_pain_as_meal(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "I had knee pain during squats"})

    assert response.status_code == 200
    assert db.scalar(select(SafetyEvent).where(SafetyEvent.event_type == "pain_signal")) is not None
    assert db.scalar(select(Meal)) is None


def test_chat_endpoint_still_blocks_red_flag_symptoms(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "יש לי כאב בחזה וסחרחורת בזמן אימון"})

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is True
    assert body["provider_status"] == "safety_override"
    assert "לעצור" in body["response"]
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "dangerous_symptoms"
    # No workout plan saved when red-flag safety fires.
    assert db.scalar(select(WorkoutPlan)) is None


def test_chat_endpoint_pain_plus_plan_request_builds_modified_plan(tmp_path):
    """Knee pain + plan request → plan is saved with knee limitations, response
    acknowledges pain and stops the user from pushing through it."""
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "יש לי כאב ברך שמאל, תבנה לי תוכנית כוח של 2 ימים בלי ציוד"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is False
    assert body["provider_status"] == "local_tool"
    # Pain acknowledged.
    assert "כאב" in body["response"]
    assert "ברך" in body["response"]
    assert "לא אבחנה" in body["response"]
    assert "טווח ללא כאב" in body["response"]
    assert "לעצור" in body["response"] or "לא לדחוף" in body["response"]
    assert "ריפוי" not in body["response"]
    assert "טיפול" not in body["response"]
    # Plan was actually saved.
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    # Plan's safety notes and limitations carry the knee context forward.
    safety_notes = saved.plan_json.get("safety_notes") or []
    decision_inputs = saved.plan_json.get("decision_inputs") or {}
    assert "ברך" in (decision_inputs.get("limitations") or "") or any(
        "ברך" in note for note in safety_notes
    )


def test_chat_endpoint_vague_pain_plan_asks_critical_clarification_without_saving(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "יש לי כאב, תבנה לי תוכנית כוח"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is False
    assert body["provider_status"] == "local_tool"
    assert "איפה הכאב" in body["response"]
    assert "חד" in body["response"]
    assert "אל תדחוף דרך כאב" in body["response"]
    assert db.scalar(select(WorkoutPlan)) is None
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "pain_signal"


def test_chat_endpoint_red_flag_blocks_plan_even_with_plan_request(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "כואב לי החזה, תבנה לי תוכנית כוח של 3 ימים"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is True
    assert "לעצור" in body["response"]
    assert db.scalar(select(WorkoutPlan)) is None


def test_chat_endpoint_uses_safety_response_for_extreme_diet_request(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "I want to lose 8kg in a month. Give me a 900 calorie meal plan."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is True
    assert body["provider_status"] == "safety_override"
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "extreme_dieting"
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "safety_override"))
    assert usage is not None


def test_chat_endpoint_dispatches_workout_plan_intent_to_module(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "Create a 2-day dumbbell workout plan"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית אימון" in body["response"]
    assert "תרגיל ראשון" in body["response"]
    assert "RPE או מאמץ מילולי" in body["response"]
    assert "full_body" not in body["response"]
    assert "upper_lower" not in body["response"]
    assert_no_raw_plan_labels(body["response"])
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.days_per_week == 2
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None
    assert_no_storage_confirmation(body["response"])


def test_chat_new_monthly_plan_with_current_creates_candidate_and_asks_for_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]

    response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "רוצה למחוק את הישנה" in body["response"]
    assert "כן להחליף" in body["response"]
    assert "להשאיר קיימת" in body["response"]
    assert_no_storage_confirmation(body["response"])
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert candidate is not None
    assert candidate.is_current is False
    assert candidate.plan_json["plan_type"] == "monthly_plan"
    assert len(candidate.plan_json["progression_schedule"]) == 4
    assert "שבוע 4" in candidate.plan_json["progression_model"]
    assert "דילואד" in candidate.plan_json["progression_model"]
    assert "20-40%" in candidate.plan_json["progression_model"]
    assert "דילואד" not in body["response"]
    coach_message = db.get(ChatMessage, body["coach_message_id"])
    assert coach_message is not None
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert pending is not None
    assert pending.action_type == "activate_workout_plan"
    assert pending.subject_id == candidate.id
    assert pending.payload_json["current_plan_id"] == current_id
    assert coach_message.metadata_json["pending_action_id"] == pending.id
    assert "candidate_plan_id" not in coach_message.metadata_json
    assert "current_plan_id" not in coach_message.metadata_json


def test_chat_new_two_week_plan_with_current_creates_candidate_and_keeps_current(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]

    response = client.post(
        "/api/chat",
        json={"message": "תבנה לי תוכנית לשבועיים עם משקולות"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית לשבועיים" in body["response"]
    assert "שבוע 1" in body["response"]
    assert "שבוע 2" in body["response"]
    assert "היא לא מחליפה עדיין" in body["response"]
    assert "כן להחליף" in body["response"]
    assert_no_storage_confirmation(body["response"])
    assert_no_raw_plan_labels(body["response"])
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert candidate is not None
    assert candidate.is_current is False
    assert candidate.plan_json["plan_type"] == "two_week_plan"
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert pending is not None
    assert pending.action_type == "activate_workout_plan"
    assert pending.subject_id == candidate.id


def test_chat_hebrew_full_plan_replacement_creates_candidate_not_scoped_edit(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]

    response = client.post(
        "/api/chat",
        json={"message": "תחליף לי את כל התוכנית לתוכנית חודשית חדשה במכון"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "בניתי תוכנית חדשה" in body["response"]
    assert "היא לא מחליפה עדיין" in body["response"]
    assert "כן להחליף" in body["response"]
    assert "איזה שינוי נקודתי" not in body["response"]
    assert_no_raw_plan_labels(body["response"])
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert candidate is not None
    assert candidate.is_current is False
    assert candidate.plan_json["plan_type"] == "monthly_plan"
    assert "חדר כושר" in candidate.plan_json["equipment_needed"]
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert pending is not None
    assert pending.subject_id == candidate.id
    assert pending.payload_json["current_plan_id"] == current_id


def test_chat_confirms_plan_replacement_deletes_old_plan_and_keeps_log_history(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_body = current_response.json()
    current_id = current_body["id"]
    workout_id = current_body["days"][0]["workout_id"]
    log_response = client.post("/api/workout-logs", json={"workout_id": workout_id, "status": "completed"})
    log_id = log_response.json()["id"]
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    candidate_body = candidate_response.json()
    session_id = candidate_body["session_id"]
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert candidate is not None

    response = client.post("/api/chat", json={"session_id": session_id, "message": "כן, תחליף ותמחק את הישנה"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "התוכנית החדשה פעילה" in body["response"]
    assert "לתעד RPE או מאמץ מילולי, כאב ומה הושלם" in body["response"]
    assert "לא לנחש" in body["response"]
    assert_no_storage_confirmation(body["response"])
    assert db.get(WorkoutPlan, current_id) is None
    activated = db.get(WorkoutPlan, candidate.id)
    assert activated is not None
    assert activated.is_current is True
    old_workout = db.get(Workout, workout_id)
    assert old_workout is None
    preserved_log = db.get(WorkoutLog, log_id)
    assert preserved_log is not None
    assert preserved_log.workout_id is None
    resolved = db.scalar(select(PendingAction).where(PendingAction.subject_id == candidate.id))
    assert resolved is not None
    assert resolved.status == "resolved"
    assert resolved.resolution == "confirmed"


def test_chat_declines_plan_replacement_keeps_current_and_removes_candidate(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    session_id = candidate_response.json()["session_id"]
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert candidate is not None

    response = client.post("/api/chat", json={"session_id": session_id, "message": "לא, תשאיר את הקיימת"})

    assert response.status_code == 200
    body = response.json()
    assert "התוכנית הפעילה נשארת" in body["response"]
    assert_no_storage_confirmation(body["response"])
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    assert db.get(WorkoutPlan, candidate.id) is None
    resolved = db.scalar(select(PendingAction).where(PendingAction.subject_id == candidate.id))
    assert resolved is not None
    assert resolved.status == "resolved"
    assert resolved.resolution == "declined"


def test_chat_unrelated_message_does_not_resolve_pending_plan_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    session_id = candidate_response.json()["session_id"]
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert pending is not None

    response = client.post("/api/chat", json={"session_id": session_id, "message": "What is RPE?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "RPE" in body["response"]
    db.refresh(pending)
    assert pending.status == "pending"
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True


def test_chat_ambiguous_yes_does_not_confirm_pending_plan_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    session_id = candidate_response.json()["session_id"]
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert pending is not None
    assert candidate is not None

    response = client.post("/api/chat", json={"session_id": session_id, "message": "כן אבל יש לי שאלה על RPE"})

    assert response.status_code == 200
    assert "התוכנית החדשה פעילה" not in response.json()["response"]
    db.refresh(pending)
    assert pending.status == "pending"
    assert db.get(WorkoutPlan, current_id).is_current is True
    assert db.get(WorkoutPlan, candidate.id) is not None
    assert db.get(WorkoutPlan, candidate.id).is_current is False


def test_chat_save_new_one_off_does_not_confirm_pending_plan_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    session_id = candidate_response.json()["session_id"]
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert pending is not None
    assert candidate is not None

    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Give me a short workout for today and save new one-off, 20 minutes."},
    )

    assert response.status_code == 200
    db.refresh(pending)
    assert pending.status == "pending"
    assert pending.subject_id == candidate.id
    assert db.get(WorkoutPlan, current_id).is_current is True
    db.refresh(candidate)
    assert candidate.is_current is False
    plans = db.scalars(select(WorkoutPlan)).all()
    one_offs = [plan for plan in plans if (plan.plan_json or {}).get("plan_type") == "single_workout"]
    assert len(one_offs) == 1
    assert one_offs[0].is_current is False


def test_chat_ambiguous_no_does_not_decline_pending_plan_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    session_id = candidate_response.json()["session_id"]
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert pending is not None
    assert candidate is not None

    response = client.post("/api/chat", json={"session_id": session_id, "message": "לא בטוח, מה ההבדל בין התוכניות?"})

    assert response.status_code == 200
    assert "התוכנית הפעילה נשארת" not in response.json()["response"]
    db.refresh(pending)
    assert pending.status == "pending"
    assert db.get(WorkoutPlan, current_id).is_current is True
    assert db.get(WorkoutPlan, candidate.id) is not None
    assert db.get(WorkoutPlan, candidate.id).is_current is False


def test_chat_replacement_question_does_not_confirm_pending_plan_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    session_id = candidate_response.json()["session_id"]
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    candidate = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert pending is not None
    assert candidate is not None

    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "מה זה אומר להחליף את התוכנית?"},
    )

    assert response.status_code == 200
    assert "התוכנית החדשה פעילה" not in response.json()["response"]
    db.refresh(pending)
    assert pending.status == "pending"
    assert db.get(WorkoutPlan, current_id).is_current is True
    assert db.get(WorkoutPlan, candidate.id) is not None
    assert db.get(WorkoutPlan, candidate.id).is_current is False

    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "ומה זה אומר לא להחליף?"},
    )

    assert response.status_code == 200
    assert "התוכנית הפעילה נשארת" not in response.json()["response"]
    db.refresh(pending)
    assert pending.status == "pending"
    assert db.get(WorkoutPlan, current_id).is_current is True
    assert db.get(WorkoutPlan, candidate.id) is not None
    assert db.get(WorkoutPlan, candidate.id).is_current is False


def test_chat_scoped_no_bench_edit_updates_current_plan_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Create a 3-day dumbbell plan with bench",
            "days_per_week": 3,
            "equipment": ["dumbbells", "bench"],
        },
    )
    current_id = plan_response.json()["id"]

    response = client.post("/api/chat", json={"message": "אין לי ספסל בתוכנית, תחליף רק את מה שצריך"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "בלי לבנות חדשה" in body["response"]
    assert "ספסל" in body["response"]
    plans = db.scalars(select(WorkoutPlan)).all()
    assert [plan.id for plan in plans] == [current_id]
    saved = db.get(WorkoutPlan, current_id)
    assert saved is not None
    assert saved.is_current is True
    assert "bench" not in [item.lower() for item in saved.equipment_needed]
    serialized = json.dumps(saved.plan_json, ensure_ascii=False)
    assert "ספסל" not in serialized
    rows = db.scalars(select(WorkoutExercise)).all()
    assert rows
    assert "ספסל" not in json.dumps([row.alternatives for row in rows], ensure_ascii=False)
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "remove_bench"
    assert db.scalar(select(PendingAction)) is None


def test_chat_plan_change_summary_uses_recent_structured_edit(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post(
        "/api/workout-plans",
        json={
            "prompt": "Create a 2-day dumbbell plan with bench",
            "days_per_week": 2,
            "equipment": ["dumbbells", "bench"],
        },
    )
    edit_response = client.post("/api/chat", json={"message": "no bench in my plan, replace only what needs it"})
    assert edit_response.status_code == 200
    assert edit_response.json()["provider_status"] == "local_tool"

    response = client.post("/api/chat", json={"message": "מה השתנה לי בתוכנית?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "הסרתי שימוש בספסל" in body["response"]
    assert "לא החלפתי את כל התוכנית" in body["response"]
    assert "RPE" in body["response"]
    coach_message = db.get(ChatMessage, body["coach_message_id"])
    assert coach_message.metadata_json["intent"] == "workout_plan_change_summary"


def test_chat_current_plan_summary_uses_saved_plan_without_long_dump(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day dumbbell plan", "days_per_week": 3, "equipment": ["dumbbells"]},
    ).json()

    response = client.post("/api/chat", json={"message": "תראה לי את התוכנית שלי"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "התוכנית הפעילה שלך" in body["response"]
    assert plan["name"] in body["response"]
    assert "תקציר ימים" in body["response"]
    assert "לא מדביק כאן את כל התוכנית" in body["response"]
    assert "RPE" in body["response"]
    assert len(body["response"]) < 900
    coach_message = db.get(ChatMessage, body["coach_message_id"])
    assert coach_message.metadata_json["intent"] == "current_workout_plan_summary"


def test_chat_next_workout_summary_uses_loggable_saved_workout(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day dumbbell plan", "days_per_week": 3, "equipment": ["dumbbells"]},
    ).json()

    response = client.post("/api/chat", json={"message": "פתח לי את האימון הבא"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "האימון הבא שלך" in body["response"]
    assert "RPE" in body["response"]
    coach_message = db.get(ChatMessage, body["coach_message_id"])
    assert coach_message.metadata_json["intent"] == "next_workout_summary"
    assert coach_message.metadata_json["next_workout_id"] == plan["days"][0]["workout_id"]
    assert plan["days"][0]["exercises"][0]["exercise_id"] in coach_message.metadata_json["exercise_ids"]


def test_chat_workout_log_after_no_bench_substitution_keeps_progression_generic(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Create a one day dumbbell plan with bench",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["dumbbells", "bench"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    target_exercise = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )
    edit_response = client.post("/api/chat", json={"message": "אין לי ספסל בתוכנית, תחליף רק את מה שצריך"})
    assert edit_response.status_code == 200

    edited_workout = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_workout["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )
    assert "ספסל" not in json.dumps(edited_exercise.get("alternatives") or [], ensure_ascii=False)
    assert "ציוד חסר" in edited_exercise["notes"]

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי לחיצת רצפה עם משקולות 3 סטים 10,10,9 חזרות, RPE 7, בלי כאב"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שלב אחד" in body["response"]
    assert "רק ל" not in body["response"]
    assert "ספסל" not in body["response"]
    logs = db.scalars(select(WorkoutLog).order_by(WorkoutLog.id)).all()
    assert logs[-1].workout_id == edited_workout["id"]

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    adjusted = next(
        exercise
        for exercise in next_response.json()["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert adjusted["progression_next_step"] is None


def test_chat_scoped_reduce_volume_edit_updates_sets_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 2-day beginner plan", "days_per_week": 2},
    )
    current_id = plan_response.json()["id"]
    saved = db.get(WorkoutPlan, current_id)
    before_sets = saved.plan_json["days"][0]["exercises"][0]["sets"]

    response = client.post("/api/chat", json={"message": "תוריד נפח מהתוכנית השבוע, אני עייף"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "הורדתי נפח" in body["response"]
    assert "בלי לבנות חדשה" in body["response"]
    db.refresh(saved)
    after_sets = saved.plan_json["days"][0]["exercises"][0]["sets"]
    assert after_sets == str(max(1, int(before_sets) - 1))
    first_workout = db.scalar(select(Workout).where(Workout.plan_id == current_id).order_by(Workout.id))
    first_row = db.scalar(select(WorkoutExercise).where(WorkoutExercise.workout_id == first_workout.id).order_by(WorkoutExercise.id))
    assert first_row.sets == after_sets
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "reduce_volume"
    assert len(db.scalars(select(WorkoutPlan)).all()) == 1
    assert db.scalar(select(PendingAction)) is None


def test_chat_vague_scoped_plan_edit_asks_one_question_without_changing_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day beginner plan", "days_per_week": 2})
    current_id = plan_response.json()["id"]
    saved = db.get(WorkoutPlan, current_id)
    before = json.dumps(saved.plan_json, ensure_ascii=False, sort_keys=True)

    response = client.post("/api/chat", json={"message": "תשנה לי את התוכנית"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "איזה שינוי נקודתי" in body["response"]
    assert "להחליף תרגיל" in body["response"]
    db.refresh(saved)
    after = json.dumps(saved.plan_json, ensure_ascii=False, sort_keys=True)
    assert after == before
    assert db.scalar(select(PendingAction)) is None


def test_chat_scoped_row_machine_unavailable_updates_pull_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 4,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    current_id = plan_response.json()["id"]
    target_exercise = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_pull"
    )

    response = client.post("/api/chat", json={"message": "אין לי מכונה לחתירה בתוכנית, תחליף רק את זה"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "בלי לבנות תוכנית חדשה" in body["response"]
    assert "חתירה" in body["response"]
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []

    saved = db.get(WorkoutPlan, current_id)
    db.refresh(saved)
    row = db.get(WorkoutExercise, target_exercise["exercise_id"])
    assert row is not None
    assert row.name == "חתירת משקולת יד בתמיכה"
    assert not any("מכונה" in alternative for alternative in row.alternatives)
    assert any("גומייה" in alternative or "כבל" in alternative for alternative in row.alternatives)
    assert "מכונת חתירה לא זמינה" in row.notes
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "replace_row_machine"


def test_chat_scoped_cable_unavailable_removes_cable_refs_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 4,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    current_id = plan_response.json()["id"]
    before_name_alt_text = json.dumps(
        [
            {"name": exercise["name"], "alternatives": exercise.get("alternatives", [])}
            for day in plan_response.json()["days"]
            for exercise in day["exercises"]
        ],
        ensure_ascii=False,
    )
    assert "כבל" in before_name_alt_text or "פולי" in before_name_alt_text

    response = client.post("/api/chat", json={"message": "אין לי כבלים בתוכנית, תחליף רק את מה שצריך"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "בלי לבנות תוכנית חדשה" in body["response"]
    assert "כבל" in body["response"]
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []

    saved = db.get(WorkoutPlan, current_id)
    db.refresh(saved)
    saved_name_alt_text = json.dumps(
        [
            {"name": exercise["name"], "alternatives": exercise.get("alternatives", [])}
            for day in saved.plan_json["days"]
            for exercise in day["exercises"]
        ],
        ensure_ascii=False,
    )
    assert "כבל" not in saved_name_alt_text
    assert "פולי" not in saved_name_alt_text
    assert any(
        "כבל/פולי חסר" in (exercise.get("notes") or "")
        for day in saved.plan_json["days"]
        for exercise in day["exercises"]
    )
    leg_press = next(
        (
            exercise
            for day in saved.plan_json["days"]
            for exercise in day["exercises"]
            if "לחיצת רגליים" in exercise["name"]
        ),
        None,
    )
    assert leg_press is not None
    assert "כבל/פולי חסר" not in (leg_press.get("notes") or "")
    assert not any("חזה" in alternative for alternative in leg_press.get("alternatives", []))
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "remove_cable"
    assert saved.plan_json["plan_edit_history"][-1]["changed_exercises"] > 0

    rows = db.scalars(select(WorkoutExercise)).all()
    row_name_alt_text = json.dumps(
        [{"name": row.name, "alternatives": row.alternatives or []} for row in rows],
        ensure_ascii=False,
    )
    assert "כבל" not in row_name_alt_text
    assert "פולי" not in row_name_alt_text


def test_chat_scoped_cable_unavailable_removes_metadata_only_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 2,
            "equipment": ["bodyweight"],
        },
    )
    current_id = plan_response.json()["id"]
    saved = db.get(WorkoutPlan, current_id)
    saved.equipment_needed = ["bodyweight", "כבל"]
    plan_json = dict(saved.plan_json)
    plan_json["equipment_needed"] = ["bodyweight", "כבל"]
    decision_inputs = dict(plan_json.get("decision_inputs") or {})
    decision_inputs["equipment"] = ["bodyweight", "כבל"]
    plan_json["decision_inputs"] = decision_inputs
    saved.plan_json = plan_json
    db.commit()

    exercise_text = json.dumps(
        [
            {"name": exercise["name"], "alternatives": exercise.get("alternatives", [])}
            for day in saved.plan_json["days"]
            for exercise in day["exercises"]
        ],
        ensure_ascii=False,
    )
    assert "כבל" not in exercise_text
    assert "פולי" not in exercise_text

    response = client.post("/api/chat", json={"message": "אין לי כבלים בתוכנית, תחליף רק את מה שצריך"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "בלי לבנות תוכנית חדשה" in body["response"]
    assert "איזה תרגיל בדיוק" not in body["response"]
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []

    db.refresh(saved)
    assert "כבל" not in saved.equipment_needed
    assert "כבל" not in saved.plan_json["equipment_needed"]
    assert "כבל" not in saved.plan_json["decision_inputs"]["equipment"]
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "remove_cable"
    assert saved.plan_json["plan_edit_history"][-1]["changed_exercises"] == 0


def test_chat_workout_log_after_cable_substitution_keeps_progression_generic(tmp_path):
    client, db = make_client_and_db(tmp_path)
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
    edit_response = client.post("/api/chat", json={"message": "אין לי כבלים בתוכנית, תחליף רק את מה שצריך"})
    assert edit_response.status_code == 200

    edited_workout = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_workout["exercises"]
        if "כבל/פולי חסר" in (exercise.get("notes") or "")
    )

    response = client.post(
        "/api/chat",
        json={
            "message": (
                f"תעד אימון: עשיתי {edited_exercise['name']} 3 סטים 10,10,9 חזרות, "
                "RPE 7, בלי כאב"
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שלב אחד" in body["response"]
    assert "כבל" not in body["response"]
    assert "פולי" not in body["response"]
    logs = db.scalars(select(WorkoutLog).order_by(WorkoutLog.id)).all()
    assert logs[-1].workout_id == edited_workout["id"]

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    adjusted = next(
        exercise
        for exercise in next_response.json()["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert adjusted["adjustment"] == "substitution_progression_gate"
    assert adjusted["progression_next_step"] is None


def test_chat_workout_log_after_row_machine_substitution_keeps_progression_generic(tmp_path):
    client, db = make_client_and_db(tmp_path)
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
    target_exercise = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_pull"
    )
    edit_response = client.post("/api/chat", json={"message": "אין לי מכונה לחתירה בתוכנית, תחליף רק את זה"})
    assert edit_response.status_code == 200

    edited_workout = client.get("/api/workouts/next").json()
    edited_exercise = next(
        exercise
        for exercise in edited_workout["exercises"]
        if exercise["exercise_id"] == target_exercise["exercise_id"]
    )
    assert edited_exercise["name"] == "חתירת משקולת יד בתמיכה"

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי חתירת משקולת יד בתמיכה 3 סטים 10,10,9 חזרות, RPE 7, בלי כאב"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שלב אחד" in body["response"]
    assert "רק ל" not in body["response"]
    assert "חתירה בכבל" not in body["response"]
    logs = db.scalars(select(WorkoutLog).order_by(WorkoutLog.id)).all()
    assert logs[-1].workout_id == edited_workout["id"]

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    adjusted = next(
        exercise
        for exercise in next_response.json()["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert adjusted["progression_next_step"] is None


def test_chat_scoped_pushups_too_hard_regresses_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "תבנה לי תוכנית שבועית למתחיל בלי ציוד",
            "duration_weeks": 1,
            "days_per_week": 2,
            "equipment": ["bodyweight"],
            "experience_level": "beginner",
        },
    )
    current_id = plan_response.json()["id"]
    target_exercise = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )
    before_sets = target_exercise["sets"]

    response = client.post("/api/chat", json={"message": "שכיבות סמיכה קשות מדי בתוכנית, תן לי גרסה קלה יותר"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "בלי לבנות תוכנית חדשה" in body["response"]
    assert "גרסה קלה יותר" in body["response"]
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []

    saved = db.get(WorkoutPlan, current_id)
    db.refresh(saved)
    row = db.get(WorkoutExercise, target_exercise["exercise_id"])
    assert row is not None
    assert row.name == "שכיבת סמיכה על קיר"
    assert row.sets == str(max(1, int(before_sets) - 1))
    assert any("שיפוע גבוה" in alternative for alternative in row.alternatives)
    assert "קשות מדי" in row.notes
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "regress_pushup"


def test_chat_scoped_deadlift_replacement_without_reason_asks_one_question(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 4,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    current_id = plan_response.json()["id"]
    saved = db.get(WorkoutPlan, current_id)
    before = json.dumps(saved.plan_json, ensure_ascii=False, sort_keys=True)

    response = client.post("/api/chat", json={"message": "תחליף לי את הדדליפט בתוכנית"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "ציוד" in body["response"]
    assert "כאב" in body["response"]
    assert "קשה מדי" in body["response"]
    db.refresh(saved)
    after = json.dumps(saved.plan_json, ensure_ascii=False, sort_keys=True)
    assert after == before
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []


def test_chat_scoped_knee_pain_edit_updates_squat_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 4,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    current_id = plan_response.json()["id"]
    target_exercise = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "squat" or "סקוואט" in exercise["name"]
    )
    before_sets = target_exercise["sets"]

    response = client.post("/api/chat", json={"message": "כואבת לי הברך בסקוואט שבתוכנית, תחליף רק את זה"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert body["safety_flagged"] is False
    assert "בלי לבנות תוכנית חדשה" in body["response"]
    assert "טווח ללא כאב" in body["response"]
    assert db.scalar(select(SafetyEvent).where(SafetyEvent.event_type == "pain_signal")) is not None
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []

    saved = db.get(WorkoutPlan, current_id)
    db.refresh(saved)
    squat_exercises = [
        exercise
        for day in saved.plan_json["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "squat" or "סקוואט" in exercise["name"]
    ]
    assert squat_exercises
    assert any("קופסה" in exercise["name"] for exercise in squat_exercises)
    assert all(int(exercise["sets"]) >= 1 for exercise in squat_exercises)
    assert not any(
        "מדרגה" in alternative or "מכרע" in alternative or "לאנג" in alternative
        for exercise in squat_exercises
        for alternative in exercise.get("alternatives", [])
    )
    assert any(
        "ברך רגישה" in note
        for exercise in squat_exercises
        for note in exercise.get("safety_notes", [])
    )
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "pain_substitution"

    row = db.get(WorkoutExercise, target_exercise["exercise_id"])
    assert row is not None
    assert "קופסה" in row.name
    assert row.sets == str(max(1, int(before_sets) - 1))
    assert not any("מדרגה" in alternative or "מכרע" in alternative or "לאנג" in alternative for alternative in row.alternatives)
    assert "כאב ברך" in row.notes


def test_chat_scoped_shoulder_pain_edit_updates_press_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 4,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    current_id = plan_response.json()["id"]
    target_exercise = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "vertical_push"
    )
    horizontal_push = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "horizontal_push"
    )
    before_sets = target_exercise["sets"]

    response = client.post("/api/chat", json={"message": "כואבת לי הכתף בלחיצת כתפיים שבתוכנית, תחליף רק את זה"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert body["safety_flagged"] is False
    assert "בלי לבנות תוכנית חדשה" in body["response"]
    assert "טווח ללא כאב" in body["response"]
    assert db.scalar(select(SafetyEvent).where(SafetyEvent.event_type == "pain_signal")) is not None
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []

    saved = db.get(WorkoutPlan, current_id)
    db.refresh(saved)
    vertical_presses = [
        exercise
        for day in saved.plan_json["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "vertical_push"
    ]
    assert vertical_presses
    assert any("לנדמיין" in exercise["name"] for exercise in vertical_presses)
    assert any(
        "כתף רגישה" in note
        for exercise in vertical_presses
        for note in exercise.get("safety_notes", [])
    )
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "pain_substitution"

    row = db.get(WorkoutExercise, target_exercise["exercise_id"])
    assert row is not None
    assert "לנדמיין" in row.name
    assert row.sets == str(max(1, int(before_sets) - 1))
    assert "כאב כתף" in row.notes
    unchanged_row = db.get(WorkoutExercise, horizontal_push["exercise_id"])
    assert unchanged_row.name == horizontal_push["name"]


def test_chat_scoped_general_back_pain_edit_updates_hinge_without_replacement(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a four day intermediate gym hypertrophy plan",
            "duration_weeks": 4,
            "days_per_week": 4,
            "equipment": ["gym"],
            "experience_level": "intermediate",
        },
    )
    current_id = plan_response.json()["id"]
    target_exercise = next(
        exercise
        for day in plan_response.json()["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "hip_hinge"
    )
    before_sets = target_exercise["sets"]

    response = client.post("/api/chat", json={"message": "כואב לי הגב בדדליפט שבתוכנית, תחליף רק את זה"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert body["safety_flagged"] is False
    assert "בלי לבנות תוכנית חדשה" in body["response"]
    assert "טווח ללא כאב" in body["response"]
    assert "איפה הכאב" not in body["response"]
    assert db.scalar(select(SafetyEvent).where(SafetyEvent.event_type == "pain_signal")) is not None
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []

    saved = db.get(WorkoutPlan, current_id)
    db.refresh(saved)
    hinges = [
        exercise
        for day in saved.plan_json["days"]
        for exercise in day["exercises"]
        if exercise.get("movement_pattern") == "hip_hinge"
    ]
    assert hinges
    assert any("הינג" in exercise["name"] and "קיר" in exercise["name"] for exercise in hinges)
    assert any(
        "גב תחתון רגיש" in note
        for exercise in hinges
        for note in exercise.get("safety_notes", [])
    )
    assert saved.plan_json["plan_edit_history"][-1]["edit_type"] == "pain_substitution"

    row = db.get(WorkoutExercise, target_exercise["exercise_id"])
    assert row is not None
    assert "הינג" in row.name
    assert row.sets == str(max(1, int(before_sets) - 1))
    assert not any("דדליפט רומני" in alternative for alternative in row.alternatives)
    assert "כאב גב תחתון" in row.notes


def test_chat_scoped_vague_pain_edit_asks_safety_question_without_changing_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post("/api/workout-plans", json={"prompt": "Create a 2-day beginner plan", "days_per_week": 2})
    current_id = plan_response.json()["id"]
    saved = db.get(WorkoutPlan, current_id)
    before = json.dumps(saved.plan_json, ensure_ascii=True, sort_keys=True)

    response = client.post("/api/chat", json={"message": "כואב לי בתוכנית, תחליף את התרגיל"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert body["safety_flagged"] is False
    assert "איפה הכאב" in body["response"]
    assert "חד/מחמיר" in body["response"]
    assert db.scalar(select(SafetyEvent).where(SafetyEvent.event_type == "pain_signal")) is not None
    db.refresh(saved)
    after = json.dumps(saved.plan_json, ensure_ascii=True, sort_keys=True)
    assert after == before
    assert [plan.id for plan in db.scalars(select(WorkoutPlan)).all()] == [current_id]
    assert db.scalars(select(PendingAction)).all() == []


def test_chat_pending_plan_resolution_handles_missing_candidate(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    candidate_response = client.post(
        "/api/chat",
        json={"message": "Create a new 4-day workout plan for muscle with dumbbells"},
    )
    session_id = candidate_response.json()["session_id"]
    pending = db.scalar(select(PendingAction).where(PendingAction.status == "pending"))
    assert pending is not None
    assert db.get(WorkoutPlan, pending.subject_id) is not None
    pending.subject_id = 999999
    db.commit()

    response = client.post("/api/chat", json={"session_id": session_id, "message": "yes replace"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "כבר לא זמינה" in body["response"]
    db.refresh(pending)
    assert pending.status == "cancelled"
    assert pending.resolution == "candidate_missing"


def test_chat_endpoint_dispatches_single_workout_plan_without_replacing_current(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]

    response = client.post(
        "/api/chat",
        json={"message": "תן לי אימון אחד להיום, 20 דקות, בבית"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "אימון יחיד" in body["response"]
    assert "אימון חד-פעמי" in body["response"]
    assert "לא מחליף את התוכנית הפעילה" in body["response"]
    assert "להתחיל ב" in body["response"]
    assert "RPE או מאמץ מילולי" in body["response"]
    assert "לא לנחש" in body["response"]
    assert "1 ימים" not in body["response"]
    assert "ימים בשבוע" not in body["response"]
    assert_no_storage_confirmation(body["response"])
    assert_no_raw_plan_labels(body["response"])
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    one_off = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert one_off is not None
    assert one_off.plan_json["plan_type"] == "single_workout"
    assert one_off.plan_json["session_length_minutes"] == 20
    assert one_off.plan_json["equipment_needed"] == ["bodyweight"]
    assert one_off.is_current is False
    assert db.scalars(select(PendingAction)).all() == []


def test_chat_bare_hebrew_today_workout_stays_one_off_with_active_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]

    response = client.post("/api/chat", json={"message": "אימון להיום 20 דקות בלי ציוד"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "אימון יחיד" in body["response"]
    assert "אימון חד-פעמי" in body["response"]
    assert "לא מחליף את התוכנית הפעילה" in body["response"]
    assert_no_raw_plan_labels(body["response"])
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    one_off = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert one_off is not None
    assert one_off.is_current is False
    assert one_off.plan_json["plan_type"] == "single_workout"
    assert one_off.plan_json["session_length_minutes"] == 20
    assert one_off.plan_json["equipment_needed"] == ["bodyweight"]
    assert db.scalars(select(PendingAction)).all() == []


def test_chat_endpoint_infers_hebrew_single_workout_gym_duration_and_uses_neutral_saved_response(tmp_path):
    client, db = make_client_and_db(tmp_path)
    payload = valid_payload()
    payload["training_location"] = "home"
    payload["available_equipment"] = ["resistance bands"]
    payload["session_length_minutes"] = 45
    client.post("/api/onboarding", json=payload)

    response = client.post(
        "/api/chat",
        json={"message": "תן לי אימון אחד להיום בחדר כושר, 30 דקות, בלי לפנות אליי בלשון זכר או נקבה."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "אימון יחיד" in body["response"]
    assert "אימון חד-פעמי" in body["response"]
    assert "לא מחליף את התוכנית הפעילה" in body["response"]
    assert "הפעולה הבאה" in body["response"]
    assert "RPE או מאמץ מילולי" in body["response"]
    assert_no_storage_confirmation(body["response"])
    assert_no_raw_plan_labels(body["response"])
    assert "לבצע היום את היום" not in body["response"]
    assert "פתח את" not in body["response"]
    assert "מסך האימונים" not in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["plan_type"] == "single_workout"
    assert saved.plan_json["session_length_minutes"] == 30
    assert saved.plan_json["days"][0]["estimated_duration_minutes"] == 30
    assert "חדר כושר" in saved.plan_json["equipment_needed"]
    assert "bodyweight" not in saved.plan_json["equipment_needed"]
    exercise_names = [exercise["name"] for exercise in saved.plan_json["days"][0]["exercises"]]
    assert any("מכונה" in name or "משקולות" in name for name in exercise_names)


def test_chat_endpoint_dispatches_hebrew_single_workout_with_soft_pain(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "יש לי כאב ברך קל, תבנה לי אימון יחיד בבית"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert body["safety_flagged"] is False
    assert "אימון יחיד" in body["response"]
    assert "ברך" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["plan_type"] == "single_workout"
    assert "ברך" in (saved.plan_json["decision_inputs"].get("limitations") or "")


def test_chat_endpoint_dispatches_manual_meal_log_intent_to_module(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "Log meal: protein shake with 25g protein"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "ארוחה" in body["response"]
    saved = db.scalar(select(Meal))
    assert saved is not None
    assert saved.calories_min is not None
    assert_no_storage_confirmation(body["response"])


def test_chat_endpoint_logs_workout_with_coaching_response_not_save_confirmation(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "Log workout: I did 3 sets of 10 goblet squats, RPE 7, no pain."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "RPE 7" in body["response"]
    assert_no_storage_confirmation(body["response"])
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.status == "completed"


def test_chat_endpoint_logs_meal_with_coaching_response_not_save_confirmation(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "I ate rice, chicken breast, salad and tahini for lunch."})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "קלוריות" in body["response"]
    assert "חלבון" in body["response"]
    assert_no_storage_confirmation(body["response"])
    saved_meal = db.scalar(select(Meal))
    assert saved_meal is not None


def test_chat_endpoint_logs_workout_with_negated_pain_without_safety_override(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי דדליפט רומני 3 סטים 10,10,9 עם 18 קילו, RPE 8, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert body["safety_flagged"] is False
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.status == "completed"
    assert saved_log.pain_flag is False
    assert db.scalar(select(SafetyEvent)) is None


def test_chat_endpoint_hebrew_rir_log_is_exercise_level_evidence(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "\u05ea\u05e2\u05d3 \u05d0\u05d9\u05de\u05d5\u05df: "
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10 \u05e2\u05dd 50 \u05e7\u05f4\u05d2, "
                "RIR 2, \u05d1\u05dc\u05d9 \u05db\u05d0\u05d1."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "\u05d7\u05e1\u05e8 \u05ea\u05e8\u05d2\u05d9\u05dc \u05de\u05e8\u05db\u05d6\u05d9" not in body["response"]
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.status == "completed"
    assert saved_log.rpe is None
    assert saved_log.pain_flag is False
    result = saved_log.exercise_results[0]
    assert result["exercise"] == "\u05dc\u05d7\u05d9\u05e6\u05ea \u05d7\u05d6\u05d4"
    assert result["rir"] == 2


def test_chat_endpoint_hebrew_rir_log_targets_next_workout_for_progression(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a one day beginner gym plan",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["gym"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    workout_id = plan_response.json()["days"][0]["workout_id"]

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "\u05ea\u05e2\u05d3 \u05d0\u05d9\u05de\u05d5\u05df: "
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10 \u05e2\u05dd 50 \u05e7\u05f4\u05d2, "
                "\u05e0\u05e9\u05d0\u05e8\u05d5 \u05dc\u05d9 2 \u05d7\u05d6\u05e8\u05d5\u05ea "
                "\u05d1\u05e8\u05d6\u05e8\u05d1\u05d4, \u05d1\u05dc\u05d9 \u05db\u05d0\u05d1."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "RIR 2" in body["response"]
    assert "RPE/RIR" in body["response"]
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.workout_id == workout_id
    assert saved_log.rpe is None
    assert saved_log.exercise_results[0]["rir"] == 2

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    body = next_response.json()
    assert body["adaptation"]["load_signal"] == "progress_candidate"
    assert body["adaptation"]["progress_evidence"] == "exercise_log"


def test_chat_endpoint_zero_rir_log_is_conservative(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a one day beginner gym plan",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["gym"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200

    response = client.post(
        "/api/chat",
        json={
            "message": (
                "\u05ea\u05e2\u05d3 \u05d0\u05d9\u05de\u05d5\u05df: "
                "\u05e2\u05e9\u05d9\u05ea\u05d9 \u05dc\u05d7\u05d9\u05e6\u05ea "
                "\u05d7\u05d6\u05d4 3x10, RIR 0, \u05d1\u05dc\u05d9 \u05db\u05d0\u05d1."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "RIR 0" in body["response"]
    assert "\u05dc\u05d0 \u05dc\u05d4\u05d5\u05e1\u05d9\u05e3" in body["response"]
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.exercise_results[0]["rir"] == 0

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    next_body = next_response.json()
    assert next_body["adaptation"]["load_signal"] == "recovery_needed"
    assert next_body["adaptation"]["exercise_adjustments"][0]["reason"] == "near_failure_rir"


def test_chat_endpoint_high_rir_log_recommends_small_underload_adjustment(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a one day beginner gym plan",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["gym"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    exercise = plan_response.json()["days"][0]["exercises"][0]

    response = client.post(
        "/api/chat",
        json={"message": f"תעד אימון: עשיתי {exercise['name']} 3x10, RIR 5, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert "RIR 5" in body["response"]
    assert "RIR 1-3" in body["response"]
    assert "\u05e2\u05d5\u05de\u05e1 \u05e7\u05d8\u05df" in body["response"]
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.exercise_results[0]["rir"] == 5

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    next_body = next_response.json()
    assert next_body["adaptation"]["load_signal"] == "progress_candidate"
    assert next_body["adaptation"]["exercise_adjustments"][0]["reason"] == "high_rir_underload"


def test_chat_endpoint_natural_hebrew_underload_log_recommends_small_adjustment(tmp_path):
    client, db = make_client_and_db(tmp_path)
    plan_response = client.post(
        "/api/workout-plans",
        json={
            "prompt": "Build a one day beginner gym plan",
            "duration_weeks": 1,
            "days_per_week": 1,
            "equipment": ["gym"],
            "experience_level": "beginner",
        },
    )
    assert plan_response.status_code == 200
    exercise = plan_response.json()["days"][0]["exercises"][0]

    response = client.post(
        "/api/chat",
        json={"message": f"תעד אימון: עשיתי {exercise['name']} 3x10, היה קל מדי ונשאר לי מלא כוח, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert "קל מדי" in body["response"]
    assert "עומס קטן" in body["response"]
    assert "RPE" not in body["response"]
    assert "RIR" not in body["response"]
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.rpe is None
    assert saved_log.exercise_results[0].get("rir") is None
    assert saved_log.exercise_results[0]["effort_signal"] == "underloaded"

    next_response = client.get("/api/workouts/next")

    assert next_response.status_code == 200
    next_body = next_response.json()
    assert next_body["adaptation"]["load_signal"] == "progress_candidate"
    assert next_body["adaptation"]["exercise_adjustments"][0]["reason"] == "qualitative_underload"


def test_chat_endpoint_natural_hebrew_too_hard_log_is_conservative(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי לחיצת חזה 3x10, היה כבד מדי ובקושי סיימתי, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert "קשה או כבד מדי" in body["response"]
    assert "להוריד מעט" in body["response"]
    assert "RPE" not in body["response"]
    assert "RIR" not in body["response"]
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.rpe is None
    assert saved_log.exercise_results[0].get("rir") is None
    assert saved_log.exercise_results[0]["effort_signal"] == "too_hard"


def test_chat_endpoint_natural_hebrew_controlled_log_keeps_verbal_effort(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי לחיצת חזה 3x10, היה מאתגר אבל בשליטה, בלי כאב."},
    )

    assert response.status_code == 200
    body = response.json()
    assert "בשליטה" in body["response"]
    assert "לחזור על אותו מבנה" in body["response"]
    assert "RPE 1-10" in body["response"]
    assert "RIR" in body["response"]
    assert "מעלים עומס" in body["response"]
    saved_log = db.scalar(select(WorkoutLog))
    assert saved_log is not None
    assert saved_log.rpe is None
    assert saved_log.exercise_results[0].get("rir") is None
    assert saved_log.exercise_results[0]["effort_signal"] == "controlled"


def test_chat_workout_log_for_progression_gate_asks_for_missing_rpe(tmp_path):
    client, db = make_client_and_db(tmp_path)
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
    clean_log = client.post(
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
    assert clean_log.status_code == 200
    assert any(
        exercise["adjustment"] == "substitution_progression_gate"
        for exercise in client.get("/api/workouts/next").json()["execution_plan"]["adjusted_exercises"]
    )

    response = client.post("/api/chat", json={"message": "סיימתי את האימון"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "חסר RPE" in body["response"]
    assert "כאב" in body["response"]
    assert "הגרסה הנוכחית" in body["response"]
    assert "לא ננחש" in body["response"]
    logs = db.scalars(select(WorkoutLog).order_by(WorkoutLog.id)).all()
    assert logs[-1].workout_id == edited_workout["id"]
    assert logs[-1].rpe is None


def test_chat_workout_log_with_session_rpe_no_pain_opens_progression_gate(tmp_path):
    client, db = make_client_and_db(tmp_path)
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

    response = client.post(
        "/api/chat",
        json={"message": "סיימתי את האימון, מאמץ 8 מתוך 10, בלי כאב"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שלב אחד" in body["response"]
    assert "לוג כללי" in body["response"]
    assert "חזרות/RPE" in body["response"]
    assert "לא לנחש" in body["response"]
    assert "חסר" not in body["response"]
    logs = db.scalars(select(WorkoutLog).order_by(WorkoutLog.id)).all()
    assert logs[-1].workout_id == edited_workout["id"]
    assert logs[-1].rpe == 8

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    execution = next_response.json()["execution_plan"]
    adjusted = next(
        exercise
        for exercise in execution["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert next_response.json()["adaptation"]["progress_evidence"] == "session_rpe_no_pain"
    assert execution["load_signal"] == "progress_candidate"
    assert adjusted["adjustment"] == "substitution_progression_gate"
    assert "שלב אחד" in adjusted["execution_note"]
    assert "לוג" in adjusted["execution_note"]
    assert "כללי" in adjusted["execution_note"]
    assert "חזרות/RPE" in adjusted["execution_note"]
    assert "לא לנחש" in adjusted["execution_note"]


def test_chat_workout_log_with_exercise_reps_names_next_progression_step(tmp_path):
    client, db = make_client_and_db(tmp_path)
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

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי שכיבת סמיכה על קיר 1 סט 10 חזרות, RPE 8, בלי כאב"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שיפוע גבוה" in body["response"]
    assert "לא לנחש" in body["response"]
    assert "לוג כללי" not in body["response"]
    logs = db.scalars(select(WorkoutLog).order_by(WorkoutLog.id)).all()
    assert logs[-1].workout_id == edited_workout["id"]
    assert logs[-1].exercise_results

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    adjusted = next(
        exercise
        for exercise in next_response.json()["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert adjusted["progression_next_step"] == "שכיבת סמיכה בשיפוע גבוה"


def test_chat_workout_log_after_pain_substitution_keeps_progression_generic(tmp_path):
    client, db = make_client_and_db(tmp_path)
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

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי סקוואט לקופסה בטווח קצר 1 סט 10 חזרות, RPE 7, בלי כאב"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שלב אחד" in body["response"]
    assert "רק ל" not in body["response"]
    assert "לא לנחש" in body["response"]
    assert "ישיבה-קימה" not in body["response"]
    logs = db.scalars(select(WorkoutLog).order_by(WorkoutLog.id)).all()
    assert logs[-1].workout_id == edited_workout["id"]

    next_response = client.get("/api/workouts/next")
    assert next_response.status_code == 200
    adjusted = next(
        exercise
        for exercise in next_response.json()["execution_plan"]["adjusted_exercises"]
        if exercise["source_exercise_id"] == edited_exercise["exercise_id"]
    )
    assert adjusted["progression_next_step"] is None


def test_chat_endpoint_blocks_provider_when_daily_token_budget_is_spent(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("DAILY_AI_TOKEN_LIMIT", "5")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    db.add(
        UsageEvent(
            user_id=None,
            usage_date=date.today(),
            task="chat",
            provider="configured",
            model="fake-model",
            estimated_tokens_in=6,
            estimated_tokens_out=0,
        )
    )
    db.commit()

    response = client.post("/api/chat", json={"message": "How should I structure recovery tomorrow?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "budget_exceeded"
    assert "תקציב" in body["response"]
    saved = db.scalar(select(UsageEvent).where(UsageEvent.provider == "budget_exceeded"))
    assert saved is not None
    assert saved.task == "chat"


def test_chat_endpoint_replaces_non_hebrew_provider_response(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: EnglishOnlyProvider())

    response = client.post("/api/chat", json={"message": "How should I recover tomorrow?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "עברית" in body["response"]
    assert "Do a light workout" not in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert saved[-1].role == "coach"
    assert "Do a light workout" not in saved[-1].content


def test_chat_endpoint_replaces_mixed_english_provider_response(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: MixedEnglishProvider())

    response = client.post("/api/chat", json={"message": "איך להתאושש מחר?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "עברית" in body["response"]
    assert "do a light workout" not in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "do a light workout" not in saved[-1].content


def test_chat_endpoint_keeps_hebrew_provider_response_with_short_english_terms(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: HebrewWithEnglishTermsProvider(),
    )

    response = client.post("/api/chat", json={"message": "איך להתאושש מחר?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "mobility" in body["response"]
    assert "HIIT" in body["response"]
    assert "Zone 2" in body["response"]
    assert "רובה לא בעברית" not in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "Zone 2" in saved[-1].content


def test_chat_endpoint_replaces_provider_response_with_generic_echoed_english_phrase(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: EchoedGenericEnglishProvider(),
    )

    response = client.post("/api/chat", json={"message": "How should I recover tomorrow?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "recover tomorrow" not in body["response"]
    assert "עברית" in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "recover tomorrow" not in saved[-1].content


def test_chat_endpoint_strips_markdown_markers_from_provider_response(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: MarkdownProvider())

    response = client.post("/api/chat", json={"message": "איזה אימון מתאים לי היום?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "**" not in body["response"]
    assert "•" not in body["response"]
    assert "שליחות מלאות" not in body["response"]
    assert "נחת את הגוף" not in body["response"]
    assert "full body" in body["response"]
    assert "חזרות נקיות" in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "**" not in saved[-1].content
    assert "שליחות מלאות" not in saved[-1].content


def test_chat_endpoint_repairs_provider_quality_artifacts_before_saving(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: BrowserArtifactProvider())

    response = client.post("/api/chat", json={"message": "שלום, תן לי פעולה אחת קטנה להיום"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "서" not in body["response"]
    assert "reserve in reserve" not in body["response"]
    assert "even" not in body["response"]
    assert "חזרות ברזרבה" in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert saved[-1].metadata_json["quality_repair_applied"] is True
    assert saved[-1].metadata_json["quality_issues"] == []


def test_chat_endpoint_answers_creatine_question_locally(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "קריאטין מסוכן?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "קריאטין" in body["response"]
    assert "3-5" in body["response"]
    assert "רופא" in body["response"] or "דיאטן" in body["response"]
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None


def test_chat_endpoint_answers_stimulant_supplement_safety_locally(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "פרה-וורקאאוט עם הרבה קפאין ו-yohimbine לפני אימון ערב - בטוח או לוותר?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "קפאין" in body["response"]
    assert "yohimbine" in body["response"]
    assert "אימון ערב" in body["response"]
    assert "לוותר" in body["response"]
    assert "סביב אימון ערב" not in body["response"]
    assert "בטוח" not in body["response"]
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None


def test_chat_endpoint_answers_weekly_action_plan_locally_in_natural_hebrew(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "תן לי action plan קצר לשבוע עם שני אימוני כוח והליכות. בלי אנגלית מיותרת."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שני אימוני כוח" in body["response"]
    assert "הליכה" in body["response"]
    assert "לקבוע" in body["response"]
    assert "action plan" not in body["response"]
    assert "דחיפת אדמה" not in body["response"]
    assert "משיכת גוף" not in body["response"]
    assert "בהירוג" not in body["response"]
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None


def test_chat_endpoint_answers_knee_squat_substitution_locally(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "הברך רגישה בסקוואט. במה להחליף?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "כאב" in body["response"]
    assert "סקוואט לקופסה" in body["response"]
    assert "דדליפט רומני" in body["response"]
    assert "אבחן" not in body["response"]
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None


def test_chat_endpoint_answers_fitness_term_guidance_locally(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "מה עדיף באימון כוח: RPE 8 או להשאיר 2 חזרות ברזרבה?"},
    )
    hypertrophy_response = client.post(
        "/api/chat",
        json={"message": "תסביר לי היפרטרופיה, סטים קשים ו-RIR בלי להישמע כמו תרגום."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "RPE 8" in body["response"]
    assert "RIR 2" in body["response"]
    assert "80%" not in body["response"]
    assert "טנק" not in body["response"]
    assert hypertrophy_response.status_code == 200
    hypertrophy_body = hypertrophy_response.json()
    assert hypertrophy_body["provider_status"] == "local_tool"
    assert "היפרטרופיה" in hypertrophy_body["response"]
    assert "סט קשה" in hypertrophy_body["response"]
    assert "גדילת שריר" in hypertrophy_body["response"]
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None


def test_chat_endpoint_answers_explicit_rpe_rir_values_without_swapping_numbers(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "מה ההבדל בין RPE 9 לבין RIR 1?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "RPE 9" in body["response"]
    assert "RIR 1" in body["response"]
    assert "חזרה נקייה אחת" in body["response"]
    assert "1 חזרות" not in body["response"]
    assert "RPE 8" not in body["response"]
    assert "RIR 2" not in body["response"]


def test_chat_endpoint_answers_generic_rpe_question_without_assuming_values(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "What is RPE?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "RPE" in body["response"]
    assert "סולם" in body["response"] or "דירוג" in body["response"]
    assert "RPE 8" not in body["response"]
    assert "RIR 2" not in body["response"]


def test_chat_endpoint_answers_mixed_rpe_rir_prompt_without_overwriting_user_value(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "באימון Push אני מרגיש שה-RPE גבוה אבל נשאר לי RIR 3 בבנץ׳. איך לפרש את זה?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "RIR 3" in body["response"]
    assert "RIR 2" not in body["response"]
    assert "לא סתירה" in body["response"]
    assert "עייפות כללית" in body["response"]


def test_chat_endpoint_answers_doms_and_deload_guidance_locally(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    doms_response = client.post("/api/chat", json={"message": "מה זה DOMS ומה לעשות אם השרירים תפוסים?"})
    deload_response = client.post(
        "/api/chat",
        json={"message": "אני עייף כבר שבוע והביצועים יורדים. צריך דילואד?"},
    )

    assert doms_response.status_code == 200
    assert deload_response.status_code == 200
    assert doms_response.json()["provider_status"] == "local_tool"
    assert deload_response.json()["provider_status"] == "local_tool"
    assert "כאבי שרירים מאוחרים" in doms_response.json()["response"]
    assert "דילואד" in deload_response.json()["response"]
    assert "תורד" not in doms_response.json()["response"]
    assert "פחתת" not in deload_response.json()["response"]


def test_chat_endpoint_answers_zone2_and_split_choice_guidance_locally(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    zone_response = client.post("/api/chat", json={"message": "מה זה Zone 2 ואיך אדע שאני שם בלי שעון דופק?"})
    split_response = client.post(
        "/api/chat",
        json={"message": "מה עדיף לשריר: full-body או push/pull/legs? תענה כמו מאמן ישראלי."},
    )

    assert zone_response.status_code == 200
    assert split_response.status_code == 200
    assert zone_response.json()["provider_status"] == "local_tool"
    assert split_response.json()["provider_status"] == "local_tool"
    assert "בדיקת דיבור" in zone_response.json()["response"]
    assert "הואל" not in zone_response.json()["response"]
    assert "full-body" in split_response.json()["response"]
    assert "push/pull/legs" in split_response.json()["response"]
    assert "לא יש" not in split_response.json()["response"]
    assert "משרירה" not in split_response.json()["response"]


def test_chat_endpoint_answers_warmup_and_cooldown_guidance_locally(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    warmup_response = client.post("/api/chat", json={"message": "איך לעשות חימום טוב לפני אימון כוח?"})
    cooldown_response = client.post(
        "/api/chat",
        json={"message": "צריך קירור ומתיחות אחרי אימון כדי למנוע DOMS?"},
    )

    assert warmup_response.status_code == 200
    assert cooldown_response.status_code == 200
    assert warmup_response.json()["provider_status"] == "local_tool"
    assert cooldown_response.json()["provider_status"] == "local_tool"
    assert "חימום דינמי" in warmup_response.json()["response"]
    assert "סט הכנה" in warmup_response.json()["response"]
    assert "קירור" in cooldown_response.json()["response"]
    assert "לא מבטיח" in cooldown_response.json()["response"]
    assert "DOMS" in cooldown_response.json()["response"]


def test_chat_endpoint_answers_low_energy_one_action_locally(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "אין לי כוח היום, תן לי פעולה אחת קטנה"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "פעולה אחת" in body["response"]
    assert "10 דקות" in body["response"]
    assert "ספק הבינה המלאכותית לא מוגדר" not in body["response"]


def test_chat_endpoint_keeps_local_fitness_term_guidance_gender_neutral_when_requested(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    zone_response = client.post(
        "/api/chat",
        json={"message": "מה זה Zone 2 ואיך יודעים שזה הקצב הנכון? בלי לפנות אליי בלשון זכר או נקבה."},
    )
    split_response = client.post(
        "/api/chat",
        json={"message": "מה עדיף: full-body או push/pull/legs? בלי לפנות אליי בלשון זכר או נקבה."},
    )
    progression_response = client.post(
        "/api/chat",
        json={
            "message": "מה זה progressive overload ואיך להתקדם אם כל הסטים קלים? בלי לפנות אליי בלשון זכר או נקבה."
        },
    )

    assert zone_response.status_code == 200
    assert split_response.status_code == 200
    assert progression_response.status_code == 200
    for response in [
        zone_response.json()["response"],
        split_response.json()["response"],
        progression_response.json()["response"],
    ]:
        assert "אתה" not in response
        assert "מתאמן" not in response
        assert "תוכל" not in response
        assert "בחר " not in response
        assert "הוסף" not in response
        assert "תוסיף" not in response
        assert "תתקדם" not in response
        assert "הגעת" not in response
    assert "אפשר לדבר" in zone_response.json()["response"]
    assert "לבחור את המבנה" in split_response.json()["response"]
    assert "להוסיף 1-2 חזרות" in progression_response.json()["response"]


def test_chat_endpoint_answers_equipment_and_missed_workout_guidance_locally(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    equipment_response = client.post(
        "/api/chat",
        json={"message": "אני מתחיל ויש לי רק גומייה. איזה תרגיל גב לעשות במקום חתירה במכונה?"},
    )
    missed_response = client.post(
        "/api/chat",
        json={"message": "פספסתי שני אימונים השבוע. תן לי דרך לחזור בלי להרגיש שאני מתחיל מאפס."},
    )

    assert equipment_response.status_code == 200
    assert missed_response.status_code == 200
    assert equipment_response.json()["provider_status"] == "local_tool"
    assert missed_response.json()["provider_status"] == "local_tool"
    assert "חבר את הגומייה" in equipment_response.json()["response"]
    assert "התרוקן" not in equipment_response.json()["response"]
    assert "אנחת" not in missed_response.json()["response"]
    assert "בואו" not in missed_response.json()["response"]
    assert "גרסה קצרה" in missed_response.json()["response"]
    assert "זמן" in missed_response.json()["response"]
    assert "עייפות" in missed_response.json()["response"]
    assert "לא מחזירים את כל הנפח" in missed_response.json()["response"]


def test_chat_endpoint_does_not_log_negated_missed_workout_guidance(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "I did not work out yesterday, how should I continue?"})

    assert response.status_code == 200
    assert response.json()["provider_status"] == "local_tool"
    assert db.scalar(select(WorkoutLog)) is None


def test_chat_endpoint_answers_return_after_break_guidance_locally(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "לא התאמנתי חודש, איך לחזור לחדר כושר בלי להיפצע?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "60-80%" in body["response"]
    assert "RPE 5-7" in body["response"]
    assert "2-4 חזרות ברזרבה" in body["response"]
    assert "אימון פיצוי" in body["response"]
    assert "2-3 אימונים נקיים" in body["response"]
    assert db.scalar(select(WorkoutPlan)) is None


def test_chat_endpoint_answers_nutrition_guidance_locally_in_natural_hebrew(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    workout_nutrition = client.post(
        "/api/chat",
        json={
            "message": "אני מנסה לרדת קצת באחוזי שומן אבל לא רוצה לספור קלוריות. מה לאכול היום סביב אימון ערב?"
        },
    )
    image_uncertainty = client.post(
        "/api/chat",
        json={"message": "אם אעלה תמונה של קערת אורז, עוף וטחינה, כמה מדויק אפשר להעריך קלוריות? אין לי תמונה כרגע."},
    )

    assert workout_nutrition.status_code == 200
    assert image_uncertainty.status_code == 200
    assert workout_nutrition.json()["provider_status"] == "local_tool"
    assert image_uncertainty.json()["provider_status"] == "local_tool"
    assert "לחם עם דלק" not in workout_nutrition.json()["response"]
    assert "ברך" not in workout_nutrition.json()["response"]
    assert "התמקדי" not in workout_nutrition.json()["response"]
    assert "חלבון" in workout_nutrition.json()["response"]
    assert "טווח" in image_uncertainty.json()["response"]
    assert "לא מספר מדויק" in image_uncertainty.json()["response"]
    assert "מסך הארוחות" in image_uncertainty.json()["response"]
    assert "לרדידת" not in image_uncertainty.json()["response"]


def test_chat_endpoint_keeps_meal_image_guidance_local_even_with_provider_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)

    def fail_if_called(_api_key, _model):
        raise AssertionError("text provider should not handle meal image guidance")

    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", fail_if_called)

    response = client.post(
        "/api/chat",
        json={"message": "אם אעלה תמונה של שקשוקה, תוכל לתת לי קלוריות מדויקות?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "טווח" in body["response"]
    assert "לא מספר" in body["response"]
    assert "מסך הארוחות" in body["response"]


def test_chat_endpoint_sends_coaching_knowledge_to_configured_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post("/api/chat", json={"message": "איך לבנות שבוע אימונים מאוזן?"})

    assert response.status_code == 200
    assert provider.last_request is not None
    request_payload = json.loads(provider.last_request.input_text)
    knowledge = request_payload["context"]["coaching_knowledge"]
    assert any("150-300" in rule for rule in knowledge["rules"])
    assert any("כאב בחזה" in rule for rule in knowledge["safety_boundaries"])
    assert "תכנות אימונים" in knowledge["trainer_skill_domains"]
    assert any("FITT" in rule for rule in knowledge["programming_model"])
    assert any("רגרסיה" in rule for rule in knowledge["progression_regression"])
    assert any("עומס וחזרות" in item for item in knowledge["program_design_summary"])
    assert any("סקוואט" in item for item in knowledge["technique_cues_summary"])
    assert any("ביצועים יורדים" in item for item in knowledge["deload_rules"])
    assert "עברית בלבד" in provider.last_request.instructions
    assert "עברית ישראלית טבעית" in provider.last_request.instructions
    assert "אל תתרגם מילולית מונחי כושר" in provider.last_request.instructions
    assert provider.last_request.max_output_tokens <= 320
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "configured"))
    assert usage is not None
    assert usage.token_breakdown_json["system_prompt"] > 0
    assert usage.token_breakdown_json["history"] >= 0
    assert usage.token_breakdown_json["memory"] >= 0
    assert usage.token_breakdown_json["tools"] > 0
    assert usage.token_breakdown_json["message"] > 0
    assert usage.token_breakdown_json["output"] == 12
    saved = db.scalar(select(ChatMessage).where(ChatMessage.role == "coach").order_by(ChatMessage.id.desc()))
    assert saved is not None
    token_metadata = saved.metadata_json["token_breakdown"]
    assert token_metadata["total"] == usage.token_breakdown_json["total"]
    assert token_metadata["conversation_total"] == usage.token_breakdown_json["total"]


def test_chat_endpoint_uses_haiku_chat_model_by_default_for_configured_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_CHAT_MODEL", raising=False)
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    selected_models: list[str] = []

    def capture_model(_api_key, model):
        selected_models.append(model)
        return provider

    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", capture_model)

    response = client.post("/api/chat", json={"message": "איך לבנות שבוע אימונים מאוזן?"})

    assert response.status_code == 200
    assert selected_models == ["claude-haiku-4-5"]
    assert provider.last_request is not None


def test_chat_endpoint_sends_query_retrieved_knowledge_to_configured_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post("/api/chat", json={"message": "האם כפיפות בטן יורידו לי שומן בבטן?"})

    assert response.status_code == 200
    assert provider.last_request is not None
    request_payload = json.loads(provider.last_request.input_text)
    knowledge = request_payload["context"]["coaching_knowledge"]
    assert knowledge["retrieved_knowledge"][0]["topic"] == "common_fitness_myth_protocols.spot_reduction"
    assert "common_fitness_myth_protocols" not in knowledge
    assert len(str(knowledge)) < 7000


def test_intent_llm_fallback_flag_off_never_invoked(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("INTENT_LLM_FALLBACK_ENABLED", "false")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    provider = IntentFallbackProvider({"intent": "workout_plan", "confidence": "high"})
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "בא לי מסגרת מסודרת לחודש הקרוב כדי לחזור לכושר"},
    )

    assert response.status_code == 200
    assert response.json()["provider_status"] == "configured"
    assert provider.extract_calls == 0
    assert provider.chat_calls == 1
    assert db.scalar(select(WorkoutPlan)) is None


def test_intent_llm_fallback_routes_free_form_hebrew_plan_request(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("INTENT_LLM_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    provider = IntentFallbackProvider({"intent": "workout_plan", "confidence": "high"})
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "בא לי מסגרת מסודרת לחודש הקרוב כדי לחזור לכושר"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert provider.extract_calls == 1
    assert provider.chat_calls == 0
    assert db.scalar(select(WorkoutPlan)) is not None
    assert db.scalar(select(UsageEvent).where(UsageEvent.provider == "configured")) is not None
    coach_message = db.scalar(select(ChatMessage).where(ChatMessage.role == "coach").order_by(ChatMessage.id.desc()))
    assert coach_message is not None
    assert coach_message.metadata_json["intent"] == "workout_plan"
    assert coach_message.metadata_json["intent_llm_fallback"] is True


def test_intent_llm_fallback_unknown_result_continues_general_chat(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("INTENT_LLM_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    provider = IntentFallbackProvider({"intent": "unknown", "confidence": "high"})
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "בא לי מסגרת מסודרת לחודש הקרוב כדי לחזור לכושר"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "תשובה כללית" in body["response"]
    assert provider.extract_calls == 1
    assert provider.chat_calls == 1
    assert db.scalar(select(WorkoutPlan)) is None


def test_intent_llm_fallback_does_not_override_deterministic_workout_log(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("INTENT_LLM_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    provider = IntentFallbackProvider({"intent": "workout_plan", "confidence": "high"})
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי סקוואט 3 סטים, RPE 7, בלי כאב"},
    )

    assert response.status_code == 200
    assert response.json()["provider_status"] == "local_tool"
    assert provider.extract_calls == 0
    assert provider.chat_calls == 0
    assert db.scalar(select(WorkoutLog)) is not None


def test_intent_llm_fallback_never_runs_for_safety_override(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("INTENT_LLM_FALLBACK_ENABLED", "true")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = IntentFallbackProvider({"intent": "workout_plan", "confidence": "high"})
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "אני רוצה לקחת קלנבוטרול כדי לרדת מהר במשקל"},
    )

    assert response.status_code == 200
    assert response.json()["provider_status"] == "safety_override"
    assert provider.extract_calls == 0
    assert provider.chat_calls == 0


def test_fitness_term_intent_stays_local_when_provider_is_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "אני עייף כבר שבוע והביצועים יורדים. צריך דילואד?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "דילואד" in body["response"]
    assert provider.last_request is None


def test_fitness_term_intent_does_not_call_bad_provider_when_local_answer_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: EnglishOnlyProvider(),
    )

    response = client.post(
        "/api/chat",
        json={"message": "אני עייף כבר שבוע והביצועים יורדים. צריך דילואד?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "דילואד" in body["response"]
    attempted = db.scalar(select(UsageEvent).where(UsageEvent.provider == "configured"))
    assert attempted is None


def test_migrated_knowledge_intent_repairs_neutral_address_request_before_fallback(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: GenderedHebrewProvider(),
    )

    response = client.post(
        "/api/chat",
        json={
            "message": "איך לבנות הרגל אימון עקבי בשבוע עמוס? בלי לפנות אליי בלשון זכר או נקבה."
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "להוסיף צעד אחד" in body["response"]
    for broken_phrase in ["אתה", "הוסף", "תוסיף", "תתקדם", "הגעת"]:
        assert broken_phrase not in body["response"]
    saved = db.scalar(select(ChatMessage).where(ChatMessage.role == "coach").order_by(ChatMessage.id.desc()))
    assert saved is not None
    assert saved.metadata_json["quality_repair_applied"] is True
    assert saved.metadata_json["quality_issues"] == []
    attempted = db.scalar(select(UsageEvent).where(UsageEvent.provider == "configured"))
    assert attempted is not None


def test_provider_neutral_address_violation_without_local_fallback_repairs_when_possible(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: GenderedHebrewProvider(),
    )

    response = client.post(
        "/api/chat",
        json={"message": "איך לבנות שבוע אימונים מאוזן? בלי לפנות אליי בלשון זכר או נקבה."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "לא עמדה בבקשת ניסוח ניטרלי" not in body["response"]
    assert "להוסיף צעד אחד" in body["response"]
    for original_phrase in ["כמה חזרות אתה", "הוסף צעד", "תוסיף חזרות"]:
        assert original_phrase not in body["response"]
    saved = db.scalar(select(ChatMessage).where(ChatMessage.role == "coach").order_by(ChatMessage.id.desc()))
    assert saved is not None
    assert saved.content == body["response"]
    assert saved.metadata_json["quality_repair_applied"] is True
    assert saved.metadata_json["quality_issues"] == []


def test_provider_neutral_address_violation_returns_rejection_when_repair_cannot_clear_it(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    enable_language_guard(monkeypatch)
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: UnrepairableGenderedHebrewProvider(),
    )

    response = client.post(
        "/api/chat",
        json={"message": "איך לחשוב על עקביות באימון? בלי לפנות אליי בלשון זכר או נקבה."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "לא עמדה בבקשת ניסוח ניטרלי" in body["response"]
    assert "מתאמן" not in body["response"]
    saved = db.scalar(select(ChatMessage).where(ChatMessage.role == "coach").order_by(ChatMessage.id.desc()))
    assert saved is not None
    assert saved.metadata_json["quality_issues"] == ["neutral_address"]


def test_provider_hebrew_command_is_allowed_when_neutral_address_was_not_requested(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: GenderedHebrewProvider(),
    )

    response = client.post(
        "/api/chat",
        json={"message": "איך לבנות הרגל אימון עקבי בשבוע עמוס?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "הוסף צעד אחד" in body["response"]
    assert "כמה חזרות אתה מקבל" in body["response"]


def test_nutrition_guidance_is_routed_with_meal_context(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "אני מנסה לרדת באחוזי שומן בלי לספור קלוריות. מה לאכול סביב אימון ערב?"},
    )

    assert response.status_code == 200
    assert response.json()["provider_status"] == "configured"
    assert provider.last_request is not None
    knowledge = json.loads(provider.last_request.input_text)["context"]["coaching_knowledge"]
    # meal context family (not general_chat) provides nutrition summaries.
    assert "practical_nutrition_summary" in knowledge


def test_creatine_intent_stays_local_when_provider_is_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post("/api/chat", json={"message": "כדאי לי לקחת קריאטין?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "קריאטין" in body["response"]
    assert provider.last_request is None


def test_knee_squat_intent_stays_local_when_provider_is_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "הברך רגישה בסקוואט, במה להחליף?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert provider.last_request is None
    assert "אל תדחוף" in body["response"]


def test_supplement_safety_intent_stays_local_when_provider_is_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "פרה-וורקאאוט עם הרבה קפאין לפני אימון ערב - בטוח?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert provider.last_request is None
    assert "קפאין" in body["response"]


def test_low_energy_intent_stays_local_when_provider_is_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "אין לי כוח היום, תן לי פעולה אחת קטנה"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert provider.last_request is None
    assert "פעולה אחת" in body["response"]


def test_kept_local_intents_use_canned_response_without_api_key(tmp_path):
    """When ANTHROPIC_API_KEY is not configured, the four migrated knowledge intents
    keep their existing canned Hebrew response (non-regressive fallback)."""
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "כדאי לי לקחת קריאטין?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "קריאטין" in body["response"]


def test_budget_exceeded_migrated_intent_falls_back_local(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("DAILY_AI_TOKEN_LIMIT", "5")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    db.add(
        UsageEvent(
            user_id=None,
            usage_date=date.today(),
            task="chat",
            provider="configured",
            model="fake-model",
            estimated_tokens_in=6,
            estimated_tokens_out=0,
        )
    )
    db.commit()
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post(
        "/api/chat",
        json={"message": "אני עייף כבר שבוע והביצועים יורדים. צריך דילואד?"},
    )

    assert response.status_code == 200
    body = response.json()
    # Over budget: serve the local answer instead of a budget-exceeded notice, and never call the provider.
    assert body["provider_status"] == "local_tool"
    assert "דילואד" in body["response"]
    assert provider.last_request is None


def test_chat_endpoint_dispatches_hebrew_workout_plan_intent_to_module(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "תבנה לי תוכנית אימון של 2 ימים עם משקולות"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית אימון" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.days_per_week == 2


def test_chat_endpoint_dispatches_natural_hebrew_want_monthly_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "אני רוצה תוכנית אימונים לחודש במכון שתתחיל היום"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.is_current is True
    assert saved.plan_json["plan_type"] == "monthly_plan"


def test_chat_endpoint_dispatches_hebrew_training_week_creation_to_saved_workout_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "בנה לי שבוע אימונים קצר בלי ריצה לפי מה שאתה זוכר"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית אימון" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["plan_type"] == "weekly_plan"
    assert saved.days_per_week >= 1


def test_chat_endpoint_dispatches_natural_hebrew_weekly_plan_without_workout_word(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "תבנה לי תוכנית שבועית למתקדם בלי ציוד"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית שבועית" in body["response"]
    assert "בסוף השבוע" in body["response"]
    assert "הפעולה הבאה" in body["response"]
    assert "RPE או מאמץ מילולי" in body["response"]
    assert "לא לנחש" in body["response"]
    assert_no_storage_confirmation(body["response"])
    assert_no_raw_plan_labels(body["response"])
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["plan_type"] == "weekly_plan"
    assert saved.plan_json["experience_level"] == "advanced"
    assert saved.plan_json["equipment_needed"] == ["bodyweight"]


def test_chat_endpoint_dispatches_natural_hebrew_monthly_plan_without_workout_word(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post(
        "/api/chat",
        json={"message": "תבנה לי תוכנית חודשית של 4 ימים בחדר כושר להיפרטרופיה, אני ברמה בינונית"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית חודשית" in body["response"]
    assert "בסוף כל שבוע" in body["response"]
    assert "הפעולה הבאה" in body["response"]
    assert "RPE או מאמץ מילולי" in body["response"]
    assert "לא לנחש" in body["response"]
    assert_no_storage_confirmation(body["response"])
    assert_no_raw_plan_labels(body["response"])
    assert "דילואד" not in body["response"]
    assert len(body["response"]) < 650
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.is_current is True
    assert saved.plan_json["plan_type"] == "monthly_plan"
    assert saved.days_per_week == 4
    assert saved.plan_json["goal"] == "build_muscle"
    assert saved.plan_json["experience_level"] == "intermediate"
    assert len(saved.plan_json["progression_schedule"]) == 4
    assert "שבוע 4" in saved.plan_json["progression_model"]
    assert "דילואד" in saved.plan_json["progression_model"]
    assert "20-40%" in saved.plan_json["progression_model"]


def test_chat_endpoint_dispatches_hebrew_fat_loss_plan_without_punishment_or_calorie_claims(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "תבנה לי תוכנית חיטוב ביתית לשבוע"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "הפעולה הבאה" in body["response"]
    assert "קלוריות" not in body["response"]
    assert "ענישה" not in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["goal"] == "lose_fat"
    assert "הליכה" in saved.plan_json["days"][0]["notes"]
    assert "500-1,000 צעדים" in saved.plan_json["progression_rule"]
    assert "ענישה" not in json.dumps(saved.plan_json, ensure_ascii=False)


def test_chat_endpoint_mentions_two_week_horizon_in_response(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "תבנה לי תוכנית לשבועיים עם משקולות"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית לשבועיים" in body["response"]
    assert "שבוע 1" in body["response"]
    assert "שבוע 2" in body["response"]
    assert "בסוף שבוע 2" in body["response"]
    assert "בלוק נוסף" in body["response"]
    assert "הפעולה הבאה" in body["response"]
    assert "RPE או מאמץ מילולי" in body["response"]
    assert "לא לנחש" in body["response"]
    assert_no_storage_confirmation(body["response"])
    assert_no_raw_plan_labels(body["response"])
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["plan_type"] == "two_week_plan"


def test_chat_endpoint_surfaces_endurance_first_action_in_hebrew_plan_response(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "אירובי בסיסי בקצב שיחה" in body["response"]
    assert "לתעד RPE או מאמץ מילולי" in body["response"]
    assert "לא לנחש" in body["response"]
    assert "ריצה" not in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["goal"] == "improve_endurance"
    assert saved.plan_json["plan_type"] == "two_week_plan"
    assert saved.plan_json["days"][0]["exercises"][0]["movement_pattern"] == "cardiorespiratory"


def test_chat_endpoint_surfaces_mobility_first_action_in_hebrew_plan_response(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "תן לי תוכנית מוביליטי חודשית עם משקל גוף"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "זרימת מוביליטי ירך-גב-כתף" in body["response"]
    assert "לתעד RPE או מאמץ מילולי" in body["response"]
    assert "לא לנחש" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["goal"] == "improve_mobility"
    assert saved.plan_json["plan_type"] == "monthly_plan"
    assert saved.plan_json["equipment_needed"] == ["bodyweight"]
    assert "משקולת" not in json.dumps(saved.plan_json["days"], ensure_ascii=False)
    first_day = saved.plan_json["days"][0]
    assert first_day["exercises"][0]["movement_pattern"] == "mobility"
    assert first_day["exercises"][1]["movement_pattern"] == "balance"


def test_chat_endpoint_previews_candidate_plan_first_action_before_replacement_confirmation(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    client.post("/api/chat", json={"message": "תבנה לי תוכנית לב ריאה לשבועיים בלי ריצה"})

    response = client.post("/api/chat", json={"message": "תן לי תוכנית מוביליטי חודשית עם משקל גוף"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "זרימת מוביליטי ירך-גב-כתף" in body["response"]
    assert "היא לא מחליפה עדיין" in body["response"]
    assert "כן להחליף" in body["response"]
    assert "לא לנחש" not in body["response"]
    assert "לתעד RPE/כאב" not in body["response"]
    assert "לתעד RPE או מאמץ מילולי" not in body["response"]
    plans = db.scalars(select(WorkoutPlan).order_by(WorkoutPlan.id)).all()
    assert len(plans) == 2
    assert plans[-1].is_current is False
    assert plans[-1].plan_json["goal"] == "improve_mobility"
    assert plans[-1].plan_json["days"][0]["exercises"][0]["movement_pattern"] == "mobility"


def test_chat_endpoint_mentions_spacing_for_four_day_beginner_hebrew_plan(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "תבנה לי תוכנית חודשית למתחיל בלי ציוד, 4 ימים בשבוע, ראשון עד רביעי ברצף"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "פיזור שבועי" in body["response"]
    assert "יום מנוחה" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    spacing = saved.plan_json["decision_inputs"]["weekly_spacing_guidance"]
    assert "ימים צפופים" in spacing
    assert any("גרסת מינימום" in item for item in saved.plan_json["tracking_guidance"])


def test_chat_endpoint_saves_hebrew_short_week_plan_request_without_explicit_workout_word(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post("/api/chat", json={"message": "תבנה לי תוכנית קצרה לשבוע הקרוב, 20 דקות ביום"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "תוכנית אימון" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["plan_type"] == "weekly_plan"


def test_chat_endpoint_surfaces_brief_assumptions_for_minimal_hebrew_plan_request(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "תבנה לי תוכנית"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "הנחות:" in body["response"]
    assert "איפה הכאב" not in body["response"]
    assert body["response"].count("הנחתי") <= 3
    assert "3 אימונים בשבוע" in body["response"]
    assert "45 דקות" in body["response"]
    assert "משקל גוף" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assumptions = saved.plan_json["decision_inputs"]["assumptions"]
    assert len(assumptions) >= 5
    assert any("שיפור כושר כללי" in assumption for assumption in assumptions)
    assert any("משקל גוף" in assumption for assumption in assumptions)


def test_chat_endpoint_dispatches_feminine_hebrew_workout_plan_intent_to_module(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())

    response = client.post(
        "/api/chat",
        json={"message": "תבני לי תוכנית אימון של 4 שבועות, 4 ימים בשבוע, בלי ריצה ועם ברך רגישה."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "ברך" in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.days_per_week == 4
    assert saved.plan_json["plan_type"] == "monthly_plan"
    assert "ברך" in (saved.plan_json["decision_inputs"].get("limitations") or "")


def test_chat_endpoint_answers_motivation_locally_in_natural_hebrew(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "אין לי מוטיבציה היום, בא לי לוותר"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "ספק הבינה המלאכותית לא מוגדר" not in body["response"]
    assert "מוטיבציה" in body["response"]
    assert "עקביות" in body["response"]


def test_chat_endpoint_answers_rest_day_question_locally(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "כמה ימי מנוחה צריך בין אימונים?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "מנוחה" in body["response"]
    assert "48 שעות" in body["response"]


def test_chat_endpoint_answers_progress_plateau_locally(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "המשקל תקוע שבועיים מה לעשות?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "ממוצע שבועי" in body["response"]
    assert "מים" in body["response"]


def test_chat_endpoint_answers_muscle_or_fat_question_without_medical_verdict(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "עליתי 2 קילו, זה שריר או שומן?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "שריר" in body["response"]
    assert "מגמה" in body["response"] or "ממוצע שבועי" in body["response"]


def test_chat_endpoint_motivation_response_is_personalized_by_recent_workouts(tmp_path):
    client, _db = make_client_and_db(tmp_path)
    client.post("/api/workout-logs", json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"})

    response = client.post("/api/chat", json={"message": "אין לי מוטיבציה היום"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    # A grounded sentence about the user's recent logged training is prepended.
    assert "תיעדת" in body["response"]


def test_chat_endpoint_humanizes_workout_log_confirmation(tmp_path):
    client, _db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "עשיתי 3 סטים של 10 חזרות בסקוואט"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "רשמתי את האימון" in body["response"]
    assert "רמת ביטחון" not in body["response"]


def test_chat_endpoint_session_rpe_log_does_not_progress_from_missing_exercise_data(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "סיימתי אימון, מאמץ 8 מתוך 10, בלי כאב"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "חסר תרגיל מרכזי" in body["response"]
    assert "לא להוסיף חזרה מתוך ניחוש" in body["response"]
    assert "להוסיף חזרה אחת" not in body["response"]
    saved = db.scalar(select(WorkoutLog))
    assert saved is not None
    assert saved.rpe == 8
    assert saved.exercise_results == []


def test_chat_endpoint_hebrew_shorthand_log_is_exercise_level_evidence(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "תעד אימון: עשיתי לחיצת חזה 3x10 עם 50 ק״ג. מאמץ 8 מתוך 10, בלי כאב"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "חסר תרגיל מרכזי" not in body["response"]
    assert "להוסיף חזרה אחת" in body["response"]
    saved = db.scalar(select(WorkoutLog))
    assert saved is not None
    assert saved.rpe == 8
    assert saved.exercise_results[0]["exercise"] == "לחיצת חזה"
    assert saved.exercise_results[0]["reps"] == [10, 10, 10]
    assert saved.exercise_results[0]["weight"] == "50 ק״ג"


def test_chat_endpoint_logs_gym_slang_workout_with_pain_acknowledgement(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "כואבת לי הברך אבל עשיתי רגליים"})

    assert response.status_code == 200
    body = response.json()
    # Logged as a workout, pain acknowledged, safety not hard-blocked.
    assert body["safety_flagged"] is False
    assert body["provider_status"] == "local_tool"
    assert "רשמתי את האימון" in body["response"]
    assert "כאב" in body["response"]
    saved = db.scalar(select(WorkoutLog))
    assert saved is not None
    assert saved.pain_flag is True


def test_chat_endpoint_safety_red_flag_beats_motivation_keywords(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "אין לי מוטיבציה ויש לי כאב בחזה בזמן אימון"},
    )

    assert response.status_code == 200
    body = response.json()
    # Safety must win over any new motivation/progress intent.
    assert body["safety_flagged"] is True
    assert body["provider_status"] == "safety_override"
    assert "לעצור" in body["response"]
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "dangerous_symptoms"


def test_chat_endpoint_safety_extreme_diet_beats_progress_keywords(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post(
        "/api/chat",
        json={"message": "המשקל תקוע, תן לי דיאטה של 600 קלוריות כדי לרדת מהר"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is True
    assert body["provider_status"] == "safety_override"
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "extreme_dieting"


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'coach.db'}")
    init_db(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()

    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), db


def enable_language_guard(monkeypatch) -> None:
    monkeypatch.setenv("LANGUAGE_GUARD_ENABLED", "true")


def assert_no_storage_confirmation(text: str) -> None:
    forbidden = ["נשמר", "שמרתי", "תיעוד האימון", "תיעוד הארוחה", "זכרתי"]
    for phrase in forbidden:
        assert phrase not in text


def assert_no_raw_plan_labels(text: str) -> None:
    forbidden = ["full_body", "upper_lower", "push_pull_legs", "single_workout", "weekly_plan", "two_week_plan", "monthly_plan"]
    for phrase in forbidden:
        assert phrase not in text


def valid_payload():
    return {
        "name": "Lior",
        "main_goal": "build_muscle",
        "experience_level": "beginner",
        "training_location": "gym",
        "available_equipment": ["dumbbells"],
        "weekly_availability": 3,
        "session_length_minutes": 45,
        "preferred_workout_days": ["Monday"],
        "coaching_style": "direct",
        "consent_disclaimer": True,
    }


class EnglishOnlyProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text="Do a light workout tomorrow and eat enough protein.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class MixedEnglishProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text="כן. do a light workout tomorrow and eat protein.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class HebrewWithEnglishTermsProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text="היום תעשה mobility קצרה לירך, HIIT לא יותר מפעם אחת, ו-Zone 2 קל ביום אחר.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class GenderedHebrewProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text=(
                "התקדמות הדרגתית היא הגדלת עומס לאורך זמן. הוסף צעד אחד בכל שבוע, "
                "ואם כל הסטים קלים תוסיף חזרות. כמה חזרות אתה מקבל כרגע?"
            ),
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class UnrepairableGenderedHebrewProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text="אם אתה מתאמן עייף, תוכל לבחור יום קל יותר ולשמור על רצף.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class EchoedGenericEnglishProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text="כן. recover tomorrow עם הליכה קלה וחלבון מספיק.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class IntentFallbackProvider:
    def __init__(self, structured_output):
        self.structured_output = structured_output
        self.extract_calls = 0
        self.chat_calls = 0
        self.last_request = None
        self.last_tool = None

    def extract_tool(self, request, tool):
        from backend.app.services.ai_provider import AIResult

        self.extract_calls += 1
        self.last_request = request
        self.last_tool = tool
        return AIResult(
            text="",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=9,
            estimated_tokens_out=2,
            structured_output=self.structured_output,
        )

    def chat(self, request):
        from backend.app.services.ai_provider import AIResult

        self.chat_calls += 1
        self.last_request = request
        return AIResult(
            text="תשובה כללית בעברית.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=12,
            estimated_tokens_out=4,
        )


class MarkdownProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text=(
                "• היום תעשה **full body קצר** עם 2 סטים לכל תרגיל.\n"
                "המטרה היא להישאר תחת 10 שליחות מלאות ואז נחת את הגוף בסדר."
            ),
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class BrowserArtifactProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text="פעולה אחת: 10 דקות הליכה ללא서בר. RIR הוא לא reserve in reserve, even אם הסט קשה.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=10,
            estimated_tokens_out=8,
        )


class CapturingProvider:
    def __init__(self):
        self.last_request = None

    def chat(self, request):
        from backend.app.services.ai_provider import AIResult

        self.last_request = request
        return AIResult(
            text="בנה שבוע פשוט: שני אימוני כוח, הליכה קלה ויום התאוששות.",
            provider_status="configured",
            used_model="fake-model",
            estimated_tokens_in=20,
            estimated_tokens_out=12,
        )
