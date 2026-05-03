"""Khalti KPG-2 payment integration."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import requests

from api.config import APP_BASE_URL, FRONTEND_URL, KHALTI_INIT_URL, KHALTI_LOOKUP_URL, KHALTI_SECRET_KEY
from api.services.api_key_service import get_default_api_key
from api.services.billing_db import connect, init_db, iso_now, new_id, row_to_dict
from api.services.credit_service import add_credits
from api.services.csv_service import ApiError
from api.services.payment_plans import get_plan


def purchase_order_id() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"NDH-{stamp}-{new_id()[:8].upper()}"


class KhaltiService:
    def __init__(
        self,
        secret_key: str | None = None,
        init_url: str | None = None,
        lookup_url: str | None = None,
    ):
        self.secret_key = secret_key if secret_key is not None else KHALTI_SECRET_KEY
        self.init_url = init_url or KHALTI_INIT_URL
        self.lookup_url = lookup_url or KHALTI_LOOKUP_URL

    @property
    def headers(self) -> dict[str, str]:
        if not self.secret_key:
            raise ApiError(
                "PAYMENT_GATEWAY_NOT_CONFIGURED",
                "Khalti secret key is not configured",
                status_code=503,
            )
        return {"Authorization": f"Key {self.secret_key}", "Content-Type": "application/json"}

    def initiate_payment(
        self,
        user_id: str,
        plan_id: str,
        customer_info: dict[str, str],
    ) -> dict[str, Any]:
        init_db()
        plan = get_plan(plan_id)
        order_id = new_id()
        poid = purchase_order_id()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO payment_orders
                    (id, user_id, gateway, amount, credits, status, purchase_order_id, raw_response, created_at)
                VALUES (?, ?, 'khalti', ?, ?, 'pending', ?, '{}', ?)
                """,
                (order_id, user_id, plan.amount, plan.credits, poid, iso_now()),
            )

        payload = {
            "return_url": f"{APP_BASE_URL}/api/v1/payments/khalti/callback",
            "website_url": FRONTEND_URL,
            "amount": plan.amount_paisa,
            "purchase_order_id": poid,
            "purchase_order_name": f"NepseDataHome {plan.name}",
            "customer_info": {
                "name": customer_info.get("name") or "NepseDataHome User",
                "email": customer_info.get("email") or "user@example.com",
                "phone": customer_info.get("phone") or "9800000000",
            },
        }
        response = requests.post(self.init_url, headers=self.headers, json=payload, timeout=20)
        try:
            body = response.json()
        except ValueError as exc:
            raise ApiError(
                "KHALTI_BAD_RESPONSE",
                "Khalti returned a non-JSON response",
                {"status_code": response.status_code},
                status_code=502,
            ) from exc

        if response.status_code >= 400:
            with connect() as conn:
                conn.execute(
                    "UPDATE payment_orders SET status = 'failed', raw_response = ? WHERE id = ?",
                    (json.dumps(body), order_id),
                )
            raise ApiError(
                "KHALTI_INIT_FAILED",
                "Could not initiate Khalti payment",
                {"gateway_response": body},
                status_code=502,
            )

        with connect() as conn:
            conn.execute(
                """
                UPDATE payment_orders
                SET gateway_payment_id = ?, raw_response = ?
                WHERE id = ?
                """,
                (body.get("pidx"), json.dumps(body), order_id),
            )
        return {"order_id": order_id, "purchase_order_id": poid, **body}

    def lookup_payment(self, pidx: str) -> dict[str, Any]:
        response = requests.post(self.lookup_url, headers=self.headers, json={"pidx": pidx}, timeout=20)
        try:
            body = response.json()
        except ValueError as exc:
            raise ApiError(
                "KHALTI_BAD_RESPONSE",
                "Khalti returned a non-JSON lookup response",
                {"status_code": response.status_code},
                status_code=502,
            ) from exc
        if response.status_code >= 400:
            raise ApiError(
                "KHALTI_LOOKUP_FAILED",
                "Could not verify Khalti payment",
                {"gateway_response": body},
                status_code=502,
            )
        return body

    def verify_payment(self, pidx: str, lookup_response: dict[str, Any] | None = None) -> dict[str, Any]:
        init_db()
        lookup = lookup_response or self.lookup_payment(pidx)
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM payment_orders WHERE gateway = 'khalti' AND gateway_payment_id = ?",
                (pidx,),
            ).fetchone()
        order = row_to_dict(row)
        if not order:
            raise ApiError(
                "PAYMENT_ORDER_NOT_FOUND",
                "No payment order found for this Khalti pidx",
                {"pidx": pidx},
                status_code=404,
            )

        if order["status"] == "paid":
            return {"status": "paid", "order": order, "idempotent": True}

        expected_paisa = int(order["amount"]) * 100
        paid_paisa = int(lookup.get("total_amount") or lookup.get("amount") or 0)
        if lookup.get("status") != "Completed":
            with connect() as conn:
                conn.execute(
                    """
                    UPDATE payment_orders
                    SET raw_response = ?, gateway_reference = ?, verified_at = ?
                    WHERE id = ?
                    """,
                    (json.dumps(lookup), lookup.get("transaction_id"), iso_now(), order["id"]),
                )
            return {"status": lookup.get("status", "pending"), "order": order}
        if paid_paisa != expected_paisa:
            with connect() as conn:
                conn.execute(
                    "UPDATE payment_orders SET status = 'amount_mismatch', raw_response = ?, verified_at = ? WHERE id = ?",
                    (json.dumps(lookup), iso_now(), order["id"]),
                )
            raise ApiError(
                "PAYMENT_AMOUNT_MISMATCH",
                "Verified amount does not match the selected credit pack",
                {"expected_paisa": expected_paisa, "paid_paisa": paid_paisa},
                status_code=400,
            )

        api_key = get_default_api_key(order["user_id"])
        plan_id = _plan_id_from_order(order)
        balance = add_credits(api_key["id"], int(order["credits"]), 30, plan_id=plan_id)
        with connect() as conn:
            conn.execute(
                """
                UPDATE payment_orders
                SET status = 'paid', gateway_reference = ?, raw_response = ?, verified_at = ?
                WHERE id = ? AND status != 'paid'
                """,
                (lookup.get("transaction_id"), json.dumps(lookup), iso_now(), order["id"]),
            )
        return {"status": "paid", "order": order, "balance": balance, "idempotent": False}


def _plan_id_from_order(order: dict[str, Any]) -> str:
    amount = int(order["amount"])
    credits = int(order["credits"])
    for plan_id in ("starter_50", "student_100", "developer_500"):
        plan = get_plan(plan_id)
        if plan.amount == amount and plan.credits == credits:
            return plan_id
    return "free"


def khalti_service() -> KhaltiService:
    return KhaltiService(secret_key=os.getenv("KHALTI_SECRET_KEY", KHALTI_SECRET_KEY))
