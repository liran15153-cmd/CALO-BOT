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

        if "short workout" in normalized or "short workouts" in normalized:
            memories.append(("preference", "User prefers short workouts"))
        if "direct coaching" in normalized or "prefer direct" in normalized:
            memories.append(("preference", "User prefers direct coaching"))
        if "after work" in normalized:
            memories.append(("schedule", "User usually trains after work"))
        if "dumbbell" in normalized:
            memories.append(("equipment", "User has access to dumbbells"))
        if "resistance band" in normalized:
            memories.append(("equipment", "User has access to resistance bands"))
        if "hate running" in normalized or "dislike running" in normalized:
            memories.append(("preference", "User dislikes running"))
        if "knee pain" in normalized or "knee hurts" in normalized:
            memories.append(("safety_limitation", "User reported knee pain during training"))

        return memories

