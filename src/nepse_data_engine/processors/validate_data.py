from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from nepse_data_engine.config import CLEAN_DIR, QUALITY_DIR

def validate_file(file: Path) -> dict:
    df = pd.read_csv(file)
    errors = []
    warnings = []

    required = ["date", "symbol", "close"]

    for col in required:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    if errors:
        return {
            "file": str(file),
            "rows": len(df),
            "errors": errors,
            "warnings": warnings,
        }

    duplicates = int(df.duplicated(subset=["date", "symbol"]).sum())

    if duplicates > 0:
        errors.append(f"Duplicate date-symbol rows: {duplicates}")

    for col in ["open", "high", "low", "close", "volume", "turnover"]:
        if col in df.columns:
            null_count = int(df[col].isna().sum())
            if null_count > 0:
                warnings.append(f"{col} null values: {null_count}")

    if {"high", "low"}.issubset(df.columns):
        bad_high_low = df[df["high"].notna() & df["low"].notna() & (df["high"] < df["low"])]
        if len(bad_high_low) > 0:
            errors.append(f"Rows with high < low: {len(bad_high_low)}")

    if {"close", "high", "low"}.issubset(df.columns):
        bad_close = df[
            df["close"].notna()
            & df["high"].notna()
            & df["low"].notna()
            & ((df["close"] > df["high"]) | (df["close"] < df["low"]))
        ]
        if len(bad_close) > 0:
            warnings.append(f"Rows with close outside high-low range: {len(bad_close)}")

    if "volume" in df.columns:
        bad_volume = df[df["volume"].notna() & (df["volume"] < 0)]
        if len(bad_volume) > 0:
            errors.append(f"Rows with negative volume: {len(bad_volume)}")

    return {
        "file": str(file),
        "rows": len(df),
        "errors": errors,
        "warnings": warnings,
    }

def validate_all(fail_on_error: bool = True) -> dict:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(CLEAN_DIR.glob("*/*/*.csv"))
    reports = [validate_file(file) for file in files]

    total_errors = sum(len(r["errors"]) for r in reports)
    total_warnings = sum(len(r["warnings"]) for r in reports)

    summary = {
        "files_checked": len(files),
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "reports": reports,
    }

    report_path = QUALITY_DIR / "validation_report.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    rows = []

    for report in reports:
        for error in report["errors"]:
            rows.append({"file": report["file"], "level": "error", "message": error})
        for warning in report["warnings"]:
            rows.append({"file": report["file"], "level": "warning", "message": warning})

    pd.DataFrame(rows).to_csv(QUALITY_DIR / "validation_issues.csv", index=False)

    if fail_on_error and total_errors > 0:
        raise ValueError(f"Validation failed with {total_errors} errors.")

    return summary
