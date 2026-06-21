import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models import ChatMessage, User
from backend.app.schemas import ChatRequest, ChatResponse, MealTextRequest, WorkoutLogRequest, WorkoutPlanRequest
from backend.app.services.ai_provider import build_ai_provider
from backend.app.services.chat_service import ChatService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.coach_intent_service import CoachIntentService
from backend.app.services.language_guard import (
    assess_hebrew_response_quality,
    repair_hebrew_coach_response,
)
from backend.app.services.meal_service import MealService
from backend.app.services.memory_service import MemoryService
from backend.app.services.pending_action_service import PendingActionService
from backend.app.services.pain_text import extract_pain_area
from backend.app.services.profile_service import ProfileService
from backend.app.services.safety_service import SafetyService
from backend.app.services.summary_service import SummaryService
from backend.app.services.token_budgeting import build_optimized_chat_request
from backend.app.services.usage_service import UsageService
from backend.app.services.workout_service import WorkoutService


COACH_CHAT_MAX_OUTPUT_TOKENS = 320
ToolResult = str | tuple[str, dict[str, Any]]


class CoachEngine:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def respond(self, payload: ChatRequest, user_id: int | None = None) -> ChatResponse:
        profile_service = ProfileService(self.db)
        user = self.db.get(User, user_id) if user_id is not None else profile_service.get_default_user()
        if user is None:
            raise ValueError("User not found")
        chat_service = ChatService(self.db)
        session = chat_service.get_or_create_session(user_id=user.id, session_id=payload.session_id)

        user_message = chat_service.add_message(
            user_id=user.id,
            session_id=session.id,
            role="user",
            content=payload.message,
        )
        MemoryService(self.db).extract_and_store(user_id=user.id, source_text=payload.message)

        safety = SafetyService(self.db)
        safety_result = safety.classify(payload.message)
        if safety_result.flagged:
            safety.record_event(user_id=user.id, source_text=payload.message, result=safety_result)
            UsageService(self.db).record(
                user_id=user.id,
                task="chat",
                provider="safety_override",
                model=None,
                estimated_tokens_in=0,
                estimated_tokens_out=0,
            )
            coach_message = chat_service.add_message(
                user_id=user.id,
                session_id=session.id,
                role="coach",
                content=safety_result.response,
                metadata={"safety": True},
            )
            MemoryService(self.db).refresh_long_term_summary(user_id=user.id)
            return ChatResponse(
                session_id=session.id,
                user_message_id=user_message.id,
                coach_message_id=coach_message.id,
                response=safety_result.response,
                safety_flagged=True,
                provider_status="safety_override",
            )

        # Soft pain ("יש לי כאב ברך") is NOT a block. Record the audit event and
        # carry the pain area forward so downstream paths (plan generation, response
        # wrappers) can acknowledge it and adapt rather than refusing.
        pain_area: str | None = None
        if safety_result.event_type == "pain_signal":
            safety.record_event(user_id=user.id, source_text=payload.message, result=safety_result)
            pain_area = extract_pain_area(payload.message)

        pending_tool_response = self._handle_pending_plan_action(
            user_id=user.id,
            payload_text=payload.message,
            resolved_by_message_id=user_message.id,
        )
        if pending_tool_response is not None:
            response_text, response_metadata = _unpack_tool_result(pending_tool_response)
            return self._respond_local_tool(
                chat_service=chat_service,
                user=user,
                session=session,
                user_message=user_message,
                response_text=response_text,
                intent_name="plan_replacement_confirmation",
                metadata=response_metadata,
            )

        intent = CoachIntentService().classify(payload.message)
        tool_response = self._handle_tool_intent(
            user_id=user.id,
            session_id=session.id,
            user_message_id=user_message.id,
            intent_name=intent.name,
            payload_text=intent.payload_text,
            pain_area=pain_area,
        )
        if tool_response is not None:
            response_text, response_metadata = _unpack_tool_result(tool_response)
            UsageService(self.db).record(
                user_id=user.id,
                task="chat",
                provider="local_tool",
                model=None,
                estimated_tokens_in=0,
                estimated_tokens_out=0,
            )
            coach_message = chat_service.add_message(
                user_id=user.id,
                session_id=session.id,
                role="coach",
                content=response_text,
                metadata={"provider_status": "local_tool", "intent": intent.name, **response_metadata},
            )
            MemoryService(self.db).refresh_long_term_summary(user_id=user.id)
            return ChatResponse(
                session_id=session.id,
                user_message_id=user_message.id,
                coach_message_id=coach_message.id,
                response=response_text,
                safety_flagged=False,
                provider_status="local_tool",
            )

        usage_service = UsageService(self.db)
        fallback = _KNOWLEDGE_INTENT_FALLBACKS.get(intent.name)
        fallback_text = fallback(intent.payload_text) if fallback else None

        # Without a provider key the migrated knowledge intents keep their existing local
        # answer, so behavior is unchanged unless Anthropic is configured.
        if fallback_text is not None and not self.settings.anthropic_api_key:
            return self._respond_local_tool(
                chat_service=chat_service,
                user=user,
                session=session,
                user_message=user_message,
                response_text=fallback_text,
                intent_name=intent.name,
            )

        if self.settings.anthropic_api_key and usage_service.is_daily_ai_token_budget_exceeded(user_id=user.id):
            if fallback_text is not None:
                return self._respond_local_tool(
                    chat_service=chat_service,
                    user=user,
                    session=session,
                    user_message=user_message,
                    response_text=fallback_text,
                    intent_name=intent.name,
                )
            budget_response = (
                "תקציב הבינה המלאכותית היומי נוצל. לא שלחתי בקשה לספק הבינה המלאכותית. "
                "אפשר להגדיל את DAILY_AI_TOKEN_LIMIT או להמתין לחלון היומי הבא."
            )
            usage_service.record(
                user_id=user.id,
                task="chat",
                provider="budget_exceeded",
                model=None,
                estimated_tokens_in=0,
                estimated_tokens_out=0,
            )
            coach_message = chat_service.add_message(
                user_id=user.id,
                session_id=session.id,
                role="coach",
                content=budget_response,
                metadata={"provider_status": "budget_exceeded"},
            )
            MemoryService(self.db).refresh_long_term_summary(user_id=user.id)
            return ChatResponse(
                session_id=session.id,
                user_message_id=user_message.id,
                coach_message_id=coach_message.id,
                response=budget_response,
                safety_flagged=False,
                provider_status="budget_exceeded",
            )

        context = ContextBuilder(self.db).build(
            user_id=user.id,
            session_id=session.id,
            intent=_PROVIDER_CONTEXT_INTENT_FOR.get(intent.name, intent.name),
            user_message=payload.message,
        )
        provider = build_ai_provider(self.settings.anthropic_api_key, self.settings.chat_model)
        ai_request = build_optimized_chat_request(
            context=context,
            user_message=payload.message,
            max_output_tokens=COACH_CHAT_MAX_OUTPUT_TOKENS,
        )
        ai_result = provider.chat(ai_request)
        usage_event = UsageService(self.db).record_ai_result(user_id=user.id, task="chat", request=ai_request, result=ai_result)
        token_breakdown = usage_event.token_breakdown_json or {}
        token_metadata = {
            **token_breakdown,
            "conversation_total": self._conversation_token_total(session.id) + int(token_breakdown.get("total", 0) or 0),
        }
        response_text = repair_hebrew_coach_response(payload.message, ai_result.text)
        quality = assess_hebrew_response_quality(payload.message, response_text)
        quality_metadata = {
            "language_guard_mode": self.settings.language_guard_mode,
            "quality_repair_applied": response_text != ai_result.text,
            "quality_issues": list(quality.issues),
        }

        if ai_result.provider_status == "configured" and quality.ok:
            provider_status = "configured"
        elif fallback_text is not None:
            # Provider unusable (broken Hebrew, error, or not configured): fall back to the
            # vetted local answer so migrated knowledge intents never regress. The provider
            # call was already recorded above, so do not double-count usage here.
            quality_metadata["quality_fallback_reason"] = ",".join(quality.issues) or ai_result.provider_status
            return self._respond_local_tool(
                chat_service=chat_service,
                user=user,
                session=session,
                user_message=user_message,
                response_text=fallback_text,
                intent_name=intent.name,
                record_usage=False,
                metadata=quality_metadata,
            )
        elif ai_result.provider_status == "configured":
            if "neutral_address" in quality.issues:
                response_text = (
                    "קיבלתי מספק הבינה המלאכותית תשובה שלא עמדה בבקשת ניסוח ניטרלי, ולכן לא אציג אותה. "
                    "אפשר לשלוח שוב את הבקשה, והמאמן יחזיר תשובה בעברית ניטרלית וברורה."
                )
            else:
                response_text = (
                    "קיבלתי מספק הבינה המלאכותית תשובה שרובה לא בעברית, ולכן לא אציג אותה. "
                    "נסה לשלוח שוב את הבקשה, והמאמן יחזיר תשובה בעברית ברורה."
                )
            provider_status = "configured"
        else:
            provider_status = ai_result.provider_status

        coach_message = chat_service.add_message(
            user_id=user.id,
            session_id=session.id,
            role="coach",
            content=response_text,
            metadata={
                "provider_status": provider_status,
                "model": ai_result.used_model,
                "intent": intent.name,
                "token_breakdown": token_metadata,
                **quality_metadata,
            },
        )
        MemoryService(self.db).refresh_long_term_summary(user_id=user.id)

        return ChatResponse(
            session_id=session.id,
            user_message_id=user_message.id,
            coach_message_id=coach_message.id,
            response=response_text,
            safety_flagged=False,
            provider_status=provider_status,
        )

    def _respond_local_tool(
        self,
        *,
        chat_service: ChatService,
        user,
        session,
        user_message,
        response_text: str,
        intent_name: str,
        record_usage: bool = True,
        metadata: dict | None = None,
    ) -> ChatResponse:
        if record_usage:
            UsageService(self.db).record(
                user_id=user.id,
                task="chat",
                provider="local_tool",
                model=None,
                estimated_tokens_in=0,
                estimated_tokens_out=0,
            )
        coach_message = chat_service.add_message(
            user_id=user.id,
            session_id=session.id,
            role="coach",
            content=response_text,
            metadata={"provider_status": "local_tool", "intent": intent_name, **(metadata or {})},
        )
        MemoryService(self.db).refresh_long_term_summary(user_id=user.id)
        return ChatResponse(
            session_id=session.id,
            user_message_id=user_message.id,
            coach_message_id=coach_message.id,
            response=response_text,
            safety_flagged=False,
            provider_status="local_tool",
        )

    def _conversation_token_total(self, session_id: int) -> int:
        messages = self.db.scalars(
            select(ChatMessage).where(ChatMessage.session_id == session_id, ChatMessage.role == "coach")
        ).all()
        total = 0
        for message in messages:
            breakdown = (message.metadata_json or {}).get("token_breakdown") or {}
            value = breakdown.get("total")
            if isinstance(value, int):
                total += value
        return total

    def _handle_pending_plan_action(
        self,
        *,
        user_id: int,
        payload_text: str,
        resolved_by_message_id: int,
    ) -> ToolResult | None:
        pending = PendingActionService(self.db).current(user_id=user_id)
        if pending is None:
            return None

        if _declines_plan_replacement(payload_text):
            result = PendingActionService(self.db).resolve(
                user_id=user_id,
                action_id=pending.id,
                decision="decline",
                resolved_by_message_id=resolved_by_message_id,
            )
            return (
                f"{result['message']} הפעולה הבאה: להמשיך לפי האימון הבא בתוכנית הקיימת, או לבקש שינוי נקודתי אם משהו לא מתאים.",
                {
                    "resolved_pending_action_id": pending.id,
                    "pending_action_resolution": result["pending_action"]["resolution"],
                },
            )

        if _confirms_plan_replacement(payload_text):
            result = PendingActionService(self.db).resolve(
                user_id=user_id,
                action_id=pending.id,
                decision="confirm",
                resolved_by_message_id=resolved_by_message_id,
            )
            workout_plan = result.get("workout_plan")
            resolution = result["pending_action"]["resolution"]
            return (
                _activated_plan_response(workout_plan) if workout_plan and resolution == "confirmed" else result["message"],
                {
                    "resolved_pending_action_id": pending.id,
                    "pending_action_resolution": resolution,
                },
            )

        return None

    def _handle_tool_intent(
        self,
        user_id: int,
        session_id: int,
        user_message_id: int,
        intent_name: str,
        payload_text: str,
        pain_area: str | None = None,
    ) -> ToolResult | None:
        if intent_name == "workout_plan":
            limitations = f"רגישות ב{pain_area}" if pain_area else None
            workout_service = WorkoutService(self.db)
            current_before = workout_service.current_plan(user_id=user_id)
            plan = workout_service.generate_plan(
                user_id=user_id,
                request=WorkoutPlanRequest(prompt=payload_text, limitations=limitations),
            )
            serialized = WorkoutService.serialize_plan(plan)
            is_replacement_candidate = (
                current_before is not None
                and current_before.id != plan.id
                and not plan.is_current
                and serialized.get("plan_type") == "multi_week"
            )
            metadata = {}
            if is_replacement_candidate:
                pending = PendingActionService(self.db).create_workout_plan_replacement(
                    user_id=user_id,
                    candidate_plan_id=plan.id,
                    current_plan_id=current_before.id,
                    session_id=session_id,
                    created_from_message_id=user_message_id,
                )
                metadata = {"pending_action_id": pending.id}
            return (
                _workout_plan_saved_response(
                    serialized,
                    pain_area=pain_area,
                    replacement_candidate=is_replacement_candidate,
                ),
                metadata,
            )

        if intent_name == "workout_log":
            log = WorkoutService(self.db).parse_log(user_id=user_id, request=WorkoutLogRequest(text=payload_text))
            return _workout_log_coach_response(log)

        if intent_name == "meal_log":
            meal = MealService(self.db).log_manual_meal(user_id=user_id, request=MealTextRequest(text=payload_text))
            return _meal_log_coach_response(meal)

        if intent_name == "meal_image_guidance":
            return _meal_image_guidance_response()

        if intent_name == "supplement_safety_guidance":
            return _supplement_safety_guidance_response(payload_text)

        if intent_name == "knee_squat_substitution":
            return _knee_squat_substitution_response()

        if intent_name == "low_energy_action_guidance":
            return _low_energy_action_guidance_response()

        if intent_name == "missed_workout_guidance":
            return _missed_workout_guidance_response()

        if intent_name == "weekly_action_plan_guidance":
            return _weekly_action_plan_guidance_response()

        if intent_name == "equipment_substitution_guidance":
            return _equipment_substitution_guidance_response(payload_text)

        if intent_name == "fitness_term_guidance":
            return _fitness_term_guidance_response(payload_text)

        if intent_name == "creatine_guidance":
            return _creatine_guidance_response()

        if intent_name == "memory_ack":
            return _memory_ack_response()

        if intent_name == "weekly_summary":
            summary = SummaryService(self.db).weekly_summary(user_id=user_id)
            return f"{summary.summary_text} הפעולה הבאה: {summary.next_action}"

        if intent_name == "daily_summary":
            summary = SummaryService(self.db).daily_summary(user_id=user_id)
            return f"{summary['summary']} הפעולה הבאה: {summary['next_action']}"

        return None


def _hebrew_confidence(value: str | None) -> str:
    return {"low": "נמוכה", "medium": "בינונית", "high": "גבוהה"}.get(value or "", value or "לא ידועה")


def _unpack_tool_result(result: ToolResult) -> tuple[str, dict[str, Any]]:
    if isinstance(result, tuple):
        return result
    return result, {}


def _confirms_plan_replacement(text: str) -> bool:
    normalized = text.lower().strip()
    return any(
        phrase in normalized
        for phrase in [
            "כן",
            "מאשר",
            "תחליף",
            "תמחק",
            "מחק",
            "החלף",
            "להחליף",
            "החדשה",
            "yes",
            "replace",
            "delete old",
            "save new",
            "activate",
        ]
    )


def _declines_plan_replacement(text: str) -> bool:
    normalized = text.lower().strip()
    return any(
        phrase in normalized
        for phrase in [
            "לא",
            "אל תחליף",
            "אל תמחק",
            "עזוב",
            "תשאיר",
            "השאר",
            "תשאיר את הקיימת",
            "no",
            "cancel",
            "keep old",
            "keep current",
        ]
    )


def _workout_plan_saved_response(
    serialized: dict,
    pain_area: str | None = None,
    *,
    replacement_candidate: bool = False,
) -> str:
    name = _natural_plan_name(str(serialized.get("name") or "תוכנית אימון"))
    if serialized.get("plan_type") == "single_session":
        body = f"אימון יחיד מוכן: {name}. זה אימון חד-פעמי ולא מחליף את התוכנית הפעילה."
    else:
        days_per_week = serialized.get("days_per_week")
        days_text = "יום אחד בשבוע" if days_per_week == 1 else f"{days_per_week} ימים בשבוע"
        if replacement_candidate:
            body = (
                f"בניתי תוכנית חדשה: {name}, {days_text}. "
                "היא לא מחליפה עדיין את התוכנית הפעילה. "
                "רוצה למחוק את הישנה ולהפוך את החדשה לתוכנית הפעילה?"
            )
        else:
            body = f"תוכנית אימון מוכנה: {name} עם {days_text}. הפעולה הבאה: לעבור על היום הראשון ולוודא שהעומס מתאים."

    if pain_area:
        ack = (
            f"שמתי לב שציינת כאב ב{pain_area}. בניתי את התוכנית סביב זה, עם תרגילים שמכבדים את הטווח. "
            "אם הכאב חוזר, מחמיר או חד — לעצור, ולא לדחוף דרך כאב. אם יש סימן רציני, לפנות לאיש מקצוע מוסמך."
        )
        return f"{ack} {body}"

    return body


def _activated_plan_response(serialized: dict) -> str:
    name = _natural_plan_name(str(serialized.get("name") or "תוכנית אימון"))
    days_per_week = serialized.get("days_per_week")
    days_text = "יום אחד בשבוע" if days_per_week == 1 else f"{days_per_week} ימים בשבוע"
    return f"התוכנית החדשה פעילה עכשיו: {name}, {days_text}. הפעולה הבאה: להתחיל מהאימון הראשון ולתעד איך הוא הרגיש."


def _workout_log_coach_response(log) -> str:
    if log.pain_flag:
        return (
            "הכאב הוא הסימן החשוב כאן. לעצור תנועות שמכאיבות, להוריד עומס או טווח באימון הבא, "
            "ואם הכאב חד, מחמיר או חוזר - לפנות לאיש מקצוע מתאים."
        )
    if log.status == "skipped":
        return "לא משלימים אימון שפוספס בכוח. הפעולה הבאה: לחזור בגרסה קצרה של 20-30 דקות או לבצע את האימון הבא כרגיל."
    if log.status in {"partial", "modified"}:
        return "אימון חלקי עדיין נותן מידע טוב לתכנון. הפעולה הבאה: באימון הבא לשמור על אותו עומס או להוריד סט אחד אם העייפות נשארת."
    if log.rpe is not None:
        if log.rpe >= 9:
            return f"RPE {log.rpe} אומר שהאימון היה קשה מאוד. הפעולה הבאה: באימון הבא לשמור עומס או להוריד מעט נפח, לא להוסיף עוד סטים."
        return f"RPE {log.rpe} נראה מאמץ בשליטה. הפעולה הבאה: לחזור על אותו מבנה, ואם הטכניקה נשארת נקייה להוסיף חזרה אחת בתרגיל המרכזי."
    if log.exercise_results:
        return "האימון נראה ברור מספיק לתכנון הבא. הפעולה הבאה: באימון הבא לתעד גם RPE כללי כדי לדעת אם להעלות או לשמור עומס."
    return "הכיוון ברור. הפעולה הבאה: באימון הבא להוסיף תרגיל מרכזי, חזרות או RPE כדי שאפשר יהיה להתאים עומס בצורה מדויקת יותר."


def _meal_log_coach_response(meal) -> str:
    calories = _range_text(meal.calories_min, meal.calories_max, "קלוריות")
    protein = _range_text(meal.protein_min, meal.protein_max, "גרם חלבון")
    return (
        f"ההערכה לארוחה הזו היא {calories} ו-{protein}. "
        "זה טווח, לא מספר מדויק. הפעולה הבאה: בארוחה הבאה לבחור עוגן חלבון אחד ולהשאיר את זה פשוט."
    )


def _range_text(low: int | None, high: int | None, unit: str) -> str:
    if low is None or high is None:
        return f"טווח {unit} לא ברור"
    return f"{low}-{high} {unit}"


def _natural_plan_name(name: str) -> str:
    replacements = {
        "full_body": "גוף מלא",
        "upper_lower": "עליון/תחתון",
        "push_pull_legs": "דחיפה/משיכה/רגליים",
        "single_session": "אימון יחיד",
    }
    for raw, natural in replacements.items():
        name = name.replace(raw, natural)
    return name


def _fitness_term_guidance_response(text: str) -> str:
    normalized = text.lower()
    if "zone 2" in normalized or "זון 2" in normalized:
        return (
            "Zone 2 הוא קצב אירובי קל-בינוני שאפשר להחזיק לאורך זמן. בלי שעון דופק, אפשר להשתמש בבדיקת דיבור: "
            "אם אפשר לדבר במשפטים קצרים אבל לא לשיר בנוחות, זה בערך הטווח. "
            "הפעולה הבאה: 20-30 דקות הליכה מהירה או אופניים בקצב הזה."
        )

    if "full-body" in normalized or "full body" in normalized or "push/pull/legs" in normalized or "ppl" in normalized:
        return (
            "אין חלוקת אימונים קסומה. כשיש 2-3 אימונים בשבוע, full-body בדרך כלל עדיף כי כל הגוף מקבל גירוי בתדירות טובה. "
            "push/pull/legs מתאים יותר כשיש 5-6 ימי אימון ורצף יציב. "
            "הפעולה הבאה: לבחור את המבנה שאפשר לבצע בעקביות חודש שלם."
        )

    has_warmup = any(term in normalized for term in ["warmup", "warm-up", "חימום", "מוביליטי", "mobility"])
    has_cooldown = any(term in normalized for term in ["cooldown", "cool-down", "קירור", "מתיחות"])
    if has_warmup or has_cooldown:
        if has_warmup and has_cooldown:
            return (
                "לפני אימון כוח: 5-8 דקות חימום דינמי, תנועה קלה למפרקים הרלוונטיים, ואז סט הכנה קל לתרגיל הראשון. "
                "אחרי האימון: קירור קצר יכול לעזור להוריד דופק, אבל מתיחות לא מבטיחות מניעת DOMS. "
                "הפעולה הבאה: לבצע סט הכנה אחד קל לפני התרגיל הכבד הראשון."
            )
        if has_warmup:
            return (
                "חימום דינמי טוב מכין את הגוף לתרגילים של היום, לא צריך להיות שיעור mobility ארוך. "
                "מספיק 5-8 דקות: העלאת דופק קלה, תנועה למפרקים שיעבדו, וסט הכנה קל לפני התרגיל הראשון. "
                "הפעולה הבאה: לבצע סט הכנה אחד עם בערך חצי מהעומס המתוכנן."
            )
        return (
            "קירור אחרי אימון יכול להיות 3-5 דקות הליכה או נשימה רגועה. הוא לא חייב להיות טקס ארוך, ומתיחות לא מבטיחות מניעת DOMS. "
            "אם רוצים גמישות, עדיף להקדיש למתיחות זמן נפרד או סוף אימון רגוע. "
            "הפעולה הבאה: היום לסיים ב-3 דקות הליכה קלה ולתעד איך הגוף מרגיש."
        )

    if "היפרטרופיה" in normalized or "סטים קשים" in normalized:
        return (
            "היפרטרופיה היא גדילת שריר. בפועל היא מגיעה משילוב של סטים קשים, טכניקה טובה והתאוששות מספקת. "
            "סט קשה הוא סט שבו נשארות בערך 1-3 חזרות נקיות ברזרבה, לא בהכרח כשל מוחלט. "
            "הפעולה הבאה: ברוב הסטים לשמור RIR 1-3 ולתעד אם הביצוע נשאר יציב."
        )

    if "rpe" in normalized or "rir" in normalized or "חזרות ברזרבה" in normalized:
        comparison_response = _rpe_rir_comparison_response(normalized)
        if comparison_response:
            return comparison_response
        mixed_response = _mixed_rpe_rir_response(normalized)
        if mixed_response:
            return mixed_response
        return (
            "RPE הוא דירוג מאמץ בסולם 1-10: כמה הסט או האימון הרגישו קשה בפועל. "
            "בכוח, מספר נמוך הוא קל יותר, מספר בינוני הוא מאמץ בשליטה, ומספר גבוה מאוד אומר שכמעט לא נשארו חזרות נקיות. "
            "הפעולה הבאה: באימון הבא לתעד RPE כללי אחד בסוף, כדי שנוכל להתאים עומס בלי לנחש."
        )

    if "doms" in normalized or "שרירים תפוסים" in normalized or "כאבי שרירים" in normalized:
        return (
            "DOMS הם כאבי שרירים מאוחרים שמופיעים לרוב יום-יומיים אחרי עומס חדש או חזק. "
            "זה לא מדד לאיכות האימון ולא חובה כדי להתקדם. "
            "אם הכאב קל-בינוני: חימום ארוך, תנועה קלה, ולהוריד סט או שניים אם הטכניקה נפגעת."
        )

    if "דילואד" in normalized or "deload" in normalized or "ביצועים יורדים" in normalized:
        return (
            "כן, שבוע של עייפות וירידה בביצועים יכול להצדיק דילואד. "
            "לא צריך למחוק את האימונים: להוריד בערך 20-40% מהסטים או מהעומס, ולהשאיר טכניקה נקייה ו-RPE בינוני. "
            "אם יש כאב חד, סחרחורת או חולשה חריגה, לעצור ולפנות לאיש מקצוע."
        )

    if (
        "progression" in normalized
        or "progressive overload" in normalized
        or "פרוגרסיה" in normalized
        or "התקדמות" in normalized
        or "להתקדם" in normalized
    ):
        return (
            "progressive overload הוא עיקרון פשוט: להעלות את הדרישה בהדרגה כשהביצוע יציב. "
            "אם כל הסטים הרגישו קלים והטכניקה נשארה נקייה, כדאי לבחור שינוי אחד קטן בלבד. "
            "האפשרות הפשוטה: להוסיף 1-2 חזרות לכל סט; אם כבר בקצה טווח החזרות, להעלות עומס קטן. "
            "לא להוסיף גם משקל וגם סטים באותו שבוע בלי סיבה."
        )

    return (
        "הכלל הפשוט: להשאיר את המונח המקצועי כשהוא טבעי, ולתרגם רק את ההחלטה המעשית. "
        "הפעולה הבאה: לכתוב מה המונח או המצב באימון, ואחזיר פירוש קצר ומה עושים איתו."
    )


def _rpe_rir_comparison_response(normalized_text: str) -> str | None:
    rpe_match = re.search(r"rpe\s*[-:]?\s*(10|[1-9])", normalized_text)
    rir_match = re.search(r"rir\s*[-:]?\s*(\d+)", normalized_text)
    reserve_match = re.search(r"(\d+)\s+חזרות\s+ברזרבה", normalized_text)
    if not rpe_match or not (rir_match or reserve_match):
        return None

    rpe_value = int(rpe_match.group(1))
    rir_value = int((rir_match or reserve_match).group(1))
    rir_text = _hebrew_rir_reps(rir_value)
    return (
        f"RPE {rpe_value} הוא דירוג מאמץ: כמה הסט הרגיש קשה בסולם 1-10. "
        f"RIR {rir_value} אומר שנשארו בערך {rir_text} לפני כשל. "
        f"בפועל RPE {rpe_value} בדרך כלל קרוב ל-RIR {rir_value}, אבל RIR קל יותר למדידה כי סופרים חזרות שנשארו. "
        f"הפעולה הבאה: בסט כבד לעצור סביב RIR {max(1, rir_value)} אם הטכניקה נשארת נקייה."
    )


def _hebrew_rir_reps(value: int) -> str:
    if value == 1:
        return "חזרה נקייה אחת"
    if value == 2:
        return "שתי חזרות נקיות"
    return f"{value} חזרות נקיות"


def _mixed_rpe_rir_response(normalized_text: str) -> str | None:
    if "rpe" not in normalized_text or "rir" not in normalized_text:
        return None

    rir_match = re.search(r"rir\s*[-:]?\s*(\d+)", normalized_text)
    if not rir_match:
        return None

    rir_value = int(rir_match.group(1))
    if "גבוה" in normalized_text or "high" in normalized_text:
        return (
            f"RPE גבוה יחד עם RIR {rir_value} הוא לא סתירה. זה אומר שהסט הרגיש קשה, אבל כנראה עדיין נשארו "
            f"בערך {rir_value} חזרות נקיות לפני כשל. זה יכול להגיע מעייפות כללית, נשימה, טכניקה או סטרס, לא רק מהשריר עצמו. "
            "הפעולה הבאה: לשמור את אותו עומס בסט הבא ולתעד גם חזרות, עומס ותחושת טכניקה."
        )

    return None


def _equipment_substitution_guidance_response(text: str) -> str:
    normalized = text.lower()
    if "גומייה" in normalized or "גומיות" in normalized or "band" in normalized:
        return (
            "שמור על אותה תבנית תנועה: משיכה אופקית לגב. חבר את הגומייה לעוגן יציב בגובה חזה, "
            "עמוד זקוף ומשוך את המרפקים לאחור לצד הגוף. "
            "עשה 2-3 סטים של 10-15 חזרות, בלי כאב ובלי למשוך מהגב התחתון."
        )

    if "ספסל" in normalized or "bench" in normalized:
        return (
            "אם אין ספסל, שמור על דפוס הדחיפה ובחר גרסה יציבה: לחיצת חזה על הרצפה או שכיבות סמיכה בשיפוע. "
            "עשה 2-3 סטים בשליטה והשאר 1-3 חזרות ברזרבה. "
            "אם הכתף לא נוחה, קצר טווח או עבור לגרסה קלה יותר."
        )

    return (
        "בחר חלופה לפי דפוס התנועה, לא לפי שם התרגיל. במקום מכונה חפש אותו כיוון פעולה: דחיפה, משיכה, סקוואט או הינג׳. "
        "הפעולה הבאה: כתוב איזה תרגיל חסר ואיזה ציוד יש לך, ואציע חלופה אחת ברורה."
    )


def _missed_workout_guidance_response() -> str:
    return (
        "לא מתחילים מאפס אחרי פספוס. השבוע חוזרים עם גרסה קצרה: אימון אחד מלא או שני אימונים קצרים יותר, בלי להחזיר את כל הנפח בבת אחת. "
        "הפעולה הבאה: בחר יום אחד קרוב, עשה 20-30 דקות, ותעד שסיימת."
    )


def _nutrition_guidance_response(text: str) -> str:
    normalized = text.lower()
    if "תמונה" in normalized and ("מדויק" in normalized or "להעריך" in normalized):
        return _meal_image_guidance_response()

    return (
        "בלי לספור קלוריות, סביב אימון ערב כדאי לשמור על פשוט: ארוחה רגילה 2-3 שעות לפני האימון עם חלבון, פחמימה וירק. "
        "אם יש רעב קרוב לאימון, אפשר פרי או יוגורט/כריך קטן. "
        "הפעולה הבאה: היום לבחור מנת חלבון אחת ופחמימה אחת סביב האימון, בלי להפוך את זה לחישוב מדויק."
    )


def _meal_image_guidance_response() -> str:
    return (
        "מתמונה אפשר לתת הערכה בטווח בלבד, לא מספר מדויק יחיד. הדיוק תלוי בגודל מנה, שמן, רוטב ומה שלא רואים בתמונה. "
        "כשיש תמונה, להעלות אותה במסך הארוחות; הניתוח יציג מזונות שזוהו, טווח קלוריות, רמת ביטחון ושאלת הבהרה אחת אם חסר מידע."
    )


def _supplement_safety_guidance_response(text: str) -> str:
    normalized = text.lower()
    if "yohimbine" in normalized or "יוהימבין" in normalized:
        return (
            "עם הרבה קפאין ו-yohimbine לפני אימון ערב, עדיף לוותר. זה שילוב ממריץ שעלול להעלות דופק, לפגוע בשינה "
            "ולהרגיש לא טוב בזמן אימון, במיוחד אם יש רגישות לקפאין, לחץ דם, חרדה או תרופות קבועות. "
            "הפעולה הבאה: לבחור קפה קטן מוקדם יותר או בלי ממריץ, ולעצור אם יש דפיקות לב, סחרחורת או כאב בחזה."
        )

    if "fat burner" in normalized or "שורף שומן" in normalized or "שורפי שומן" in normalized:
        return (
            "שורפי שומן הם לרוב ממריצים באריזה שיווקית, לא בסיס להתקדמות. לפני אימון ערב הם עלולים לפגוע בשינה, "
            "והשינה חשובה יותר לירידה בשומן מאשר תוסף כזה. הפעולה הבאה: לוותר עליו היום ולשמור על אימון, חלבון וצעדים."
        )

    return (
        "תוסף pre-workout אינו חובה. אם יש הרבה קפאין או ממריצים, במיוחד לפני אימון ערב, עדיף לבחור מינון נמוך יותר "
        "או לוותר כדי לא לפגוע בשינה ובתחושה באימון. הפעולה הבאה: לבדוק כמה קפאין יש במנה ולא לערבב כמה ממריצים יחד."
    )


def _weekly_action_plan_guidance_response() -> str:
    return (
        "השבוע מספיק פשוט: שני אימוני כוח קצרים ושתי הליכות קלות. "
        "אימון כוח ראשון בתחילת השבוע ואימון שני אחרי לפחות יום מנוחה: גוף מלא, 2-3 סטים לכל תרגיל, 8-12 חזרות, בלי להגיע לכשל. "
        "בימים בלי כוח: הליכה של 20-30 דקות בקצב נוח. "
        "הפעולה הבאה: לקבוע עכשיו שני ימי כוח ביומן ולהשאיר את ההליכות כגיבוי קל, לא כעוד אימון קשה."
    )


def _low_energy_action_guidance_response() -> str:
    return (
        "פעולה אחת: 10 דקות הליכה קלה או אופניים קלים, בלי למדוד ביצועים ובלי להשלים נפח. "
        "המטרה היום היא לשמור רצף, לא לנצח את התוכנית. "
        "אם יש סחרחורת, כאב חד, כאב בחזה או חולשה חריגה: לעצור ולפנות לעזרה מתאימה."
    )


def _creatine_guidance_response() -> str:
    return (
        "קריאטין הוא תוסף אופציונלי, לא חובה. לרוב הוא נחשב בטוח לאדם בריא במינון מקובל, "
        "אבל זה לא ייעוץ רפואי. אם יש מחלת כליות, תרופות קבועות, הריון, קטינות או ספק רפואי, "
        "דבר עם רופא או דיאטן לפני שימוש. אם אין מניעה: 3-5 גרם ביום של creatine monohydrate, "
        "עם מים, בלי לצפות לקסם. קודם ודא שהתוכנית, החלבון והשינה עקביים."
    )


def _memory_ack_response() -> str:
    return "מעכשיו אתחשב בזה בתכנון אימונים, התאמות ופעולה הבאה. אם זה משפיע על האימון הקרוב, כדאי לבחור גרסה שמתאימה לזה כבר היום."


def _knee_squat_substitution_response() -> str:
    return (
        "אל תדחוף דרך כאב ברך. החלף היום לאחת משלוש חלופות: סקוואט לקופסה בטווח קצר וללא כאב, "
        "דדליפט רומני עם משקולות או גומייה, או גשר ירך. שמור RPE 6-7 ו-1-2 חזרות ברזרבה. "
        "אם הכאב חד, מחמיר או נמשך, עצור והתייעץ עם איש מקצוע מוסמך. הפעולה הבאה: בחר חלופה אחת ותעד אם הייתה רגישות."
    )


# Provider-routed knowledge intents keep a vetted local fallback. Safety-sensitive
# and deterministic coaching intents stay in _handle_tool_intent.
_KNOWLEDGE_INTENT_FALLBACKS = {
    "nutrition_guidance": _nutrition_guidance_response,
}

# Map each provider-routed intent to the context family that retrieves the most relevant knowledge.
_PROVIDER_CONTEXT_INTENT_FOR = {
    "nutrition_guidance": "meal_log",
}
