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
            return Check("not_configured", "DATABASE_URL לא מוגדר")
        if self.settings.database_url.startswith("sqlite"):
            if self.settings.supabase_auth_required or self.settings.app_env == "production":
                return Check("invalid", "SQLite הוא מסד נתונים מקומי בלבד")
            return Check("local_sqlite", "SQLite למסד נתונים מקומי בפיתוח")
        return Check("configured", "מסד נתונים שאינו SQLite מוגדר")

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
                return Check("invalid", "חסרים: " + ", ".join(missing))
            return Check("not_configured", "אימות Supabase אופציונלי בפיתוח מקומי")
        if _project_ref(self.settings.supabase_url or "") is None:
            return Check("invalid", "SUPABASE_URL אינו כתובת פרויקט Supabase")
        if _jwks_project_ref(self.settings.supabase_jwks_url or "") is None:
            return Check("invalid", "SUPABASE_JWKS_URL אינו כתובת JWKS של Supabase")
        if _project_ref(self.settings.supabase_url or "") != _jwks_project_ref(self.settings.supabase_jwks_url or ""):
            return Check("invalid", "פרויקט SUPABASE_JWKS_URL אינו תואם ל-SUPABASE_URL")
        return Check("configured", "הגדרת אימות Supabase קיימת")

    def _jwks_check(self) -> Check:
        if not self.settings.supabase_jwks_url:
            return Check("not_configured", "כתובת JWKS לא מוגדרת")
        if _jwks_project_ref(self.settings.supabase_jwks_url) is None:
            return Check("invalid", "כתובת JWKS לא תקינה")
        return Check("configured", "כתובת JWKS מוגדרת לאימות JWT מקומי")

    def _storage_check(self) -> Check:
        if not self.settings.supabase_storage_bucket:
            return Check("invalid", "SUPABASE_STORAGE_BUCKET לא מוגדר")
        if self.settings.supabase_configured:
            return Check("configured", f"מיכל אחסון Supabase '{self.settings.supabase_storage_bucket}' מוגדר")
        if self.settings.supabase_auth_required or self.settings.app_env == "production":
            return Check("invalid", "אחסון Supabase נדרש מחוץ לפיתוח מקומי")
        return Check("local", "שמירת תמונות ארוחה מקומית")

    def _issues(self, checks: dict[str, Check]) -> list[str]:
        issues: list[str] = []
        if not self.settings.supabase_auth_required:
            issues.append("אימות Supabase לא נדרש")
        if checks["database"].status == "invalid":
            if self.settings.supabase_auth_required:
                issues.append("אימות Supabase דורש DATABASE_URL שאינו SQLite")
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

