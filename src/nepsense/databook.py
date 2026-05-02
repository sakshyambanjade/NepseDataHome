"""Public data book builders.

The data book is the easy-access layer on top of raw daily snapshots: one
complete market file plus one history file per symbol.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import quote

import pandas as pd

from nepsense.config import DATA_DIR, MASTER_DIR, NORMALIZED_DIR, PROJECT_ROOT
from nepsense.storage import _read_all_csv, build_master

logger = logging.getLogger(__name__)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _symbol_filename(symbol: str) -> str:
    """Return a filesystem-safe filename for a market symbol."""
    return f"{quote(symbol, safe='-._~')}.csv"


def build_data_book(
    source_root: Path = NORMALIZED_DIR,
    output_root: Path = DATA_DIR / "history",
    rebuild_master: bool = True,
) -> dict[str, object]:
    """Build trader-friendly daily and per-company history files.

    Args:
        source_root: Normalized daily snapshots.
        output_root: Directory for public history outputs.
        rebuild_master: Whether to rebuild master CSV/Parquet/DuckDB first.

    Returns:
        Data book manifest.
    """
    output_root.mkdir(parents=True, exist_ok=True)
    by_symbol_dir = output_root / "by_symbol"
    by_date_dir = output_root / "by_date"
    by_symbol_dir.mkdir(parents=True, exist_ok=True)
    by_date_dir.mkdir(parents=True, exist_ok=True)

    if rebuild_master:
        build_master(use_adjusted=False)

    data = _read_all_csv(source_root)
    data["date"] = pd.to_datetime(data["date"], errors="coerce").dt.date.astype(str)
    data["symbol"] = data["symbol"].astype(str).str.strip().str.upper()
    data = data.dropna(subset=["date", "symbol"])
    data = data[data["symbol"].str.len() > 0]
    data = data.drop_duplicates(subset=["date", "symbol"])
    data = data.sort_values(["symbol", "date"])

    all_prices_path = output_root / "nepse_all_prices.csv"
    data.sort_values(["date", "symbol"]).to_csv(all_prices_path, index=False)

    symbols = []
    for symbol, history in data.groupby("symbol", sort=True):
        symbol_path = by_symbol_dir / _symbol_filename(symbol)
        history.sort_values("date").to_csv(symbol_path, index=False)
        symbols.append(
            {
                "symbol": symbol,
                "rows": int(len(history)),
                "first_date": str(history["date"].min()),
                "last_date": str(history["date"].max()),
                "file": str(symbol_path.relative_to(output_root)),
            }
        )

    for date_str, daily in data.groupby("date", sort=True):
        daily_path = by_date_dir / f"{date_str}.csv"
        daily.sort_values("symbol").to_csv(daily_path, index=False)

    manifest = {
        "dataset": "nepsense-data-book",
        "rows": int(len(data)),
        "symbols": len(symbols),
        "trading_days": int(data["date"].nunique()),
        "date_range": {
            "start": str(data["date"].min()),
            "end": str(data["date"].max()),
        },
        "outputs": {
            "all_prices_csv": _display_path(all_prices_path),
            "master_csv": _display_path(MASTER_DIR / "nepsense_prices.csv"),
            "master_parquet": _display_path(MASTER_DIR / "nepsense_prices.parquet"),
            "master_duckdb": _display_path(MASTER_DIR / "nepsense_prices.duckdb"),
            "by_symbol_dir": _display_path(by_symbol_dir),
            "by_date_dir": _display_path(by_date_dir),
        },
        "symbol_files": symbols,
    }

    manifest_path = output_root / "manifest.json"
    with open(manifest_path, "w") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)

    logger.info(
        "Built data book with %s rows, %s symbols, %s trading days",
        manifest["rows"],
        manifest["symbols"],
        manifest["trading_days"],
    )
    return manifest
