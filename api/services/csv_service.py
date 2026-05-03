"""CSV-backed data access for the API MVP.

This keeps the first API version deployable without BigQuery. The service can
be swapped behind the routes once the cloud tables are available.
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from api.config import (
    ALL_PRICES_CSV,
    API_SOURCE_NAME,
    COMPANY_MASTER_CSV,
    DEFAULT_QUERY_LIMIT,
    MANIFEST_JSON,
    MAX_QUERY_LIMIT,
    NEPAL_TIMEZONE,
    QUALITY_DIR,
)


class ApiError(Exception):
    """Structured API exception."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


def _empty_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _as_float(value: Any, default: float = 0.0) -> float:
    value = _empty_to_none(value)
    if value is None:
        return default
    return float(value)


def _as_int(value: Any) -> int | None:
    value = _empty_to_none(value)
    if value is None:
        return None
    return int(float(value))


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": str(row.get("date", "")),
        "symbol": str(row.get("symbol", "")).strip().upper(),
        "open": _as_float(row.get("open")),
        "high": _as_float(row.get("high")),
        "low": _as_float(row.get("low")),
        "close": _as_float(row.get("close")),
        "volume": _as_int(row.get("volume")) or 0,
        "turnover": _as_float(row.get("turnover")),
        "transactions": _as_int(row.get("transactions")),
        "source": row.get("source") or API_SOURCE_NAME,
        "created_at": row.get("created_at") or None,
        "updated_at": row.get("updated_at") or None,
        "source_confidence": _as_float(row.get("source_confidence"), 0.0),
    }


@lru_cache(maxsize=1)
def load_prices() -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """Load price history into symbol/date indexes."""
    if not ALL_PRICES_CSV.exists():
        raise ApiError(
            "DATASET_NOT_FOUND",
            "Master history file is missing",
            {"path": str(ALL_PRICES_CSV)},
        )

    by_symbol: dict[str, list[dict[str, Any]]] = {}
    by_date: dict[str, list[dict[str, Any]]] = {}
    with open(ALL_PRICES_CSV, newline="") as price_file:
        reader = csv.DictReader(price_file)
        for raw in reader:
            row = _clean_row(raw)
            if not row["date"] or not row["symbol"]:
                continue
            by_symbol.setdefault(row["symbol"], []).append(row)
            by_date.setdefault(row["date"], []).append(row)

    for rows in by_symbol.values():
        rows.sort(key=lambda item: item["date"])
    for rows in by_date.values():
        rows.sort(key=lambda item: item["symbol"])
    return by_symbol, by_date


@lru_cache(maxsize=1)
def load_company_master() -> dict[str, dict[str, Any]]:
    if not COMPANY_MASTER_CSV.exists():
        return {}
    companies: dict[str, dict[str, Any]] = {}
    with open(COMPANY_MASTER_CSV, newline="") as company_file:
        reader = csv.DictReader(company_file)
        for row in reader:
            symbol = str(row.get("symbol", "")).strip().upper()
            if symbol:
                companies[symbol] = row
    return companies


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    if not MANIFEST_JSON.exists():
        return {}
    with open(MANIFEST_JSON) as manifest_file:
        return json.load(manifest_file)


def now_nepal() -> str:
    return datetime.now(ZoneInfo(NEPAL_TIMEZONE)).isoformat()


def normalize_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_QUERY_LIMIT
    if limit < 1:
        raise ApiError("INVALID_LIMIT", "limit must be greater than zero", {"limit": limit})
    return min(limit, MAX_QUERY_LIMIT)


def list_symbols() -> list[dict[str, Any]]:
    by_symbol, _ = load_prices()
    companies = load_company_master()
    symbols = []
    for symbol, rows in sorted(by_symbol.items()):
        company = companies.get(symbol, {})
        symbols.append(
            {
                "symbol": symbol,
                "company_name": company.get("company_name") or None,
                "sector": company.get("sector") or None,
                "status": company.get("status") or None,
                "first_trade_date": rows[0]["date"],
                "last_trade_date": rows[-1]["date"],
                "rows": len(rows),
            }
        )
    return symbols


def get_symbol(symbol: str) -> dict[str, Any]:
    symbol = symbol.upper()
    by_symbol, _ = load_prices()
    if symbol not in by_symbol:
        raise ApiError("SYMBOL_NOT_FOUND", f"No data found for symbol {symbol}", {"symbol": symbol})
    company = load_company_master().get(symbol, {})
    rows = by_symbol[symbol]
    listed_shares = _as_int(company.get("listed_shares"))
    return {
        "symbol": symbol,
        "company_name": company.get("company_name") or None,
        "sector": company.get("sector") or None,
        "status": company.get("status") or None,
        "listed_shares": listed_shares,
        "first_trade_date": rows[0]["date"],
        "last_trade_date": rows[-1]["date"],
        "rows": len(rows),
    }


def get_prices(
    symbol: str,
    start: date | None = None,
    end: date | None = None,
    limit: int | None = None,
    adjusted: bool = False,
) -> dict[str, Any]:
    symbol = symbol.upper()
    by_symbol, _ = load_prices()
    if symbol not in by_symbol:
        raise ApiError("SYMBOL_NOT_FOUND", f"No data found for symbol {symbol}", {"symbol": symbol})

    start_str = start.isoformat() if start else None
    end_str = end.isoformat() if end else None
    rows = by_symbol[symbol]
    if start_str:
        rows = [row for row in rows if row["date"] >= start_str]
    if end_str:
        rows = [row for row in rows if row["date"] <= end_str]

    query_limit = normalize_limit(limit)
    rows = rows[:query_limit]
    return {
        "meta": {
            "symbol": symbol,
            "start": start_str,
            "end": end_str,
            "count": len(rows),
            "source": API_SOURCE_NAME,
            "adjusted": adjusted,
            "last_updated": now_nepal(),
        },
        "data": rows,
    }


def get_daily_market(date_value: date, limit: int | None = None) -> dict[str, Any]:
    date_str = date_value.isoformat()
    _, by_date = load_prices()
    rows = by_date.get(date_str)
    if not rows:
        raise ApiError("DATE_NOT_FOUND", f"No market data found for {date_str}", {"date": date_str})
    query_limit = normalize_limit(limit)
    rows = rows[:query_limit]
    return {
        "meta": {
            "date": date_str,
            "count": len(rows),
            "source": API_SOURCE_NAME,
            "last_updated": now_nepal(),
        },
        "data": rows,
    }


def coverage() -> dict[str, Any]:
    manifest = load_manifest()
    symbols = list_symbols()
    return {
        "meta": {
            "source": API_SOURCE_NAME,
            "last_updated": now_nepal(),
        },
        "data": {
            "rows": manifest.get("rows"),
            "symbols": manifest.get("symbols", len(symbols)),
            "trading_days": manifest.get("trading_days"),
            "date_range": manifest.get("date_range", {}),
            "symbol_coverage": symbols,
        },
    }


def data_quality() -> dict[str, Any]:
    manifest = load_manifest()
    by_symbol, _ = load_prices()
    duplicate_pairs = 0
    ohlc_errors = 0
    zero_volume_days = 0
    future_dates = 0
    today = date.today().isoformat()

    for rows in by_symbol.values():
        seen = set()
        for row in rows:
            pair = (row["date"], row["symbol"])
            if pair in seen:
                duplicate_pairs += 1
            seen.add(pair)
            if row["date"] > today:
                future_dates += 1
            if row["volume"] == 0:
                zero_volume_days += 1
            if (
                row["open"] < 0
                or row["high"] < 0
                or row["low"] < 0
                or row["close"] < 0
                or row["volume"] < 0
                or row["high"] < max(row["open"], row["close"], row["low"])
                or row["low"] > min(row["open"], row["close"], row["high"])
            ):
                ohlc_errors += 1

    return {
        "meta": {
            "source": API_SOURCE_NAME,
            "last_updated": now_nepal(),
        },
        "data": {
            "rows_checked": manifest.get("rows"),
            "duplicate_symbol_date_rows": duplicate_pairs,
            "future_date_rows": future_dates,
            "ohlcv_error_rows": ohlc_errors,
            "zero_volume_rows": zero_volume_days,
            "status": "passing" if duplicate_pairs == 0 and future_dates == 0 and ohlc_errors == 0 else "warning",
        },
    }


def sources() -> dict[str, Any]:
    by_symbol, _ = load_prices()
    counts: dict[str, int] = {}
    for rows in by_symbol.values():
        for row in rows:
            source = str(row.get("source") or "unknown")
            counts[source] = counts.get(source, 0) + 1
    return {"meta": {"last_updated": now_nepal()}, "data": counts}


def anomalies() -> dict[str, Any]:
    issues_path = QUALITY_DIR / "validation_issues.csv"
    if not issues_path.exists():
        return {"meta": {"last_updated": now_nepal()}, "data": []}
    with open(issues_path, newline="") as issues_file:
        rows = list(csv.DictReader(issues_file))
    return {"meta": {"count": len(rows), "last_updated": now_nepal()}, "data": rows[:1000]}


def symbol_csv_path(symbol: str) -> Path:
    symbol = symbol.upper()
    get_symbol(symbol)
    path = ALL_PRICES_CSV.parent / "by_symbol" / f"{symbol}.csv"
    if not path.exists():
        raise ApiError("DOWNLOAD_NOT_FOUND", f"Download file missing for {symbol}", {"symbol": symbol})
    return path
