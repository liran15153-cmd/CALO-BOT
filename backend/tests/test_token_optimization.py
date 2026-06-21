from datetime import date
import json

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import sessionmaker

from backend.app.config import get_settings
from backend.app.db import init_db, make_engine
from backend.app.models import ChatMessage, ChatSession, Meal, UsageEvent, UserMemory, WorkoutLog, WorkoutPlan
from backend.app.schemas import OnboardingPayload
from backend.app.services.ai_provider import AIRequest, AIResult
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.profile_service import ProfileService
from backend.app.services.token_budgeting import (
    build_legacy_chat_request,
    build_optimized_chat_request,
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
            UserMemory(user_id=profile.user_id, memory_type="preference", content="Prefers short workouts after work"),
            UserMemory(user_id=profile.user_id, memory_type="equipment", content="Has dumbbells and resistance bands"),
            UserMemory(
                user_id=profile.user_id,
                memory_type="safety_limitation",
                content="Knee gets sensitive in deep squats",
                is_sensitive=True,
            ),
            WorkoutPlan(
                user_id=profile.user_id,
                name="Short Strength",
                goal="build_muscle",
                duration_weeks=4,
                days_per_week=3,
                equipment_needed=["dumbbells", "bands"],
                plan_json={
                    "plan_type": "multi_week",
                    "training_split": "full_body",
                    "experience_level": "beginner",
                    "session_length_minutes": 35,
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
    assert "Prefers short workouts after work" in optimized_context["memories"]
    assert "Knee gets sensitive" in optimized_context["caution_notes"][0]
    assert optimized_context["recent_chat"]
    assert "coaching_knowledge" in optimized_context
    assert "safety_boundaries" in knowledge
    assert optimized.input_components.keys() >= {"message", "history", "memory", "tools"}


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
