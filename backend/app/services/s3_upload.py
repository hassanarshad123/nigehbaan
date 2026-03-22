"""S3 upload service for report photos."""

from __future__ import annotations

import base64
import logging
import uuid
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)

_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
_ALLOWED_TYPES = {"image/jpeg", "image/png"}

# Lazy S3 client
_s3_client = None


def _get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
    return _s3_client


def _detect_mime(data: bytes) -> str | None:
    """Detect MIME type from file magic bytes."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return None


def _ext_from_mime(mime: str) -> str:
    return "jpg" if mime == "image/jpeg" else "png"


def upload_base64_image(base64_str: str, key_prefix: str = "reports") -> str | None:
    """Decode a base64 data URI, validate, upload to S3, return the URL.

    Returns ``None`` if upload fails or validation rejects the file.
    """
    try:
        # Strip data URI prefix if present: data:image/png;base64,...
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]

        raw = base64.b64decode(base64_str)
    except Exception:
        logger.warning("Invalid base64 data")
        return None

    if len(raw) > _MAX_FILE_SIZE:
        logger.warning("File too large: %d bytes (max %d)", len(raw), _MAX_FILE_SIZE)
        return None

    mime = _detect_mime(raw)
    if mime not in _ALLOWED_TYPES:
        logger.warning("Invalid file type: %s", mime)
        return None

    ext = _ext_from_mime(mime)
    key = f"{key_prefix}/{uuid.uuid4().hex}.{ext}"

    try:
        s3 = _get_s3()
        s3.upload_fileobj(
            BytesIO(raw),
            settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": mime},
        )
        url = f"https://{settings.s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
        logger.info("Uploaded photo to S3: %s", key)
        return url
    except ClientError as exc:
        logger.error("S3 upload failed: %s", exc)
        return None
