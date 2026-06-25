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
from backend.app.services.coach_intent_service import CoachIntent, CoachIntentService
from backend.app.services.intent_llm_fallback import IntentLlmFallback
from backend.app.services.language_guard import (
    assess_hebrew_response_quality,
    repair_hebrew_coach_response,
)
from backend.app.services.meal_service import MealService
from backend.app.services.memory_service import MemoryService
from backend.app.services.pending_action_service import PendingActionService
from backend.app.services.pain_text import extract_pain_area, has_explicit_pain_status, vague_pain_plan_clarification_response
from backend.app.services.profile_service import ProfileService
from backend.app.services.safety_service import SafetyService
from backend.app.services.token_budgeting import build_optimized_chat_request
from backend.app.services.usage_service import UsageService
from backend.app.services.workout_plan_builder import is_persistent_plan_type, is_single_workout_plan
from backend.app.services.workout_service import WorkoutService


COACH_CHAT_MAX_OUTPUT_TOKENS = 320
ToolResult = str | tuple[str, dict[str, Any]]
_PLAN_EDIT_RESPONSE_SUMMARIES = {
    "remove_bench": "הסרתי שימוש בספסל והחלפתי תרגילים או חלופות שדרשו ספסל.",
    "remove_cable": "הסרתי שימוש בכבל/פולי והחלפתי תרגילים או חלופות שדרשו כבל.",
    "replace_row_machine": "החלפתי חתירה במכונה לחלופת משיכה שמתאימה לציוד זמין.",
    "regress_pushup": "העברתי שכיבות סמיכה לגרסה קלה יותר מאותו דפוס תנועה.",
    "pain_substitution": "עדכנתי רק את התרגילים הרלוונטיים סביב הכאב, בלי לאבחן ובלי לבנות תוכנית חדשה.",
    "reduce_volume": "הורדתי נפח בתוכנית הפעילה בלי לשנות את כל המבנה.",
}


class CoachEngine:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def respond(self, payload: ChatRequest, user_id: int | None = None) -> ChatResponse:
        profile_service = ProfileService(self.db)
        user = self.db.get(User, user_id) if user_id is not None else profile_service.get_default_user()
        if user is None:
            raise ValueError("משתמש לא נמצא")
        chat_service = ChatService(self.db)
        session = chat_service.get_or_create_session(user_id=user.id, session_id=payload.session_id)

        user_message = chat_service.add_message(
            user_id=user.id,
            session_id=session.id,
            role="user",
            content=payload.message,
        )

        safety = SafetyService(self.db)
        memory = MemoryService(self.db)
        safety_result = safety.classify(payload.message)
        if safety_result.flagged:
            safety_event = safety.record_event(user_id=user.id, source_text=payload.message, result=safety_result)
            memory.process_user_message(
                user_id=user.id,
                text=payload.message,
                source_message_id=user_message.id,
                safety_event_id=safety_event.id,
            )
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
        safety_event_id: int | None = None
        if safety_result.event_type == "pain_signal":
            safety_event = safety.record_event(user_id=user.id, source_text=payload.message, result=safety_result)
            safety_event_id = safety_event.id
            pain_area = extract_pain_area(payload.message)
        memory.process_user_message(
            user_id=user.id,
            text=payload.message,
            source_message_id=user_message.id,
            safety_event_id=safety_event_id,
        )

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

        intent_service = CoachIntentService()
        intent = intent_service.classify(payload.message)
        usage_service = UsageService(self.db)
        intent_fallback_metadata: dict[str, Any] = {}
        if (
            intent.name == "general_chat"
            and self.settings.intent_llm_fallback_enabled
            and self.settings.anthropic_api_key
            and not usage_service.is_daily_ai_token_budget_exceeded(user_id=user.id)
        ):
            provider = build_ai_provider(self.settings.anthropic_api_key, self.settings.chat_model)
            fallback_classifier = IntentLlmFallback(provider)
            fallback_intent_name, fallback_confidence = fallback_classifier.classify(payload.message)
            if fallback_classifier.last_request is not None and fallback_classifier.last_result is not None:
                usage_service.record_ai_result(
                    user_id=user.id,
                    task="chat",
                    request=fallback_classifier.last_request,
                    result=fallback_classifier.last_result,
                )
            if fallback_intent_name is not None:
                intent = CoachIntent(name=fallback_intent_name, payload_text=payload.message)
                intent_fallback_metadata = {
                    "intent_llm_fallback": True,
                    "intent_llm_confidence": fallback_confidence,
                }
        secondary_intent = intent_service.secondary_state_intent(payload.message, intent.name)
        tool_response = self._handle_tool_intent(
            user_id=user.id,
            session_id=session.id,
            user_message_id=user_message.id,
            intent_name=intent.name,
            payload_text=intent.payload_text,
            raw_text=payload.message,
            pain_area=pain_area,
            pain_signal=safety_result.event_type == "pain_signal",
        )
        if tool_response is not None:
            response_text, response_metadata = _unpack_tool_result(tool_response)
            response_metadata = {**intent_fallback_metadata, **response_metadata}
            if secondary_intent is not None:
                response_text = _append_secondary_intent_prompt(response_text, secondary_intent)
                response_metadata = {**response_metadata, "secondary_intent": secondary_intent}
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
            return ChatResponse(
                session_id=session.id,
                user_message_id=user_message.id,
                coach_message_id=coach_message.id,
                response=response_text,
                safety_flagged=False,
                provider_status="local_tool",
            )

        fallback = _KNOWLEDGE_INTENT_FALLBACKS.get(intent.name)
        fallback_text = fallback(intent.payload_text) if fallback else None
        if fallback_text is not None and intent.name in {"motivation_recovery", "progress_metric"}:
            fallback_text = self._personalize_with_recent_activity(user.id, fallback_text)

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
                metadata=intent_fallback_metadata,
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
                    metadata=intent_fallback_metadata,
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
                metadata={**intent_fallback_metadata, **quality_metadata},
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
                **intent_fallback_metadata,
                **quality_metadata,
            },
        )

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

    def _personalize_with_recent_activity(self, user_id: int, text: str) -> str:
        """Prepend one grounded sentence when the user has recent logged workouts.

        Read-only: it only counts recent WorkoutLog rows already owned by the coach
        layer. With no history, the safe general answer is returned unchanged.
        """
        from datetime import date, timedelta

        from sqlalchemy import select

        from backend.app.models import WorkoutLog

        week_ago = date.today() - timedelta(days=7)
        recent_completed = self.db.scalars(
            select(WorkoutLog).where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.logged_on >= week_ago,
                WorkoutLog.status == "completed",
            )
        ).all()
        count = len(recent_completed)
        if count <= 0:
            return text
        if count == 1:
            prefix = "ראיתי שתיעדת אימון אחד בשבוע האחרון — הבסיס קיים, בוא נמשיך מכאן. "
        else:
            prefix = f"ראיתי שתיעדת {count} אימונים בשבוע האחרון — יש לך רצף, אל תזלזל בזה. "
        return f"{prefix}{text}"

    def _handle_tool_intent(
        self,
        user_id: int,
        session_id: int,
        user_message_id: int,
        intent_name: str,
        payload_text: str,
        raw_text: str | None = None,
        pain_area: str | None = None,
        pain_signal: bool = False,
    ) -> ToolResult | None:
        if intent_name == "workout_plan":
            if pain_signal and pain_area is None:
                return (
                    vague_pain_plan_clarification_response(),
                    {"missing_critical_info": "pain_area"},
                )
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
                and not is_single_workout_plan((current_before.plan_json or {}).get("plan_type"))
                and current_before.id != plan.id
                and not plan.is_current
                and is_persistent_plan_type(serialized.get("plan_type"))
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

        if intent_name == "workout_plan_edit":
            result = WorkoutService(self.db).apply_scoped_plan_edit(user_id=user_id, text=payload_text)
            return (
                result["message"],
                {
                    "plan_edit_status": result["status"],
                    "plan_edit_type": result["edit_type"],
                    "changed_exercises": result["changed_exercises"],
                },
            )

        if intent_name == "workout_plan_change_summary":
            return (
                _workout_plan_change_summary_response(WorkoutService(self.db).current_plan(user_id=user_id)),
                {"plan_change_summary": True},
            )

        if intent_name == "current_workout_plan_summary":
            workout_service = WorkoutService(self.db)
            return (
                _current_workout_plan_summary_response(
                    workout_service.current_plan(user_id=user_id),
                    workout_service=workout_service,
                ),
                {"current_workout_plan_summary": True},
            )

        if intent_name == "next_workout_summary":
            next_workout = WorkoutService(self.db).next_workout(user_id=user_id)
            return (
                _next_workout_summary_response(next_workout),
                _next_workout_summary_metadata(next_workout),
            )

        if intent_name == "workout_log":
            workout_service = WorkoutService(self.db)
            next_workout = workout_service.next_workout(user_id=user_id)
            workout_id = (
                next_workout.get("id")
                if next_workout and _text_log_targets_next_workout(raw_text or payload_text, next_workout)
                else None
            )
            log = workout_service.log_workout(
                user_id=user_id,
                request=WorkoutLogRequest(text=payload_text, workout_id=workout_id),
            )
            gate = _progression_gate_from_next_workout(next_workout) if workout_id else None
            return (
                "רשמתי את האימון. "
                f"{_workout_log_coach_response(log, progression_gate=gate, pain_status_known=_text_has_explicit_pain_status(payload_text))}"
            )

        if intent_name == "meal_log":
            meal = MealService(self.db).log_manual_meal(user_id=user_id, request=MealTextRequest(text=payload_text))
            return f"רשמתי את הארוחה. {_meal_log_coach_response(meal)}"

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

        if intent_name == "return_after_break_guidance":
            return _return_after_break_guidance_response()

        if intent_name == "weekly_action_plan_guidance":
            return _weekly_action_plan_guidance_response()

        if intent_name == "equipment_substitution_guidance":
            return _equipment_substitution_guidance_response(payload_text)

        if intent_name == "fitness_term_guidance":
            return _fitness_term_guidance_response(payload_text)

        if intent_name == "creatine_guidance":
            return _creatine_guidance_response()

        if intent_name == "non_fitness":
            return _non_fitness_response()

        return None


def _hebrew_confidence(value: str | None) -> str:
    return {"low": "נמוכה", "medium": "בינונית", "high": "גבוהה"}.get(value or "", value or "לא ידועה")


def _unpack_tool_result(result: ToolResult) -> tuple[str, dict[str, Any]]:
    if isinstance(result, tuple):
        return result
    return result, {}


def _append_secondary_intent_prompt(response_text: str, secondary_intent: str) -> str:
    if secondary_intent == "workout_plan":
        return (
            f"{response_text} קלטתי גם בקשה לאימון או תוכנית, אבל לא אשמור תוכנית מתוך אותה הודעה. "
            "הפעולה הבאה: שלח בקשת אימון אחת בנפרד."
        )
    if secondary_intent == "meal_log":
        return (
            f"{response_text} קלטתי גם ארוחה לתיעוד, אבל לא אשמור ארוחה מתוך אותה הודעה. "
            "הפעולה הבאה: שלח את הארוחה בנפרד."
        )
    if secondary_intent == "workout_log":
        return (
            f"{response_text} קלטתי גם תיעוד אימון, אבל לא אשמור אותו מתוך אותה הודעה. "
            "הפעולה הבאה: שלח את תיעוד האימון בנפרד."
        )
    return response_text


def _confirms_plan_replacement(text: str) -> bool:
    normalized = _normalize_plan_replacement_decision(text)
    if _has_plan_replacement_question_framing(normalized):
        return False
    if normalized in {"כן", "מאשר", "מאשרת", "yes", "confirm"}:
        return True
    explicit_action = any(
        phrase in normalized
        for phrase in [
            "תחליף",
            "תמחק",
            "מחק",
            "החלף",
            "להחליף",
            "הפעל את החדשה",
            "תפעיל את החדשה",
            "כן להחליף",
            "yes replace",
            "replace",
            "delete old",
            "activate",
        ]
    )
    if explicit_action:
        return True
    tokens = set(normalized.split())
    return bool({"כן", "yes"} & tokens) and any(
        phrase in normalized for phrase in ["החדשה", "להחליף", "תמחק", "תחליף", "replace", "activate"]
    )


def _has_plan_replacement_question_framing(text: str) -> bool:
    return "?" in text or any(
        marker in text
        for marker in [
            "מה זה",
            "מה אומר",
            "מה המשמעות",
            "מה ההבדל",
            "איך",
            "למה",
            "האם",
            "תסביר",
            "הסבר",
            "what",
            "how",
            "why",
            "explain",
            "difference",
        ]
    )


def _declines_plan_replacement(text: str) -> bool:
    normalized = _normalize_plan_replacement_decision(text)
    if _has_plan_replacement_question_framing(normalized):
        return False
    if normalized in {"לא", "no", "cancel", "עזוב", "עזבי"}:
        return True
    return any(
        phrase in normalized
        for phrase in [
            "אל תחליף",
            "אל תחליפי",
            "אל תמחק",
            "אל תמחקי",
            "לא להחליף",
            "לא למחוק",
            "תשאיר",
            "תשאירי",
            "השאר",
            "השאירי",
            "תשאיר את הקיימת",
            "להשאיר קיימת",
            "keep old",
            "keep current",
            "keep existing",
        ]
    )


def _normalize_plan_replacement_decision(text: str) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r"[\"'`.,!?;:(){}\[\]\-]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _workout_plan_change_summary_response(plan) -> str:
    if plan is None:
        return "אין כרגע תוכנית אימון פעילה שאפשר לסכם. הפעולה הבאה: לבנות תוכנית שבועית, לשבועיים או חודשית."
    edit_history = list((plan.plan_json or {}).get("plan_edit_history") or [])
    if not edit_history:
        return (
            "לא מצאתי עריכת תוכנית שמורה בתוכנית הפעילה. "
            "הפעולה הבאה: לבצע את האימון הבא ולתעד RPE או מאמץ מילולי, כאב ומה הושלם."
        )
    latest = edit_history[-1]
    edit_type = str(latest.get("edit_type") or "scoped_edit")
    summary = _PLAN_EDIT_RESPONSE_SUMMARIES.get(edit_type, "עשיתי שינוי נקודתי בתוכנית הפעילה בלי לבנות תוכנית חדשה.")
    changed = latest.get("changed_exercises")
    changed_text = f" זה נגע ב-{changed} תרגילים/חלופות." if isinstance(changed, int) and changed > 0 else ""
    return (
        f"השינוי האחרון בתוכנית: {summary}{changed_text} "
        "לא החלפתי את כל התוכנית. הפעולה הבאה: באימון הקרוב לבצע את הגרסה המעודכנת ולתעד RPE או מאמץ מילולי, כאב ומה הושלם."
    )


def _current_workout_plan_summary_response(plan, *, workout_service: WorkoutService) -> str:
    if plan is None:
        return "אין כרגע תוכנית אימון פעילה. הפעולה הבאה: לבקש תוכנית שבועית, לשבועיים או חודשית לפי הזמינות והציוד שלך."
    serialized = workout_service.serialize_plan_with_rows(plan)
    days = serialized.get("days") or []
    plan_type = serialized.get("plan_type") or "monthly_plan"
    days_per_week = serialized.get("days_per_week") or plan.days_per_week
    duration_weeks = serialized.get("duration_weeks") or plan.duration_weeks
    day_summaries = []
    for day in days[:3]:
        exercises = day.get("exercises") or []
        first_exercise = (exercises[0] or {}).get("name") if exercises else None
        if first_exercise:
            day_summaries.append(f"{day.get('name')}: מתחיל ב-{first_exercise}")
        elif day.get("name"):
            day_summaries.append(str(day.get("name")))
    days_text = "; ".join(day_summaries) if day_summaries else "אין פירוט ימים זמין כרגע."
    more_text = f" ועוד {len(days) - 3} ימים." if len(days) > 3 else "."
    return (
        f"התוכנית הפעילה שלך: {serialized.get('name') or plan.name}. "
        f"סוג: {plan_type}, משך {duration_weeks} שבועות, {days_per_week} ימים בשבוע. "
        f"תקציר ימים: {days_text}{more_text} "
        "אני לא מדביק כאן את כל התוכנית כדי לא להפוך את הצ׳אט לדאמפ ארוך; היא שמורה כתוכנית מובנית. "
        "הפעולה הבאה: לפתוח את האימון הבא ולתעד RPE או מאמץ מילולי, כאב ומה הושלם."
    )


def _next_workout_summary_response(next_workout: dict[str, Any] | None) -> str:
    if next_workout is None:
        return "אין כרגע אימון הבא כי אין תוכנית פעילה. הפעולה הבאה: לבקש תוכנית שבועית, לשבועיים או חודשית לפי הזמינות והציוד שלך."
    plan = next_workout.get("plan") or {}
    execution_plan = next_workout.get("execution_plan") or {}
    adaptation = next_workout.get("adaptation") or {}
    exercises = execution_plan.get("adjusted_exercises") or next_workout.get("exercises") or []
    exercise_lines = []
    for exercise in exercises[:4]:
        name = exercise.get("name") or "תרגיל"
        sets = exercise.get("sets") or "-"
        reps = exercise.get("reps_or_duration") or "-"
        rest = exercise.get("rest") or "-"
        exercise_lines.append(f"{name}: {sets} סטים, {reps}, מנוחה {rest}")
    exercises_text = "; ".join(exercise_lines) if exercise_lines else "אין פירוט תרגילים זמין כרגע."
    more_text = f" ועוד {len(exercises) - 4} תרגילים." if len(exercises) > 4 else "."
    load_summary = execution_plan.get("summary") or adaptation.get("next_adjustment") or "לבצע לפי התוכנית הנוכחית."
    gate = _progression_gate_from_next_workout(next_workout)
    gate_text = f" שער התקדמות: {gate.get('execution_note')}" if gate else ""
    plan_text = f" מתוך {plan.get('name')}" if plan.get("name") else ""
    return (
        f"האימון הבא שלך: {next_workout.get('name') or 'האימון הבא'}{plan_text}. "
        f"הנחיית ביצוע: {load_summary} "
        f"תרגילים ראשונים: {exercises_text}{more_text}{gate_text} "
        "הפעולה הבאה: לבצע את האימון הזה ולתעד לכל הפחות מה הושלם, RPE או מאמץ מילולי, והאם היה כאב."
    )


def _next_workout_summary_metadata(next_workout: dict[str, Any] | None) -> dict[str, Any]:
    if next_workout is None:
        return {"next_workout_summary": True, "next_workout_id": None, "exercise_ids": []}
    execution_plan = next_workout.get("execution_plan") or {}
    exercises = execution_plan.get("adjusted_exercises") or next_workout.get("exercises") or []
    return {
        "next_workout_summary": True,
        "next_workout_id": next_workout.get("id"),
        "exercise_ids": [exercise.get("exercise_id") for exercise in exercises if exercise.get("exercise_id")],
    }



def _workout_plan_saved_response(
    serialized: dict,
    pain_area: str | None = None,
    *,
    replacement_candidate: bool = False,
) -> str:
    name = _natural_plan_name(str(serialized.get("name") or "תוכנית אימון"))
    assumptions_text = _plan_assumptions_text(serialized)
    weekly_spacing_text = _plan_weekly_spacing_text(serialized)
    horizon_text = _plan_horizon_text(serialized)
    if is_single_workout_plan(serialized.get("plan_type")):
        body = (
            f"אימון יחיד מוכן: {name}. {assumptions_text}"
            "זה אימון חד-פעמי ולא מחליף את התוכנית הפעילה. "
            f"{_first_workout_next_action(serialized, single_workout=True)}"
        )
    else:
        days_per_week = serialized.get("days_per_week")
        days_text = "יום אחד בשבוע" if days_per_week == 1 else f"{days_per_week} ימים בשבוע"
        if replacement_candidate:
            body = (
                f"בניתי תוכנית חדשה: {name}, {days_text}. {assumptions_text}{weekly_spacing_text}{horizon_text}"
                f"{_first_workout_preview(serialized)}"
                "היא לא מחליפה עדיין את התוכנית הפעילה. "
                "רוצה למחוק את הישנה ולהפוך את החדשה לתוכנית הפעילה? "
                "הפעולה הבאה: לענות 'כן להחליף' כדי להפעיל אותה, או 'להשאיר קיימת' כדי למחוק את המועמדת."
            )
        else:
            body = (
                f"תוכנית אימון מוכנה: {name} עם {days_text}. {assumptions_text}{weekly_spacing_text}{horizon_text}"
                f"{_first_workout_next_action(serialized)}"
            )

    if pain_area:
        ack = (
            f"שמתי לב שציינת כאב ב{pain_area}. זו לא אבחנה; התאמתי את התוכנית שמרנית לטווח ללא כאב. "
            "אם הכאב חוזר, מחמיר או חד - לעצור, ולא לדחוף דרך כאב. אם יש סימן רציני, לפנות לאיש מקצוע מוסמך."
        )
        return f"{ack} {body}"

    return body


def _first_workout_next_action(serialized: dict, *, single_workout: bool = False) -> str:
    days = serialized.get("days") or []
    first_day = days[0] if days else {}
    day_name = str(first_day.get("name") or "היום הראשון")
    exercises = first_day.get("exercises") or []
    first_exercise = str((exercises[0] or {}).get("name") or "התרגיל הראשון") if exercises else "התרגיל הראשון"
    if single_workout:
        return f"הפעולה הבאה: להתחיל ב{first_exercise}, לבצע את שאר האימון לפי הסדר, ולתעד RPE או מאמץ מילולי, כאב ומה הושלם - לא לנחש."
    return f"הפעולה הבאה: להתחיל מ{day_name}, תרגיל ראשון {first_exercise}, ואז לתעד RPE או מאמץ מילולי, כאב ומה הושלם - לא לנחש."


def _first_workout_preview(serialized: dict) -> str:
    days = serialized.get("days") or []
    first_day = days[0] if days else {}
    exercises = first_day.get("exercises") or []
    if not exercises:
        return ""
    first_exercise = str((exercises[0] or {}).get("name") or "").strip()
    if not first_exercise:
        return ""
    return f"האימון הראשון בתוכנית החדשה מתחיל ב{first_exercise}. "


def _plan_assumptions_text(serialized: dict) -> str:
    assumptions = (serialized.get("decision_inputs") or {}).get("assumptions") or []
    if not assumptions:
        return ""
    visible = _visible_plan_assumptions(assumptions)
    if not visible:
        return ""
    return f"הנחות: {'; '.join(visible)}. "


def _visible_plan_assumptions(assumptions: list[str]) -> list[str]:
    cleaned = [str(assumption).strip().rstrip(".") for assumption in assumptions if str(assumption).strip()]
    if not cleaned:
        return []
    priorities = [
        ("ימי אימון", "אימונים בשבוע"),
        ("משך אימון", "דקות"),
        ("ציוד", "משקל גוף"),
        ("אופק תוכנית", "תוכנית חודשית"),
        ("מטרה", "שיפור כושר"),
        ("רמת ניסיון", "מתחיל/ה"),
    ]
    selected: list[str] = []
    for terms in priorities:
        match = next((item for item in cleaned if item not in selected and any(term in item for term in terms)), None)
        if match:
            selected.append(match)
        if len(selected) >= 3:
            return selected
    for item in cleaned:
        if item not in selected:
            selected.append(item)
        if len(selected) >= 3:
            break
    return selected


def _plan_weekly_spacing_text(serialized: dict) -> str:
    days_per_week = serialized.get("days_per_week") or 0
    if days_per_week < 4:
        return ""
    guidance = (serialized.get("decision_inputs") or {}).get("weekly_spacing_guidance")
    if not guidance:
        return ""
    first_sentence = str(guidance).strip().split(".")[0].strip()
    if not first_sentence:
        return ""
    return f"{first_sentence}. "


def _plan_horizon_text(serialized: dict) -> str:
    plan_type = str(serialized.get("plan_type") or "")
    keyword_sets = {
        "weekly_plan": ("בסוף השבוע",),
        "two_week_plan": ("שבוע 1", "שבוע 2"),
        "monthly_plan": ("בסוף כל שבוע",),
    }
    keywords = keyword_sets.get(plan_type)
    if not keywords:
        return ""
    label = _natural_plan_name(plan_type)
    for item in serialized.get("tracking_guidance") or []:
        text = str(item).strip().rstrip(".")
        if text and all(keyword in text for keyword in keywords):
            return f"{label}: {text}. "
    return f"{label}: לתעד RPE או מאמץ מילולי, כאב והשלמות לפני שינוי עומס או נפח. "


def _activated_plan_response(serialized: dict) -> str:
    name = _natural_plan_name(str(serialized.get("name") or "תוכנית אימון"))
    days_per_week = serialized.get("days_per_week")
    days_text = "יום אחד בשבוע" if days_per_week == 1 else f"{days_per_week} ימים בשבוע"
    horizon_text = _plan_horizon_text(serialized)
    return (
        f"התוכנית החדשה פעילה עכשיו: {name}, {days_text}. {horizon_text}"
        "הפעולה הבאה: להתחיל מהאימון הראשון ולתעד RPE או מאמץ מילולי, כאב ומה הושלם - לא לנחש."
    )


def _text_log_targets_next_workout(text: str, next_workout: dict[str, Any]) -> bool:
    normalized = text.lower()
    explicit_current_workout = [
        "עשיתי את האימון",
        "סיימתי את האימון",
        "סיימתי אימון של היום",
        "האימון של היום",
        "האימון הבא",
        "האימון בתוכנית",
        "תעד אימון",
        "לתעד אימון",
        "רשום אימון",
        "רשמתי אימון",
        "סיימתי אימון",
        "עשיתי אימון",
        "finished the workout",
        "did the workout",
        "today's workout",
        "next workout",
        "current workout",
    ]
    if any(phrase in normalized for phrase in explicit_current_workout):
        return True

    execution_plan = next_workout.get("execution_plan") or {}
    for exercise in execution_plan.get("adjusted_exercises") or []:
        name = str(exercise.get("name") or "").strip().lower()
        if len(name) >= 4 and name in normalized:
            return True
    return False


def _progression_gate_from_next_workout(next_workout: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_workout:
        return None
    execution_plan = next_workout.get("execution_plan") or {}
    for exercise in execution_plan.get("adjusted_exercises") or []:
        notes = str(exercise.get("notes") or "")
        if exercise.get("adjustment") == "substitution_progression_gate" or any(
            marker in notes for marker in ["הוחלף", "קשות מדי", "לא זמינה", "לא זמין"]
        ):
            return exercise
    return None


def _text_has_explicit_pain_status(text: str) -> bool:
    return has_explicit_pain_status(text)


def _workout_log_coach_response(
    log,
    *,
    progression_gate: dict[str, Any] | None = None,
    pain_status_known: bool = True,
) -> str:
    if log.pain_flag:
        return (
            "הכאב הוא הסימן החשוב כאן. לעצור תנועות שמכאיבות, להוריד עומס או טווח באימון הבא, "
            "ואם הכאב חד, מחמיר או חוזר - לפנות לאיש מקצוע מתאים."
        )
    if log.status == "skipped":
        return "לא משלימים אימון שפוספס בכוח. הפעולה הבאה: לחזור בגרסה קצרה של 20-30 דקות או לבצע את האימון הבא כרגיל."
    if log.status in {"partial", "modified"}:
        return "אימון חלקי עדיין נותן מידע טוב לתכנון. הפעולה הבאה: באימון הבא לשמור על אותו עומס או להוריד סט אחד אם העייפות נשארת."
    if progression_gate and log.status == "completed" and (log.rpe is None or not pain_status_known):
        exercise_name = str(progression_gate.get("name") or "התרגיל שהוחלף")
        missing = []
        if log.rpe is None:
            missing.append("RPE 1-10")
        if not pain_status_known:
            missing.append("האם הופיע כאב")
        return (
            f"זה נשמר, אבל חסר {' ו'.join(missing)} כדי להחליט על שער ההתקדמות של {exercise_name}. "
            "הפעולה הבאה: שלח את החסר במשפט אחד; בלי זה נשמור את הגרסה הנוכחית ולא ננחש."
        )
    if progression_gate and log.status == "completed" and log.rpe is not None and pain_status_known:
        exercise_name = str(progression_gate.get("name") or "התרגיל שהוחלף")
        if log.rpe >= 9:
            return (
                f"RPE {log.rpe} גבוה מדי לשער התקדמות של {exercise_name}. "
                "הפעולה הבאה: לשמור את הגרסה הנוכחית או להוריד מעט נפח, בלי להעלות שלב."
            )
        if not log.exercise_results:
            return (
                f"RPE {log.rpe} ובלי כאב פותחים שער זהיר של שלב אחד ל{exercise_name}. "
                "זה לוג כללי, אז באימון הבא לתעד גם חזרות/RPE לתרגיל הזה - לא לנחש; אם זה עובר RPE 8 או מופיע כאב - לשמור."
            )
        next_step = str(progression_gate.get("progression_next_step") or "").strip()
        if next_step:
            return (
                f"הלוג של {exercise_name} נקי: RPE {log.rpe} ובלי כאב. "
                f"הפעולה הבאה: להתקדם שלב אחד בלבד, רק ל{next_step}; לתעד בפועל ולא לנחש. אם זה עובר RPE 8 או מופיע כאב - לחזור לגרסה הנוכחית."
            )
        return (
            f"RPE {log.rpe} ובלי כאב מספיקים לשער ההתקדמות של {exercise_name}. "
            "הפעולה הבאה: להתקדם שלב אחד בלבד, לתעד בפועל ולא לנחש; אם זה עובר RPE 8 או מופיע כאב - לשמור את הגרסה הנוכחית."
        )
    if log.rpe is not None:
        if log.rpe >= 9:
            return f"RPE {log.rpe} אומר שהאימון היה קשה מאוד. הפעולה הבאה: באימון הבא לשמור עומס או להוריד מעט נפח, לא להוסיף עוד סטים."
        if log.exercise_results:
            return f"RPE {log.rpe} נראה מאמץ בשליטה. הפעולה הבאה: לחזור על אותו מבנה, ואם הטכניקה נשארת נקייה להוסיף חזרה אחת בתרגיל המרכזי ולתעד בפועל."
        return f"RPE {log.rpe} נראה מאמץ בשליטה, אבל חסר תרגיל מרכזי עם חזרות. הפעולה הבאה: לחזור על אותו מבנה ולתעד תרגיל מרכזי, חזרות, RPE וכאב - לא להוסיף חזרה מתוך ניחוש."
    if log.exercise_results:
        rir = _first_logged_rir(log)
        if rir is not None:
            if rir <= 0:
                return f"RIR {rir} אומר שהסט היה קרוב לכשל. הפעולה הבאה: באימון הבא לשמור עומס או להוריד מעט, ולא להוסיף חזרות עד שיש סט נקי יותר."
            if rir <= 3:
                return f"RIR {rir} עם תיעוד חזרות נותן בסיס להתקדמות זהירה. הפעולה הבאה: באימון הבא להוסיף חזרה אחת או עומס קטן אחד בלבד, ולתעד שוב RPE/RIR וכאב."
            return f"RIR {rir} אומר שנשאר הרבה מרווח. הפעולה הבאה: להעלות עומס קטן או להאט קצב כדי לכוון ל-RIR 1-3, בלי קפיצה גדולה."
        effort_signal = _first_logged_effort_signal(log)
        if effort_signal == "too_hard":
            return "כתבת שהסט היה קשה או כבד מדי. הפעולה הבאה: באימון הבא לשמור עומס או להוריד מעט, ולתעד אם נשארו 1-3 חזרות נקיות."
        if effort_signal == "underloaded":
            return "כתבת שזה היה קל מדי או שנשאר הרבה כוח. הפעולה הבאה: להעלות עומס קטן או להאט קצב, ולכוון ל-1-3 חזרות נקיות ברזרבה."
        if effort_signal == "controlled":
            return "נשמע שהמאמץ היה בשליטה. הפעולה הבאה: לחזור על אותו מבנה ולתעד RPE 1-10 או RIR וכאב לפני שמעלים עומס."
        return "האימון נראה ברור מספיק לתכנון הבא. הפעולה הבאה: באימון הבא לתעד גם RPE כללי כדי לדעת אם להעלות או לשמור עומס."
    return "הכיוון ברור. הפעולה הבאה: באימון הבא להוסיף תרגיל מרכזי, חזרות או RPE כדי שאפשר יהיה להתאים עומס בצורה מדויקת יותר."


def _meal_log_coach_response(meal) -> str:
    calories = _range_text(meal.calories_min, meal.calories_max, "קלוריות")
    protein = _range_text(meal.protein_min, meal.protein_max, "גרם חלבון")
    return (
        f"ההערכה לארוחה הזו היא {calories} ו-{protein}. "
        "זה טווח, לא מספר מדויק. הפעולה הבאה: בארוחה הבאה לבחור עוגן חלבון אחד ולהשאיר את זה פשוט."
    )


def _first_logged_rir(log) -> int | None:
    for result in getattr(log, "exercise_results", None) or []:
        if not isinstance(result, dict):
            continue
        value = result.get("rir")
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            return int(value)
    return None


def _first_logged_effort_signal(log) -> str | None:
    for result in getattr(log, "exercise_results", None) or []:
        if not isinstance(result, dict):
            continue
        value = result.get("effort_signal")
        if value in {"too_hard", "underloaded", "controlled"}:
            return str(value)
    return None


def _range_text(low: int | None, high: int | None, unit: str) -> str:
    if low is None or high is None:
        return f"טווח {unit} לא ברור"
    return f"{low}-{high} {unit}"


def _natural_plan_name(name: str) -> str:
    replacements = {
        "full_body": "גוף מלא",
        "upper_lower": "עליון/תחתון",
        "push_pull_legs": "דחיפה/משיכה/רגליים",
        "single_workout": "אימון יחיד",
        "single_session": "אימון יחיד",
        "weekly_plan": "תוכנית שבועית",
        "two_week_plan": "תוכנית לשבועיים",
        "monthly_plan": "תוכנית חודשית",
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
        "לא מתחילים מאפס אחרי פספוס, ולא מחזירים את כל הנפח בבת אחת. "
        "אם זה היה בגלל זמן: לחזור לאימון הבא בתור או לבצע את האימון שפספסת בגרסה קצרה. "
        "אם זה היה בגלל עייפות, כאב או שינה גרועה: גרסת מינימום של 20-30 דקות, פחות סטים ובלי להעלות עומס. "
        "הפעולה הבאה: לבחור חלון אחד קרוב, לסיים גרסה קצרה, ולתעד מה הפריע."
    )


def _return_after_break_guidance_response() -> str:
    return (
        "אחרי הפסקה ארוכה לא חוזרים ביום הראשון למספרים הישנים, וגם לא עושים אימון פיצוי. "
        "שבוע החזרה צריך להיות קל-בינוני: בערך 60-80% מהנפח או העומס שהיית רגיל אליו, RPE 5-7, ולהשאיר 2-4 חזרות ברזרבה. "
        "אם ההפסקה הייתה בגלל מחלה, כאב או שינה גרועה, התחל אפילו נמוך יותר ואל תעלה עומס עד שהתגובה ברורה. "
        "הפעולה הבאה: לעשות אימון בסיסי קצר, לתעד RPE או מאמץ מילולי, כאב/עייפות, ולהעלות רק אחרי 2-3 אימונים נקיים."
    )


def _nutrition_guidance_response(text: str) -> str:
    normalized = text.lower()
    if "תמונה" in normalized and ("מדויק" in normalized or "להעריך" in normalized):
        return _meal_image_guidance_response()

    ate_food = any(verb in normalized for verb in ["אכלתי", "i ate", "i had", "זללתי", "טרפתי", "חיסלתי"])
    asks_judgment = any(
        marker in normalized
        for marker in ["חיטוב", "משמין", "דופק", "הורס", "מקלקל", "מעלה", "יעלה", "ישמין"]
    )
    if ate_food and asks_judgment:
        return (
            "ארוחה אחת לא בונה ולא הורסת חיטוב — מה שקובע הוא המאזן השבועי, לא מנה בודדת. "
            "אם רוב השבוע מסודר עם חלבון, ירקות ולא יותר מדי קלוריות, ארוחה חופשית נכנסת בלי דרמה. "
            "הפעולה הבאה: לחזור לארוחה הרגילה הבאה כרגיל, ולהסתכל על המגמה השבועית ולא על היום הבודד."
        )

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


def _motivation_recovery_response(text: str) -> str:
    normalized = text.lower()
    asks_rest = any(
        phrase in normalized
        for phrase in ["מנוחה", "ימי מנוחה", "יום מנוחה", "rest day", "rest between"]
    ) and not any(
        phrase in normalized for phrase in ["אין מוטיבציה", "בא לי לוותר", "נמאס", "מאסתי", "אין חשק"]
    )
    if asks_rest:
        return (
            "מנוחה היא חלק מהאימון, לא בזבוז. בין אימון קשה לאותה קבוצת שרירים כדאי בערך 48 שעות. "
            "אם מפצלים קבוצות, אפשר להתאמן בימים סמוכים. "
            "הפעולה הבאה: לשמור לפחות יום מנוחה אחד מלא בשבוע, ולישון טוב — שם נבנה השריר."
        )
    return (
        "ימים בלי חשק זה נורמלי, וזה לא אומר שנכשלת. אל תחכה למוטיבציה — היא מגיעה אחרי שמתחילים, לא לפני. "
        "הפעולה הבאה: תעשה היום גרסה קטנה, אפילו 10-15 דקות. עקביות מנצחת מושלמות, "
        "ולסמן אימון קצר עדיף על לדלג לגמרי."
    )


def _progress_metric_response(text: str) -> str:
    normalized = text.lower()
    if "שריר או שומן" in normalized:
        return (
            "קשה לדעת ממספר אחד על המשקל אם זה שריר או שומן, והמשקל קופץ עם מים, מלח ואוכל. "
            "מה שבאמת מראה התקדמות: עומסים שעולים באימון, היקפים ותמונות כל כמה שבועות. "
            "הפעולה הבאה: לשקול במשקל ממוצע שבועי, ולהסתכל על המגמה לאורך זמן ולא על יום בודד."
        )
    return (
        "שבועיים בלי תזוזה במשקל זה לא בהכרח תקיעה — המשקל זז עם מים, שינה ואוכל. "
        "לפני ששוברים הכל, כדאי להסתכל על ממוצע שבועי ועל העומסים באימון, לא על מספר יומי. "
        "הפעולה הבאה: לשמור על העקביות עוד 1-2 שבועות, לוודא חלבון וצעדים, ואז לשנות דבר אחד בלבד."
    )
def _non_fitness_response() -> str:
    return "אני ממוקד בכושר, תזונה כללית, התאוששות והרגלים. הפעולה הבאה: שלח שאלה שקשורה לאימון, ארוחה, כאב באימון או התקדמות."


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
    "equipment_substitution_guidance": _equipment_substitution_guidance_response,
    "missed_workout_guidance": lambda _payload_text: _missed_workout_guidance_response(),
    "return_after_break_guidance": lambda _payload_text: _return_after_break_guidance_response(),
    "weekly_action_plan_guidance": lambda _payload_text: _weekly_action_plan_guidance_response(),
    "supplement_safety_guidance": _supplement_safety_guidance_response,
    "low_energy_action_guidance": lambda _payload_text: _low_energy_action_guidance_response(),
    "creatine_guidance": lambda _payload_text: _creatine_guidance_response(),
    "knee_squat_substitution": lambda _payload_text: _knee_squat_substitution_response(),
    "motivation_recovery": _motivation_recovery_response,
    "progress_metric": _progress_metric_response,
}

# Map each provider-routed intent to the context family that retrieves the most relevant knowledge.
_PROVIDER_CONTEXT_INTENT_FOR = {
    "nutrition_guidance": "meal_log",
    "equipment_substitution_guidance": "workout_plan",
    "weekly_action_plan_guidance": "workout_plan",
    "missed_workout_guidance": "workout_log",
    "return_after_break_guidance": "workout_log",
    "fitness_term_guidance": "general_chat",
    # Motivation and progress answers are grounded in the user's recent training history.
    "motivation_recovery": "workout_log",
    "progress_metric": "workout_log",
}
