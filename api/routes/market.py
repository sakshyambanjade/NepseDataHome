"""Market-wide routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from api.services.auth_dependency import require_credits
from api.services.csv_service import get_daily_market

router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/daily/{date_value}")
def market_daily(
    date_value: date,
    limit: int | None = Query(default=None, ge=1),
    _: dict = Depends(require_credits(3)),
) -> dict:
    return get_daily_market(date_value, limit=limit)
