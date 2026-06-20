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
                    "לעצור את האימון עכשיו. סחרחורת, עילפון או כאב בחזה בזמן אימון יכולים להיות סימן רציני. "
                    "לפנות לאיש מקצוע רפואי מוסמך לפני המשך אימון."
                ),
            )

        if has_pain_or_injury_signal(normalized):
            return SafetyResult(
                flagged=True,
                event_type="pain_or_injury",
                severity="medium",
                response=(
                    "לעצור כל תנועה שגורמת לכאב. אני לא יכול לאבחן פציעה, אבל אפשר לעבור לתנועה קלה ללא כאב "
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

        dangerous_substance = self._dangerous_substance_label(normalized)
        if dangerous_substance:
            return SafetyResult(
                flagged=True,
                event_type="dangerous_substance",
                severity="high",
                response=(
                    f"אני לא יכול לעזור בשימוש ב-{dangerous_substance} או בחומרים מסוכנים לירידה במשקל או לאימון. "
                    "זה יכול להיות מסוכן גם כשנשמע כמו קיצור דרך. פנה לאיש מקצוע רפואי מוסמך אם כבר נלקח חומר כזה "
                    "או אם יש תסמינים חריגים. הפעולה הבאה: לבחור יעד בטוח יותר דרך אימונים, אוכל מספק ושינה."
                ),
            )

        if any(
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
        ) or self._has_extreme_calorie_target(normalized) or self._has_rapid_weight_loss_target(normalized):
            return SafetyResult(
                flagged=True,
                event_type="extreme_dieting",
                severity="high",
                response=(
                    "אני לא יכול לעזור עם הגבלה קיצונית או הוראות לירידה מהירה במשקל. איש מקצוע כמו דיאטן קליני "
                    "או גורם רפואי מוסמך יכול לעזור לבנות תוכנית בטוחה יותר. אני כן יכול לעזור בהרגלים כלליים וברי קיימא."
                ),
            )

        return SafetyResult(flagged=False)

    @staticmethod
    def _has_extreme_calorie_target(text: str) -> bool:
        if not any(
            term in text
            for term in [
                "per day",
                "daily",
                "diet",
                "target",
                "limit",
                "only eat",
                "meal plan",
                "lose weight",
                "cut weight",
                "ביום",
                "יומי",
                "דיאטה",
                "יעד",
                "להגביל",
                "רק לאכול",
                "לרדת במשקל",
            ]
        ):
            return False
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

    @staticmethod
    def _dangerous_substance_label(text: str) -> str | None:
        labels = {
            "dnp": "DNP",
            "clenbuterol": "clenbuterol",
            "קלנבוטרול": "קלנבוטרול",
            "anabolic": "סטרואידים אנאבוליים",
            "steroid": "סטרואידים",
            "סטרואיד": "סטרואידים",
            "סטרואידים": "סטרואידים",
            "diuretic": "משתנים",
            "משתן": "משתנים",
            "משתנים": "משתנים",
            "ephedrine": "ephedrine",
            "אפדרין": "אפדרין",
        }
        for term, label in labels.items():
            if term in text:
                return label
        return None

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
