"""Usage tracking helpers for Access Guard."""

from __future__ import annotations

from datetime import timedelta

from api.services.billing_db import connect, init_db, iso_now, new_id, utc_now


def record_api_key_ip(api_key_id: str, ip_address: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO api_key_ip_logs
                (id, api_key_id, ip_address, first_seen, last_seen, request_count)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(api_key_id, ip_address) DO UPDATE SET
                last_seen = excluded.last_seen,
                request_count = api_key_ip_logs.request_count + 1
            """,
            (new_id(), api_key_id, ip_address, iso_now(), iso_now()),
        )


def count_ips_today(api_key_id: str) -> int:
    init_db()
    since = utc_now().date().isoformat()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(DISTINCT ip_address) AS count
            FROM api_key_ip_logs
            WHERE api_key_id = ? AND substr(last_seen, 1, 10) >= ?
            """,
            (api_key_id, since),
        ).fetchone()
    return int(row["count"] or 0)


def count_requests_last_minute(api_key_id: str) -> int:
    init_db()
    since = (utc_now() - timedelta(minutes=1)).isoformat()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM api_usage_logs
            WHERE api_key_id = ? AND created_at >= ?
            """,
            (api_key_id, since),
        ).fetchone()
    return int(row["count"] or 0)


def get_plan(plan_id: str) -> dict:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if row:
        return dict(row)
    return {
        "id": "free",
        "name": "Free",
        "max_devices": 1,
        "max_api_keys": 1,
        "max_ips_per_day": 1,
        "rate_limit_per_minute": 5,
    }

