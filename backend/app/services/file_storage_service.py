from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_MEAL_IMAGE_BYTES = 5 * 1024 * 1024


class FileStorageService:
    def __init__(self, upload_root: Path):
        self.upload_root = upload_root

    async def store_meal_image(self, user_id: int, file: UploadFile) -> Path:
        extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
        if extension is None:
            raise ValueError("Only JPEG, PNG, and WEBP meal images are allowed")

        content = await file.read(MAX_MEAL_IMAGE_BYTES + 1)
        if len(content) > MAX_MEAL_IMAGE_BYTES:
            raise ValueError("Meal image is too large; max size is 5 MB")
        if _detect_image_extension(content) != extension:
            raise ValueError("Uploaded image bytes do not match JPEG, PNG, or WEBP")

        today = date.today().isoformat()
        target_dir = self.upload_root / "meals" / str(user_id) / today
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{uuid4().hex}{extension}"
        target.write_bytes(content)
        return target.resolve()


def _detect_image_extension(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
        return ".webp"
    return None
