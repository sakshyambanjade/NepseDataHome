"""Signed token helpers for dashboard/auth routes."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from api.config import AUTH_TOKEN_EXP_MINUTES, AUTH_TOKEN_SECRET
from api.services.csv_service import ApiError


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")


def _b64url_decode(raw: str) -> bytes:
    pad = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(f"{raw}{pad}")


def _sign(payload_part: str) -> str:
    digest = hmac.new(
        AUTH_TOKEN_SECRET.encode("utf-8"),
        payload_part.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def create_access_token(user_id: str, email: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=AUTH_TOKEN_EXP_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(expires_at.timestamp()),
        "ver": 1,
    }
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(payload_part)
    return f"v1.{payload_part}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        raise ApiError("AUTH_INVALID_TOKEN", "Invalid token format", status_code=401)

    payload_part = parts[1]
    signature = parts[2]
    expected = _sign(payload_part)
    if not hmac.compare_digest(signature, expected):
        raise ApiError("AUTH_INVALID_TOKEN", "Invalid token signature", status_code=401)

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ApiError("AUTH_INVALID_TOKEN", "Malformed token payload", status_code=401)

    exp = int(payload.get("exp") or 0)
    now_epoch = int(datetime.now(timezone.utc).timestamp())
    if exp <= now_epoch:
        raise ApiError("AUTH_TOKEN_EXPIRED", "Session token expired", status_code=401)

    if not payload.get("sub"):
        raise ApiError("AUTH_INVALID_TOKEN", "Token subject missing", status_code=401)

    return payload
