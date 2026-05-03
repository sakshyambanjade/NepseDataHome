"""Device and session binding for account-sharing control."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import Any

from api.services.billing_db import connect, init_db, iso_now, new_id, utc_now
from api.services.csv_service import ApiError
from api.services.usage_service import get_plan


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def active_plan_for_user(user_id: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT plan_id
            FROM api_keys
            WHERE user_id = ? AND status = 'active'
            ORDER BY
                CASE plan_id
                    WHEN 'developer_500' THEN 1
                    WHEN 'student_100' THEN 2
                    WHEN 'starter_50' THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    return get_plan(row["plan_id"] if row else "free")


def register_device_session(
    user_id: str,
    device_id: str,
    device_name: str | None,
    ip_address: str,
    user_agent: str | None,
) -> dict[str, Any]:
    init_db()
    plan = active_plan_for_user(user_id)
    with connect() as conn:
        existing_device = conn.execute(
            "SELECT * FROM user_devices WHERE user_id = ? AND device_id = ?",
            (user_id, device_id),
        ).fetchone()
        active_devices = conn.execute(
            "SELECT COUNT(*) AS count FROM user_devices WHERE user_id = ? AND status = 'active'",
            (user_id,),
        ).fetchone()["count"]

        if not existing_device and int(active_devices) >= int(plan["max_devices"]):
            raise ApiError(
                "DEVICE_LIMIT_REACHED",
                "This plan allows only one active device. Reset your device or upgrade your plan.",
                {"max_devices": int(plan["max_devices"]), "plan": plan["id"]},
                status_code=403,
            )

        if existing_device:
            conn.execute(
                """
                UPDATE user_devices
                SET status = 'active', device_name = ?, ip_address = ?, user_agent = ?, last_seen = ?
                WHERE user_id = ? AND device_id = ?
                """,
                (device_name, ip_address, user_agent, iso_now(), user_id, device_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_devices
                    (id, user_id, device_id, device_name, ip_address, user_agent, status, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (new_id(), user_id, device_id, device_name, ip_address, user_agent, iso_now(), iso_now()),
            )

        conn.execute(
            "UPDATE active_sessions SET status = 'expired' WHERE user_id = ? AND device_id != ?",
            (user_id, device_id),
        )
        raw_session = f"ndh_session_{secrets.token_urlsafe(32)}"
        session_id = new_id()
        expires_at = (utc_now() + timedelta(days=30)).isoformat()
        conn.execute(
            """
            INSERT INTO active_sessions
                (id, user_id, device_id, session_token_hash, ip_address, last_active, expires_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (session_id, user_id, device_id, hash_session_token(raw_session), ip_address, iso_now(), expires_at),
        )

    return {
        "session_id": session_id,
        "session_token": raw_session,
        "device_id": device_id,
        "expires_at": expires_at,
    }


def list_devices(user_id: str) -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, device_id, device_name, ip_address, user_agent, status, first_seen, last_seen
            FROM user_devices
            WHERE user_id = ?
            ORDER BY last_seen DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def reset_devices(user_id: str) -> dict[str, Any]:
    init_db()
    seven_days_ago = (utc_now() - timedelta(days=7)).isoformat()
    with connect() as conn:
        recent = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM abuse_events
            WHERE user_id = ? AND event_type = 'device_reset' AND created_at >= ?
            """,
            (user_id, seven_days_ago),
        ).fetchone()["count"]
        if recent:
            raise ApiError(
                "DEVICE_RESET_LIMIT",
                "Device reset is available once every 7 days on this plan.",
                status_code=429,
            )
        conn.execute("UPDATE user_devices SET status = 'reset' WHERE user_id = ?", (user_id,))
        conn.execute("UPDATE active_sessions SET status = 'expired' WHERE user_id = ?", (user_id,))
        conn.execute(
            """
            INSERT INTO abuse_events
                (id, user_id, event_type, risk_score, action, details, created_at)
            VALUES (?, ?, 'device_reset', 0, 'reset_devices', '{}', ?)
            """,
            (new_id(), user_id, iso_now()),
        )
    return {"status": "reset"}
