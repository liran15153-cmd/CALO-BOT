from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.config import Settings, get_settings
from backend.app.db import get_db
from backend.app.models import User
from backend.app.services.profile_service import ProfileService


@dataclass(frozen=True)
class AuthContext:
    user: User
    access_token: str | None = None


@dataclass(frozen=True)
class SupabaseUser:
    auth_user_id: str
    email: str | None = None


def get_auth_context(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    settings = get_settings()
    if not settings.supabase_auth_required:
        return AuthContext(user=ProfileService(db).get_default_user())

    token = _bearer_token(request)
    if token is None:
        raise HTTPException(status_code=401, detail="Missing Supabase access token")

    supabase_user = verify_supabase_access_token(token, settings=settings)
    user = ProfileService(db).get_or_create_auth_user(
        auth_user_id=supabase_user.auth_user_id,
        email=supabase_user.email,
    )
    return AuthContext(user=user, access_token=token)


def get_current_user(context: AuthContext = Depends(get_auth_context)) -> User:
    return context.user


def verify_supabase_access_token(token: str, *, settings: Settings | None = None) -> SupabaseUser:
    current_settings = settings or get_settings()
    if not current_settings.supabase_url or not current_settings.supabase_publishable_key:
        raise HTTPException(status_code=503, detail="Supabase Auth is not configured")

    url = current_settings.supabase_url.rstrip("/") + "/auth/v1/user"
    try:
        response = httpx.get(
            url,
            headers={
                "apikey": current_settings.supabase_publishable_key,
                "Authorization": f"Bearer {token}",
            },
            timeout=8,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=401, detail="Invalid Supabase access token") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Supabase access token")

    payload: dict[str, Any] = response.json()
    auth_user_id = str(payload.get("id") or "").strip()
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Invalid Supabase access token")
    email = payload.get("email")
    return SupabaseUser(auth_user_id=auth_user_id, email=str(email) if email else None)


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
