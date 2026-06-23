from backend.app.services.ai_provider import AIRequest, AnthropicProvider, NoConfiguredAIProvider, build_ai_provider


def test_no_configured_provider_does_not_fake_ai_response():
    provider = NoConfiguredAIProvider()

    result = provider.chat(AIRequest(instructions="coach", input_text="Build a plan"))

    assert result.provider_status == "not_configured"
    assert "ספק הבינה המלאכותית לא מוגדר" in result.text
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


def test_anthropic_provider_reports_provider_error_when_request_fails():
    provider = AnthropicProvider(api_key="redacted", model="claude-haiku-4-5", client=FailingAnthropicClient())

    result = provider.chat(AIRequest(instructions="coach", input_text="hello"))

    assert result.provider_status == "provider_error"
    assert result.used_model == "claude-haiku-4-5"
    assert "בקשת הבינה המלאכותית נכשלה" in result.text


def test_anthropic_provider_counts_component_and_legacy_baseline_tokens():
    fake_client = CountingAnthropicClient()
    provider = AnthropicProvider(api_key="redacted", model="claude-haiku-4-5", client=fake_client)

    result = provider.chat(
        AIRequest(
            instructions="coach system",
            input_text='{"context":{"profile":"compact"},"user_message":"hello"}',
            input_components={
                "message": "hello",
                "history": "previous turn",
                "memory": "compact profile",
                "tools": "compact knowledge",
            },
            token_audit={"baseline_input_tokens": 200, "optimized_input_tokens": 80},
            baseline_input_text="legacy full context payload",
        )
    )

    assert result.token_breakdown["source"] == "anthropic_usage+anthropic_count_tokens"
    assert result.token_breakdown["system_prompt"] > 0
    assert result.token_breakdown["message"] > 0
    assert result.token_breakdown["audit"]["baseline_input_tokens_provider"] == 240
    assert result.token_breakdown["audit"]["input_reduction_ratio_provider"] == 0.5833


SAMPLE_TOOL = {
    "name": "save_facts",
    "description": "Save extracted coaching facts.",
    "input_schema": {
        "type": "object",
        "properties": {"facts": {"type": "array"}},
        "required": ["facts"],
    },
}


def test_extract_tool_returns_structured_output_and_passes_tool_schema():
    fake_client = FakeToolClient()
    provider = AnthropicProvider(api_key="redacted", model="claude-haiku-4-5", client=fake_client)

    result = provider.extract_tool(AIRequest(instructions="extract facts", input_text="יש לי קטלבל"), SAMPLE_TOOL)

    assert result.provider_status == "configured"
    assert result.structured_output == {"facts": [{"type": "equipment", "text_he": "יש קטלבל"}]}
    call = fake_client.messages.calls[0]
    assert call["tools"] == [SAMPLE_TOOL]
    assert call["tool_choice"] == {"type": "tool", "name": "save_facts"}
    assert result.estimated_tokens_in == 7
    assert result.estimated_tokens_out == 3


def test_no_configured_provider_extract_tool_is_not_configured():
    result = NoConfiguredAIProvider().extract_tool(AIRequest(instructions="x", input_text="y"), SAMPLE_TOOL)

    assert result.provider_status == "not_configured"
    assert result.structured_output is None


def test_extract_tool_reports_provider_error_when_request_fails():
    provider = AnthropicProvider(api_key="redacted", model="claude-haiku-4-5", client=FailingAnthropicClient())

    result = provider.extract_tool(AIRequest(instructions="x", input_text="y"), SAMPLE_TOOL)

    assert result.provider_status == "provider_error"
    assert result.structured_output is None


def test_extract_tool_reports_provider_error_when_no_tool_use_block():
    # FakeAnthropicClient returns a text-only response, i.e. the model ignored the tool.
    provider = AnthropicProvider(api_key="redacted", model="claude-haiku-4-5", client=FakeAnthropicClient())

    result = provider.extract_tool(AIRequest(instructions="x", input_text="y"), SAMPLE_TOOL)

    assert result.provider_status == "provider_error"
    assert result.structured_output is None


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


class FakeTokenCount:
    def __init__(self, input_tokens):
        self.input_tokens = input_tokens


class CountingUsage:
    input_tokens = 100
    output_tokens = 10


class CountingResponse(FakeResponse):
    usage = CountingUsage()


class CountingMessages(FakeMessages):
    def create(self, **kwargs):
        self.calls.append(kwargs)
        return CountingResponse()

    def count_tokens(self, **kwargs):
        content = kwargs["messages"][0]["content"]
        if content == "legacy full context payload":
            return FakeTokenCount(240)
        return FakeTokenCount(max(1, len(str(content).split()) * 3))


class CountingAnthropicClient:
    def __init__(self):
        self.messages = CountingMessages()


class FailingMessages:
    def create(self, **_kwargs):
        raise RuntimeError("boom")


class FailingAnthropicClient:
    def __init__(self):
        self.messages = FailingMessages()


class FakeToolUseBlock:
    type = "tool_use"
    name = "save_facts"
    input = {"facts": [{"type": "equipment", "text_he": "יש קטלבל"}]}


class FakeToolResponse:
    content = [FakeToolUseBlock()]
    usage = FakeUsage()


class FakeToolMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeToolResponse()


class FakeToolClient:
    def __init__(self):
        self.messages = FakeToolMessages()
