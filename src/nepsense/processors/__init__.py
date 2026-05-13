"""Data normalization and schema mapping."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from nepsense.config import (
    NORMALIZED_DIR,
    RAW_DIR,
    SOURCE_CONFIDENCE_SCALE,
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
    "source confidence": "source_confidence",
    "source_confidence": "source_confidence",
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


def _coalesce_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Merge columns that normalize to the same standard name."""
    if not df.columns.has_duplicates:
        return df

    merged = pd.DataFrame(index=df.index)
    seen: set[str] = set()

    for col in df.columns:
        if col in seen:
            continue

        matches = df.loc[:, df.columns == col]
        if matches.shape[1] > 1:
            merged[col] = matches.bfill(axis=1).iloc[:, 0]
            logger.warning(
                "Coalesced %s columns named '%s' after alias normalization",
                matches.shape[1],
                col,
            )
        else:
            merged[col] = matches.iloc[:, 0]
        seen.add(col)

    return merged


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
    
    try:
        df = pd.read_csv(input_file, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read CSV file {input_file}: {e}")
        raise
    
    initial_rows = len(df)
    logger.info(f"Loaded {initial_rows} raw rows with columns: {list(df.columns)}")
    
    # Normalize column names
    original_columns = list(df.columns)
    df.columns = [normalize_column_name(c) for c in df.columns]
    df = _coalesce_duplicate_columns(df)
    normalized_columns = list(df.columns)
    
    # Log column mapping
    column_mapping = dict(zip(original_columns, normalized_columns))
    logger.debug(f"Column mapping: {column_mapping}")
    
    # Validate required columns
    required = ["date", "symbol", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.warning(f"Missing required columns: {missing}")
        logger.info(f"Available columns: {list(df.columns)}")
        # Try to infer missing columns
        if "date" in missing and "date" not in df.columns:
            # Look for date-like columns
            date_candidates = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]
            if date_candidates:
                logger.info(f"Using '{date_candidates[0]}' as date column")
                df = df.rename(columns={date_candidates[0]: "date"})
                missing.remove("date")
        
        if "symbol" in missing and "symbol" not in df.columns:
            # Look for symbol-like columns
            symbol_candidates = [c for c in df.columns if any(term in c.lower() for term in ["symbol", "code", "stock", "ticker"])]
            if symbol_candidates:
                logger.info(f"Using '{symbol_candidates[0]}' as symbol column")
                df = df.rename(columns={symbol_candidates[0]: "symbol"})
                missing.remove("symbol")
        
        if "close" in missing and "close" not in df.columns:
            # Look for price-like columns
            price_candidates = [c for c in df.columns if any(term in c.lower() for term in ["close", "ltp", "price", "last"])]
            if price_candidates:
                logger.info(f"Using '{price_candidates[0]}' as close column")
                df = df.rename(columns={price_candidates[0]: "close"})
                missing.remove("close")
        
        if missing:
            raise ValueError(f"Missing required columns after inference: {missing}")
    
    # Ensure all standard columns exist
    for col in STANDARD_OHLCV_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Merge metadata from company master
    from nepsense.config import METADATA_DIR
    master_path = METADATA_DIR / "company_master.csv"
    if master_path.exists():
        try:
            master_df = pd.read_csv(master_path)
            master_df["symbol"] = master_df["symbol"].astype(str).str.strip().str.upper()
            
            # Clean symbol column in current df for merging
            df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
            
            # For each row, if company_name or sector is missing, fill from master
            # Create a mapping for faster lookup
            name_map = dict(zip(master_df["symbol"], master_df["company_name"]))
            sector_map = dict(zip(master_df["symbol"], master_df["sector"]))
            
            def fill_metadata(row):
                symbol = row["symbol"]
                if pd.isna(row.get("company_name")) or not str(row.get("company_name")).strip():
                    row["company_name"] = name_map.get(symbol, row.get("company_name"))
                if pd.isna(row.get("sector")) or not str(row.get("sector")).strip():
                    row["sector"] = sector_map.get(symbol, row.get("sector"))
                return row
            
            df = df.apply(fill_metadata, axis=1)
            logger.info("Merged company metadata from master list")
        except Exception as e:
            logger.warning(f"Failed to merge company metadata: {e}")

    source_label = next(
        (part.removeprefix("source=") for part in input_file.parts if part.startswith("source=")),
        None,
    )
    if source_label:
        missing_source = df["source"].isna() | (df["source"].astype(str).str.strip() == "")
        df.loc[missing_source, "source"] = source_label
    
    # Select only standard columns
    df = df[STANDARD_OHLCV_COLUMNS]
    
    # Clean and validate data types
    try:
        # Handle date column
        if df["date"].notna().any():
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        else:
            logger.warning("Date column is empty, will be filled with collection date")
            
        # Clean symbol column
        df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
        
        # Clean numeric columns
        numeric_cols = ["open", "high", "low", "close", "volume", "turnover", "transactions"]
        for col in numeric_cols:
            if col in df.columns and df[col].notna().any():
                # Remove commas and other formatting
                df[col] = df[col].astype(str).str.replace(",", "").str.replace(" ", "")
                # Convert to numeric, coercing errors
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "source_confidence" in df.columns:
            df["source_confidence"] = pd.to_numeric(df["source_confidence"], errors="coerce")
            sharesansar_rows = (
                df["source"].astype(str).str.contains("sharesansar", case=False, na=False)
                & df["source_confidence"].isna()
            )
            df.loc[sharesansar_rows, "source_confidence"] = 0.90
            archive_rows = df["source"].notna() & df["source_confidence"].isna()
            df.loc[archive_rows, "source_confidence"] = SOURCE_CONFIDENCE_SCALE["archive"]
    
    except Exception as e:
        logger.error(f"Error during data cleaning: {e}")
        raise
    
    # Remove rows with missing critical data
    before_cleaning = len(df)
    df = df.dropna(subset=["symbol", "close"])
    df = df[df["symbol"].str.len() > 0]  # Remove empty symbols
    
    # Remove duplicate symbol-date pairs
    df = df.drop_duplicates(subset=["date", "symbol"])
    
    # Sort by date and symbol
    df = df.sort_values(["date", "symbol"])
    
    # Final validation
    final_rows = len(df)
    removed_rows = before_cleaning - final_rows
    
    if final_rows == 0:
        raise ValueError(f"No valid data rows remaining after cleaning (removed {removed_rows} invalid rows)")
    
    logger.info(
        f"Normalized to {final_rows} valid rows "
        f"(removed {removed_rows} invalid/duplicate rows from {initial_rows} raw rows)"
    )
    
    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
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
    files = sorted(
        file
        for file in input_root.rglob("*.csv")
        if not any(part.startswith(".") for part in file.relative_to(input_root).parts)
    )
    logger.info(f"Found {len(files)} raw files to normalize")
    
    normalized = 0
    for input_file in files:
        try:
            date_str = input_file.stem
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
                logger.info("Skipping raw CSV without YYYY-MM-DD filename: %s", input_file)
                continue

            relative_parts = input_file.relative_to(input_root).parts
            if relative_parts and relative_parts[0].startswith("source="):
                year, month, _ = date_str.split("-")
                output_file = output_root / relative_parts[0] / year / month / input_file.name
                output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_file = dated_output_path(output_root, date_str)

            normalize_file(input_file, output_file)
            normalized += 1
        except Exception as e:
            logger.error(f"Failed to normalize {input_file}: {e}")
            continue
    
    logger.info(f"Successfully normalized {normalized} files")
    return normalized
