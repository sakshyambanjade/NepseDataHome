"""Credit accounting and usage logging."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from api.services.billing_db import connect, init_db, iso_now, new_id, parse_ts, utc_now
from api.services.csv_service import ApiError


def add_credits(
    api_key_id: str,
    credits: int,
    valid_days: int,
    plan_id: str | None = None,
) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM api_keys WHERE id = ?", (api_key_id,)).fetchone()
        if not row:
            raise ApiError(
                "API_KEY_NOT_FOUND",
                "API key not found",
                {"api_key_id": api_key_id},
                status_code=404,
            )

        current_expires_at = parse_ts(row["expires_at"])
        base = current_expires_at if current_expires_at and current_expires_at > utc_now() else utc_now()
        expires_at = (base + timedelta(days=valid_days)).isoformat()
        new_balance = int(row["credits_remaining"] or 0) + credits
        if plan_id:
            conn.execute(
                "UPDATE api_keys SET credits_remaining = ?, expires_at = ?, plan_id = ? WHERE id = ?",
                (new_balance, expires_at, plan_id, api_key_id),
            )
        else:
            conn.execute(
                "UPDATE api_keys SET credits_remaining = ?, expires_at = ? WHERE id = ?",
                (new_balance, expires_at, api_key_id),
            )
    return get_balance(api_key_id)


def deduct_credits(
    api_key: dict[str, Any],
    credits_used: int,
    endpoint: str,
) -> dict[str, Any]:
    init_db()
    if credits_used < 1:
        raise ApiError("INVALID_CREDIT_COST", "credits_used must be positive", status_code=500)

    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM api_keys
            WHERE id = ? AND credits_remaining >= ? AND status = 'active'
            """,
            (api_key["id"], credits_used),
        ).fetchone()
        if not row:
            raise ApiError(
                "INSUFFICIENT_CREDITS",
                "Not enough API credits for this request",
                {"credits_required": credits_used},
                status_code=402,
            )
        remaining = int(row["credits_remaining"]) - credits_used
        conn.execute(
            "UPDATE api_keys SET credits_remaining = ? WHERE id = ?",
            (remaining, api_key["id"]),
        )
        conn.execute(
            """
            INSERT INTO api_usage_logs
                (id, user_id, api_key_id, endpoint, credits_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_id(), api_key["user_id"], api_key["id"], endpoint, credits_used, iso_now()),
        )
        updated = conn.execute("SELECT * FROM api_keys WHERE id = ?", (api_key["id"],)).fetchone()

    return {
        "credits_remaining": int(updated["credits_remaining"]),
        "credits_used": credits_used,
        "expires_at": updated["expires_at"],
    }


def get_balance(api_key_id: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, key_prefix, status, credits_remaining, expires_at, created_at
            FROM api_keys
            WHERE id = ?
            """,
            (api_key_id,),
        ).fetchone()
    if not row:
        raise ApiError(
            "API_KEY_NOT_FOUND",
            "API key not found",
            {"api_key_id": api_key_id},
            status_code=404,
        )
    return dict(row)


def expire_old_credits() -> int:
    init_db()
    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE api_keys
            SET credits_remaining = 0, status = 'expired'
            WHERE expires_at IS NOT NULL AND expires_at <= ? AND status = 'active'
            """,
            (iso_now(),),
        )
        return cursor.rowcount
