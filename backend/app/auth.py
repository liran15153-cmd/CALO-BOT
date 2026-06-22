from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlparse

import httpx
import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWK
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


JWKS_CACHE_SECONDS = 600
JWKS_TIMEOUT_SECONDS = 5
ALLOWED_SUPABASE_JWT_ALGS = {"ES256", "RS256"}
_jwks_cache: dict[str, tuple[float, dict[str, PyJWK]]] = {}


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
    _validate_supabase_auth_config(current_settings)

    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") not in ALLOWED_SUPABASE_JWT_ALGS:
            raise ValueError("unexpected jwt alg")
        kid = str(header.get("kid") or "").strip()
        if not kid:
            raise ValueError("missing jwt kid")
        signing_key = _jwks_key(current_settings, kid)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=sorted(ALLOWED_SUPABASE_JWT_ALGS),
            audience="authenticated",
            issuer=_supabase_issuer(current_settings),
            options={"require": ["exp", "iss", "sub", "aud", "role"]},
        )
    except (jwt.PyJWTError, ValueError, TypeError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=401, detail="Invalid Supabase access token") from exc

    if payload.get("role") != "authenticated":
        raise HTTPException(status_code=401, detail="Invalid Supabase access token")
    auth_user_id = str(payload.get("sub") or "").strip()
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Invalid Supabase access token")
    email = payload.get("email")
    return SupabaseUser(auth_user_id=auth_user_id, email=str(email) if email else None)


def _validate_supabase_auth_config(settings: Settings) -> None:
    if not settings.supabase_url or not settings.supabase_publishable_key or not settings.supabase_jwks_url:
        raise HTTPException(status_code=503, detail="Supabase Auth is not configured")
    project = _project_ref(settings.supabase_url)
    if project is None:
        raise HTTPException(status_code=503, detail="Supabase URL is invalid")
    jwks_project = _jwks_project_ref(settings.supabase_jwks_url)
    if jwks_project is None:
        raise HTTPException(status_code=503, detail="Supabase JWKS URL is invalid")
    if jwks_project != project:
        raise HTTPException(status_code=503, detail="Supabase JWKS URL does not match SUPABASE_URL")


def _jwks_key(settings: Settings, kid: str) -> PyJWK:
    keys = _jwks_keys(settings)
    if kid not in keys:
        keys = _jwks_keys(settings, force_refresh=True)
    if kid not in keys:
        raise ValueError("unknown jwt kid")
    return keys[kid]


def _jwks_keys(settings: Settings, *, force_refresh: bool = False) -> dict[str, PyJWK]:
    assert settings.supabase_jwks_url is not None
    cached = _jwks_cache.get(settings.supabase_jwks_url)
    if not force_refresh and cached and monotonic() - cached[0] < JWKS_CACHE_SECONDS:
        return cached[1]
    response = httpx.get(settings.supabase_jwks_url, timeout=JWKS_TIMEOUT_SECONDS)
    if response.status_code != 200:
        raise ValueError("jwks fetch failed")
    keys = {
        str(raw_key.get("kid")): PyJWK(raw_key, algorithm=str(raw_key.get("alg")))
        for raw_key in response.json().get("keys", [])
        if raw_key.get("kid") and raw_key.get("alg") in ALLOWED_SUPABASE_JWT_ALGS
    }
    _jwks_cache[settings.supabase_jwks_url] = (monotonic(), keys)
    return keys


def _supabase_issuer(settings: Settings) -> str:
    assert settings.supabase_url is not None
    return settings.supabase_url.rstrip("/") + "/auth/v1"


def _project_ref(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or parsed.path not in {"", "/"} or not host.endswith(".supabase.co"):
        return None
    return host.removesuffix(".supabase.co")


def _jwks_project_ref(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if (
        parsed.scheme != "https"
        or parsed.path != "/auth/v1/.well-known/jwks.json"
        or not host.endswith(".supabase.co")
    ):
        return None
    return host.removesuffix(".supabase.co")


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
