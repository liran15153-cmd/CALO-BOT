from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models import UsageEvent
from backend.app.services.ai_provider import AIRequest, AIResult


class UsageService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        user_id: int | None,
        task: str,
        provider: str,
        model: str | None,
        estimated_tokens_in: int = 0,
        estimated_tokens_out: int = 0,
        cost_estimate: float | None = None,
        usage_date: date | None = None,
    ) -> UsageEvent:
        event = UsageEvent(
            user_id=user_id,
            usage_date=usage_date or date.today(),
            task=task,
            provider=provider,
            model=model,
            estimated_tokens_in=estimated_tokens_in,
            estimated_tokens_out=estimated_tokens_out,
            cost_estimate=cost_estimate,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def record_ai_result(self, *, user_id: int | None, task: str, request: AIRequest, result: AIResult) -> UsageEvent:
        tokens_in = result.estimated_tokens_in
        if tokens_in == 0 and result.provider_status != "not_configured":
            tokens_in = rough_token_count(request.instructions + "\n" + request.input_text)
        return self.record(
            user_id=user_id,
            task=task,
            provider=result.provider_status,
            model=result.used_model,
            estimated_tokens_in=tokens_in,
            estimated_tokens_out=result.estimated_tokens_out,
        )

    def daily_totals(self, *, usage_date: date | None = None) -> dict[str, Any]:
        day = usage_date or date.today()
        events = self.db.scalars(select(UsageEvent).where(UsageEvent.usage_date == day)).all()
        estimated_tokens_in = sum(event.estimated_tokens_in or 0 for event in events)
        estimated_tokens_out = sum(event.estimated_tokens_out or 0 for event in events)
        estimated_tokens_total = estimated_tokens_in + estimated_tokens_out
        daily_ai_token_limit = get_settings().daily_ai_token_limit
        return {
            "usage_date": day,
            "chat_requests_count": sum(1 for event in events if event.task == "chat"),
            "image_analysis_count": sum(1 for event in events if event.task == "image_analysis"),
            "summary_requests_count": sum(1 for event in events if event.task == "summary"),
            "estimated_tokens_in": estimated_tokens_in,
            "estimated_tokens_out": estimated_tokens_out,
            "estimated_tokens_total": estimated_tokens_total,
            "daily_ai_token_limit": daily_ai_token_limit,
            "tokens_remaining": max(0, daily_ai_token_limit - estimated_tokens_total),
        }

    def is_daily_ai_token_budget_exceeded(self, *, usage_date: date | None = None) -> bool:
        daily_ai_token_limit = get_settings().daily_ai_token_limit
        if daily_ai_token_limit <= 0:
            return False
        totals = self.daily_totals(usage_date=usage_date)
        return totals["estimated_tokens_total"] >= daily_ai_token_limit


def rough_token_count(text: str) -> int:
    return max(1, len(text.split())) if text else 0
