from dataclasses import dataclass, field
import base64
import mimetypes
from pathlib import Path
from typing import Any, Protocol

from backend.app.services.token_budgeting import build_token_breakdown, estimate_text_tokens


@dataclass(frozen=True)
class AIRequest:
    instructions: str
    input_text: str
    max_output_tokens: int = 600
    input_components: dict[str, str] = field(default_factory=dict)
    token_audit: dict[str, Any] = field(default_factory=dict)
    baseline_input_text: str | None = None


@dataclass(frozen=True)
class AIResult:
    text: str
    provider_status: str
    used_model: str | None
    estimated_tokens_in: int = 0
    estimated_tokens_out: int = 0
    token_breakdown: dict[str, Any] = field(default_factory=dict)
    structured_output: dict[str, Any] | None = None


class AIProvider(Protocol):
    def chat(self, request: AIRequest) -> AIResult:
        ...

    def structured(self, request: AIRequest) -> AIResult:
        ...

    def extract_tool(self, request: AIRequest, tool: dict[str, Any]) -> AIResult:
        ...

    def summarize(self, request: AIRequest) -> AIResult:
        ...

    def analyze_image(self, image_path: Path, note: str | None = None) -> AIResult:
        ...


class NoConfiguredAIProvider:
    provider_status = "not_configured"

    def chat(self, request: AIRequest) -> AIResult:
        return self._not_configured()

    def structured(self, request: AIRequest) -> AIResult:
        return self._not_configured()

    def extract_tool(self, request: AIRequest, tool: dict[str, Any]) -> AIResult:
        return self._not_configured()

    def summarize(self, request: AIRequest) -> AIResult:
        return self._not_configured()

    def analyze_image(self, image_path: Path, note: str | None = None) -> AIResult:
        return self._not_configured()

    @staticmethod
    def _not_configured() -> AIResult:
        return AIResult(
            text="ספק הבינה המלאכותית לא מוגדר. הגדר את ANTHROPIC_API_KEY כדי להפעיל תשובות מאמן דרך Claude.",
            provider_status="not_configured",
            used_model=None,
        )


class AnthropicProvider:
    provider_status = "configured"

    def __init__(self, api_key: str, model: str, client: Any | None = None):
        self.model = model
        if client is not None:
            self.client = client
        else:
            from anthropic import Anthropic

            self.client = Anthropic(api_key=api_key)

    def chat(self, request: AIRequest) -> AIResult:
        return self._responses_text(request)

    def structured(self, request: AIRequest) -> AIResult:
        structured_request = AIRequest(
            instructions=request.instructions,
            input_text=f"{request.input_text}\n\nהחזר JSON תקין בלבד.",
            max_output_tokens=request.max_output_tokens,
            input_components=request.input_components,
            token_audit=request.token_audit,
            baseline_input_text=request.baseline_input_text,
        )
        return self._responses_text(structured_request)

    def extract_tool(self, request: AIRequest, tool: dict[str, Any]) -> AIResult:
        """Call the model with a forced tool so it returns schema-validated structured
        output. Returns ``structured_output`` with the tool input, or ``provider_error``
        when the call fails or the model returns no matching ``tool_use`` block."""
        response = self._call_messages_api(
            model=self.model,
            system=request.instructions,
            messages=[{"role": "user", "content": request.input_text}],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            max_tokens=request.max_output_tokens,
        )
        if response is None:
            return self._provider_error()
        tool_input = _extract_anthropic_tool_use(response, tool["name"])
        if tool_input is None:
            return AIResult(text="", provider_status="provider_error", used_model=self.model)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None) or _rough_token_count(
            request.instructions + "\n" + request.input_text
        )
        output_tokens = getattr(usage, "output_tokens", None) or 0
        component_counts = self._count_request_components(request)
        count_source = "anthropic_usage+anthropic_count_tokens" if component_counts else "anthropic_usage+local_estimate"
        token_breakdown = build_token_breakdown(
            request=request,
            output_text="",
            input_total=input_tokens,
            output_total=output_tokens,
            component_token_counts=component_counts,
            source=count_source,
        )
        return AIResult(
            text="",
            provider_status="configured",
            used_model=self.model,
            estimated_tokens_in=input_tokens,
            estimated_tokens_out=output_tokens,
            token_breakdown=token_breakdown,
            structured_output=tool_input,
        )

    def summarize(self, request: AIRequest) -> AIResult:
        return self._responses_text(request)

    def analyze_image(self, image_path: Path, note: str | None = None) -> AIResult:
        mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
        encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
        response = self._call_messages_api(
            model=self.model,
            system="הערך תזונת ארוחה מתמונה. החזר JSON עם טווחים, אי-ודאות, וכל טקסט למשתמש בעברית בלבד.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": encoded_image,
                            },
                        },
                        {"type": "text", "text": f"הערת משתמש: {note or ''}"},
                    ],
                }
            ],
            max_tokens=700,
        )
        if response is None:
            return self._provider_error()
        text = _extract_anthropic_text(response)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None) or _rough_token_count(note or "")
        output_tokens = getattr(usage, "output_tokens", None) or _rough_token_count(text)
        return AIResult(
            text=text,
            provider_status="configured",
            used_model=self.model,
            estimated_tokens_in=input_tokens,
            estimated_tokens_out=output_tokens,
            token_breakdown={
                "message": input_tokens,
                "output": output_tokens,
                "input_total": input_tokens,
                "total": input_tokens + output_tokens,
                "source": "anthropic_usage_image",
            },
        )

    def _responses_text(self, request: AIRequest) -> AIResult:
        response = self._call_messages_api(
            model=self.model,
            system=request.instructions,
            messages=[{"role": "user", "content": request.input_text}],
            max_tokens=request.max_output_tokens,
        )
        if response is None:
            return self._provider_error()
        text = _extract_anthropic_text(response)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None) or _rough_token_count(
            request.instructions + "\n" + request.input_text
        )
        output_tokens = getattr(usage, "output_tokens", None) or _rough_token_count(text)
        component_counts = self._count_request_components(request)
        count_source = "anthropic_usage+anthropic_count_tokens" if component_counts else "anthropic_usage+local_estimate"
        token_breakdown = build_token_breakdown(
            request=request,
            output_text=text,
            input_total=input_tokens,
            output_total=output_tokens,
            component_token_counts=component_counts,
            source=count_source,
        )
        baseline_count = self._count_text_tokens(request.baseline_input_text)
        if baseline_count:
            audit = token_breakdown.setdefault("audit", {})
            audit["baseline_input_tokens_provider"] = baseline_count
            audit["optimized_input_tokens_provider"] = input_tokens
            audit["input_reduction_ratio_provider"] = round(1 - (input_tokens / baseline_count), 4)
        return AIResult(
            text=text,
            provider_status="configured",
            used_model=self.model,
            estimated_tokens_in=input_tokens,
            estimated_tokens_out=output_tokens,
            token_breakdown=token_breakdown,
        )

    def _call_messages_api(self, **kwargs: Any) -> Any | None:
        try:
            return self.client.messages.create(**kwargs)
        except Exception:
            return None

    def _count_request_components(self, request: AIRequest) -> dict[str, int] | None:
        components = {"system_prompt": request.instructions, **request.input_components}
        counts: dict[str, int] = {}
        try:
            for name, text in components.items():
                if not text:
                    counts[name] = 0
                    continue
                count = self._count_text_tokens(text)
                if count is None:
                    return None
                counts[name] = count
        except Exception:
            return None
        return counts

    def _count_text_tokens(self, text: str | None) -> int | None:
        if not text:
            return None
        counter = getattr(getattr(self.client, "messages", None), "count_tokens", None)
        if counter is None:
            return None
        result = counter(model=self.model, messages=[{"role": "user", "content": text}])
        return int(getattr(result, "input_tokens", 0) or 0)

    def _provider_error(self) -> AIResult:
        return AIResult(
            text="בקשת הבינה המלאכותית נכשלה. בדוק את פרטי Anthropic, הרשאת המודל או מבנה הבקשה.",
            provider_status="provider_error",
            used_model=self.model,
        )


def build_ai_provider(api_key: str | None, model: str) -> AIProvider:
    if not api_key:
        return NoConfiguredAIProvider()
    return AnthropicProvider(api_key=api_key, model=model)


def _extract_anthropic_text(response: Any) -> str:
    content = getattr(response, "content", None) or []
    text_parts = [getattr(block, "text", "") for block in content if getattr(block, "type", None) == "text"]
    return "\n".join(part for part in text_parts if part)


def _extract_anthropic_tool_use(response: Any, tool_name: str) -> dict[str, Any] | None:
    content = getattr(response, "content", None) or []
    for block in content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool_name:
            tool_input = getattr(block, "input", None)
            if isinstance(tool_input, dict):
                return tool_input
    return None


def _rough_token_count(text: str) -> int:
    return estimate_text_tokens(text)
