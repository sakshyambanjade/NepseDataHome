"""Utility functions for numeric data processing."""

from __future__ import annotations

import pandas as pd


def to_number(series: pd.Series, errors: str = "coerce") -> pd.Series:
    """Convert series to numeric, handling common formatting variations.
    
    Args:
        series: Input series with mixed numeric formats
        errors: How to handle errors ('coerce' = NaN, 'raise' = error)
    
    Returns:
        Numeric series
    """
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)  # Remove commas
        .str.replace("Rs.", "", regex=False)  # Remove currency
        .str.replace("रु", "", regex=False)  # Remove Nepali currency
        .str.replace("%", "", regex=False)  # Remove percentage
        .str.replace("-", "", regex=False)  # Remove dash (missing)
        .replace({"": None, "nan": None, "None": None, "N/A": None})
    )
    return pd.to_numeric(cleaned, errors=errors)


def validate_ohlc(df: pd.DataFrame) -> dict[str, list[str]]:
    """Validate OHLC data integrity.
    
    Returns dict with 'errors' and 'warnings' lists.
    """
    errors = []
    warnings = []

    # Check required columns
    required = ["open", "high", "low", "close"]
    for col in required:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
    
    if errors:
        return {"errors": errors, "warnings": warnings}

    # Strict High check: high >= max(open, close, low)
    # Using a small epsilon for floating point comparisons
    max_other = df[["open", "close", "low"]].max(axis=1)
    bad_high = df[df["high"] < (max_other - 0.001)]
    if len(bad_high) > 0:
        errors.append(f"High < max(Open, Close, Low) in {len(bad_high)} rows")

    # Strict Low check: low <= min(open, close, high)
    min_other = df[["open", "close", "high"]].min(axis=1)
    bad_low = df[df["low"] > (min_other + 0.001)]
    if len(bad_low) > 0:
        errors.append(f"Low > min(Open, Close, High) in {len(bad_low)} rows")

    # Volume >= 0
    if "volume" in df.columns:
        bad_volume = df[df["volume"] < 0]
        if len(bad_volume) > 0:
            errors.append(f"Negative volume in {len(bad_volume)} rows")

    # Turnover >= 0
    if "turnover" in df.columns:
        bad_turnover = df[df["turnover"] < 0]
        if len(bad_turnover) > 0:
            errors.append(f"Negative turnover in {len(bad_turnover)} rows")
            
    # Transactions >= 0
    if "transactions" in df.columns:
        bad_trans = df[df["transactions"] < 0]
        if len(bad_trans) > 0:
            errors.append(f"Negative transactions in {len(bad_trans)} rows")

    return {"errors": errors, "warnings": warnings}
