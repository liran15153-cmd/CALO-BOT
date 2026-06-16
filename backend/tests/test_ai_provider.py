from backend.app.services.ai_provider import AIRequest, AnthropicProvider, NoConfiguredAIProvider, build_ai_provider


def test_no_configured_provider_does_not_fake_ai_response():
    provider = NoConfiguredAIProvider()

    result = provider.chat(AIRequest(instructions="coach", input_text="Build a plan"))

    assert result.provider_status == "not_configured"
    assert result.text == "AI provider is not configured. Set ANTHROPIC_API_KEY to enable Claude coach responses."
    assert result.used_model is None


def test_build_ai_provider_uses_no_configured_provider_without_key():
    provider = build_ai_provider(api_key=None, model="claude-haiku-4-5")

    assert isinstance(provider, NoConfiguredAIProvider)


def test_anthropic_provider_calls_messages_api_with_model_and_input():
    fake_client = FakeAnthropicClient()
    provider = AnthropicProvider(api_key="redacted", model="claude-haiku-4-5", client=fake_client)

    result = provider.chat(AIRequest(instructions="coach instructions", input_text="hello"))

    assert result.text == "coach output"
    assert result.provider_status == "configured"
    assert fake_client.messages.calls[0]["model"] == "claude-haiku-4-5"
    assert fake_client.messages.calls[0]["system"] == "coach instructions"
    assert fake_client.messages.calls[0]["messages"] == [{"role": "user", "content": "hello"}]
    assert fake_client.messages.calls[0]["max_tokens"] == 600
    assert result.estimated_tokens_in == 7
    assert result.estimated_tokens_out == 3


class FakeUsage:
    input_tokens = 7
    output_tokens = 3


class FakeTextBlock:
    type = "text"
    text = "coach output"


class FakeResponse:
    content = [FakeTextBlock()]
    usage = FakeUsage()


class FakeMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse()


class FakeAnthropicClient:
    def __init__(self):
        self.messages = FakeMessages()
