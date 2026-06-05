"""
server/services/storage.py

Luồng upload (client-side direct upload):
    1. Client gọi GET /logs/upload-sign → nhận signed params
    2. Client POST file thẳng lên Cloudinary endpoint với signed params
    3. Client gửi media_url kết quả về BE qua LogCreate / LogUpdate

Luồng delete (background task):
    media_url → extract public_id → cloudinary.uploader.destroy(public_id)
    Chạy sau khi response đã trả về client, không block request.
"""

import hashlib
import time

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from server.config import settings

_UPLOAD_FOLDER = "logget/logs"


def _configure() -> None:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def generate_signed_params() -> dict:
    _configure()
    timestamp = int(time.time())
    params = {"folder": _UPLOAD_FOLDER, "timestamp": timestamp}
    signature = cloudinary.utils.api_sign_request(params, settings.cloudinary_api_secret)
    return {
        "cloud_name": settings.cloudinary_cloud_name,
        "api_key": settings.cloudinary_api_key,
        "timestamp": timestamp,
        "signature": signature,
        "folder": _UPLOAD_FOLDER,
    }


def _extract_public_id(url: str) -> str | None:
    """
    Cloudinary URL: https://res.cloudinary.com/<cloud>/<type>/upload/[v<ver>/]<public_id>.<ext>
    Trả về public_id (bao gồm folder prefix nếu có).
    """
    try:
        path = url.split("/upload/", 1)[1]
        if path.startswith("v") and "/" in path:  # strip version segment
            path = path.split("/", 1)[1]
        return path.rsplit(".", 1)[0]  # strip extension
    except (IndexError, AttributeError):
        return None


def delete_media(media_url: str) -> None:
    """Sync — dùng làm BackgroundTask, không cần async."""
    _configure()
    public_id = _extract_public_id(media_url)
    if public_id:
        cloudinary.uploader.destroy(public_id)