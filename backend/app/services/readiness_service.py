from dataclasses import dataclass
from urllib.parse import urlparse

from backend.app.config import Settings


@dataclass(frozen=True)
class Check:
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"status": self.status, "detail": self.detail}


class ReadinessService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def status(self) -> dict:
        checks = {
            "database": self._database_check(),
            "supabase_auth": self._supabase_auth_check(),
            "jwks": self._jwks_check(),
            "storage": self._storage_check(),
        }
        issues = self._issues(checks)
        production_ready = not issues and self.settings.supabase_auth_required
        return {
            "status": "ready" if production_ready else "not_ready",
            "service": "calo-coach",
            "auth_required": self.settings.supabase_auth_required,
            "production_ready": production_ready,
            "checks": {name: check.to_dict() for name, check in checks.items()},
            "issues": issues,
        }

    def _database_check(self) -> Check:
        if not self.settings.database_url:
            return Check("not_configured", "DATABASE_URL is not set")
        if self.settings.database_url.startswith("sqlite"):
            if self.settings.supabase_auth_required or self.settings.app_env == "production":
                return Check("invalid", "SQLite is local-only")
            return Check("local_sqlite", "SQLite local development database")
        return Check("configured", "Non-SQLite database configured")

    def _supabase_auth_check(self) -> Check:
        missing = []
        if not self.settings.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.settings.supabase_publishable_key:
            missing.append("SUPABASE_PUBLISHABLE_KEY")
        if not self.settings.supabase_jwks_url:
            missing.append("SUPABASE_JWKS_URL")
        if missing:
            if self.settings.supabase_auth_required:
                return Check("invalid", "Missing " + ", ".join(missing))
            return Check("not_configured", "Supabase Auth is optional in local development")
        if _project_ref(self.settings.supabase_url or "") is None:
            return Check("invalid", "SUPABASE_URL is not a Supabase project URL")
        if _jwks_project_ref(self.settings.supabase_jwks_url or "") is None:
            return Check("invalid", "SUPABASE_JWKS_URL is not a Supabase JWKS URL")
        if _project_ref(self.settings.supabase_url or "") != _jwks_project_ref(self.settings.supabase_jwks_url or ""):
            return Check("invalid", "SUPABASE_JWKS_URL project does not match SUPABASE_URL")
        return Check("configured", "Supabase Auth config is present")

    def _jwks_check(self) -> Check:
        if not self.settings.supabase_jwks_url:
            return Check("not_configured", "JWKS URL is not set")
        if _jwks_project_ref(self.settings.supabase_jwks_url) is None:
            return Check("invalid", "JWKS URL is malformed")
        return Check("configured", "JWKS URL is configured for local JWT verification")

    def _storage_check(self) -> Check:
        if not self.settings.supabase_storage_bucket:
            return Check("invalid", "SUPABASE_STORAGE_BUCKET is not set")
        if self.settings.supabase_configured:
            return Check("configured", f"Supabase Storage bucket '{self.settings.supabase_storage_bucket}' configured")
        if self.settings.supabase_auth_required or self.settings.app_env == "production":
            return Check("invalid", "Supabase Storage is required outside local development")
        return Check("local", "Local meal-image storage fallback")

    def _issues(self, checks: dict[str, Check]) -> list[str]:
        issues: list[str] = []
        if not self.settings.supabase_auth_required:
            issues.append("Supabase Auth is not required")
        if checks["database"].status == "invalid":
            if self.settings.supabase_auth_required:
                issues.append("Supabase Auth requires a non-SQLite DATABASE_URL")
            else:
                issues.append(checks["database"].detail)
        for name in ("supabase_auth", "jwks", "storage"):
            if checks[name].status == "invalid":
                issues.append(checks[name].detail)
        return issues


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

