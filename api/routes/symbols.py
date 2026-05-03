"""Symbol routes."""

from __future__ import annotations

from fastapi import APIRouter

from api.services.csv_service import get_symbol, list_symbols

router = APIRouter(prefix="/api/v1/symbols", tags=["symbols"])


@router.get("")
def symbols() -> dict:
    rows = list_symbols()
    return {"meta": {"count": len(rows)}, "data": rows}


@router.get("/{symbol}")
def symbol_profile(symbol: str) -> dict:
    return {"meta": {"symbol": symbol.upper()}, "data": get_symbol(symbol)}

