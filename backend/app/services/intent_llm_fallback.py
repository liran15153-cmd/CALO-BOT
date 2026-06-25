from typing import Any

from backend.app.services.ai_provider import AIProvider, AIRequest, AIResult
from backend.app.services.coach_intent_service import CoachIntentService


class IntentLlmFallback:
    KNOWN_INTENTS = tuple(
        dict.fromkeys(rule.intent_name or rule.name for rule in CoachIntentService._INTENT_RULES)
    )

    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.last_request: AIRequest | None = None
        self.last_result: AIResult | None = None

    def classify(self, text: str) -> tuple[str | None, str]:
        """Return (intent_name, confidence) or (None, 'low') if unsure/error."""
        request = AIRequest(
            instructions=(
                "סיווג intent למאמן כושר בעברית. המסווג הדטרמיניסטי כבר רץ; "
                "להחזיר intent רק אם ברור שההודעה מבקשת פעולה קיימת. "
                "לא לעקוף בטיחות, תיעוד אימון/ארוחה, עריכת תוכנית או בקשת תוכנית שכבר זוהו. "
                "כוונות מרכזיות: workout_plan לבניית אימון/תוכנית; workout_log לתיעוד אימון; "
                "meal_log לתיעוד ארוחה; workout_plan_edit לעריכה נקודתית; summaries לסיכומי תוכנית; "
                "guidance לשאלות ידע/התאוששות/ציוד/תוספים; non_fitness לנושא לא קשור. "
                "אם לא בטוח, לבחור unknown עם confidence low."
            ),
            input_text=text,
            max_output_tokens=80,
            input_components={"message": text},
        )
        tool = {
            "name": "classify_coach_intent",
            "description": "Classify a Hebrew-first fitness coach message into an existing route.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "intent": {"type": "string", "enum": [*self.KNOWN_INTENTS, "unknown"]},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["intent", "confidence"],
                "additionalProperties": False,
            },
        }
        self.last_request = request
        try:
            result = self.provider.extract_tool(request, tool)
        except Exception:
            self.last_result = None
            return None, "low"
        self.last_result = result

        output = result.structured_output
        if not isinstance(output, dict):
            return None, "low"
        intent = _clean_label(output.get("intent"))
        confidence = _clean_label(output.get("confidence"))
        if intent not in self.KNOWN_INTENTS or confidence not in {"high", "medium"}:
            return None, "low"
        return intent, confidence


def _clean_label(value: Any) -> str:
    return str(value or "").strip().lower()
