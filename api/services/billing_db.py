"""SQLite persistence for API keys, credits, orders, and usage logs."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from api.config import BILLING_DB


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def new_id() -> str:
    return str(uuid.uuid4())


def db_path() -> Path:
    return Path(BILLING_DB)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    if isinstance(data.get("raw_response"), str) and data["raw_response"]:
        data["raw_response"] = json.loads(data["raw_response"])
    if isinstance(data.get("raw_payload"), str) and data["raw_payload"]:
        data["raw_payload"] = json.loads(data["raw_payload"])
    return data


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price_npr INTEGER NOT NULL,
                monthly_credits INTEGER NOT NULL,
                max_devices INTEGER NOT NULL,
                max_api_keys INTEGER NOT NULL,
                max_ips_per_day INTEGER NOT NULL,
                rate_limit_per_minute INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                key_hash TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                credits_remaining INTEGER DEFAULT 0,
                expires_at TEXT,
                plan_id TEXT DEFAULT 'free' REFERENCES plans(id),
                blocked_until TEXT,
                block_reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS payment_orders (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                gateway TEXT NOT NULL,
                amount INTEGER NOT NULL,
                credits INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                purchase_order_id TEXT UNIQUE NOT NULL,
                gateway_payment_id TEXT,
                gateway_reference TEXT,
                raw_response TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                verified_at TEXT
            );

            CREATE TABLE IF NOT EXISTS api_usage_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                api_key_id TEXT REFERENCES api_keys(id),
                endpoint TEXT NOT NULL,
                credits_used INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_devices (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                device_id TEXT NOT NULL,
                device_name TEXT,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'active',
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, device_id)
            );

            CREATE TABLE IF NOT EXISTS active_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                device_id TEXT NOT NULL,
                session_token_hash TEXT NOT NULL,
                ip_address TEXT,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS api_key_ip_logs (
                id TEXT PRIMARY KEY,
                api_key_id TEXT REFERENCES api_keys(id),
                ip_address TEXT NOT NULL,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                request_count INTEGER DEFAULT 1,
                UNIQUE(api_key_id, ip_address)
            );

            CREATE TABLE IF NOT EXISTS abuse_events (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                api_key_id TEXT REFERENCES api_keys(id),
                event_type TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS payment_events (
                id TEXT PRIMARY KEY,
                order_id TEXT REFERENCES payment_orders(id),
                gateway TEXT NOT NULL,
                event_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                raw_payload TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
            CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
            CREATE INDEX IF NOT EXISTS idx_orders_gateway_payment ON payment_orders(gateway_payment_id);
            CREATE INDEX IF NOT EXISTS idx_usage_api_key ON api_usage_logs(api_key_id);
            CREATE INDEX IF NOT EXISTS idx_ip_logs_api_key ON api_key_ip_logs(api_key_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON active_sessions(user_id, status);
            CREATE INDEX IF NOT EXISTS idx_payment_events_order ON payment_events(order_id, created_at);
            """
        )
        _ensure_columns(conn)
        seed_plans(conn)


def _ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(api_keys)").fetchall()}
    additions = {
        "plan_id": "ALTER TABLE api_keys ADD COLUMN plan_id TEXT DEFAULT 'free'",
        "blocked_until": "ALTER TABLE api_keys ADD COLUMN blocked_until TEXT",
        "block_reason": "ALTER TABLE api_keys ADD COLUMN block_reason TEXT",
    }
    for column, statement in additions.items():
        if column not in existing:
            conn.execute(statement)


def seed_plans(conn: sqlite3.Connection) -> None:
    plans = [
        ("free", "Free", 0, 100, 1, 1, 1, 5),
        ("starter_50", "Rs. 50 Starter Pack", 50, 5000, 1, 1, 2, 10),
        ("student_100", "Rs. 100 Student Pack", 100, 12000, 1, 1, 3, 20),
        ("developer_500", "Rs. 500 Developer Pack", 500, 75000, 2, 2, 5, 60),
        ("broker", "Broker", 0, 0, 10, 10, 25, 600),
    ]
    conn.executemany(
        """
        INSERT INTO plans
            (id, name, price_npr, monthly_credits, max_devices, max_api_keys, max_ips_per_day, rate_limit_per_minute)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            price_npr = excluded.price_npr,
            monthly_credits = excluded.monthly_credits,
            max_devices = excluded.max_devices,
            max_api_keys = excluded.max_api_keys,
            max_ips_per_day = excluded.max_ips_per_day,
            rate_limit_per_minute = excluded.rate_limit_per_minute
        """,
        plans,
    )


def expiry_from_days(days: int) -> str:
    return (utc_now() + timedelta(days=days)).isoformat()


def log_payment_event(
    order_id: str | None,
    gateway: str,
    event_type: str,
    status: str,
    message: str | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> None:
    init_db()
    payload = json.dumps(raw_payload or {}, default=str)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO payment_events (id, order_id, gateway, event_type, status, message, raw_payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id(), order_id, gateway, event_type, status, message, payload, iso_now()),
        )
