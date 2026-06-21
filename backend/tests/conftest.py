import pytest

from backend.app.config import get_settings


@pytest.fixture(autouse=True)
def isolate_ai_provider_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    monkeypatch.delenv("ANTHROPIC_CHAT_MODEL", raising=False)
    monkeypatch.setenv("DAILY_AI_TOKEN_LIMIT", "50000")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
