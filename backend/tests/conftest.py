import pytest

from backend.app.config import get_settings


@pytest.fixture(autouse=True)
def isolate_ai_provider_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
