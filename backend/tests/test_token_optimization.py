from datetime import date
import json

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import sessionmaker

from backend.app.config import get_settings
from backend.app.db import init_db, make_engine
from backend.app.models import ChatMessage, ChatSession, Meal, UsageEvent, WorkoutLog, WorkoutPlan
from backend.app.schemas import OnboardingPayload
from backend.app.services.ai_provider import AIRequest, AIResult
from backend.app.services.coaching_knowledge import CoachingKnowledgeService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.profile_service import ProfileService
from backend.app.services.token_budgeting import (
    build_legacy_chat_request,
    build_optimized_chat_request,
    compact_provider_context,
    estimate_request_input_tokens,
)
from backend.app.services.usage_service import UsageService


def test_default_chat_model_is_haiku_when_no_override(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_CHAT_MODEL", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.chat_model == "claude-haiku-4-5"


def test_usage_event_persists_token_breakdown_and_usage_api_sums_categories(tmp_path):
    db = make_session(tmp_path)
    service = UsageService(db)
    request = AIRequest(
        instructions="coach system",
        input_text='{"user":"hello"}',
        input_components={
            "message": "hello",
            "history": "previous turn",
            "memory": "profile and memories",
            "tools": "knowledge",
        },
    )
    result = AIResult(
        text="answer",
        provider_status="configured",
        used_model="fake-model",
        estimated_tokens_in=24,
        estimated_tokens_out=6,
        token_breakdown={
            "system_prompt": 4,
            "history": 3,
            "memory": 6,
            "tools": 8,
            "message": 3,
            "output": 6,
            "input_total": 24,
            "total": 30,
            "source": "test_provider_usage",
        },
    )

    event = service.record_ai_result(user_id=None, task="chat", request=request, result=result)
    totals = service.daily_totals()

    expected = {"system_prompt": 4, "history": 3, "memory": 6, "tools": 8, "message": 3, "output": 6}
    for component, tokens in expected.items():
        assert event.token_breakdown_json[component] == tokens
        assert totals["token_breakdown"][component] == tokens
    assert totals["token_breakdown"]["total"] == 30


def test_init_db_adds_token_breakdown_column_to_existing_usage_table(tmp_path):
    db_path = tmp_path / "legacy.db"
    engine = make_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE usage_events ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER, "
                "usage_date DATE NOT NULL, "
                "task VARCHAR(60) NOT NULL, "
                "provider VARCHAR(60) NOT NULL, "
                "model VARCHAR(120), "
                "estimated_tokens_in INTEGER DEFAULT 0, "
                "estimated_tokens_out INTEGER DEFAULT 0, "
                "cost_estimate FLOAT, "
                "created_at DATETIME, "
                "updated_at DATETIME)"
            )
        )

    init_db(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("usage_events")}
    assert "token_breakdown_json" in columns


def test_optimized_chat_request_cuts_input_tokens_by_half_without_dropping_context(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())
    session = ChatSession(user_id=profile.user_id, title="token audit")
    db.add(session)
    db.commit()
    db.refresh(session)
    for index in range(6):
        db.add(
            ChatMessage(
                session_id=session.id,
                user_id=profile.user_id,
                role="user" if index % 2 == 0 else "coach",
                content=f"history turn {index}: keep workouts short and practical",
            )
        )
    db.add_all(
        [
            WorkoutPlan(
                user_id=profile.user_id,
                name="Short Strength",
                goal="build_muscle",
                duration_weeks=4,
                days_per_week=3,
                equipment_needed=["dumbbells", "bands"],
                plan_json={
                    "plan_type": "monthly_plan",
                    "training_split": "full_body",
                    "experience_level": "beginner",
                    "session_length_minutes": 35,
                    "progression_schedule": [
                        "שבוע 1: כיול עומס ולוג מלא.",
                        "שבוע 2: התקדמות קטנה רק אם RPE וכאב יציבים.",
                        "שבוע 3: לשמור או להוסיף חזרה נקייה אחת.",
                    ],
                    "tracking_guidance": [
                        "לא לנחש מה היה באימון הקודם: לתעד את התרגיל המרכזי - חזרות, משקל אם יש, ו-RIR או כמה חזרות נשארו ברזרבה.",
                        "בסוף כל שבוע לבדוק השלמות, RPE, כאב ושינה לפני שינוי נפח או עומס.",
                        "לתעד אחרי כל אימון: הושלם/חלקי/פוספס, RPE וכאב.",
                    ],
                    "source_refs": ["ACSM resistance training guidance"],
                    "decision_inputs": {"weekly_availability": 3},
                },
                progression_rule="Add reps before load.",
                recovery_note="Keep one rest day between strength sessions.",
                is_current=True,
            ),
            WorkoutLog(
                user_id=profile.user_id,
                workout_id=None,
                logged_on=date.today(),
                status="completed",
                exercise_results=[],
                rpe=7,
                notes="Finished short session",
                pain_flag=False,
                parse_confidence="medium",
            ),
            Meal(
                user_id=profile.user_id,
                eaten_on=date.today(),
                meal_type="lunch",
                note="Chicken rice salad",
                calories_min=550,
                calories_max=750,
                protein_min=35,
                protein_max=50,
                carbs_min=50,
                carbs_max=80,
                fat_min=15,
                fat_max=30,
                confidence="medium",
            ),
        ]
    )
    db.commit()
    user_message = "How should I build a balanced training week and stay consistent?"

    context = ContextBuilder(db).build(
        user_id=profile.user_id,
        session_id=session.id,
        intent="general_chat",
        user_message=user_message,
    )
    legacy = build_legacy_chat_request(context=context, user_message=user_message)
    optimized = build_optimized_chat_request(context=context, user_message=user_message)

    legacy_tokens = estimate_request_input_tokens(legacy)
    optimized_tokens = estimate_request_input_tokens(optimized)
    payload = json.loads(optimized.input_text)
    optimized_context = payload["context"]
    knowledge = optimized_context["coaching_knowledge"]

    assert optimized_tokens <= legacy_tokens * 0.5
    assert optimized_context["profile"]["goal"] == "build_muscle"
    optimized_plan = optimized_context["current_workout_plan"]
    assert optimized_plan["type"] == "monthly_plan"
    assert optimized_plan["weeks"] == 4
    assert any("שבוע 2" in item for item in optimized_plan["progression_schedule"])
    assert any("לא לנחש" in item for item in optimized_plan["tracking_guidance"])
    assert any("בסוף כל שבוע" in item for item in optimized_plan["tracking_guidance"])
    assert optimized_context["recent_chat"]
    assert "coaching_knowledge" in optimized_context
    assert "safety_boundaries" in knowledge
    assert optimized.input_components.keys() >= {"message", "history", "memory", "tools"}


def test_optimized_workout_log_request_keeps_qualitative_effort_instruction(tmp_path):
    db = make_session(tmp_path)
    profile = ProfileService(db).upsert_onboarding(valid_payload())
    user_message = (
        "\u05d4\u05d9\u05d4 \u05e7\u05dc \u05de\u05d3\u05d9 "
        "\u05d1\u05e1\u05e7\u05d5\u05d5\u05d0\u05d8, "
        "\u05de\u05d4 \u05dc\u05e2\u05e9\u05d5\u05ea "
        "\u05d1\u05d0\u05d9\u05de\u05d5\u05df \u05d4\u05d1\u05d0?"
    )

    context = ContextBuilder(db).build(
        user_id=profile.user_id,
        intent="workout_log",
        user_message=user_message,
    )
    optimized = build_optimized_chat_request(context=context, user_message=user_message)
    payload = json.loads(optimized.input_text)
    knowledge = payload["context"]["coaching_knowledge"]
    qualitative_effort = "\u05de\u05d0\u05de\u05e5 \u05de\u05d9\u05dc\u05d5\u05dc\u05d9"
    not_number = "\u05dc\u05d0 \u05de\u05e1\u05e4\u05e8"
    substitution_gate = "\u05e9\u05e2\u05e8 \u05d4\u05d7\u05dc\u05e4\u05d4"
    pain = "\u05db\u05d0\u05d1"

    assert any(
        qualitative_effort in item and not_number in item
        for item in knowledge["coaching_behavior"]
    )
    assert any(
        substitution_gate in item and "RPE 1-10" in item and pain in item
        for item in knowledge["coaching_behavior"]
    )
    assert qualitative_effort in optimized.input_components["tools"]
    assert substitution_gate in optimized.input_components["tools"]
    assert not_number in optimized.input_text


def test_compact_workout_plan_context_keeps_builder_rules_and_retrieved_actions():
    query = "תבנה לי תוכנית כוח עם משקולות ובלי ספסל"
    knowledge = CoachingKnowledgeService().for_provider_context("workout_plan", query=query)
    compact = compact_provider_context(
        context={
            "profile": {},
            "current_workout_plan": {},
            "recent_workouts": [],
            "training_status": {},
            "recent_meals": [],
            "memory_safety": [],
            "recent_chat": [],
            "coaching_knowledge": knowledge,
        },
        user_message=query,
    )

    compact_knowledge = compact["coaching_knowledge"]
    assert "plan_horizon_summary" in compact_knowledge
    assert any(
        "single_workout" in item
        and "weekly_plan" in item
        and "two_week_plan" in item
        and "monthly_plan" in item
        for item in compact_knowledge["plan_horizon_summary"]
    )
    assert "goal_programming_summary" in compact_knowledge
    assert "weekly_structure_summary" in compact_knowledge
    assert "equipment_substitution_summary" in compact_knowledge
    assert "exercise_prescription_summary" in compact_knowledge
    assert "cardio_programming_summary" in compact_knowledge
    assert "periodization_summary" in compact_knowledge
    assert "warmup_mobility_summary" in compact_knowledge
    assert "exercise_library_summary" in compact_knowledge
    assert "adherence_coaching_summary" in compact_knowledge
    assert any(hit.get("guidance") or hit.get("action") for hit in compact_knowledge.get("retrieved_knowledge", []))


def test_compact_provider_context_keeps_plan_outline_and_recent_edits():
    compact = compact_provider_context(
        context={
            "profile": {},
            "current_workout_plan": {
                "name": "Edited Plan",
                "plan_type": "monthly_plan",
                "duration_weeks": 4,
                "days_per_week": 2,
                "workout_outline": [
                    {
                        "name": "Day 1",
                        "workout_id": 7,
                        "first_exercise": {
                            "exercise_id": 11,
                            "name": "Floor press",
                            "sets": "3",
                            "reps_or_duration": "8-10",
                        },
                    }
                ],
                "recent_plan_edits": [
                    {
                        "date": "2026-06-25",
                        "edit_type": "remove_bench",
                        "summary": "removed bench-dependent exercises or substitutions",
                        "changed_exercises": 2,
                    }
                ],
            },
            "recent_workouts": [],
            "training_status": {},
            "recent_meals": [],
            "memory_safety": [],
            "recent_chat": [],
            "coaching_knowledge": {},
        },
        user_message="what changed in my plan?",
    )

    plan = compact["current_workout_plan"]
    assert plan["outline"][0]["workout_id"] == 7
    assert plan["outline"][0]["first"]["exercise_id"] == 11
    assert plan["outline"][0]["first"]["name"] == "Floor press"
    assert plan["recent_edits"][0]["type"] == "remove_bench"
    assert plan["recent_edits"][0]["changed"] == 2


def make_session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'token.db'}")
    init_db(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def valid_payload():
    return OnboardingPayload(
        name="Lior",
        main_goal="build_muscle",
        experience_level="beginner",
        training_location="gym",
        available_equipment=["dumbbells", "resistance bands"],
        weekly_availability=3,
        session_length_minutes=45,
        preferred_workout_days=["Monday"],
        injuries_limitations="Knee sensitivity",
        nutrition_preference="high_protein",
        coaching_style="direct",
        consent_disclaimer=True,
    )
