from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any


INPUT_COMPONENTS = ("system_prompt", "history", "memory", "tools", "message")
BREAKDOWN_COMPONENTS = (*INPUT_COMPONENTS, "output")
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9\u0590-\u05FF]+|[^\sA-Za-z0-9\u0590-\u05FF]")
_PROFILE_KEYS = {"goal": "main_goal", "level": "experience_level", "location": "training_location", "equipment": "available_equipment", "days_per_week": "weekly_availability", "minutes": "session_length_minutes", "limitations": "limitations", "nutrition": "nutrition_preference", "style": "coaching_style"}
_PLAN_KEYS = {"name": "name", "goal": "goal", "type": "plan_type", "weeks": "duration_weeks", "days_per_week": "days_per_week", "split": "training_split", "minutes": "session_length_minutes", "equipment": "equipment_needed"}
_PLAN_TRIMS = {"progression": ("progression_rule", 140), "recovery": ("recovery_note", 140)}
_WORKOUT_KEYS = {"date": "date", "status": "status", "pain": "pain_flag"}
_WORKOUT_TRIMS = {"notes": ("notes", 90)}
_MEAL_KEYS = {"date": "date", "calories": "calories_range", "confidence": "confidence"}
_MEAL_TRIMS = {"note": ("note", 90)}
_KNOWLEDGE_LIMITS = {"rules": (3, 160), "safety_boundaries": (2, 180), "trainer_skill_domains": (3, 90), "programming_model": (2, 130), "progression_regression": (2, 140), "program_design_summary": (2, 140), "technique_cues_summary": (2, 120), "deload_rules": (1, 160), "intent_focus": (2, 150), "practical_nutrition_summary": (3, 130), "sports_nutrition_summary": (2, 150), "body_composition_summary": (1, 150), "sources": (5, 60)}
_RETRIEVED_LIMITS = {"summary": (2, 150), "recommendations": (2, 150), "safety": (1, 150), "sources": (3, 80)}


def build_legacy_chat_request(*, context: dict[str, Any], user_message: str, max_output_tokens: int = 320):
    from backend.app.prompts import coach_chat_prompt
    from backend.app.services.ai_provider import AIRequest

    return AIRequest(
        instructions=coach_chat_prompt(),
        input_text=json.dumps({"context": context, "user_message": user_message}, ensure_ascii=False),
        max_output_tokens=max_output_tokens,
        input_components=_chat_input_components(context=context, user_message=user_message),
        token_audit={"variant": "legacy_full_context"},
    )


def build_optimized_chat_request(*, context: dict[str, Any], user_message: str, max_output_tokens: int = 320):
    from backend.app.prompts import coach_chat_prompt
    from backend.app.services.ai_provider import AIRequest

    legacy_request = build_legacy_chat_request(
        context=context,
        user_message=user_message,
        max_output_tokens=max_output_tokens,
    )
    compact_context = compact_provider_context(context=context, user_message=user_message)
    payload = {"context": compact_context, "user_message": user_message}
    optimized_request = AIRequest(
        instructions=coach_chat_prompt(),
        input_text=compact_json(payload),
        max_output_tokens=max_output_tokens,
        input_components=_chat_input_components(context=compact_context, user_message=user_message),
        token_audit={"variant": "optimized_compact_context"},
        baseline_input_text=f"{legacy_request.instructions}\n{legacy_request.input_text}",
    )
    legacy_tokens = estimate_request_input_tokens(legacy_request)
    optimized_tokens = estimate_request_input_tokens(optimized_request)
    reduction_ratio = 0.0 if legacy_tokens <= 0 else 1 - (optimized_tokens / legacy_tokens)
    optimized_request.token_audit.update(
        {
            "baseline_input_tokens": legacy_tokens,
            "optimized_input_tokens": optimized_tokens,
            "input_reduction_ratio": round(reduction_ratio, 4),
            "largest_component_before": largest_input_component(legacy_request),
            "largest_component_after": largest_input_component(optimized_request),
        }
    )
    return optimized_request


def compact_provider_context(*, context: dict[str, Any], user_message: str) -> dict[str, Any]:
    compact = {
        "profile": _pick(context.get("profile") or {}, _PROFILE_KEYS),
        "current_workout_plan": _pick(context.get("current_workout_plan") or {}, _PLAN_KEYS, _PLAN_TRIMS),
        "recent_workouts": _records(context.get("recent_workouts") or [], _WORKOUT_KEYS, _WORKOUT_TRIMS),
        "training_status": _drop_empty(context.get("training_status") or {}),
        "recent_meals": _records(context.get("recent_meals") or [], _MEAL_KEYS, _MEAL_TRIMS),
        "memories": _compact_text_list(context.get("memories") or [], limit=4, max_chars=120),
        "caution_notes": _compact_text_list(context.get("caution_notes") or [], limit=3, max_chars=140),
        "recent_chat": _compact_recent_chat(context.get("recent_chat") or [], user_message=user_message),
        "coaching_knowledge": _compact_coaching_knowledge(context.get("coaching_knowledge") or {}),
    }
    return _drop_empty(compact)


def estimate_request_input_tokens(request: Any) -> int:
    return estimate_text_tokens((getattr(request, "instructions", "") or "") + "\n" + (getattr(request, "input_text", "") or ""))


def estimate_text_tokens(text: str | None) -> int:
    if not text:
        return 0
    normalized = str(text)
    token_like_count = len(_TOKEN_PATTERN.findall(normalized))
    char_estimate = len(normalized) // 4
    return max(1, token_like_count, char_estimate)


def build_token_breakdown(
    *,
    request: Any,
    output_text: str,
    input_total: int,
    output_total: int,
    component_token_counts: Mapping[str, int] | None = None,
    source: str,
) -> dict[str, Any]:
    input_counts = _input_component_counts(request=request, component_token_counts=component_token_counts)
    scaled_input_counts = _scale_counts_to_total(input_counts, input_total)
    breakdown: dict[str, Any] = {component: scaled_input_counts.get(component, 0) for component in INPUT_COMPONENTS}
    breakdown["output"] = output_total or estimate_text_tokens(output_text)
    breakdown["input_total"] = sum(breakdown[component] for component in INPUT_COMPONENTS)
    breakdown["total"] = breakdown["input_total"] + breakdown["output"]
    breakdown["source"] = source
    token_audit = getattr(request, "token_audit", None) or {}
    if token_audit:
        breakdown["audit"] = dict(token_audit)
    return breakdown


def largest_input_component(request: Any) -> str | None:
    counts = _input_component_counts(request=request, component_token_counts=None)
    if not counts:
        return None
    return max(counts, key=counts.get)


def compact_json(value: Any) -> str:
    return json.dumps(_drop_empty(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _chat_input_components(*, context: dict[str, Any], user_message: str) -> dict[str, str]:
    memory_context = {
        key: value
        for key, value in context.items()
        if key not in {"recent_chat", "coaching_knowledge"}
    }
    return {
        "message": user_message,
        "history": compact_json(context.get("recent_chat") or []),
        "memory": compact_json(memory_context),
        "tools": compact_json({"coaching_knowledge": context.get("coaching_knowledge") or {}}),
    }


def _input_component_counts(
    *,
    request: Any,
    component_token_counts: Mapping[str, int] | None,
) -> dict[str, int]:
    if component_token_counts:
        counts = {component: int(component_token_counts.get(component, 0) or 0) for component in INPUT_COMPONENTS}
    else:
        counts = {
            "system_prompt": estimate_text_tokens(getattr(request, "instructions", "")),
        }
        input_components = getattr(request, "input_components", None) or {}
        if input_components:
            for component in INPUT_COMPONENTS:
                if component == "system_prompt":
                    continue
                counts[component] = estimate_text_tokens(input_components.get(component, ""))
        else:
            counts["message"] = estimate_text_tokens(getattr(request, "input_text", ""))
    return {component: max(0, counts.get(component, 0)) for component in INPUT_COMPONENTS}


def _scale_counts_to_total(counts: dict[str, int], target_total: int) -> dict[str, int]:
    if target_total <= 0:
        return {component: 0 for component in INPUT_COMPONENTS}
    raw_total = sum(counts.values())
    if raw_total <= 0:
        return {component: 0 for component in INPUT_COMPONENTS}
    positive_components = [component for component, value in counts.items() if value > 0]
    scaled = {component: 0 for component in INPUT_COMPONENTS}
    if target_total >= len(positive_components):
        for component in positive_components:
            scaled[component] = 1
        remaining_total = target_total - len(positive_components)
    else:
        for component in sorted(positive_components, key=counts.get, reverse=True)[:target_total]:
            scaled[component] = 1
        return scaled

    if remaining_total > 0:
        for component, value in counts.items():
            if value <= 0:
                continue
            scaled[component] += int((value / raw_total) * remaining_total)

    remainder = target_total - sum(scaled.values())
    for component in sorted(counts, key=counts.get, reverse=True):
        if remainder <= 0:
            break
        scaled[component] += 1
        remainder -= 1
    return scaled


def _compact_recent_chat(messages: list[dict[str, Any]], *, user_message: str) -> list[dict[str, str]]:
    filtered = [
        message
        for message in messages
        if not (message.get("role") == "user" and str(message.get("content") or "") == user_message)
    ]
    return [
        {
            "role": "u" if message.get("role") == "user" else "c",
            "text": _trim(message.get("content"), max_chars=120),
        }
        for message in filtered[-2:]
        if message.get("content")
    ]


def _compact_coaching_knowledge(knowledge: dict[str, Any]) -> dict[str, Any]:
    compact = {"scope": knowledge.get("scope")}
    for key, (limit, max_chars) in _KNOWLEDGE_LIMITS.items():
        compact[key] = _compact_text_list(knowledge.get(key) or [], limit=limit, max_chars=max_chars)
    compact["retrieved_knowledge"] = _compact_retrieved_knowledge(knowledge.get("retrieved_knowledge") or [])
    return _drop_empty(compact)


def _compact_retrieved_knowledge(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact_items = []
    for item in items[:2]:
        compact = {"topic": item.get("topic")}
        for key, (limit, max_chars) in _RETRIEVED_LIMITS.items():
            compact[key] = _compact_text_list(item.get(key) or [], limit=limit, max_chars=max_chars)
        compact_items.append(_drop_empty(compact))
    return compact_items


def _pick(source: dict[str, Any], keys: dict[str, str], trims: dict[str, tuple[str, int]] | None = None) -> dict[str, Any]:
    compact = {output_key: source.get(source_key) for output_key, source_key in keys.items()}
    for output_key, (source_key, max_chars) in (trims or {}).items():
        compact[output_key] = _trim(source.get(source_key), max_chars=max_chars)
    return _drop_empty(compact)


def _records(
    records: list[dict[str, Any]],
    keys: dict[str, str],
    trims: dict[str, tuple[str, int]] | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    return [_pick(record, keys, trims) for record in records[:limit]]


def _compact_text_list(values: Any, *, limit: int, max_chars: int) -> list[str]:
    if isinstance(values, str):
        source_values = [values]
    elif isinstance(values, (list, tuple)):
        source_values = list(values)
    else:
        source_values = []
    result = []
    for value in source_values:
        text = _trim(value, max_chars=max_chars)
        if text:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _trim(value: Any, *, max_chars: int) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def _drop_empty(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: cleaned
            for key, nested in value.items()
            if (cleaned := _drop_empty(nested)) not in (None, "", [], {})
        }
    if isinstance(value, list):
        return [cleaned for item in value if (cleaned := _drop_empty(item)) not in (None, "", [], {})]
    return value
