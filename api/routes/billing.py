"""Billing, plans, and Khalti payment routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.config import FRONTEND_URL
from api.services.api_key_service import get_default_api_key, get_user
from api.services.billing_db import connect, init_db, row_to_dict
from api.services.khalti_service import khalti_service
from api.services.payment_plans import PAYMENT_PLANS

router = APIRouter(prefix="/api/v1", tags=["billing"])


class KhaltiInitiateRequest(BaseModel):
    user_id: str
    plan_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None


class KhaltiVerifyRequest(BaseModel):
    pidx: str


@router.get("/plans")
def plans() -> dict:
    return {
        "meta": {"count": len(PAYMENT_PLANS)},
        "data": [plan.__dict__ for plan in PAYMENT_PLANS.values()],
    }


@router.get("/billing/{user_id}")
def billing_summary(user_id: str) -> dict:
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
def initiate_khalti(payload: KhaltiInitiateRequest) -> dict:
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
def verify_khalti(payload: KhaltiVerifyRequest) -> dict:
    result = khalti_service().verify_payment(payload.pidx)
    return {"meta": {"gateway": "khalti"}, "data": result}


@router.get("/payments/khalti/callback")
def khalti_callback(
    request: Request,
    pidx: str = Query(...),
    status: str | None = None,
    purchase_order_id: str | None = None,
) -> RedirectResponse:
    if status == "Completed":
        khalti_service().verify_payment(pidx)
        return RedirectResponse(f"{FRONTEND_URL}/billing/success?gateway=khalti&pidx={pidx}")
    return RedirectResponse(
        f"{FRONTEND_URL}/billing/failed?gateway=khalti&pidx={pidx}&status={status or 'unknown'}"
    )
