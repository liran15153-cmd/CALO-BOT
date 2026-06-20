from dataclasses import dataclass
import re

from sqlalchemy.orm import Session

from backend.app.models import SafetyEvent
from backend.app.services.pain_text import has_pain_or_injury_signal


@dataclass(frozen=True)
class SafetyResult:
    flagged: bool
    event_type: str | None = None
    severity: str = "none"
    response: str = ""


class SafetyService:
    def __init__(self, db: Session):
        self.db = db

    def classify(self, text: str) -> SafetyResult:
        normalized = text.lower()

        if any(
            term in normalized
            for term in [
                "dizzy",
                "faint",
                "chest pain",
                "passed out",
                "blackout",
                "shortness of breath",
                "heart palpitations",
                "כאב בחזה",
                "לחץ בחזה",
                "סחרחורת",
                "עילפון",
                "התעלפתי",
                "קוצר נשימה",
                "דפיקות לב",
            ]
        ):
            return SafetyResult(
                flagged=True,
                event_type="dangerous_symptoms",
                severity="high",
                response=(
                    "עצור את האימון עכשיו. סחרחורת, עילפון או כאב בחזה בזמן אימון יכולים להיות סימן רציני. "
                    "פנה לאיש מקצוע רפואי מוסמך לפני שאתה ממשיך."
                ),
            )

        if has_pain_or_injury_signal(normalized):
            return SafetyResult(
                flagged=True,
                event_type="pain_or_injury",
                severity="medium",
                response=(
                    "עצור כל תנועה שגורמת לכאב. אני לא יכול לאבחן פציעה, אבל אפשר לעבור לתנועה קלה ללא כאב "
                    "ולהתייעץ עם איש מקצוע מוסמך אם הכאב חד או נמשך."
                ),
            )

        if any(
            term in normalized
            for term in [
                "laxative",
                "purge",
                "not eating",
                "skip all meals",
                "משלשל",
                "להקיא",
                "לא לאכול",
                "לדלג על כל הארוחות",
                "בלי אוכל",
            ]
        ):
            return SafetyResult(
                flagged=True,
                event_type="eating_disorder_risk",
                severity="high",
                response=(
                    "אני לא יכול לתמוך בהגבלת אוכל מזיקה או בהתנהגות של התרוקנות. שקול לדבר עם איש מקצוע מוסמך. "
                    "אני יכול לעזור במבנה כללי של ארוחות מאוזנות אם זה מתאים."
                ),
            )

        if self._has_extreme_calorie_target(normalized) or self._has_rapid_weight_loss_target(normalized) or any(
            term in normalized
            for term in [
                "500 calorie",
                "800 calorie",
                "starve",
                "rapid weight loss",
                "lose weight fast",
                "500 קלוריות",
                "800 קלוריות",
                "להרעיב",
                "ירידה מהירה",
                "לרדת מהר",
            ]
        ):
            return SafetyResult(
                flagged=True,
                event_type="extreme_dieting",
                severity="high",
                response=(
                    "אני לא יכול לעזור עם הגבלה קיצונית או הוראות לירידה מהירה במשקל. איש מקצוע כמו דיאטן קליני "
                    "או גורם רפואי מוסמך יכול לעזור לבנות תוכנית בטוחה יותר. אני כן יכול לעזור בהרגלים כלליים וברי קיימא."
                ),
            )

        if any(
            term in normalized
            for term in [
                "clenbuterol",
                "dnp",
                "anabolic",
                "steroid",
                "diuretic",
                "ephedrine",
                "קלנבוטרול",
                "סטרואיד",
                "סטרואידים",
                "משתן",
                "משתנים",
                "אפדרין",
            ]
        ):
            return SafetyResult(
                flagged=True,
                event_type="dangerous_substance",
                severity="high",
                response=(
                    "אני לא יכול לעזור בשימוש בחומרים מסוכנים, סטרואידים, ממריצים או משתנים לאימון או ירידה במשקל. "
                    "איש מקצוע רפואי מוסמך יכול לעזור להעריך סיכונים וחלופות בטוחות יותר."
                ),
            )

        return SafetyResult(flagged=False)

    @staticmethod
    def _has_extreme_calorie_target(text: str) -> bool:
        for match in re.finditer(r"\b(\d{3,4})\s*(?:calorie|calories|kcal|קלוריות|קלוריה)\b", text):
            if int(match.group(1)) <= 1000:
                return True
        return False

    @staticmethod
    def _has_rapid_weight_loss_target(text: str) -> bool:
        if not any(term in text for term in ["lose", "drop", "cut", "weight loss", "לרדת", "ירידה", "להוריד"]):
            return False
        if not any(term in text for term in ["month", "30 days", "חודש"]):
            return False
        for match in re.finditer(r"\b(\d{1,2}(?:\.\d+)?)\s*(?:kg|kgs|kilo|kilos|kilogram|kilograms|קילו|קג|ק\"ג)\b", text):
            if float(match.group(1)) >= 6:
                return True
        return False

    def record_event(self, user_id: int | None, source_text: str, result: SafetyResult) -> SafetyEvent:
        event = SafetyEvent(
            user_id=user_id,
            event_type=result.event_type or "unclassified",
            severity=result.severity,
            source_text=source_text,
            response_text=result.response,
            metadata_json={},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
