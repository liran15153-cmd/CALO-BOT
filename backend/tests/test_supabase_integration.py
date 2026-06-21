from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app


def test_supabase_auth_required_rejects_missing_bearer_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_AUTH_REQUIRED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-test-key")
    get_settings.cache_clear()
    client = make_client(tmp_path)

    response = client.get("/api/onboarding")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Supabase access token"


def test_supabase_migration_defines_user_owned_rls_policies():
    migration = Path("supabase/migrations/202606210001_calo_core_schema.sql")
    body_metric_migration = Path("supabase/migrations/202606210002_add_body_metric_details.sql")

    sql = migration.read_text(encoding="utf-8")
    body_metric_sql = body_metric_migration.read_text(encoding="utf-8")

    for table in (
        "fitness_profiles",
        "chat_sessions",
        "chat_messages",
        "workout_logs",
        "meal_logs",
        "body_metrics",
        "memory_summaries",
    ):
        assert f"alter table public.{table} enable row level security;" in sql
    assert "to authenticated" in sql
    assert "(select auth.uid())" in sql
    assert "with check" in sql
    assert "storage.objects" in sql
    assert "meal-images" in sql
    assert "add column if not exists body_fat_percent" in body_metric_sql
    assert "add column if not exists measurements_json" in body_metric_sql
    assert "add column if not exists source" in body_metric_sql


def test_supabase_manual_verification_sql_checks_schema_rls_and_storage():
    sql = Path("supabase/verify_schema_rls.sql").read_text(encoding="utf-8")

    assert "relrowsecurity" in sql
    assert "policy_count" in sql
    assert "body_metrics" in sql
    assert "body_fat_percent" in sql
    assert "storage.buckets" in sql


def test_env_example_contains_only_supabase_placeholders():
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "SUPABASE_URL=" in env_example
    assert "SUPABASE_PUBLISHABLE_KEY=" in env_example
    assert ("SUPABASE_SECRET_KEY" + "=") in env_example
    assert "sb_secret_" not in env_example
    assert "sb_publishable_" not in env_example


def make_client(tmp_path) -> TestClient:
    engine = make_engine(f"sqlite:///{tmp_path / 'supabase.db'}")
    init_db(engine)
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)
