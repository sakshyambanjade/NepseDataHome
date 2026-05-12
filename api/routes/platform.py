"""Platform status routes for dashboard/admin surfaces."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from api.config import ALL_PRICES_CSV, BILLING_DB, MANIFEST_JSON
from api.services.billing_db import connect, init_db

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def _iso_from_ts(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


@router.get("/status")
def platform_status() -> dict:
    init_db()
    with connect() as conn:
        users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        paid_orders = conn.execute(
            "SELECT COUNT(*) AS count FROM payment_orders WHERE status = 'paid'"
        ).fetchone()["count"]
        pending_orders = conn.execute(
            "SELECT COUNT(*) AS count FROM payment_orders WHERE status = 'pending'"
        ).fetchone()["count"]
        usage_last_day = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM api_usage_logs
            WHERE created_at >= datetime('now', '-1 day')
            """
        ).fetchone()["count"]

    csv_exists = ALL_PRICES_CSV.exists()
    manifest_exists = MANIFEST_JSON.exists()

    return {
        "meta": {},
        "data": {
            "api": {"status": "ok"},
            "billing": {
                "database": str(BILLING_DB),
                "users": users,
                "orders_paid": paid_orders,
                "orders_pending": pending_orders,
                "usage_events_24h": usage_last_day,
            },
            "data_update": {
                "latest_csv": {
                    "exists": csv_exists,
                    "updated_at": _iso_from_ts(ALL_PRICES_CSV.stat().st_mtime if csv_exists else None),
                },
                "manifest": {
                    "exists": manifest_exists,
                    "updated_at": _iso_from_ts(MANIFEST_JSON.stat().st_mtime if manifest_exists else None),
                },
            },
        },
    }
