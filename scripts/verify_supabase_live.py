from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from collections.abc import Sequence
from typing import Mapping
from urllib.parse import quote
from uuid import uuid4

import httpx


REQUIRED_ENV = [
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_TEST_USER_A_EMAIL",
    "SUPABASE_TEST_USER_A_PASSWORD",
    "SUPABASE_TEST_USER_B_EMAIL",
    "SUPABASE_TEST_USER_B_PASSWORD",
]
VERIFIER_USER_NAME = "CALO Supabase verifier"
VERIFIER_B_UPDATE_ATTEMPT_NAME = "CALO RLS verifier B attempt"


def missing_live_verification_env(env: Mapping[str, str]) -> list[str]:
    return [name for name in REQUIRED_ENV if not env.get(name)]


def env_with_dotenv_files(
    env: Mapping[str, str],
    *,
    root: Path | None = None,
    filenames: Sequence[str] = (".env", ".env.local"),
) -> dict[str, str]:
    loaded: dict[str, str] = {}
    base = root or Path.cwd()
    for filename in filenames:
        path = base / filename
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key:
                loaded[key] = value.strip().strip('"').strip("'")
    return {**loaded, **dict(env)}


def run_live_verification(env: Mapping[str, str]) -> dict:
    missing = missing_live_verification_env(env)
    if missing:
        return {"status": "skipped", "missing": missing}

    base_url = env["SUPABASE_URL"].rstrip("/")
    publishable_key = env["SUPABASE_PUBLISHABLE_KEY"]
    secret_key = env.get("SUPABASE_SECRET_KEY")
    bucket = env.get("SUPABASE_STORAGE_BUCKET") or "meal-images"

    if secret_key:
        _ensure_auth_user(
            base_url,
            secret_key,
            env["SUPABASE_TEST_USER_A_EMAIL"],
            env["SUPABASE_TEST_USER_A_PASSWORD"],
        )
        _ensure_auth_user(
            base_url,
            secret_key,
            env["SUPABASE_TEST_USER_B_EMAIL"],
            env["SUPABASE_TEST_USER_B_PASSWORD"],
        )

    try:
        user_a = _sign_in(
            base_url,
            publishable_key,
            env["SUPABASE_TEST_USER_A_EMAIL"],
            env["SUPABASE_TEST_USER_A_PASSWORD"],
        )
        user_b = _sign_in(
            base_url,
            publishable_key,
            env["SUPABASE_TEST_USER_B_EMAIL"],
            env["SUPABASE_TEST_USER_B_PASSWORD"],
        )
    except RuntimeError as exc:
        if not secret_key and "Supabase Auth sign-in failed" in str(exc):
            raise RuntimeError(
                f"{exc}. Set valid SUPABASE_TEST_USER_* credentials, or set SUPABASE_SECRET_KEY "
                "in the trusted server-side environment so the verifier can create or repair the Auth test users."
            ) from exc
        raise
    if user_a["user_id"] == user_b["user_id"]:
        raise RuntimeError("test users must be two different Supabase Auth users")

    public_user_id = None
    created_user_row = False
    storage_uploaded = False
    object_path = f"{user_a['user_id']}/{date.today().isoformat()}/verify-{uuid4().hex}.png"
    try:
        existing_rows = _select_user_rows(base_url, publishable_key, user_a["access_token"], user_a["user_id"])
        if existing_rows:
            public_user_id = int(existing_rows[0]["id"])
            rls_mutation_checks = "skipped_existing_user_row"
        else:
            public_user_id = _insert_public_user(base_url, publishable_key, user_a)
            created_user_row = True
            rls_mutation_checks = "passed"

        b_visible_rows = _select_user_rows(base_url, publishable_key, user_b["access_token"], user_a["user_id"])
        if b_visible_rows:
            raise RuntimeError("RLS failed: user B can read user A public.users row")
        if created_user_row:
            b_user_update_status = _update_public_user_name(
                base_url,
                publishable_key,
                user_b["access_token"],
                user_a["user_id"],
                VERIFIER_B_UPDATE_ATTEMPT_NAME,
            )
            if b_user_update_status >= 500:
                raise RuntimeError(f"RLS update check failed with {b_user_update_status}")
            rows_after_b_update = _select_user_rows(base_url, publishable_key, user_a["access_token"], user_a["user_id"])
            if not rows_after_b_update:
                raise RuntimeError("RLS failed: user B update removed user A public.users row")
            if rows_after_b_update[0].get("name") == VERIFIER_B_UPDATE_ATTEMPT_NAME:
                raise RuntimeError("RLS failed: user B can update user A public.users row")

            b_user_delete_status = _delete_public_user_status(
                base_url,
                publishable_key,
                user_b["access_token"],
                user_a["user_id"],
            )
            if b_user_delete_status >= 500:
                raise RuntimeError(f"RLS delete check failed with {b_user_delete_status}")
            rows_after_b_delete = _select_user_rows(base_url, publishable_key, user_a["access_token"], user_a["user_id"])
            if not rows_after_b_delete:
                raise RuntimeError("RLS failed: user B can delete user A public.users row")
        else:
            b_user_update_status = None
            b_user_delete_status = None

        _upload_storage_object(base_url, publishable_key, bucket, user_a["access_token"], object_path)
        storage_uploaded = True
        b_storage_status = _get_storage_object_status(base_url, publishable_key, bucket, user_b["access_token"], object_path)
        if b_storage_status >= 500:
            raise RuntimeError(f"Storage read isolation check failed with {b_storage_status}")
        if b_storage_status == 200:
            raise RuntimeError("Storage RLS failed: user B can read user A object")
        b_storage_delete_status = _delete_storage_object_status(
            base_url,
            publishable_key,
            bucket,
            user_b["access_token"],
            object_path,
        )
        if b_storage_delete_status >= 500:
            raise RuntimeError(f"Storage delete isolation check failed with {b_storage_delete_status}")
        a_storage_status_after_b_delete = _get_storage_object_status(
            base_url,
            publishable_key,
            bucket,
            user_a["access_token"],
            object_path,
        )
        if a_storage_status_after_b_delete != 200:
            raise RuntimeError("Storage RLS failed: user B can delete user A object")

        return {
            "status": "passed",
            "rls": "passed",
            "rls_mutation_checks": rls_mutation_checks,
            "rls_user_b_update_status": b_user_update_status,
            "rls_user_b_delete_status": b_user_delete_status,
            "storage": "passed",
            "storage_user_b_status": b_storage_status,
            "storage_user_b_delete_status": b_storage_delete_status,
            "user_a_public_user_id": public_user_id,
            "created_user_row": created_user_row,
        }
    finally:
        if created_user_row:
            _delete_public_user(base_url, publishable_key, user_a["access_token"], user_a["user_id"])
        if storage_uploaded:
            _delete_storage_object(base_url, publishable_key, bucket, user_a["access_token"], object_path)


def _sign_in(base_url: str, publishable_key: str, email: str, password: str) -> dict[str, str]:
    response = httpx.post(
        f"{base_url}/auth/v1/token?grant_type=password",
        headers={"apikey": publishable_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=20,
    )
    _raise_for_status(response, "Supabase Auth sign-in failed")
    payload = response.json()
    access_token = payload.get("access_token")
    user_id = (payload.get("user") or {}).get("id")
    if not access_token or not user_id:
        raise RuntimeError("Supabase Auth sign-in did not return access_token and user.id")
    return {"access_token": access_token, "user_id": user_id, "email": email}


def _ensure_auth_user(base_url: str, secret_key: str, email: str, password: str) -> None:
    user_id = _find_auth_user_id_by_email(base_url, secret_key, email)
    if user_id:
        response = httpx.patch(
            f"{base_url}/auth/v1/admin/users/{quote(user_id, safe='')}",
            headers=_auth_admin_headers(secret_key),
            json={"password": password, "email_confirm": True},
            timeout=20,
        )
        _raise_for_status(response, f"Supabase Auth admin update failed for {email}")
        return

    response = httpx.post(
        f"{base_url}/auth/v1/admin/users",
        headers=_auth_admin_headers(secret_key),
        json={"email": email, "password": password, "email_confirm": True},
        timeout=20,
    )
    _raise_for_status(response, f"Supabase Auth admin create failed for {email}")


def _find_auth_user_id_by_email(base_url: str, secret_key: str, email: str) -> str | None:
    target = email.casefold()
    for page in range(1, 11):
        response = httpx.get(
            f"{base_url}/auth/v1/admin/users?page={page}&per_page=100",
            headers=_auth_admin_headers(secret_key),
            timeout=20,
        )
        _raise_for_status(response, f"Supabase Auth admin list failed while checking {email}")
        users = response.json().get("users") or []
        for user in users:
            if str(user.get("email") or "").casefold() == target:
                return str(user.get("id") or "")
        if len(users) < 100:
            return None
    return None


def _insert_public_user(base_url: str, publishable_key: str, user: dict[str, str]) -> int:
    response = httpx.post(
        f"{base_url}/rest/v1/users",
        headers={
            **_data_headers(publishable_key, user["access_token"]),
            "Prefer": "return=representation",
        },
        json={"auth_user_id": user["user_id"], "email": user["email"], "name": VERIFIER_USER_NAME},
        timeout=20,
    )
    _raise_for_status(response, "RLS insert failed for user A")
    rows = response.json()
    if not rows:
        raise RuntimeError("RLS insert returned no rows for user A")
    return int(rows[0]["id"])


def _select_user_rows(base_url: str, publishable_key: str, access_token: str, auth_user_id: str) -> list[dict]:
    response = httpx.get(
        f"{base_url}/rest/v1/users?auth_user_id=eq.{quote(auth_user_id)}&select=id,auth_user_id,name",
        headers=_data_headers(publishable_key, access_token),
        timeout=20,
    )
    _raise_for_status(response, "RLS select failed")
    return response.json()


def _update_public_user_name(
    base_url: str,
    publishable_key: str,
    access_token: str,
    auth_user_id: str,
    name: str,
) -> int:
    response = httpx.patch(
        f"{base_url}/rest/v1/users?auth_user_id=eq.{quote(auth_user_id)}",
        headers=_data_headers(publishable_key, access_token),
        json={"name": name},
        timeout=20,
    )
    if response.status_code < 200 or response.status_code >= 300:
        return response.status_code
    return response.status_code


def _delete_public_user(base_url: str, publishable_key: str, access_token: str, auth_user_id: str) -> None:
    status_code = _delete_public_user_status(base_url, publishable_key, access_token, auth_user_id)
    if status_code not in {200, 204}:
        print(f"cleanup warning: user row delete returned {status_code}", file=sys.stderr)


def _delete_public_user_status(base_url: str, publishable_key: str, access_token: str, auth_user_id: str) -> int:
    response = httpx.delete(
        f"{base_url}/rest/v1/users?auth_user_id=eq.{quote(auth_user_id)}",
        headers=_data_headers(publishable_key, access_token),
        timeout=20,
    )
    return response.status_code


def _upload_storage_object(
    base_url: str,
    publishable_key: str,
    bucket: str,
    access_token: str,
    object_path: str,
) -> None:
    response = httpx.post(
        _storage_object_url(base_url, bucket, object_path),
        headers={
            "apikey": publishable_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "image/png",
            "x-upsert": "false",
        },
        content=b"\x89PNG\r\n\x1a\ncalo-live-verify",
        timeout=20,
    )
    _raise_for_status(response, "Storage upload failed for user A")


def _get_storage_object_status(
    base_url: str,
    publishable_key: str,
    bucket: str,
    access_token: str,
    object_path: str,
) -> int:
    response = httpx.get(
        _storage_object_url(base_url, bucket, object_path),
        headers={"apikey": publishable_key, "Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    return response.status_code


def _delete_storage_object(
    base_url: str,
    publishable_key: str,
    bucket: str,
    access_token: str,
    object_path: str,
) -> None:
    status_code = _delete_storage_object_status(base_url, publishable_key, bucket, access_token, object_path)
    if status_code not in {200, 204, 404}:
        print(f"cleanup warning: storage delete returned {status_code}", file=sys.stderr)


def _delete_storage_object_status(
    base_url: str,
    publishable_key: str,
    bucket: str,
    access_token: str,
    object_path: str,
) -> int:
    response = httpx.delete(
        _storage_object_url(base_url, bucket, object_path),
        headers={"apikey": publishable_key, "Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    return response.status_code


def _storage_object_url(base_url: str, bucket: str, object_path: str) -> str:
    return f"{base_url}/storage/v1/object/{quote(bucket, safe='')}/{quote(object_path, safe='/')}"


def _data_headers(publishable_key: str, access_token: str) -> dict[str, str]:
    return {
        "apikey": publishable_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _auth_admin_headers(secret_key: str) -> dict[str, str]:
    return {
        "apikey": secret_key,
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }


def _raise_for_status(response: httpx.Response, message: str) -> None:
    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(f"{message}: {response.status_code} {response.text[:500]}")


def main() -> int:
    try:
        result = run_live_verification(env_with_dotenv_files(os.environ))
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"passed", "skipped"} else 1


if __name__ == "__main__":
    sys.exit(main())
