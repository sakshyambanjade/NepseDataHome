"""Price response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class PriceBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int | float
    turnover: float = 0
    transactions: int | None = None


class PriceResponse(BaseModel):
    meta: dict
    data: list[PriceBar]

