from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.schemas import ChatRequest, ChatResponse, ChatSessionCreate
from backend.app.services.chat_service import ChatService
from backend.app.services.coach_engine import CoachEngine
from backend.app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    return CoachEngine(db).respond(payload)


@router.post("/sessions")
def create_session(payload: ChatSessionCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    session = ChatService(db).create_session(user_id=user.id, title=payload.title)
    return {"id": session.id, "title": session.title, "is_active": session.is_active}


@router.post("/sessions/{session_id}/reset")
def reset_session(session_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = ProfileService(db).get_default_user()
    try:
        session = ChatService(db).reset_session(user_id=user.id, session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": session.id, "title": session.title, "is_active": session.is_active}


@router.get("/messages")
def list_messages(session_id: int, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    user = ProfileService(db).get_default_user()
    try:
        messages = ChatService(db).list_messages(user_id=user.id, session_id=session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "provider_status": (message.metadata_json or {}).get("provider_status"),
            "safety_flagged": bool((message.metadata_json or {}).get("safety")),
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
        for message in messages
    ]
