from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app


def test_readiness_reports_local_dev_not_production_ready(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/app.db")
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "")
    monkeypatch.setenv("SUPABASE_AUTH_REQUIRED", "false")
    get_settings.cache_clear()
    client = TestClient(app)

    response = client.get("/api/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["production_ready"] is False
    assert body["checks"]["database"]["status"] == "local_sqlite"
    assert body["checks"]["supabase_auth"]["status"] == "not_configured"
    assert body["checks"]["storage"]["status"] == "local"
    assert body["issues"] == ["אימות Supabase לא נדרש"]
    assert "secret" not in str(body).lower()
    get_settings.cache_clear()


def test_readiness_rejects_auth_required_with_sqlite(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/app.db")
    monkeypatch.setenv("SUPABASE_URL", "https://nexmxwvivewvgmrritqa.supabase.co")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://nexmxwvivewvgmrritqa.supabase.co/auth/v1/.well-known/jwks.json")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-test-key")
    monkeypatch.setenv("SUPABASE_AUTH_REQUIRED", "true")
    get_settings.cache_clear()
    client = TestClient(app)

    response = client.get("/api/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["production_ready"] is False
    assert body["checks"]["database"]["status"] == "invalid"
    assert "אימות Supabase דורש DATABASE_URL שאינו SQLite" in body["issues"]
    get_settings.cache_clear()


def test_readiness_reports_ready_for_complete_supabase_config(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://db.example.com/app")
    monkeypatch.setenv("SUPABASE_URL", "https://nexmxwvivewvgmrritqa.supabase.co")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://nexmxwvivewvgmrritqa.supabase.co/auth/v1/.well-known/jwks.json")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-test-key")
    monkeypatch.setenv("SUPABASE_STORAGE_BUCKET", "meal-images")
    monkeypatch.setenv("SUPABASE_AUTH_REQUIRED", "true")
    get_settings.cache_clear()
    client = TestClient(app)

    response = client.get("/api/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["production_ready"] is True
    assert body["issues"] == []
    assert body["checks"]["database"]["status"] == "configured"
    assert body["checks"]["supabase_auth"]["status"] == "configured"
    assert body["checks"]["jwks"]["status"] == "configured"
    assert body["checks"]["storage"]["status"] == "configured"
    get_settings.cache_clear()


def test_readiness_does_not_expose_config_values(monkeypatch):
    database_url = "postgresql://app_user:" + "secret-db-pass" + "@db.example.com:5432/app"
    publishable_key = "sb_publishable_abcdefghijklmnopqrstuvwxyz1234567890"
    secret_key = "sb_" + "secret_" + "abcdefghijklmnopqrstuvwxyz1234567890"
    supabase_url = "https://nexmxwvivewvgmrritqa.supabase.co"
    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SUPABASE_URL", supabase_url)
    monkeypatch.setenv("SUPABASE_JWKS_URL", jwks_url)
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", publishable_key)
    monkeypatch.setenv("SUPABASE_SECRET_KEY", secret_key)
    monkeypatch.setenv("SUPABASE_AUTH_REQUIRED", "true")
    get_settings.cache_clear()
    client = TestClient(app)

    response = client.get("/api/readiness")

    assert response.status_code == 200
    body_text = str(response.json())
    assert database_url not in body_text
    assert publishable_key not in body_text
    assert secret_key not in body_text
    assert supabase_url not in body_text
    assert jwks_url not in body_text
    get_settings.cache_clear()
