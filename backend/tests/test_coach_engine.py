from collections.abc import Generator
from datetime import date
import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app
from backend.app.models import ChatMessage, Meal, SafetyEvent, UsageEvent, WeeklySummary, WorkoutLog, WorkoutPlan


def test_chat_endpoint_persists_user_and_no_key_coach_messages(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "Build me a beginner workout"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "not_configured"
    assert "ספק הבינה המלאכותית לא מוגדר" in body["response"]
    messages = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert [message.role for message in messages] == ["user", "coach"]


def test_chat_endpoint_uses_safety_response_for_pain(tmp_path):
    client, db = make_client_and_db(tmp_path)

    response = client.post("/api/chat", json={"message": "My knee hurts when I squat"})

    assert response.status_code == 200
    body = response.json()
    assert body["safety_flagged"] is True
    assert "עצור" in body["response"]
    event = db.scalar(select(SafetyEvent))
    assert event is not None
    assert event.event_type == "pain_or_injury"
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "safety_override"))
    assert usage is not None


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
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.days_per_week == 2
    usage = db.scalar(select(UsageEvent).where(UsageEvent.provider == "local_tool"))
    assert usage is not None


def test_chat_endpoint_dispatches_single_session_workout_plan_without_replacing_current(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/onboarding", json=valid_payload())
    current_response = client.post(
        "/api/workout-plans",
        json={"prompt": "Create a 3-day workout plan", "days_per_week": 3, "duration_weeks": 4},
    )
    current_id = current_response.json()["id"]

    response = client.post(
        "/api/chat",
        json={"message": "Build one 20 minute workout for today with bodyweight"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    one_off = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert one_off is not None
    assert one_off.plan_json["plan_type"] == "single_session"
    assert one_off.is_current is False


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


def test_chat_endpoint_answers_weekly_summary_with_local_summary_service(tmp_path):
    client, db = make_client_and_db(tmp_path)
    client.post("/api/workout-logs", json={"text": "I did 3 sets of bench press 10, 8, 7 with 50kg"})
    client.post("/api/meals/manual", json={"text": "I ate rice, chicken and salad"})

    response = client.post("/api/chat", json={"message": "תני לי סיכום שבועי לפי מה שתיעדתי"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "סיכום שבועי" in body["response"]
    assert "1 אימונים" in body["response"]
    saved_summary = db.scalar(select(WeeklySummary))
    assert saved_summary is not None
    assert saved_summary.metrics_json["workouts_completed"] == 1


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
    assert "recovery walk" in body["response"]
    assert "mobility" in body["response"]
    assert "protein" in body["response"]
    assert "רובה לא בעברית" not in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "recovery walk" in saved[-1].content


def test_chat_endpoint_keeps_hebrew_response_with_short_echoed_english_phrase(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
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
    assert "recover tomorrow" in body["response"]
    assert "רובה לא בעברית" not in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "recover tomorrow" in saved[-1].content


def test_chat_endpoint_strips_markdown_markers_from_provider_response(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: MarkdownProvider())

    response = client.post("/api/chat", json={"message": "איזה אימון מתאים לי היום?"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "configured"
    assert "**" not in body["response"]
    assert "full body" in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "**" not in saved[-1].content


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


def test_chat_endpoint_sends_coaching_knowledge_to_configured_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
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
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.days_per_week == 4


def make_client_and_db(tmp_path) -> tuple[TestClient, Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'coach.db'}")
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
            text="היום תעשה recovery walk קצר, mobility לירך, ואז protein בארוחה.",
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


class MarkdownProvider:
    def chat(self, _request):
        from backend.app.services.ai_provider import AIResult

        return AIResult(
            text="היום תעשה **full body קצר** עם 2 סטים לכל תרגיל.",
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
