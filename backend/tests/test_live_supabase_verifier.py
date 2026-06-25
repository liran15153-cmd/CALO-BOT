import httpx

import scripts.verify_supabase_live as verifier
from scripts.verify_supabase_live import env_with_dotenv_files, missing_live_verification_env, run_live_verification


def test_live_verifier_reports_missing_credentials_without_faking_success():
    missing = missing_live_verification_env({})

    assert missing == [
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_TEST_USER_A_EMAIL",
        "SUPABASE_TEST_USER_A_PASSWORD",
        "SUPABASE_TEST_USER_B_EMAIL",
        "SUPABASE_TEST_USER_B_PASSWORD",
    ]


def test_live_verifier_accepts_minimum_credentials_for_http_rls_and_storage_checks():
    env = {
        "SUPABASE_URL": "https://nexmxwvivewvgmrritqa.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_abcdefghijklmnopqrstuvwxyz1234567890",
        "SUPABASE_TEST_USER_A_EMAIL": "a@example.com",
        "SUPABASE_TEST_USER_A_PASSWORD": "password-a",
        "SUPABASE_TEST_USER_B_EMAIL": "b@example.com",
        "SUPABASE_TEST_USER_B_PASSWORD": "password-b",
    }

    assert missing_live_verification_env(env) == []


def test_live_verifier_loads_dotenv_files_without_overriding_process_env(tmp_path):
    (tmp_path / ".env").write_text(
        "SUPABASE_URL=https://from-env.example\nSUPABASE_PUBLISHABLE_KEY=from-env\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.local").write_text(
        "SUPABASE_PUBLISHABLE_KEY=from-local\nSUPABASE_TEST_USER_A_EMAIL=a@example.com\n",
        encoding="utf-8",
    )

    env = env_with_dotenv_files({"SUPABASE_URL": "https://from-process.example"}, root=tmp_path)

    assert env["SUPABASE_URL"] == "https://from-process.example"
    assert env["SUPABASE_PUBLISHABLE_KEY"] == "from-local"
    assert env["SUPABASE_TEST_USER_A_EMAIL"] == "a@example.com"


def test_live_verifier_does_not_overwrite_or_delete_existing_user_row(monkeypatch):
    env = live_env()
    deleted_user_rows = []
    deleted_storage_objects = []

    def fake_sign_in(_base_url, _publishable_key, email, _password):
        if email == "a@example.com":
            return {"access_token": "token-a", "user_id": "auth-user-a", "email": email}
        return {"access_token": "token-b", "user_id": "auth-user-b", "email": email}

    def fake_select(_base_url, _publishable_key, access_token, auth_user_id):
        if access_token == "token-a":
            return [{"id": 42, "auth_user_id": auth_user_id, "name": "Existing user"}]
        return []

    def fail_insert(*_args, **_kwargs):
        raise AssertionError("verifier must not insert/upsert when the test user row already exists")

    monkeypatch.setattr("scripts.verify_supabase_live._sign_in", fake_sign_in)
    monkeypatch.setattr("scripts.verify_supabase_live._select_user_rows", fake_select)
    monkeypatch.setattr("scripts.verify_supabase_live._insert_public_user", fail_insert, raising=False)
    monkeypatch.setattr("scripts.verify_supabase_live._upsert_public_user", fail_insert, raising=False)
    monkeypatch.setattr(
        "scripts.verify_supabase_live._delete_public_user",
        lambda *_args, **_kwargs: deleted_user_rows.append(_args),
    )
    monkeypatch.setattr("scripts.verify_supabase_live._upload_storage_object", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "scripts.verify_supabase_live._get_storage_object_status",
        lambda _base_url, _publishable_key, _bucket, access_token, _object_path: 200
        if access_token == "token-a"
        else 404,
    )
    monkeypatch.setattr("scripts.verify_supabase_live._delete_storage_object_status", lambda *_args, **_kwargs: 404)
    monkeypatch.setattr(
        "scripts.verify_supabase_live._delete_storage_object",
        lambda *_args, **_kwargs: deleted_storage_objects.append(_args),
    )

    result = run_live_verification(env)

    assert result["status"] == "passed"
    assert result["rls_mutation_checks"] == "skipped_existing_user_row"
    assert deleted_user_rows == []
    assert len(deleted_storage_objects) == 1


def test_live_verifier_checks_mutations_and_cleans_created_user_row(monkeypatch):
    env = live_env()
    delete_user_tokens = []
    storage_delete_tokens = []

    def fake_sign_in(_base_url, _publishable_key, email, _password):
        if email == "a@example.com":
            return {"access_token": "token-a", "user_id": "auth-user-a", "email": email}
        return {"access_token": "token-b", "user_id": "auth-user-b", "email": email}

    def fake_select(_base_url, _publishable_key, access_token, auth_user_id):
        if access_token == "token-b":
            return []
        if not fake_select.user_a_calls:
            fake_select.user_a_calls += 1
            return []
        fake_select.user_a_calls += 1
        return [{"id": 77, "auth_user_id": auth_user_id, "name": "CALO Supabase verifier"}]

    fake_select.user_a_calls = 0

    monkeypatch.setattr("scripts.verify_supabase_live._sign_in", fake_sign_in)
    monkeypatch.setattr("scripts.verify_supabase_live._select_user_rows", fake_select)
    monkeypatch.setattr("scripts.verify_supabase_live._insert_public_user", lambda *_args, **_kwargs: 77)
    monkeypatch.setattr("scripts.verify_supabase_live._update_public_user_name", lambda *_args, **_kwargs: 204)
    monkeypatch.setattr(
        "scripts.verify_supabase_live._delete_public_user_status",
        lambda _base_url, _publishable_key, access_token, _auth_user_id: delete_user_tokens.append(access_token) or 204,
    )
    monkeypatch.setattr("scripts.verify_supabase_live._upload_storage_object", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "scripts.verify_supabase_live._get_storage_object_status",
        lambda _base_url, _publishable_key, _bucket, access_token, _object_path: 200
        if access_token == "token-a"
        else 404,
    )
    monkeypatch.setattr(
        "scripts.verify_supabase_live._delete_storage_object_status",
        lambda _base_url, _publishable_key, _bucket, access_token, _object_path: storage_delete_tokens.append(access_token)
        or 404,
    )

    result = run_live_verification(env)

    assert result["status"] == "passed"
    assert result["created_user_row"] is True
    assert result["rls_mutation_checks"] == "passed"
    assert delete_user_tokens == ["token-b", "token-a"]
    assert storage_delete_tokens == ["token-b", "token-a"]


def test_live_verifier_bootstraps_auth_test_users_when_service_key_is_present(monkeypatch):
    env = {**live_env(), "SUPABASE_SECRET_KEY": "service-role-test-key"}
    bootstrapped = []

    def fake_bootstrap(_base_url, _secret_key, email, password):
        bootstrapped.append((email, password))

    def fake_sign_in(_base_url, _publishable_key, email, _password):
        if email == "a@example.com":
            return {"access_token": "token-a", "user_id": "auth-user-a", "email": email}
        return {"access_token": "token-b", "user_id": "auth-user-b", "email": email}

    def fake_select(_base_url, _publishable_key, access_token, auth_user_id):
        if access_token == "token-a":
            return [{"id": 42, "auth_user_id": auth_user_id, "name": "Existing user"}]
        return []

    monkeypatch.setattr("scripts.verify_supabase_live._ensure_auth_user", fake_bootstrap, raising=False)
    monkeypatch.setattr("scripts.verify_supabase_live._sign_in", fake_sign_in)
    monkeypatch.setattr("scripts.verify_supabase_live._select_user_rows", fake_select)
    monkeypatch.setattr("scripts.verify_supabase_live._upload_storage_object", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "scripts.verify_supabase_live._get_storage_object_status",
        lambda _base_url, _publishable_key, _bucket, access_token, _object_path: 200
        if access_token == "token-a"
        else 404,
    )
    monkeypatch.setattr("scripts.verify_supabase_live._delete_storage_object_status", lambda *_args, **_kwargs: 404)
    monkeypatch.setattr("scripts.verify_supabase_live._delete_storage_object", lambda *_args, **_kwargs: None)

    result = run_live_verification(env)

    assert result["status"] == "passed"
    assert bootstrapped == [
        ("a@example.com", "password-a"),
        ("b@example.com", "password-b"),
    ]


def test_live_verifier_sign_in_failure_without_service_key_explains_repair_path(monkeypatch):
    env = live_env()

    def fake_sign_in(*_args, **_kwargs):
        raise RuntimeError("Supabase Auth sign-in failed: 400 invalid_credentials")

    monkeypatch.setattr("scripts.verify_supabase_live._sign_in", fake_sign_in)

    try:
        run_live_verification(env)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("run_live_verification must fail on invalid Supabase Auth credentials")

    assert "SUPABASE_SECRET_KEY" in message
    assert "SUPABASE_TEST_USER" in message


def test_ensure_auth_user_creates_confirmed_user_when_missing(monkeypatch):
    calls = []

    def fake_get(url, headers, timeout):
        calls.append(("GET", url, headers, None, timeout))
        return httpx.Response(200, json={"users": []})

    def fake_post(url, headers, json, timeout):
        calls.append(("POST", url, headers, json, timeout))
        return httpx.Response(200, json={"user": {"id": "new-auth-user"}})

    monkeypatch.setattr(verifier.httpx, "get", fake_get)
    monkeypatch.setattr(verifier.httpx, "post", fake_post)

    verifier._ensure_auth_user("https://example.supabase.co", "service-role", "a@example.com", "password-a")

    assert calls[0][0] == "GET"
    assert calls[0][2]["Authorization"] == "Bearer service-role"
    assert calls[1] == (
        "POST",
        "https://example.supabase.co/auth/v1/admin/users",
        {
            "apikey": "service-role",
            "Authorization": "Bearer service-role",
            "Content-Type": "application/json",
        },
        {"email": "a@example.com", "password": "password-a", "email_confirm": True},
        20,
    )


def test_ensure_auth_user_repairs_existing_user_password_and_confirmation(monkeypatch):
    calls = []

    def fake_get(url, headers, timeout):
        calls.append(("GET", url, headers, None, timeout))
        return httpx.Response(200, json={"users": [{"id": "existing-auth-user", "email": "A@EXAMPLE.COM"}]})

    def fake_patch(url, headers, json, timeout):
        calls.append(("PATCH", url, headers, json, timeout))
        return httpx.Response(200, json={"user": {"id": "existing-auth-user"}})

    monkeypatch.setattr(verifier.httpx, "get", fake_get)
    monkeypatch.setattr(verifier.httpx, "patch", fake_patch)

    verifier._ensure_auth_user("https://example.supabase.co", "service-role", "a@example.com", "password-a")

    assert calls[-1] == (
        "PATCH",
        "https://example.supabase.co/auth/v1/admin/users/existing-auth-user",
        {
            "apikey": "service-role",
            "Authorization": "Bearer service-role",
            "Content-Type": "application/json",
        },
        {"password": "password-a", "email_confirm": True},
        20,
    )


def live_env() -> dict[str, str]:
    return {
        "SUPABASE_URL": "https://nexmxwvivewvgmrritqa.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_abcdefghijklmnopqrstuvwxyz1234567890",
        "SUPABASE_TEST_USER_A_EMAIL": "a@example.com",
        "SUPABASE_TEST_USER_A_PASSWORD": "password-a",
        "SUPABASE_TEST_USER_B_EMAIL": "b@example.com",
        "SUPABASE_TEST_USER_B_PASSWORD": "password-b",
    }
