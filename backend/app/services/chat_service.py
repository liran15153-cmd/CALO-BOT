from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from backend.app.models import ChatMessage, ChatSession


class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: int, title: str = "Coach chat") -> ChatSession:
        session = ChatSession(user_id=user_id, title=title, is_active=True)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_or_create_session(self, user_id: int, session_id: int | None = None) -> ChatSession:
        if session_id is not None:
            session = self.db.get(ChatSession, session_id)
            if session and session.user_id == user_id:
                return session
        active = self.db.scalar(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.is_active.is_(True))
            .order_by(ChatSession.created_at.desc())
        )
        if active:
            return active
        return self.create_session(user_id)

    def add_message(self, user_id: int, session_id: int, role: str, content: str, metadata: dict | None = None) -> ChatMessage:
        message = ChatMessage(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata_json=metadata or {},
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_messages(self, session_id: int) -> list[ChatMessage]:
        return list(
            self.db.scalars(
                select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(asc(ChatMessage.created_at), asc(ChatMessage.id))
            )
        )

    def reset_session(self, session_id: int) -> ChatSession:
        session = self.db.get(ChatSession, session_id)
        if session is None:
            raise ValueError("chat session not found")
        session.is_active = False
        self.db.commit()
        self.db.refresh(session)
        return session

