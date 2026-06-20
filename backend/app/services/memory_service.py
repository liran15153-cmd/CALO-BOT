from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import UserMemory


class MemoryService:
    def __init__(self, db: Session):
        self.db = db

    def extract_and_store(self, user_id: int, source_text: str) -> list[UserMemory]:
        candidates = self._extract(source_text)
        saved: list[UserMemory] = []
        for memory_type, content in candidates:
            existing = self.db.scalar(
                select(UserMemory).where(UserMemory.user_id == user_id, UserMemory.content == content)
            )
            if existing is not None:
                continue
            memory = UserMemory(
                user_id=user_id,
                memory_type=memory_type,
                content=content,
                source="chat",
                confidence="medium",
                is_sensitive=memory_type == "safety_limitation",
            )
            self.db.add(memory)
            saved.append(memory)
        if saved:
            self.db.commit()
            for memory in saved:
                self.db.refresh(memory)
        return saved

    @staticmethod
    def _extract(text: str) -> list[tuple[str, str]]:
        normalized = text.lower()
        memories: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()

        def remember(memory_type: str, content: str) -> None:
            candidate = (memory_type, content)
            if candidate in seen:
                return
            seen.add(candidate)
            memories.append(candidate)

        if _contains_any(normalized, ["short workout", "short workouts", "אימון קצר", "אימונים קצרים"]):
            remember("preference", "המשתמש מעדיף אימונים קצרים")
        if _contains_any(normalized, ["direct coaching", "prefer direct", "אימון ישיר", "סגנון ישיר"]):
            remember("preference", "המשתמש מעדיף אימון ישיר")
        if _contains_any(normalized, ["after work", "אחרי העבודה", "אחר העבודה"]):
            remember("schedule", "המשתמש בדרך כלל מתאמן אחרי העבודה")
        if "בערב" in normalized and _contains_any(normalized, ["אימון", "אימונים", "מתאמן", "להתאמן"]):
            remember("schedule", "המשתמש מעדיף להתאמן בערב")
        if "שלישי" in normalized and "חמישי" in normalized and "בערב" in normalized:
            remember("schedule", "המשתמש מעדיף להתאמן בשלישי וחמישי בערב")
        if _contains_any(normalized, ["dumbbell", "dumbbells", "משקולות יד", "דאמבל", "דאמבלים"]):
            remember("equipment", "למשתמש יש גישה למשקולות יד")
        if _contains_any(normalized, ["resistance band", "resistance bands", "גומיות התנגדות", "גומיות", "גומייה"]):
            remember("equipment", "למשתמש יש גישה לגומיות התנגדות")
        if _contains_any(normalized, ["hate running", "dislike running", "לא אוהב ריצה", "שונא ריצה", "בלי ריצה", "ללא ריצה"]):
            remember("preference", "המשתמש לא אוהב ריצה")
        if _contains_any(normalized, ["בלי קפיצות", "ללא קפיצות", "לא אוהב קפיצות"]):
            remember("preference", "המשתמש מעדיף אימונים בלי קפיצות")
        if _contains_any(
            normalized,
            [
                "knee pain",
                "knee hurts",
                "כאב ברך",
                "כאבי ברך",
                "ברך כואבת",
                "כואבת לי הברך",
                "רגישות ברך",
            ],
        ):
            remember("safety_limitation", "המשתמש דיווח על כאב או רגישות ברך בזמן אימון")
        if _contains_any(normalized, ["צמחוני", "טבעוני"]):
            remember("nutrition", "למשתמש יש העדפה תזונתית מהצומח")
        if _contains_any(
            normalized,
            [
                "רגיש ללקטוז",
                "רגישה ללקטוז",
                "רגישים ללקטוז",
                "רגישות ללקטוז",
                "רגיש ללאקטוז",
                "רגישה ללאקטוז",
                "רגישים ללאקטוז",
                "רגישות ללאקטוז",
            ],
        ):
            remember("nutrition", "המשתמש דיווח על רגישות ללקטוז")

        return memories


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)
