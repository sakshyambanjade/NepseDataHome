"""Import company-wise historical archives into daily NepSense data."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from nepsense.config import NORMALIZED_DIR, RAW_DIR, SOURCE_CONFIDENCE_SCALE

logger = logging.getLogger(__name__)


def _source_path(root: Path, source: str, *parts: str) -> Path:
    return root / f"source={source}" / Path(*parts)


def _daily_path(root: Path, source: str, date_str: str) -> Path:
    year, month, _ = date_str.split("-")
    return _source_path(root, source, year, month, f"{date_str}.csv")


def _normalise_company_history(
    symbol: str,
    frame: pd.DataFrame,
    source: str,
    source_confidence: float,
    start_date: str,
) -> pd.DataFrame:
    rename_map = {
        "published_date": "date",
        "traded_quantity": "volume",
        "traded_amount": "turnover",
    }
    frame = frame.rename(columns=rename_map)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
    frame = frame.dropna(subset=["date"])
    frame = frame[frame["date"] >= date.fromisoformat(start_date)]

    frame["symbol"] = symbol.upper()
    frame["source"] = source
    frame["source_confidence"] = source_confidence

    for column in ["open", "high", "low", "close", "volume", "turnover"]:
        frame[column] = pd.to_numeric(frame.get(column), errors="coerce")

    frame["transactions"] = None
    frame = frame.dropna(subset=["close"])

    columns = [
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover",
        "transactions",
        "source",
        "source_confidence",
    ]
    return frame[columns].drop_duplicates(subset=["date", "symbol"])


def import_github_companywise_archive(
    repo: str = "Aabishkar2/nepse-data",
    repo_path: str = "data/company-wise",
    branch: str = "main",
    source: str = "aabishkar2_nepse_data",
    source_confidence: float = SOURCE_CONFIDENCE_SCALE["archive"],
    start_date: str = "2007-01-01",
    timeout: int = 60,
) -> dict[str, object]:
    """Download a GitHub company-wise archive and write daily normalized files."""
    session = requests.Session()
    list_url = f"https://api.github.com/repos/{repo}/contents/{repo_path}?ref={branch}"
    response = session.get(list_url, timeout=timeout)
    response.raise_for_status()
    entries = [entry for entry in response.json() if entry.get("name", "").endswith(".csv")]

    raw_symbol_dir = _source_path(RAW_DIR, source, "by_symbol")
    raw_symbol_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    failed = []
    imported_symbols = 0

    for entry in entries:
        symbol = Path(entry["name"]).stem.upper()
        try:
            content_response = session.get(entry["download_url"], timeout=timeout)
            content_response.raise_for_status()
            raw_bytes = content_response.content

            raw_path = raw_symbol_dir / entry["name"]
            raw_path.write_bytes(raw_bytes)

            raw_frame = pd.read_csv(raw_path, low_memory=False)
            normalized = _normalise_company_history(
                symbol=symbol,
                frame=raw_frame,
                source=source,
                source_confidence=source_confidence,
                start_date=start_date,
            )
            if normalized.empty:
                continue

            frames.append(normalized)
            imported_symbols += 1
        except Exception as exc:
            logger.exception("Failed to import company-wise history for %s", symbol)
            failed.append({"symbol": symbol, "reason": str(exc)})

    if not frames:
        raise RuntimeError("No company-wise archive rows were imported")

    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = combined["date"].astype(str)
    combined = combined.drop_duplicates(subset=["date", "symbol"])
    combined = combined.sort_values(["date", "symbol"])

    written_dates = 0
    for date_str, daily in combined.groupby("date", sort=True):
        output_path = _daily_path(NORMALIZED_DIR, source, date_str)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        daily.sort_values("symbol").to_csv(output_path, index=False)
        written_dates += 1

    return {
        "repo": repo,
        "repo_path": repo_path,
        "source": source,
        "start_date": start_date,
        "symbols_found": len(entries),
        "symbols_imported": imported_symbols,
        "rows": int(len(combined)),
        "trading_days": written_dates,
        "date_range": {
            "start": str(combined["date"].min()),
            "end": str(combined["date"].max()),
        },
        "failed": failed,
    }


def import_local_companywise_archive(
    input_dir: Path,
    source: str = "companywise_archive",
    source_confidence: float = SOURCE_CONFIDENCE_SCALE["archive"],
    start_date: str = "2007-01-01",
) -> dict[str, object]:
    """Import local `SYMBOL.csv` company-wise files into daily normalized data."""
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Company-wise archive directory not found: {input_dir}")

    csv_files = sorted(input_dir.glob("*.csv"))
    raw_symbol_dir = _source_path(RAW_DIR, source, "by_symbol")
    raw_symbol_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    failed = []
    imported_symbols = 0

    for csv_file in csv_files:
        symbol = csv_file.stem.upper()
        try:
            raw_path = raw_symbol_dir / csv_file.name
            raw_path.write_bytes(csv_file.read_bytes())

            raw_frame = pd.read_csv(raw_path, low_memory=False)
            normalized = _normalise_company_history(
                symbol=symbol,
                frame=raw_frame,
                source=source,
                source_confidence=source_confidence,
                start_date=start_date,
            )
            if normalized.empty:
                continue

            frames.append(normalized)
            imported_symbols += 1
        except Exception as exc:
            logger.exception("Failed to import company-wise history for %s", symbol)
            failed.append({"symbol": symbol, "reason": str(exc)})

    if not frames:
        raise RuntimeError("No local company-wise archive rows were imported")

    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = combined["date"].astype(str)
    combined = combined.drop_duplicates(subset=["date", "symbol"])
    combined = combined.sort_values(["date", "symbol"])

    written_dates = 0
    for date_str, daily in combined.groupby("date", sort=True):
        output_path = _daily_path(NORMALIZED_DIR, source, date_str)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        daily.sort_values("symbol").to_csv(output_path, index=False)
        written_dates += 1

    return {
        "input_dir": str(input_dir),
        "source": source,
        "start_date": start_date,
        "symbols_found": len(csv_files),
        "symbols_imported": imported_symbols,
        "rows": int(len(combined)),
        "trading_days": written_dates,
        "date_range": {
            "start": str(combined["date"].min()),
            "end": str(combined["date"].max()),
        },
        "failed": failed,
    }
