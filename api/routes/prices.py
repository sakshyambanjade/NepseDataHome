"""Price history routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query
from fastapi import Depends

from api.services.auth_dependency import require_credits
from api.services.csv_service import get_prices

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])


@router.get("/{symbol}")
def prices(
    symbol: str,
    start: date | None = None,
    end: date | None = None,
    limit: int | None = Query(default=None, ge=1),
    format: str = "json",
    adjusted: bool = False,
    _: dict = Depends(require_credits(1)),
) -> dict:
    if format != "json":
        from api.services.csv_service import ApiError

        raise ApiError(
            "UNSUPPORTED_FORMAT",
            "Only json format is supported on this endpoint; use download endpoints for CSV",
            {"format": format},
        )
    return get_prices(symbol=symbol, start=start, end=end, limit=limit, adjusted=adjusted)
