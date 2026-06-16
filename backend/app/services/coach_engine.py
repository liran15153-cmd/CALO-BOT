import json

from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.prompts import coach_chat_prompt
from backend.app.schemas import ChatRequest, ChatResponse
from backend.app.services.ai_provider import AIRequest, build_ai_provider
from backend.app.services.chat_service import ChatService
from backend.app.services.context_builder import ContextBuilder
from backend.app.services.memory_service import MemoryService
from backend.app.services.profile_service import ProfileService
from backend.app.services.safety_service import SafetyService
from backend.app.services.usage_service import UsageService


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

        context = ContextBuilder(self.db).build(user_id=user.id, session_id=session.id)
        provider = build_ai_provider(self.settings.anthropic_api_key, self.settings.anthropic_model)
        ai_request = AIRequest(
            instructions=coach_chat_prompt(),
            input_text=json.dumps({"context": context, "user_message": payload.message}, ensure_ascii=False),
            max_output_tokens=600,
        )
        ai_result = provider.chat(ai_request)
        UsageService(self.db).record_ai_result(user_id=user.id, task="chat", request=ai_request, result=ai_result)
        coach_message = chat_service.add_message(
            user_id=user.id,
            session_id=session.id,
            role="coach",
            content=ai_result.text,
            metadata={"provider_status": ai_result.provider_status, "model": ai_result.used_model},
        )

        return ChatResponse(
            session_id=session.id,
            user_message_id=user_message.id,
            coach_message_id=coach_message.id,
            response=ai_result.text,
            safety_flagged=False,
            provider_status=ai_result.provider_status,
        )
