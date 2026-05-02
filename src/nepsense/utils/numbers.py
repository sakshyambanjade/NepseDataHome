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

    # High >= Low
    bad_high_low = df[
        df["high"].notna() & df["low"].notna() & (df["high"] < df["low"])
    ]
    if len(bad_high_low) > 0:
        errors.append(f"High < Low in {len(bad_high_low)} rows")

    # Close between High and Low
    bad_close = df[
        df["close"].notna()
        & df["high"].notna()
        & df["low"].notna()
        & ((df["close"] > df["high"]) | (df["close"] < df["low"]))
    ]
    if len(bad_close) > 0:
        warnings.append(f"Close outside High-Low range in {len(bad_close)} rows")

    # Volume >= 0
    if "volume" in df.columns:
        bad_volume = df[df["volume"].notna() & (df["volume"] < 0)]
        if len(bad_volume) > 0:
            errors.append(f"Negative volume in {len(bad_volume)} rows")

    # Turnover >= 0
    if "turnover" in df.columns:
        bad_turnover = df[df["turnover"].notna() & (df["turnover"] < 0)]
        if len(bad_turnover) > 0:
            errors.append(f"Negative turnover in {len(bad_turnover)} rows")

    return {"errors": errors, "warnings": warnings}
