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


def live_env() -> dict[str, str]:
    return {
        "SUPABASE_URL": "https://nexmxwvivewvgmrritqa.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_abcdefghijklmnopqrstuvwxyz1234567890",
        "SUPABASE_TEST_USER_A_EMAIL": "a@example.com",
        "SUPABASE_TEST_USER_A_PASSWORD": "password-a",
        "SUPABASE_TEST_USER_B_EMAIL": "b@example.com",
        "SUPABASE_TEST_USER_B_PASSWORD": "password-b",
    }
