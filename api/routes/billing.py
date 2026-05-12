"""Billing, plans, Khalti, and eSewa payment routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.config import FRONTEND_URL
from api.services.api_key_service import get_default_api_key, get_user
from api.services.csv_service import ApiError
from api.services.billing_db import connect, init_db, log_payment_event, row_to_dict
from api.services.esewa_service import _decode_callback_data, esewa_service
from api.services.khalti_service import khalti_service
from api.services.payment_plans import PAYMENT_PLANS
from api.services.session_dependency import require_user_session

router = APIRouter(prefix="/api/v1", tags=["billing"])


def _order_id_by_gateway_payment(gateway: str, gateway_payment_id: str | None) -> str | None:
    if not gateway_payment_id:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM payment_orders WHERE gateway = ? AND gateway_payment_id = ?",
            (gateway, gateway_payment_id),
        ).fetchone()
    return str(row["id"]) if row else None


class KhaltiInitiateRequest(BaseModel):
    user_id: str
    plan_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None


class KhaltiVerifyRequest(BaseModel):
    pidx: str


class EsewaInitiateRequest(BaseModel):
    user_id: str
    plan_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None


class EsewaVerifyRequest(BaseModel):
    transaction_uuid: str


@router.get("/plans")
def plans() -> dict:
    return {
        "meta": {"count": len(PAYMENT_PLANS)},
        "data": [plan.__dict__ for plan in PAYMENT_PLANS.values()],
    }


@router.get("/billing/{user_id}")
def billing_summary(user_id: str, claims: dict = Depends(require_user_session)) -> dict:
    if str(claims.get("sub")) != str(user_id):
        raise ApiError("AUTH_FORBIDDEN", "Cannot access another user's billing", status_code=403)
    user = get_user(user_id)
    api_key = get_default_api_key(user_id)
    init_db()
    with connect() as conn:
        orders = [
            row_to_dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM payment_orders
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
        ]
        usage = [
            dict(row)
            for row in conn.execute(
                """
                SELECT endpoint, credits_used, created_at
                FROM api_usage_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
        ]
    safe_key = {
        key: value
        for key, value in api_key.items()
        if key not in {"key_hash", "api_key"}
    }
    return {"meta": {}, "data": {"user": user, "api_key": safe_key, "payments": orders, "usage": usage}}


@router.post("/payments/khalti/initiate")
def initiate_khalti(payload: KhaltiInitiateRequest, claims: dict = Depends(require_user_session)) -> dict:
    if str(claims.get("sub")) != str(payload.user_id):
        raise ApiError("AUTH_FORBIDDEN", "Cannot initiate payment for another user", status_code=403)
    service = khalti_service()
    result = service.initiate_payment(
        user_id=payload.user_id,
        plan_id=payload.plan_id,
        customer_info={
            "name": payload.name or "",
            "email": str(payload.email or ""),
            "phone": payload.phone or "",
        },
    )
    return {"meta": {"gateway": "khalti"}, "data": result}


@router.post("/payments/khalti/verify")
def verify_khalti(payload: KhaltiVerifyRequest, claims: dict = Depends(require_user_session)) -> dict:
    result = khalti_service().verify_payment(payload.pidx)
    if str((result.get("order") or {}).get("user_id", "")) != str(claims.get("sub")):
        raise ApiError("AUTH_FORBIDDEN", "Cannot verify another user's payment", status_code=403)
    return {"meta": {"gateway": "khalti"}, "data": result}


@router.post("/payments/esewa/initiate")
def initiate_esewa(payload: EsewaInitiateRequest, claims: dict = Depends(require_user_session)) -> dict:
    if str(claims.get("sub")) != str(payload.user_id):
        raise ApiError("AUTH_FORBIDDEN", "Cannot initiate payment for another user", status_code=403)
    service = esewa_service()
    result = service.initiate_payment(
        user_id=payload.user_id,
        plan_id=payload.plan_id,
        customer_info={
            "name": payload.name or "",
            "email": str(payload.email or ""),
            "phone": payload.phone or "",
        },
    )
    return {"meta": {"gateway": "esewa"}, "data": result}


@router.post("/payments/esewa/verify")
def verify_esewa(payload: EsewaVerifyRequest, claims: dict = Depends(require_user_session)) -> dict:
    result = esewa_service().verify_payment(payload.transaction_uuid)
    if str((result.get("order") or {}).get("user_id", "")) != str(claims.get("sub")):
        raise ApiError("AUTH_FORBIDDEN", "Cannot verify another user's payment", status_code=403)
    return {"meta": {"gateway": "esewa"}, "data": result}


@router.get("/payments/esewa/callback")
def esewa_callback(
    data: str | None = Query(None),
    transaction_uuid: str | None = Query(None),
    status: str | None = Query(None),
    refId: str | None = Query(None),
) -> RedirectResponse:
    payload = _decode_callback_data(data)
    resolved_transaction_uuid = transaction_uuid or (payload or {}).get("transaction_uuid")
    resolved_status = str(status or (payload or {}).get("status") or "").lower()
    event_order_id = _order_id_by_gateway_payment("esewa", resolved_transaction_uuid)
    log_payment_event(
        event_order_id,
        "esewa",
        "callback_received",
        resolved_status or "unknown",
        raw_payload=payload or {},
    )
    if resolved_transaction_uuid and resolved_status in {"complete", "completed", "success", "successful"}:
        lookup_payload = dict(payload or {})
        if refId and "ref_id" not in lookup_payload:
            lookup_payload["ref_id"] = refId
        if "transaction_uuid" not in lookup_payload:
            lookup_payload["transaction_uuid"] = resolved_transaction_uuid
        verification = esewa_service().verify_payment(resolved_transaction_uuid, lookup_response=lookup_payload)
        user_id = (verification.get("order") or {}).get("user_id", "")
        return RedirectResponse(
            f"{FRONTEND_URL}/billing/success?gateway=esewa&transaction_uuid={resolved_transaction_uuid}&user_id={user_id}"
        )
    return RedirectResponse(
        f"{FRONTEND_URL}/billing/failed?gateway=esewa&transaction_uuid={resolved_transaction_uuid or ''}&status={resolved_status or 'unknown'}"
    )


@router.get("/payments/khalti/callback")
def khalti_callback(
    pidx: str = Query(...),
    status: str | None = None,
) -> RedirectResponse:
    event_order_id = _order_id_by_gateway_payment("khalti", pidx)
    log_payment_event(
        event_order_id,
        "khalti",
        "callback_received",
        str(status or "unknown"),
        raw_payload={"pidx": pidx, "status": status},
    )
    if status == "Completed":
        verification = khalti_service().verify_payment(pidx)
        user_id = (verification.get("order") or {}).get("user_id", "")
        return RedirectResponse(f"{FRONTEND_URL}/billing/success?gateway=khalti&pidx={pidx}&user_id={user_id}")
    return RedirectResponse(
        f"{FRONTEND_URL}/billing/failed?gateway=khalti&pidx={pidx}&status={status or 'unknown'}"
    )
