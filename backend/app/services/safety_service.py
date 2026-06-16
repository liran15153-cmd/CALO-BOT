from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.models import SafetyEvent


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

        if any(term in normalized for term in ["dizzy", "faint", "chest pain", "passed out", "blackout"]):
            return SafetyResult(
                flagged=True,
                event_type="dangerous_symptoms",
                severity="high",
                response=(
                    "Stop the workout now. Dizziness, fainting, or chest pain during exercise can be serious. "
                    "Please speak with a qualified medical professional before continuing."
                ),
            )

        if any(term in normalized for term in ["hurts", "pain", "injury", "injured", "sharp pain"]):
            return SafetyResult(
                flagged=True,
                event_type="pain_or_injury",
                severity="medium",
                response=(
                    "Stop any movement that causes pain. I cannot diagnose an injury, but you can switch to pain-free "
                    "light movement and consult a qualified professional if pain persists or is sharp."
                ),
            )

        if any(term in normalized for term in ["500 calorie", "800 calorie", "starve", "rapid weight loss", "lose weight fast"]):
            return SafetyResult(
                flagged=True,
                event_type="extreme_dieting",
                severity="high",
                response=(
                    "I cannot help with extreme restriction or rapid weight-loss instructions. A qualified dietitian or "
                    "medical professional can help set a safer plan. I can help with general, sustainable habits instead."
                ),
            )

        if any(term in normalized for term in ["laxative", "purge", "not eating", "skip all meals"]):
            return SafetyResult(
                flagged=True,
                event_type="eating_disorder_risk",
                severity="high",
                response=(
                    "I cannot support harmful food restriction or purging behavior. Please consider speaking with a "
                    "qualified professional. I can help with general balanced-meal structure if that is useful."
                ),
            )

        return SafetyResult(flagged=False)

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

