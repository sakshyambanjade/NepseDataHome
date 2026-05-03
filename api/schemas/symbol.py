"""Symbol response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class SymbolProfile(BaseModel):
    symbol: str
    company_name: str | None = None
    sector: str | None = None
    status: str | None = None
    listed_shares: int | None = None
    first_trade_date: str | None = None
    last_trade_date: str | None = None
    rows: int = 0

