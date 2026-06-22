import json
import re

from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.prompts import coach_chat_prompt
from backend.app.schemas import ChatRequest, ChatResponse, MealTextRequest, WorkoutLogRequest, WorkoutPlanRequest
from backend.app.services.ai_provider import AIRequest, build_ai_provider
from backend.app.services.chat_service import ChatService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.coach_intent_service import CoachIntentService
from backend.app.services.language_guard import (
    contains_hebrew,
    has_disallowed_latin_text,
    polish_hebrew_coach_response,
    violates_requested_neutral_address,
)
from backend.app.services.meal_service import MealService
from backend.app.services.memory_service import MemoryService
from backend.app.services.pain_text import extract_pain_area
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

        # Soft pain ("יש לי כאב ברך") is NOT a block. Record the audit event and
        # carry the pain area forward so downstream paths (plan generation, response
        # wrappers) can acknowledge it and adapt rather than refusing.
        pain_area: str | None = None
        if safety_result.event_type == "pain_signal":
            safety.record_event(user_id=user.id, source_text=payload.message, result=safety_result)
            pain_area = extract_pain_area(payload.message)

        intent = CoachIntentService().classify(payload.message)
        tool_response = self._handle_tool_intent(
            user_id=user.id,
            intent_name=intent.name,
            payload_text=intent.payload_text,
            pain_area=pain_area,
        )
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
            )

        if self.settings.anthropic_api_key and usage_service.is_daily_ai_token_budget_exceeded():
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
            intent=_PROVIDER_CONTEXT_INTENT_FOR.get(intent.name, intent.name),
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
        response_text = polish_hebrew_coach_response(ai_result.text)
        neutral_address_violation = violates_requested_neutral_address(payload.message, response_text)
        hebrew_ok = (
            contains_hebrew(response_text)
            and not has_disallowed_latin_text(response_text)
            and not neutral_address_violation
        )

        if ai_result.provider_status == "configured" and hebrew_ok:
            provider_status = "configured"
        elif fallback_text is not None:
            # Provider unusable (broken Hebrew, error, or not configured): fall back to the
            # vetted local answer so migrated knowledge intents never regress. The provider
            # call was already recorded above, so do not double-count usage here.
            return self._respond_local_tool(
                chat_service=chat_service,
                user=user,
                session=session,
                user_message=user_message,
                response_text=fallback_text,
                intent_name=intent.name,
                record_usage=False,
            )
        elif ai_result.provider_status == "configured":
            if neutral_address_violation:
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
            metadata={"provider_status": provider_status, "model": ai_result.used_model, "intent": intent.name},
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
            metadata={"provider_status": "local_tool", "intent": intent_name},
        )
        return ChatResponse(
            session_id=session.id,
            user_message_id=user_message.id,
            coach_message_id=coach_message.id,
            response=response_text,
            safety_flagged=False,
            provider_status="local_tool",
        )

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
        intent_name: str,
        payload_text: str,
        pain_area: str | None = None,
    ) -> str | None:
        if intent_name == "workout_plan":
            limitations = f"רגישות ב{pain_area}" if pain_area else None
            plan = WorkoutService(self.db).generate_plan(
                user_id=user_id,
                request=WorkoutPlanRequest(prompt=payload_text, limitations=limitations),
            )
            serialized = WorkoutService.serialize_plan(plan)
            return _workout_plan_saved_response(serialized, pain_area=pain_area)

        if intent_name == "workout_log":
            log = WorkoutService(self.db).parse_log(user_id=user_id, request=WorkoutLogRequest(text=payload_text))
            if log.pain_flag:
                return (
                    "רשמתי את האימון וגם שהיה כאב. אל תדחוף דרך כאב — אם הוא חוזר, מחמיר או חד, "
                    "עצור ושקול לפנות לאיש מקצוע מוסמך."
                )
            if log.parse_confidence == "low":
                return (
                    "רשמתי את האימון, כל הכבוד שסיימת. אם בא לך, כתוב לי גם כמה סטים, חזרות ומשקל "
                    "כדי שאוכל לעקוב אחרי ההתקדמות."
                )
            return "רשמתי את האימון, כל הכבוד שסיימת. ממשיכים לתעד כדי לראות מגמה ברורה."

        if intent_name == "meal_log":
            meal = MealService(self.db).log_manual_meal(user_id=user_id, request=MealTextRequest(text=payload_text))
            return (
                "רשמתי את הארוחה. הערכה גסה בטווח: "
                f"{meal.calories_min}-{meal.calories_max} קלוריות ו-"
                f"{meal.protein_min}-{meal.protein_max} גרם חלבון. זאת הערכה, לא מדידה מדויקת."
            )

        if intent_name == "weekly_summary":
            summary = SummaryService(self.db).weekly_summary(user_id=user_id)
            return f"{summary.summary_text} הפעולה הבאה: {summary.next_action}"

        if intent_name == "daily_summary":
            summary = SummaryService(self.db).daily_summary(user_id=user_id)
            return f"{summary['summary']} הפעולה הבאה: {summary['next_action']}"

        return None


def _workout_plan_saved_response(serialized: dict, pain_area: str | None = None) -> str:
    name = _natural_plan_name(str(serialized.get("name") or "תוכנית אימון"))
    if serialized.get("plan_type") == "single_session":
        body = f"שמרתי אימון יחיד: {name}. זה אימון חד-פעמי שנשמר ולא מחליף את התוכנית הפעילה."
    else:
        days_per_week = serialized.get("days_per_week")
        days_text = "יום אחד בשבוע" if days_per_week == 1 else f"{days_per_week} ימים בשבוע"
        body = (
            f"שמרתי תוכנית אימון: {name} עם {days_text}. "
            "אפשר לפתוח את מסך האימונים כדי לעבור על המבנה המלא."
        )

    if pain_area:
        ack = (
            f"שמתי לב שציינת כאב ב{pain_area}. בניתי את התוכנית סביב זה, עם תרגילים שמכבדים את הטווח. "
            "אם הכאב חוזר, מחמיר או חד — לעצור, ולא לדחוף דרך כאב. אם יש סימן רציני, לפנות לאיש מקצוע מוסמך."
        )
        return f"{ack} {body}"

    return body


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
        mixed_response = _mixed_rpe_rir_response(normalized)
        if mixed_response:
            return mixed_response
        return (
            "RPE 8 ו-RIR 2 הם כמעט אותו רעיון: לסיים סט קשה אבל להשאיר בערך 2 חזרות נקיות ברזרבה. "
            "לרוב המתאמנים קל יותר להתחיל עם RIR, כי פשוט שואלים כמה חזרות עוד היו נשארות בטכניקה טובה. "
            "הפעולה הבאה: בסטים המרכזיים היום לעצור סביב RIR 2, לא בכשל."
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
        return (
            "מתמונה אפשר לתת הערכה בטווח, לא מספר מדויק. הדיוק תלוי בגודל מנה, שמן, רוטב ומה שלא רואים בתמונה. "
            "בניתוח תמונה אציג מזונות שזוהו, טווח קלוריות, רמת ביטחון ושאלה אחת אם חסר מידע."
        )

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


def _knee_squat_substitution_response() -> str:
    return (
        "אל תדחוף דרך כאב ברך. החלף היום לאחת משלוש חלופות: סקוואט לקופסה בטווח קצר וללא כאב, "
        "דדליפט רומני עם משקולות או גומייה, או גשר ירך. שמור RPE 6-7 ו-1-2 חזרות ברזרבה. "
        "אם הכאב חד, מחמיר או נמשך, עצור והתייעץ עם איש מקצוע מוסמך. הפעולה הבאה: בחר חלופה אחת ותעד אם הייתה רגישות."
    )


# Open knowledge intents: routed to the provider + retrieval when Anthropic is configured,
# with the vetted local answer kept as a non-regressive fallback. Closed actions
# (logging, plan/summary generation) stay in _handle_tool_intent.
_KNOWLEDGE_INTENT_FALLBACKS = {
    "fitness_term_guidance": _fitness_term_guidance_response,
    "nutrition_guidance": _nutrition_guidance_response,
    "equipment_substitution_guidance": _equipment_substitution_guidance_response,
    "missed_workout_guidance": lambda _payload_text: _missed_workout_guidance_response(),
    "weekly_action_plan_guidance": lambda _payload_text: _weekly_action_plan_guidance_response(),
    "supplement_safety_guidance": _supplement_safety_guidance_response,
    "low_energy_action_guidance": lambda _payload_text: _low_energy_action_guidance_response(),
    "creatine_guidance": lambda _payload_text: _creatine_guidance_response(),
    "knee_squat_substitution": lambda _payload_text: _knee_squat_substitution_response(),
    "motivation_recovery": _motivation_recovery_response,
    "progress_metric": _progress_metric_response,
}

# Map each migrated intent to the context family that retrieves the most relevant knowledge.
_PROVIDER_CONTEXT_INTENT_FOR = {
    "nutrition_guidance": "meal_log",
    "equipment_substitution_guidance": "workout_plan",
    "weekly_action_plan_guidance": "workout_plan",
    "missed_workout_guidance": "workout_log",
    "fitness_term_guidance": "general_chat",
    # Motivation and progress answers are grounded in the user's recent training history.
    "motivation_recovery": "workout_log",
    "progress_metric": "workout_log",
}
