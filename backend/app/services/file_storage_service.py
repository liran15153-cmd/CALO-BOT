from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import quote
from uuid import uuid4

import httpx
from fastapi import UploadFile

from backend.app.config import Settings, get_settings


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_MEAL_IMAGE_BYTES = 5 * 1024 * 1024
_SUPABASE_STORAGE_REQUIRED_MESSAGE = "אחסון Supabase נדרש לתמונות ארוחה כאשר אימות Supabase או מצב production פעילים"


class FileStorageService:
    def __init__(self, upload_root: Path, *, access_token: str | None = None, settings: Settings | None = None):
        self.upload_root = upload_root
        self.access_token = access_token
        self.settings = settings or get_settings()

    async def store_meal_image(self, user_id: int, file: UploadFile, owner_key: str | None = None) -> str | Path:
        extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
        if extension is None:
            raise ValueError("אפשר להעלות רק תמונות ארוחה מסוג JPEG, PNG או WEBP")

        content = await file.read(MAX_MEAL_IMAGE_BYTES + 1)
        if len(content) > MAX_MEAL_IMAGE_BYTES:
            raise ValueError("תמונת הארוחה גדולה מדי; הגודל המרבי הוא 5MB")
        if _detect_image_extension(content) != extension:
            raise ValueError("קובץ התמונה לא תואם לסוג JPEG, PNG או WEBP")

        if self.settings.supabase_configured and self.access_token:
            return self._upload_supabase_object(
                content=content,
                content_type=file.content_type or "application/octet-stream",
                extension=extension,
                owner_key=owner_key or str(user_id),
            )

        if self.settings.app_env == "production" or self.settings.supabase_auth_required:
            raise ValueError(_SUPABASE_STORAGE_REQUIRED_MESSAGE)

        # Development fallback for local SQLite/no-auth runs only.
        root = self.upload_root.resolve()
        today = date.today().isoformat()
        target_dir = root / "meals" / str(user_id) / today
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{uuid4().hex}{extension}"
        target.write_bytes(content)
        return target.relative_to(root)

    def download_meal_image(self, image_path: str) -> Path:
        if not self.settings.supabase_configured or not self.access_token:
            if self.settings.app_env == "production" or self.settings.supabase_auth_required:
                raise ValueError(_SUPABASE_STORAGE_REQUIRED_MESSAGE)
            root = self.upload_root.resolve()
            path = Path(image_path)
            resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
            try:
                resolved.relative_to(root)
            except (OSError, ValueError) as exc:
                raise ValueError("תמונת הארוחה לא נמצאה") from exc
            return resolved

        response = httpx.get(
            self._storage_object_url(image_path),
            headers=self._storage_headers(),
            timeout=20,
        )
        if response.status_code != 200:
            raise ValueError("תמונת הארוחה לא נמצאה")
        suffix = Path(image_path).suffix or ".img"
        temp = NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            temp.write(response.content)
            return Path(temp.name)
        finally:
            temp.close()

    def delete_meal_image(self, image_path: str) -> None:
        if self.settings.supabase_configured and self.access_token:
            response = httpx.delete(
                self._storage_object_url(image_path),
                headers=self._storage_headers(),
                timeout=20,
            )
            if response.status_code not in {200, 204, 404}:
                raise ValueError("מחיקת תמונת הארוחה מ-Supabase נכשלה")
            return

        if self.settings.app_env == "production" or self.settings.supabase_auth_required:
            raise ValueError(_SUPABASE_STORAGE_REQUIRED_MESSAGE)

        root = self.upload_root.resolve()
        path = Path(image_path)
        try:
            resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
            resolved.relative_to(root)
        except (OSError, ValueError):
            return
        if resolved.is_file():
            resolved.unlink()

    def _upload_supabase_object(self, *, content: bytes, content_type: str, extension: str, owner_key: str) -> str:
        today = date.today().isoformat()
        object_path = f"{owner_key}/{today}/{uuid4().hex}{extension}"
        response = httpx.post(
            self._storage_object_url(object_path),
            headers={**self._storage_headers(), "Content-Type": content_type, "x-upsert": "false"},
            content=content,
            timeout=20,
        )
        if response.status_code not in {200, 201}:
            raise ValueError("שמירת תמונת הארוחה ב-Supabase נכשלה")
        return object_path

    def _storage_object_url(self, object_path: str) -> str:
        base = (self.settings.supabase_url or "").rstrip("/")
        bucket = quote(self.settings.supabase_storage_bucket, safe="")
        path = quote(object_path.lstrip("/"), safe="/")
        return f"{base}/storage/v1/object/{bucket}/{path}"

    def _storage_headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_publishable_key or "",
            "Authorization": f"Bearer {self.access_token}",
        }


def _detect_image_extension(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
        return ".webp"
    return None
