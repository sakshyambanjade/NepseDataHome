"""API key generation, hashing, validation, and rotation."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from api.services.billing_db import connect, init_db, iso_now, new_id, parse_ts, row_to_dict, utc_now
from api.services.csv_service import ApiError


KEY_PREFIX = "ndh_live"


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    token = secrets.token_urlsafe(24).replace("-", "").replace("_", "")
    raw_key = f"{KEY_PREFIX}_{token}"
    parts = raw_key.split("_")
    key_prefix = "_".join(parts[:3])[:20]
    return raw_key, key_prefix, hash_api_key(raw_key)


def create_user(email: str, name: str | None = None) -> dict[str, Any]:
    init_db()
    user_id = new_id()
    with connect() as conn:
        existing = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise ApiError(
                "USER_EXISTS",
                "A user with this email already exists",
                {"email": email},
                status_code=409,
            )
        conn.execute(
            "INSERT INTO users (id, email, name, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email, name, iso_now()),
        )
    return get_user(user_id)


def get_user(user_id: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    user = row_to_dict(row)
    if not user:
        raise ApiError("USER_NOT_FOUND", "User not found", {"user_id": user_id}, status_code=404)
    return user


def get_user_by_email(email: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    user = row_to_dict(row)
    if not user:
        raise ApiError("USER_NOT_FOUND", "User not found", {"email": email}, status_code=404)
    return user


def create_api_key(user_id: str, credits: int = 0, expires_at: str | None = None) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ApiError("USER_NOT_FOUND", "User not found", {"user_id": user_id}, status_code=404)
        key_count = conn.execute(
            "SELECT COUNT(*) AS count FROM api_keys WHERE user_id = ? AND status = 'active'",
            (user_id,),
        ).fetchone()["count"]
        plan = conn.execute("SELECT * FROM plans WHERE id = 'free'").fetchone()
        if key_count >= int(plan["max_api_keys"]):
            raise ApiError(
                "API_KEY_LIMIT_REACHED",
                "Your plan does not allow more active API keys",
                {"max_api_keys": int(plan["max_api_keys"])},
                status_code=403,
            )

    raw_key, key_prefix, key_hash = generate_api_key()
    key_id = new_id()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO api_keys
                (id, user_id, key_hash, key_prefix, status, credits_remaining, expires_at, plan_id, created_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?, 'free', ?)
            """,
            (key_id, user_id, key_hash, key_prefix, credits, expires_at, iso_now()),
        )
    key = get_api_key_by_id(key_id)
    key["api_key"] = raw_key
    key.pop("key_hash", None)
    return key


def signup_user(email: str, name: str | None = None) -> dict[str, Any]:
    user = create_user(email=email, name=name)
    api_key = create_api_key(user_id=user["id"])
    return {"user": user, "api_key": api_key}


def get_api_key_by_id(api_key_id: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM api_keys WHERE id = ?", (api_key_id,)).fetchone()
    key = row_to_dict(row)
    if not key:
        raise ApiError(
            "API_KEY_NOT_FOUND",
            "API key not found",
            {"api_key_id": api_key_id},
            status_code=404,
        )
    return key


def get_default_api_key(user_id: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM api_keys
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    key = row_to_dict(row)
    if not key:
        key = create_api_key(user_id=user_id)
        key.pop("api_key", None)
    return key


def validate_api_key(raw_key: str | None, credits_required: int = 1) -> dict[str, Any]:
    init_db()
    if not raw_key:
        raise ApiError(
            "API_KEY_REQUIRED",
            "X-API-Key header is required for this endpoint",
            status_code=401,
        )

    key_hash = hash_api_key(raw_key)
    with connect() as conn:
        row = conn.execute("SELECT * FROM api_keys WHERE key_hash = ?", (key_hash,)).fetchone()
    key = row_to_dict(row)
    if not key:
        raise ApiError("API_KEY_INVALID", "Invalid API key", status_code=401)
    if key["status"] != "active":
        raise ApiError("API_KEY_DISABLED", "API key is not active", status_code=403)
    blocked_until = parse_ts(key.get("blocked_until"))
    if blocked_until and blocked_until > utc_now():
        raise ApiError(
            "API_KEY_TEMPORARILY_BLOCKED",
            "This API key is temporarily blocked by Access Guard",
            {"blocked_until": key.get("blocked_until"), "reason": key.get("block_reason")},
            status_code=403,
        )

    expires_at = parse_ts(key.get("expires_at"))
    if expires_at and expires_at <= utc_now():
        raise ApiError("API_KEY_EXPIRED", "API key has expired", status_code=402)
    if int(key.get("credits_remaining") or 0) < credits_required:
        raise ApiError(
            "INSUFFICIENT_CREDITS",
            "Not enough API credits for this request",
            {
                "credits_required": credits_required,
                "credits_remaining": int(key.get("credits_remaining") or 0),
            },
            status_code=402,
        )
    return key


def rotate_api_key(user_id: str) -> dict[str, Any]:
    init_db()
    old_key = get_default_api_key(user_id)
    with connect() as conn:
        conn.execute("UPDATE api_keys SET status = 'rotated' WHERE id = ?", (old_key["id"],))
    return create_api_key(
        user_id=user_id,
        credits=int(old_key.get("credits_remaining") or 0),
        expires_at=old_key.get("expires_at"),
    )


def disable_api_key(api_key_id: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute("UPDATE api_keys SET status = 'disabled' WHERE id = ?", (api_key_id,))
