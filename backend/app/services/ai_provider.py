from dataclasses import dataclass
import base64
import mimetypes
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class AIRequest:
    instructions: str
    input_text: str
    max_output_tokens: int = 600


@dataclass(frozen=True)
class AIResult:
    text: str
    provider_status: str
    used_model: str | None
    estimated_tokens_in: int = 0
    estimated_tokens_out: int = 0


class AIProvider(Protocol):
    def chat(self, request: AIRequest) -> AIResult:
        ...

    def structured(self, request: AIRequest) -> AIResult:
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
        )
        return self._responses_text(structured_request)

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
        return AIResult(
            text=text,
            provider_status="configured",
            used_model=self.model,
            estimated_tokens_in=getattr(usage, "input_tokens", None) or _rough_token_count(note or ""),
            estimated_tokens_out=getattr(usage, "output_tokens", None) or _rough_token_count(text),
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
        return AIResult(
            text=text,
            provider_status="configured",
            used_model=self.model,
            estimated_tokens_in=getattr(usage, "input_tokens", None)
            or _rough_token_count(request.instructions + "\n" + request.input_text),
            estimated_tokens_out=getattr(usage, "output_tokens", None) or _rough_token_count(text),
        )

    def _call_messages_api(self, **kwargs: Any) -> Any | None:
        try:
            return self.client.messages.create(**kwargs)
        except Exception:
            return None

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


def _rough_token_count(text: str) -> int:
    return max(1, len(text.split())) if text else 0
