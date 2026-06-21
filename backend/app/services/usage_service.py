from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models import UsageEvent
from backend.app.services.ai_provider import AIRequest, AIResult
from backend.app.services.token_budgeting import BREAKDOWN_COMPONENTS, build_token_breakdown, estimate_text_tokens


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
        token_breakdown: dict[str, Any] | None = None,
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
            token_breakdown_json=token_breakdown or {},
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
        tokens_out = result.estimated_tokens_out
        token_breakdown = result.token_breakdown or build_token_breakdown(
            request=request,
            output_text=result.text,
            input_total=tokens_in,
            output_total=tokens_out,
            component_token_counts=None,
            source="local_estimate",
        )
        return self.record(
            user_id=user_id,
            task=task,
            provider=result.provider_status,
            model=result.used_model,
            estimated_tokens_in=tokens_in,
            estimated_tokens_out=tokens_out,
            token_breakdown=token_breakdown,
        )

    def daily_totals(self, *, user_id: int | None = None, usage_date: date | None = None) -> dict[str, Any]:
        day = usage_date or date.today()
        statement = select(UsageEvent).where(UsageEvent.usage_date == day)
        if user_id is not None:
            statement = statement.where(UsageEvent.user_id == user_id)
        events = self.db.scalars(statement).all()
        estimated_tokens_in = sum(event.estimated_tokens_in or 0 for event in events)
        estimated_tokens_out = sum(event.estimated_tokens_out or 0 for event in events)
        estimated_tokens_total = estimated_tokens_in + estimated_tokens_out
        token_breakdown = _sum_token_breakdowns(events)
        daily_ai_token_limit = get_settings().daily_ai_token_limit
        return {
            "usage_date": day,
            "chat_requests_count": sum(1 for event in events if event.task == "chat"),
            "image_analysis_count": sum(1 for event in events if event.task == "image_analysis"),
            "summary_requests_count": sum(1 for event in events if event.task == "summary"),
            "estimated_tokens_in": estimated_tokens_in,
            "estimated_tokens_out": estimated_tokens_out,
            "estimated_tokens_total": estimated_tokens_total,
            "token_breakdown": token_breakdown,
            "daily_ai_token_limit": daily_ai_token_limit,
            "tokens_remaining": max(0, daily_ai_token_limit - estimated_tokens_total),
        }

    def is_daily_ai_token_budget_exceeded(self, *, user_id: int | None = None, usage_date: date | None = None) -> bool:
        daily_ai_token_limit = get_settings().daily_ai_token_limit
        if daily_ai_token_limit <= 0:
            return False
        # ponytail: budget gate stays global for v1; per-user limits need product rules and abuse handling.
        totals = self.daily_totals(usage_date=usage_date)
        return totals["estimated_tokens_total"] >= daily_ai_token_limit


def rough_token_count(text: str) -> int:
    return estimate_text_tokens(text)


def _sum_token_breakdowns(events: list[UsageEvent]) -> dict[str, int]:
    totals = {component: 0 for component in BREAKDOWN_COMPONENTS}
    totals["input_total"] = 0
    totals["total"] = 0
    for event in events:
        breakdown = event.token_breakdown_json or {}
        for key in totals:
            value = breakdown.get(key, 0)
            if isinstance(value, int):
                totals[key] += value
    if totals["input_total"] == 0:
        totals["input_total"] = sum(totals[component] for component in BREAKDOWN_COMPONENTS if component != "output")
    if totals["total"] == 0:
        totals["total"] = totals["input_total"] + totals["output"]
    return totals
