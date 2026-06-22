from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.models import ChatMessage, MemorySummary, UserMemory, UserProfile
from backend.app.services.text_normalization import normalize_user_text


MIN_SUMMARY_MEMORIES = 3
MIN_SUMMARY_MESSAGES = 4
MAX_SUMMARY_MEMORIES = 12
MAX_RECENT_USER_MESSAGES = 3


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

    def refresh_long_term_summary(self, user_id: int) -> MemorySummary | None:
        memories = self.db.scalars(
            select(UserMemory)
            .where(UserMemory.user_id == user_id)
            .order_by(desc(UserMemory.created_at), desc(UserMemory.id))
            .limit(MAX_SUMMARY_MEMORIES)
        ).all()
        message_count = int(
            self.db.scalar(select(func.count(ChatMessage.id)).where(ChatMessage.user_id == user_id)) or 0
        )
        if len(memories) < MIN_SUMMARY_MEMORIES and message_count < MIN_SUMMARY_MESSAGES:
            return None

        profile = self.db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        recent_user_messages = self.db.scalars(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id, ChatMessage.role == "user")
            .order_by(desc(ChatMessage.created_at), desc(ChatMessage.id))
            .limit(MAX_RECENT_USER_MESSAGES)
        ).all()
        content = self._build_long_term_summary(
            profile=profile,
            memories=list(reversed(memories)),
            recent_user_messages=list(reversed(recent_user_messages)),
        )
        last_message_id = self.db.scalar(
            select(ChatMessage.id)
            .where(ChatMessage.user_id == user_id)
            .order_by(desc(ChatMessage.id))
            .limit(1)
        )
        source_range = {
            "memory_count": len(memories),
            "chat_message_count": message_count,
            "last_chat_message_id": last_message_id,
        }
        summary = self.db.scalar(
            select(MemorySummary).where(
                MemorySummary.user_id == user_id,
                MemorySummary.summary_type == "long_term",
            )
        )
        if summary is None:
            summary = MemorySummary(
                user_id=user_id,
                summary_type="long_term",
                content=content,
                source_range_json=source_range,
            )
            self.db.add(summary)
        else:
            summary.content = content
            summary.source_range_json = source_range
        self.db.commit()
        self.db.refresh(summary)
        return summary

    @staticmethod
    def _extract(text: str) -> list[tuple[str, str]]:
        normalized = normalize_user_text(text)
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

    @staticmethod
    def _build_long_term_summary(
        *,
        profile: UserProfile | None,
        memories: list[UserMemory],
        recent_user_messages: list[ChatMessage],
    ) -> str:
        parts: list[str] = []
        if profile is not None:
            parts.append(
                "Profile: "
                f"goal={profile.main_goal}; experience={profile.experience_level}; "
                f"location={profile.training_location}; availability={profile.weekly_availability}x/week; "
                f"session_length={profile.session_length_minutes}min"
            )
            if profile.available_equipment:
                parts.append("Equipment: " + ", ".join(profile.available_equipment[:8]))
            if profile.nutrition_preference:
                parts.append(f"Nutrition preference: {profile.nutrition_preference}")
            if profile.injuries_limitations:
                parts.append(f"Limitations: {profile.injuries_limitations}")

        if memories:
            facts = "; ".join(memory.content for memory in memories[:MAX_SUMMARY_MEMORIES])
            parts.append(f"Durable coaching facts: {facts}")

        if recent_user_messages:
            messages = "; ".join(_compact_text(message.content, limit=180) for message in recent_user_messages)
            parts.append(f"Recent user context: {messages}")

        return " | ".join(parts)[:3000]


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _compact_text(text: str, *, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."
