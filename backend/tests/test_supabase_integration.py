import base64
import json
import time
from collections.abc import Callable, Generator
from pathlib import Path

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa, utils
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from backend.app import auth as auth_module
from backend.app.auth import verify_supabase_access_token
from backend.app.config import Settings
from backend.app.config import get_settings
from backend.app.db import get_db, init_db, make_engine
from backend.app.main import app


@pytest.fixture(autouse=True)
def clear_jwks_cache():
    auth_module._jwks_cache.clear()
    yield
    auth_module._jwks_cache.clear()


def test_supabase_auth_required_rejects_missing_bearer_token(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_AUTH_REQUIRED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-test-key")
    get_settings.cache_clear()
    client = make_client(tmp_path)

    response = client.get("/api/onboarding")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Supabase access token"


def test_supabase_access_token_is_verified_locally_with_jwks(monkeypatch):
    key = JwtKey("current")
    settings = supabase_settings()
    monkeypatch.setattr("backend.app.auth.httpx.get", jwks_response({"keys": [key.jwk()]}))

    user = verify_supabase_access_token(key.token(settings=settings, email="user@example.com"), settings=settings)

    assert user.auth_user_id
    assert user.email == "user@example.com"


def test_supabase_access_token_accepts_rs256_jwks(monkeypatch):
    key = RsaJwtKey("rsa-current")
    settings = supabase_settings()
    monkeypatch.setattr("backend.app.auth.httpx.get", jwks_response({"keys": [key.jwk()]}))

    user = verify_supabase_access_token(key.token(settings=settings), settings=settings)

    assert user.auth_user_id == "user-123"


def test_supabase_jwks_cache_refreshes_once_for_unknown_kid(monkeypatch):
    old_key = JwtKey("old")
    new_key = JwtKey("new")
    settings = supabase_settings()
    calls = []

    def fake_get(url: str, **_kwargs):
        calls.append(url)
        keys = [old_key.jwk()] if len(calls) == 1 else [old_key.jwk(), new_key.jwk()]
        return FakeResponse(200, {"keys": keys})

    monkeypatch.setattr("backend.app.auth.httpx.get", fake_get)

    verify_supabase_access_token(old_key.token(settings=settings), settings=settings)
    verify_supabase_access_token(new_key.token(settings=settings), settings=settings)

    assert calls == [settings.supabase_jwks_url, settings.supabase_jwks_url]


def test_supabase_url_cannot_be_used_as_jwks_url(monkeypatch):
    key = JwtKey("current")
    settings = supabase_settings(supabase_jwks_url="https://nexmxwvivewvgmrritqa.supabase.co")
    monkeypatch.setattr("backend.app.auth.httpx.get", jwks_response({"keys": [key.jwk()]}))

    with pytest_auth_error(503, "Supabase JWKS URL is invalid"):
        verify_supabase_access_token(key.token(settings=supabase_settings()), settings=settings)


def test_supabase_jwks_url_must_match_project_ref(monkeypatch):
    key = JwtKey("current")
    settings = supabase_settings(
        supabase_jwks_url="https://otherprojectref.supabase.co/auth/v1/.well-known/jwks.json"
    )
    monkeypatch.setattr("backend.app.auth.httpx.get", jwks_response({"keys": [key.jwk()]}))

    with pytest_auth_error(503, "Supabase JWKS URL does not match SUPABASE_URL"):
        verify_supabase_access_token(key.token(settings=supabase_settings()), settings=settings)


def test_supabase_project_url_cannot_be_auth_path(monkeypatch):
    key = JwtKey("current")
    settings = supabase_settings(supabase_url="https://nexmxwvivewvgmrritqa.supabase.co/auth/v1/.well-known/jwks.json")
    monkeypatch.setattr("backend.app.auth.httpx.get", jwks_response({"keys": [key.jwk()]}))

    with pytest_auth_error(503, "Supabase URL is invalid"):
        verify_supabase_access_token(key.token(settings=supabase_settings()), settings=settings)


def test_malformed_authorization_header_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPABASE_AUTH_REQUIRED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://nexmxwvivewvgmrritqa.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-test-key")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://nexmxwvivewvgmrritqa.supabase.co/auth/v1/.well-known/jwks.json")
    get_settings.cache_clear()
    client = make_client(tmp_path)

    response = client.get("/api/onboarding", headers={"Authorization": "Token abc"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing Supabase access token"


@pytest.mark.parametrize(
    ("name", "token_factory"),
    [
        ("expired token", lambda key, settings: key.token(settings=settings, exp=int(time.time()) - 1)),
        ("missing sub", lambda key, settings: key.token(settings=settings, sub=None)),
        ("wrong issuer", lambda key, settings: key.token(settings=settings, iss="https://wrong.supabase.co/auth/v1")),
        ("wrong audience", lambda key, settings: key.token(settings=settings, aud="anon")),
        ("wrong role", lambda key, settings: key.token(settings=settings, role="anon")),
        ("wrong alg", lambda key, settings: key.token(settings=settings, alg="RS256")),
        ("anon token", lambda key, settings: key.token(settings=settings, sub="", aud="anon", role="anon")),
        ("refresh token", lambda _key, _settings: "not.a.jwt"),
        ("signed by another key", lambda _key, settings: JwtKey("current").token(settings=settings)),
    ],
)
def test_invalid_supabase_tokens_are_rejected(name, token_factory, monkeypatch):
    key = JwtKey("current")
    settings = supabase_settings()
    monkeypatch.setattr("backend.app.auth.httpx.get", jwks_response({"keys": [key.jwk()]}))

    with pytest_auth_error(401, "Invalid Supabase access token"):
        verify_supabase_access_token(token_factory(key, settings), settings=settings)


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
    ):
        assert f"alter table public.{table} enable row level security;" in sql
    assert "to authenticated" in sql
    assert "(select auth.uid())" in sql
    assert "with check" in sql
    assert "storage.objects" in sql
    assert "meal-images" in sql
    assert "values ('meal-images', 'meal-images', false)" in sql
    assert "for insert to authenticated" in sql
    assert "for select to authenticated" in sql
    assert "for delete to authenticated" in sql
    assert "(storage.foldername(name))[1] = (select auth.uid())::text" in sql
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


def test_supabase_migrations_are_non_destructive():
    # The legacy-memory/summaries cleanup migration is intentionally destructive and is
    # excluded here; this guard protects the core schema migrations from accidental drops.
    migration_sql = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in Path("supabase/migrations").glob("*.sql")
        if "drop_legacy_memory_and_summaries" not in path.name
    )

    forbidden_fragments = (
        "drop table",
        "drop schema",
        "truncate ",
        "delete from",
        "alter table public.users drop",
        "alter table public.fitness_profiles drop",
        "alter table public.chat_sessions drop",
        "alter table public.chat_messages drop",
        "alter table public.workout_plans drop",
        "alter table public.workouts drop",
        "alter table public.workout_logs drop",
        "alter table public.meal_logs drop",
        "alter table public.body_metrics drop",
    )
    for forbidden in forbidden_fragments:
        assert forbidden not in migration_sql


def test_supabase_cleanup_migration_drops_legacy_memory_and_summary_tables():
    cleanup_sql = Path(
        "supabase/migrations/202606230001_drop_legacy_memory_and_summaries.sql"
    ).read_text(encoding="utf-8").lower()

    for table in ("coaching_memories", "memory_summaries", "weekly_summaries"):
        assert f"drop table if exists public.{table}" in cleanup_sql


def test_env_example_contains_only_supabase_placeholders():
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "SUPABASE_URL=" in env_example
    assert "SUPABASE_JWKS_URL=" in env_example
    assert "SUPABASE_PUBLISHABLE_KEY=" in env_example
    assert ("SUPABASE_SECRET_KEY" + "=") in env_example
    assert "sb_secret_" not in env_example
    assert "sb_publishable_" not in env_example


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class JwtKey:
    def __init__(self, kid: str):
        self.kid = kid
        self.private_key = ec.generate_private_key(ec.SECP256R1())

    def jwk(self) -> dict:
        public_numbers = self.private_key.public_key().public_numbers()
        return {
            "kty": "EC",
            "kid": self.kid,
            "use": "sig",
            "alg": "ES256",
            "crv": "P-256",
            "x": b64url_uint(public_numbers.x),
            "y": b64url_uint(public_numbers.y),
        }

    def token(
        self,
        *,
        settings: Settings,
        sub: str | None = "user-123",
        email: str | None = None,
        iss: str | None = None,
        aud: str | None = "authenticated",
        role: str | None = "authenticated",
        exp: int | None = None,
        alg: str = "ES256",
    ) -> str:
        payload = {
            "iss": iss or f"{settings.supabase_url}/auth/v1",
            "exp": exp or int(time.time()) + 600,
            "aud": aud,
            "role": role,
        }
        if sub is not None:
            payload["sub"] = sub
        if email:
            payload["email"] = email
        header = {"alg": alg, "kid": self.kid, "typ": "JWT"}
        signing_input = b".".join([b64url_json(header), b64url_json(payload)])
        signature = self.private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        r, s = utils.decode_dss_signature(signature)
        return (signing_input + b"." + b64url(r.to_bytes(32, "big") + s.to_bytes(32, "big"))).decode()


class RsaJwtKey:
    def __init__(self, kid: str):
        self.kid = kid
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def jwk(self) -> dict:
        public_numbers = self.private_key.public_key().public_numbers()
        return {
            "kty": "RSA",
            "kid": self.kid,
            "use": "sig",
            "alg": "RS256",
            "n": b64url_int(public_numbers.n),
            "e": b64url_int(public_numbers.e),
        }

    def token(self, *, settings: Settings) -> str:
        return pyjwt.encode(
            {
                "iss": f"{settings.supabase_url}/auth/v1",
                "exp": int(time.time()) + 600,
                "aud": "authenticated",
                "role": "authenticated",
                "sub": "user-123",
            },
            self.private_key,
            algorithm="RS256",
            headers={"kid": self.kid, "typ": "JWT"},
        )


def jwks_response(payload: dict) -> Callable:
    def fake_get(url: str, **_kwargs):
        assert url.endswith("/auth/v1/.well-known/jwks.json")
        return FakeResponse(200, payload)

    return fake_get


def supabase_settings(**overrides) -> Settings:
    values = {
        "supabase_url": "https://nexmxwvivewvgmrritqa.supabase.co",
        "supabase_publishable_key": "publishable-test-key",
        "supabase_jwks_url": "https://nexmxwvivewvgmrritqa.supabase.co/auth/v1/.well-known/jwks.json",
        "supabase_auth_required": True,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def pytest_auth_error(status_code: int, detail: str):
    return pytest.raises(HTTPException, match=detail, check=lambda exc: exc.status_code == status_code)


def b64url_json(value: dict) -> bytes:
    return b64url(json.dumps(value, separators=(",", ":")).encode())


def b64url_uint(value: int) -> str:
    return b64url(value.to_bytes(32, "big")).decode()


def b64url_int(value: int) -> str:
    return b64url(value.to_bytes((value.bit_length() + 7) // 8, "big")).decode()


def b64url(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


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
