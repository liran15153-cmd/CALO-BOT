import json

from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.prompts import coach_chat_prompt
from backend.app.schemas import ChatRequest, ChatResponse, MealTextRequest, WorkoutLogRequest, WorkoutPlanRequest
from backend.app.services.ai_provider import AIRequest, build_ai_provider
from backend.app.services.chat_service import ChatService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.coach_intent_service import CoachIntentService
from backend.app.services.language_guard import contains_hebrew, has_disallowed_latin_text, strip_markdown_markers
from backend.app.services.meal_service import MealService
from backend.app.services.memory_service import MemoryService
from backend.app.services.profile_service import ProfileService
from backend.app.services.safety_service import SafetyService
from backend.app.services.summary_service import SummaryService
from backend.app.services.usage_service import UsageService
from backend.app.services.workout_service import WorkoutService


class CoachEngine:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def respond(self, payload: ChatRequest) -> ChatResponse:
        profile_service = ProfileService(self.db)
        user = profile_service.get_default_user()
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
            return ChatResponse(
                session_id=session.id,
                user_message_id=user_message.id,
                coach_message_id=coach_message.id,
                response=safety_result.response,
                safety_flagged=True,
                provider_status="safety_override",
            )

        intent = CoachIntentService().classify(payload.message)
        tool_response = self._handle_tool_intent(user_id=user.id, intent_name=intent.name, payload_text=intent.payload_text)
        if tool_response is not None:
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
                content=tool_response,
                metadata={"provider_status": "local_tool", "intent": intent.name},
            )
            return ChatResponse(
                session_id=session.id,
                user_message_id=user_message.id,
                coach_message_id=coach_message.id,
                response=tool_response,
                safety_flagged=False,
                provider_status="local_tool",
            )

        usage_service = UsageService(self.db)
        if self.settings.anthropic_api_key and usage_service.is_daily_ai_token_budget_exceeded():
            budget_response = (
                "תקציב הבינה המלאכותית היומי נוצל. שמרתי את ההודעה שלך אבל לא שלחתי בקשה לספק הבינה המלאכותית. "
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
            intent=intent.name,
            user_message=payload.message,
        )
        provider = build_ai_provider(self.settings.anthropic_api_key, self.settings.anthropic_model)
        ai_request = AIRequest(
            instructions=coach_chat_prompt(),
            input_text=json.dumps({"context": context, "user_message": payload.message}, ensure_ascii=False),
            max_output_tokens=600,
        )
        ai_result = provider.chat(ai_request)
        UsageService(self.db).record_ai_result(user_id=user.id, task="chat", request=ai_request, result=ai_result)
        response_text = strip_markdown_markers(ai_result.text)
        if ai_result.provider_status == "configured" and (
            not contains_hebrew(response_text)
            or has_disallowed_latin_text(response_text)
        ):
            response_text = (
                "קיבלתי מספק הבינה המלאכותית תשובה שרובה לא בעברית, ולכן לא אציג אותה. "
                "נסה לשלוח שוב את הבקשה, והמאמן יחזיר תשובה בעברית ברורה."
            )
        coach_message = chat_service.add_message(
            user_id=user.id,
            session_id=session.id,
            role="coach",
            content=response_text,
            metadata={"provider_status": ai_result.provider_status, "model": ai_result.used_model},
        )

        return ChatResponse(
            session_id=session.id,
            user_message_id=user_message.id,
            coach_message_id=coach_message.id,
            response=response_text,
            safety_flagged=False,
            provider_status=ai_result.provider_status,
        )

    def _handle_tool_intent(self, user_id: int, intent_name: str, payload_text: str) -> str | None:
        if intent_name == "workout_plan":
            plan = WorkoutService(self.db).generate_plan(
                user_id=user_id,
                request=WorkoutPlanRequest(prompt=payload_text),
            )
            serialized = WorkoutService.serialize_plan(plan)
            return (
                f"שמרתי תוכנית אימון: {serialized['name']} עם {serialized['days_per_week']} ימים בשבוע. "
                "פתח את מסך האימונים כדי לעבור על המבנה המלא."
            )

        if intent_name == "workout_log":
            log = WorkoutService(self.db).parse_log(user_id=user_id, request=WorkoutLogRequest(text=payload_text))
            status = "נשמר סימון כאב. עצור תנועות כואבות ופעל לפי הנחיות הבטיחות." if log.pain_flag else "תיעוד האימון נשמר."
            return f"{status} רמת ביטחון: {_hebrew_confidence(log.parse_confidence)}."

        if intent_name == "meal_log":
            meal = MealService(self.db).log_manual_meal(user_id=user_id, request=MealTextRequest(text=payload_text))
            return (
                "תיעוד הארוחה נשמר עם טווח משוער: "
                f"{meal.calories_min}-{meal.calories_max} קלוריות, "
                f"{meal.protein_min}-{meal.protein_max} גרם חלבון."
            )

        if intent_name == "weekly_summary":
            summary = SummaryService(self.db).weekly_summary(user_id=user_id)
            return f"{summary.summary_text} הפעולה הבאה: {summary.next_action}"

        if intent_name == "daily_summary":
            summary = SummaryService(self.db).daily_summary(user_id=user_id)
            return f"{summary['summary']} הפעולה הבאה: {summary['next_action']}"

        if intent_name == "creatine_guidance":
            return (
                "קריאטין הוא תוסף אופציונלי, לא חובה. לרוב הוא נחשב בטוח לאדם בריא במינון מקובל, "
                "אבל זה לא ייעוץ רפואי. אם יש מחלת כליות, תרופות קבועות, הריון, קטינות או ספק רפואי, "
                "דבר עם רופא או דיאטן לפני שימוש. אם אין מניעה: 3-5 גרם ביום של creatine monohydrate, "
                "עם מים, בלי לצפות לקסם. קודם ודא שהתוכנית, החלבון והשינה עקביים."
            )

        if intent_name == "knee_squat_substitution":
            return (
                "אל תדחוף דרך כאב ברך. החלף היום לאחת משלוש חלופות: סקוואט לקופסה בטווח קצר וללא כאב, "
                "דדליפט רומני עם משקולות או גומייה, או גשר ירך. שמור RPE 6-7 ו-1-2 חזרות ברזרבה. "
                "אם הכאב חד, מחמיר או נמשך, עצור והתייעץ עם איש מקצוע מוסמך. הפעולה הבאה: בחר חלופה אחת ותעד אם הייתה רגישות."
            )

        return None


def _hebrew_confidence(value: str | None) -> str:
    return {"low": "נמוכה", "medium": "בינונית", "high": "גבוהה"}.get(value or "", value or "לא ידועה")
