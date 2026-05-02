"""Data normalization and schema mapping."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from nepsense.config import (
    NORMALIZED_DIR,
    RAW_DIR,
    STANDARD_OHLCV_COLUMNS,
)
from nepsense.utils import dated_output_path, resolve_date

logger = logging.getLogger(__name__)


# Column name normalization mapping
COLUMN_ALIASES = {
    # Symbol
    "symbol": "symbol",
    "stock symbol": "symbol",
    "code": "symbol",
    # Company name
    "company": "company_name",
    "company name": "company_name",
    "name": "company_name",
    "security name": "company_name",
    # Sector
    "sector": "sector",
    "industry": "sector",
    # OHLCV
    "open": "open",
    "opening price": "open",
    "op": "open",
    "high": "high",
    "max price": "high",
    "max": "high",
    "low": "low",
    "min price": "low",
    "min": "low",
    "close": "close",
    "closing price": "close",
    "ltp": "close",
    "last traded price": "close",
    "last transaction price": "close",
    # Volume
    "volume": "volume",
    "vol": "volume",
    "qty": "volume",
    "quantity": "volume",
    "traded qty": "volume",
    "traded quantity": "volume",
    "traded volume": "volume",
    # Turnover
    "turnover": "turnover",
    "amount": "turnover",
    "total amount": "turnover",
    "value": "turnover",
    # Transactions
    "transactions": "transactions",
    "trans": "transactions",
    "no of transactions": "transactions",
    "transaction count": "transactions",
    # Metadata
    "date": "date",
    "source": "source",
}


def normalize_column_name(name: object) -> str:
    """Normalize column name to standard schema.
    
    Args:
        name: Column name (any type)
    
    Returns:
        Normalized column name
    """
    text = str(name).strip().lower()
    text = text.replace(".", "")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    
    return COLUMN_ALIASES.get(text, text)


def normalize_file(
    input_file: Path,
    output_file: Path,
) -> Path:
    """Normalize a raw CSV file to standard schema.
    
    Args:
        input_file: Raw CSV path
        output_file: Output normalized CSV path
    
    Returns:
        Path to output file
    """
    logger.info(f"Normalizing {input_file}...")
    
    df = pd.read_csv(input_file)
    initial_rows = len(df)
    
    # Normalize column names
    df.columns = [normalize_column_name(c) for c in df.columns]
    
    # Validate required columns
    required = ["date", "symbol", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Ensure all standard columns exist
    for col in STANDARD_OHLCV_COLUMNS:
        if col not in df.columns:
            df[col] = None
    
    # Select only standard columns
    df = df[STANDARD_OHLCV_COLUMNS]
    
    # Basic cleaning
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    
    # Remove rows with missing critical data
    df = df.dropna(subset=["date", "symbol", "close"])
    df = df[df["symbol"].str.len() > 0]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["date", "symbol"])
    df = df.sort_values(["date", "symbol"])
    
    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    final_rows = len(df)
    logger.info(
        f"Normalized to {final_rows} rows "
        f"(removed {initial_rows - final_rows} invalid rows)"
    )
    
    return output_file


def normalize_all(
    input_root: Path = RAW_DIR,
    output_root: Path = NORMALIZED_DIR,
) -> int:
    """Normalize all raw CSV files.
    
    Args:
        input_root: Where to find raw files
        output_root: Where to save normalized files
    
    Returns:
        Count of normalized files
    """
    files = sorted(input_root.glob("*/*/*.csv"))
    logger.info(f"Found {len(files)} raw files to normalize")
    
    normalized = 0
    for input_file in files:
        date_str = input_file.stem
        output_file = dated_output_path(output_root, date_str)
        
        try:
            normalize_file(input_file, output_file)
            normalized += 1
        except Exception as e:
            logger.error(f"Failed to normalize {input_file}: {e}")
            continue
    
    logger.info(f"Successfully normalized {normalized} files")
    return normalized
