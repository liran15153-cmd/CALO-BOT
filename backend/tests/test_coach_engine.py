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
    assert "לעצור" in body["response"]
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
    assert "full_body" not in body["response"]
    assert "upper_lower" not in body["response"]
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
    assert "אימון יחיד" in body["response"]
    assert "1 ימים" not in body["response"]
    assert "ימים בשבוע" not in body["response"]
    current = db.get(WorkoutPlan, current_id)
    assert current is not None
    assert current.is_current is True
    one_off = db.scalar(select(WorkoutPlan).where(WorkoutPlan.id != current_id))
    assert one_off is not None
    assert one_off.plan_json["plan_type"] == "single_session"
    assert one_off.is_current is False


def test_chat_endpoint_infers_hebrew_single_session_gym_duration_and_uses_neutral_saved_response(tmp_path):
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
    assert "פתח את" not in body["response"]
    assert "מסך האימונים" not in body["response"]
    saved = db.scalar(select(WorkoutPlan))
    assert saved is not None
    assert saved.plan_json["plan_type"] == "single_session"
    assert saved.plan_json["session_length_minutes"] == 30
    assert saved.plan_json["days"][0]["estimated_duration_minutes"] == 30
    assert "חדר כושר" in saved.plan_json["equipment_needed"]
    assert "bodyweight" not in saved.plan_json["equipment_needed"]
    exercise_names = [exercise["name"] for exercise in saved.plan_json["days"][0]["exercises"]]
    assert any("מכונה" in name or "משקולות" in name for name in exercise_names)


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
    assert "אימון אחד" in body["response"]
    assert "1 אימונים" not in body["response"]
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
    assert "mobility" in body["response"]
    assert "HIIT" in body["response"]
    assert "Zone 2" in body["response"]
    assert "רובה לא בעברית" not in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "Zone 2" in saved[-1].content


def test_chat_endpoint_replaces_provider_response_with_generic_echoed_english_phrase(tmp_path, monkeypatch):
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
    assert "recover tomorrow" not in body["response"]
    assert "עברית" in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "recover tomorrow" not in saved[-1].content


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
    assert "•" not in body["response"]
    assert "שליחות מלאות" not in body["response"]
    assert "נחת את הגוף" not in body["response"]
    assert "full body" in body["response"]
    assert "חזרות נקיות" in body["response"]
    saved = db.scalars(select(ChatMessage).order_by(ChatMessage.id)).all()
    assert "**" not in saved[-1].content
    assert "שליחות מלאות" not in saved[-1].content


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
    assert "לרדידת" not in image_uncertainty.json()["response"]


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
    assert "עברית ישראלית טבעית" in provider.last_request.instructions
    assert "אל תתרגם מילולית מונחי כושר" in provider.last_request.instructions


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


def test_migrated_knowledge_intent_uses_provider_with_retrieval_when_configured(tmp_path, monkeypatch):
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
    # A formerly canned (local_tool) intent now answers from the provider...
    assert body["provider_status"] == "configured"
    assert body["response"] == "בנה שבוע פשוט: שני אימוני כוח, הליכה קלה ויום התאוששות."
    # ...grounded in the now-reachable deload knowledge.
    assert provider.last_request is not None
    knowledge = json.loads(provider.last_request.input_text)["context"]["coaching_knowledge"]
    assert any("deload" in hit["topic"] for hit in knowledge.get("retrieved_knowledge", []))


def test_migrated_knowledge_intent_falls_back_to_local_when_provider_hebrew_is_bad(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
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
    # Provider returned non-Hebrew, so we serve the vetted local answer instead (no regression).
    assert body["provider_status"] == "local_tool"
    assert "דילואד" in body["response"]
    # The provider was still attempted (usage recorded), we just rejected its output.
    attempted = db.scalar(select(UsageEvent).where(UsageEvent.provider == "configured"))
    assert attempted is not None


def test_migrated_knowledge_intent_falls_back_when_provider_violates_neutral_address_request(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, db = make_client_and_db(tmp_path)
    monkeypatch.setattr(
        "backend.app.services.coach_engine.build_ai_provider",
        lambda _api_key, _model: GenderedHebrewProvider(),
    )

    response = client.post(
        "/api/chat",
        json={
            "message": "מה זה progressive overload ואיך להתקדם אם כל הסטים קלים? בלי לפנות אליי בלשון זכר או נקבה."
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider_status"] == "local_tool"
    assert "להוסיף 1-2 חזרות" in body["response"]
    for broken_phrase in ["אתה", "הוסף", "תוסיף", "תתקדם", "הגעת"]:
        assert broken_phrase not in body["response"]
    attempted = db.scalar(select(UsageEvent).where(UsageEvent.provider == "configured"))
    assert attempted is not None


def test_provider_neutral_address_violation_without_local_fallback_returns_neutral_rejection(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
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
    assert "לא עמדה בבקשת ניסוח ניטרלי" in body["response"]
    for original_phrase in ["כמה חזרות אתה", "הוסף צעד", "תוסיף חזרות"]:
        assert original_phrase not in body["response"]
    saved = db.scalar(select(ChatMessage).where(ChatMessage.role == "coach").order_by(ChatMessage.id.desc()))
    assert saved is not None
    assert saved.content == body["response"]


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
        json={"message": "מה זה progressive overload ואיך להתקדם אם כל הסטים קלים?"},
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


def test_creatine_intent_uses_provider_with_knowledge_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    get_settings.cache_clear()
    client, _db = make_client_and_db(tmp_path)
    provider = CapturingProvider()
    monkeypatch.setattr("backend.app.services.coach_engine.build_ai_provider", lambda _api_key, _model: provider)

    response = client.post("/api/chat", json={"message": "כדאי לי לקחת קריאטין?"})

    assert response.status_code == 200
    body = response.json()
    # With an API key, creatine questions go to the LLM with retrieval-augmented
    # coaching knowledge instead of returning the canned local paragraph.
    assert body["provider_status"] == "configured"
    assert provider.last_request is not None
    knowledge = json.loads(provider.last_request.input_text)["context"]["coaching_knowledge"]
    assert knowledge


def test_knee_squat_intent_uses_provider_with_workout_plan_context_when_configured(tmp_path, monkeypatch):
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
    assert body["provider_status"] == "configured"
    assert provider.last_request is not None
    knowledge = json.loads(provider.last_request.input_text)["context"]["coaching_knowledge"]
    assert knowledge


def test_supplement_safety_intent_uses_provider_when_configured(tmp_path, monkeypatch):
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
    assert body["provider_status"] == "configured"
    assert provider.last_request is not None


def test_low_energy_intent_uses_provider_when_configured(tmp_path, monkeypatch):
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
    assert body["provider_status"] == "configured"
    assert provider.last_request is not None


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
            text=(
                "• היום תעשה **full body קצר** עם 2 סטים לכל תרגיל.\n"
                "המטרה היא להישאר תחת 10 שליחות מלאות ואז נחת את הגוף בסדר."
            ),
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
