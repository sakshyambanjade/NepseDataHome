"""NepseDataHome Access Guard risk scoring and auto-actions."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from api.services.billing_db import connect, init_db, iso_now, new_id, utc_now
from api.services.csv_service import ApiError
from api.services.usage_service import count_ips_today, count_requests_last_minute, get_plan, record_api_key_ip


def log_abuse_event(
    api_key: dict[str, Any],
    event_type: str,
    risk_score: int,
    action: str,
    details: dict[str, Any],
) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO abuse_events
                (id, user_id, api_key_id, event_type, risk_score, action, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id(),
                api_key["user_id"],
                api_key["id"],
                event_type,
                risk_score,
                action,
                json.dumps(details),
                iso_now(),
            ),
        )


def temporarily_block_key(api_key_id: str, minutes: int, reason: str) -> str:
    blocked_until = (utc_now() + timedelta(minutes=minutes)).isoformat()
    with connect() as conn:
        conn.execute(
            "UPDATE api_keys SET blocked_until = ?, block_reason = ? WHERE id = ?",
            (blocked_until, reason, api_key_id),
        )
    return blocked_until


def disable_key(api_key_id: str, reason: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE api_keys SET status = 'blocked', block_reason = ? WHERE id = ?",
            (reason, api_key_id),
        )


def evaluate_request(api_key: dict[str, Any], ip_address: str, user_agent: str | None) -> dict[str, Any]:
    """Calculate risk and apply autonomous access-control actions."""
    plan = get_plan(api_key.get("plan_id") or "free")
    record_api_key_ip(api_key["id"], ip_address)

    ips_today = count_ips_today(api_key["id"])
    requests_last_minute = count_requests_last_minute(api_key["id"])
    max_ips = int(plan["max_ips_per_day"])
    max_rpm = int(plan["rate_limit_per_minute"])

    risk = 0
    reasons: list[str] = []
    if ips_today > max_ips:
        risk += 45
        reasons.append("ip_limit_exceeded")
    if ips_today >= 5:
        risk += 45
        reasons.append("five_or_more_ips_today")
    if requests_last_minute >= max_rpm:
        risk += 55
        reasons.append("rate_limit_exceeded")
    if user_agent and "python" in user_agent.lower() and ips_today > max_ips:
        risk += 10
        reasons.append("scripted_multi_ip_use")

    details = {
        "ip_address": ip_address,
        "ips_today": ips_today,
        "max_ips_per_day": max_ips,
        "requests_last_minute": requests_last_minute,
        "rate_limit_per_minute": max_rpm,
        "reasons": reasons,
    }

    if risk >= 90:
        disable_key(api_key["id"], "ACCOUNT_SHARING_DETECTED")
        log_abuse_event(api_key, "account_sharing", risk, "blocked", details)
        raise ApiError(
            "ACCOUNT_SHARING_DETECTED",
            "This API key is being used from too many devices or locations.",
            {"action": "Please reset your API key or upgrade your plan.", **details},
            status_code=403,
        )
    if risk >= 61:
        blocked_until = temporarily_block_key(api_key["id"], 15, "SUSPICIOUS_API_USAGE")
        log_abuse_event(api_key, "suspicious_usage", risk, "temporary_block", details)
        raise ApiError(
            "SUSPICIOUS_API_USAGE",
            "This API key is temporarily limited because of unusual usage.",
            {"blocked_until": blocked_until, **details},
            status_code=429,
        )
    if risk >= 31:
        log_abuse_event(api_key, "elevated_risk", risk, "allow_log", details)

    return {"risk_score": risk, **details}
