from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class FileStorageService:
    def __init__(self, upload_root: Path):
        self.upload_root = upload_root

    async def store_meal_image(self, user_id: int, file: UploadFile) -> Path:
        extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
        if extension is None:
            raise ValueError("Only JPEG, PNG, and WEBP meal images are allowed")

        today = date.today().isoformat()
        target_dir = self.upload_root / "meals" / str(user_id) / today
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{uuid4().hex}{extension}"
        content = await file.read()
        target.write_bytes(content)
        return target.resolve()

