"""eSewa payment integration."""

from __future__ import annotations

import binascii
import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

import requests

from api.config import APP_BASE_URL, ESEWA_INIT_URL, ESEWA_MERCHANT_CODE, ESEWA_SECRET_KEY, ESEWA_VERIFY_URL
from api.services.api_key_service import get_default_api_key
from api.services.billing_db import connect, init_db, iso_now, log_payment_event, new_id, row_to_dict
from api.services.credit_service import add_credits
from api.services.csv_service import ApiError
from api.services.payment_plans import get_plan


def purchase_order_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"NDH-{stamp}-{new_id()[:8].upper()}"


def generate_esewa_signature(secret_key: str, message: str) -> str:
    digest = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def _safe_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _decode_callback_data(data: str | None) -> dict[str, Any] | None:
    if not data:
        return None

    candidates = [data]
    padding = "=" * (-len(data) % 4)
    if padding:
        candidates.append(f"{data}{padding}")

    for candidate in candidates:
        try:
            decoded = base64.b64decode(candidate).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            decoded = candidate
        try:
            return json.loads(decoded)
        except ValueError:
            continue
    return None


class EsewaService:
    def __init__(
        self,
        merchant_code: str | None = None,
        secret_key: str | None = None,
        init_url: str | None = None,
        verify_url: str | None = None,
    ):
        self.merchant_code = merchant_code if merchant_code is not None else ESEWA_MERCHANT_CODE
        self.secret_key = secret_key if secret_key is not None else ESEWA_SECRET_KEY
        self.init_url = init_url or ESEWA_INIT_URL
        self.verify_url = verify_url or ESEWA_VERIFY_URL

    def initiate_payment(
        self,
        user_id: str,
        plan_id: str,
        customer_info: dict[str, str],
    ) -> dict[str, Any]:
        init_db()
        plan = get_plan(plan_id)
        order_id = new_id()
        transaction_uuid = purchase_order_id()
        order_reference = purchase_order_id()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO payment_orders
                    (id, user_id, gateway, amount, credits, status, purchase_order_id, gateway_payment_id, raw_response, created_at)
                VALUES (?, ?, 'esewa', ?, ?, 'pending', ?, ?, '{}', ?)
                """,
                (order_id, user_id, plan.amount, plan.credits, order_reference, transaction_uuid, iso_now()),
            )
        
        log_payment_event(order_id, "esewa", "initiate_started", "pending", raw_payload={"plan_id": plan_id})

        message = f"{plan.amount},{transaction_uuid},{self.merchant_code}"
        signature = generate_esewa_signature(self.secret_key, message)
        payload = {
            "amount": str(plan.amount),
            "tax_amount": "0",
            "total_amount": str(plan.amount),
            "transaction_uuid": transaction_uuid,
            "product_code": self.merchant_code,
            "product_service_charge": "0",
            "product_delivery_charge": "0",
            "success_url": f"{APP_BASE_URL}/api/v1/payments/esewa/callback",
            "failure_url": f"{APP_BASE_URL}/api/v1/payments/esewa/callback",
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": signature,
            "customer_name": customer_info.get("name") or "NepseDataHome User",
            "customer_email": customer_info.get("email") or "user@example.com",
            "customer_phone": customer_info.get("phone") or "9800000000",
        }
        response = {
            "order_id": order_id,
            "transaction_uuid": transaction_uuid,
            "purchase_order_id": order_reference,
            "payment_url": self.init_url,
            "form_data": payload,
        }
        log_payment_event(order_id, "esewa", "initiate_success", "pending", raw_payload=response)
        return response

    def lookup_payment(self, transaction_uuid: str, total_amount: int, product_code: str | None = None) -> dict[str, Any]:
        response = requests.get(
            self.verify_url,
            params={
                "product_code": product_code or self.merchant_code,
                "total_amount": total_amount,
                "transaction_uuid": transaction_uuid,
            },
            timeout=20,
        )
        try:
            body = response.json()
        except ValueError as exc:
            raise ApiError(
                "ESEWA_BAD_RESPONSE",
                "eSewa returned a non-JSON verification response",
                {"status_code": response.status_code},
                status_code=502,
            ) from exc
        if response.status_code >= 400:
            raise ApiError(
                "ESEWA_LOOKUP_FAILED",
                "Could not verify eSewa payment",
                {"gateway_response": body},
                status_code=502,
            )
        return body

    def verify_payment(self, transaction_uuid: str, lookup_response: dict[str, Any] | None = None) -> dict[str, Any]:
        init_db()
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM payment_orders WHERE gateway = 'esewa' AND gateway_payment_id = ?",
                (transaction_uuid,),
            ).fetchone()
        order = row_to_dict(row)
        if not order:
            raise ApiError(
                "PAYMENT_ORDER_NOT_FOUND",
                "No payment order found for this eSewa transaction",
                {"transaction_uuid": transaction_uuid},
                status_code=404,
            )

        if order["status"] == "paid":
            log_payment_event(order["id"], "esewa", "verify_idempotent", "paid", raw_payload=lookup_response or {})
            return {"status": "paid", "order": order, "idempotent": True}

        lookup = lookup_response or self.lookup_payment(transaction_uuid, int(order["amount"]), self.merchant_code)
        status = _normalize_status(lookup.get("status") or lookup.get("transaction_status") or lookup.get("payment_status"))
        expected_amount = int(order["amount"])
        paid_amount = _safe_int(
            lookup.get("total_amount") or lookup.get("amount") or lookup.get("paid_amount") or lookup.get("transaction_amount")
        )

        if status not in {"completed", "complete", "success", "successful"}:
            with connect() as conn:
                conn.execute(
                    """
                    UPDATE payment_orders
                    SET raw_response = ?, gateway_reference = ?, verified_at = ?
                    WHERE id = ?
                    """,
                    (json.dumps(lookup), lookup.get("ref_id") or lookup.get("reference_id"), iso_now(), order["id"]),
                )
            log_payment_event(order["id"], "esewa", "verify_pending", "pending", raw_payload=lookup)
            return {"status": status or "pending", "order": order}

        if paid_amount != expected_amount:
            with connect() as conn:
                conn.execute(
                    "UPDATE payment_orders SET status = 'amount_mismatch', raw_response = ?, verified_at = ? WHERE id = ?",
                    (json.dumps(lookup), iso_now(), order["id"]),
                )
            log_payment_event(
                order["id"],
                "esewa",
                "verify_amount_mismatch",
                "amount_mismatch",
                message="Paid amount does not match plan",
                raw_payload=lookup,
            )
            raise ApiError(
                "PAYMENT_AMOUNT_MISMATCH",
                "Verified amount does not match the selected credit pack",
                {"expected_amount": expected_amount, "paid_amount": paid_amount},
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
                (lookup.get("ref_id") or lookup.get("reference_id"), json.dumps(lookup), iso_now(), order["id"]),
            )
        log_payment_event(order["id"], "esewa", "verify_paid", "paid", raw_payload=lookup)
        return {"status": "paid", "order": order, "balance": balance, "idempotent": False}


def _plan_id_from_order(order: dict[str, Any]) -> str:
    amount = int(order["amount"])
    plan_credits = int(order["credits"])
    for plan_id in ("starter_50", "student_100", "developer_500"):
        plan = get_plan(plan_id)
        if plan.amount == amount and plan.credits == plan_credits:
            return plan_id
    return "free"


def esewa_service() -> EsewaService:
    return EsewaService(
        secret_key=os.getenv("ESEWA_SECRET_KEY", ESEWA_SECRET_KEY),
        merchant_code=os.getenv("ESEWA_MERCHANT_CODE", ESEWA_MERCHANT_CODE),
    )