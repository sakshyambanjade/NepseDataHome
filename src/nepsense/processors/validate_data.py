"""Data quality validation and reporting."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from nepsense.config import NORMALIZED_DIR, QUALITY_DIR
from nepsense.utils.numbers import validate_ohlc

logger = logging.getLogger(__name__)


def validate_file(file: Path) -> dict:
    """Validate a single price data file.
    
    Checks:
    - Required columns
    - No duplicates
    - OHLC integrity
    - Valid dates
    - Reasonable values
    
    Args:
        file: CSV file path
    
    Returns:
        Validation report dict
    """
    df = pd.read_csv(file)
    errors = []
    warnings = []

    # Required columns
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

    # Check for duplicates
    duplicates = df.duplicated(subset=["date", "symbol"]).sum()
    if duplicates > 0:
        errors.append(f"Duplicate date-symbol pairs: {duplicates}")

    # Check for future dates
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    today = pd.Timestamp("today")
    future = (df["date_dt"] > today).sum()
    if future > 0:
        errors.append(f"Future dates found: {future} rows")

    # OHLC validation
    ohlc_result = validate_ohlc(df)
    errors.extend(ohlc_result["errors"])
    warnings.extend(ohlc_result["warnings"])

    # Check for data with no source
    if "source" in df.columns:
        no_source = df["source"].isna().sum()
        if no_source > 0:
            warnings.append(f"Rows missing source: {no_source}")

    # Check for unusual price movements (>90% without corporate action)
    if "close" in df.columns and len(df) > 1:
        df["pct_change"] = df.groupby("symbol")["close"].pct_change().abs()
        extreme = (df["pct_change"] > 0.9).sum()
        if extreme > 0:
            warnings.append(
                f"Extreme price movements (>90%) found in {extreme} rows "
                "(verify corporate actions)"
            )

    return {
        "file": str(file),
        "rows": len(df),
        "errors": errors,
        "warnings": warnings,
    }


def validate_all(
    input_root: Path = NORMALIZED_DIR,
    fail_on_error: bool = False,
) -> dict:
    """Validate all data files and generate report.
    
    Args:
        input_root: Root directory with files to validate
        fail_on_error: If True, raise error if any validation fails
    
    Returns:
        Comprehensive validation report
    """
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(input_root.glob("*/*/*.csv"))
    logger.info(f"Validating {len(files)} files...")

    reports = []
    for file in files:
        try:
            report = validate_file(file)
            reports.append(report)
        except Exception as e:
            logger.error(f"Error validating {file}: {e}")
            reports.append({
                "file": str(file),
                "rows": 0,
                "errors": [f"Validation exception: {str(e)}"],
                "warnings": [],
            })

    # Aggregate results
    total_errors = sum(len(r["errors"]) for r in reports)
    total_warnings = sum(len(r["warnings"]) for r in reports)

    summary = {
        "files_checked": len(files),
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "reports": reports,
    }

    # Save JSON report
    report_path = QUALITY_DIR / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved validation report to {report_path}")

    # Save CSV with issues
    issue_rows = []
    for report in reports:
        for error in report["errors"]:
            issue_rows.append({
                "file": report["file"],
                "level": "ERROR",
                "message": error,
            })
        for warning in report["warnings"]:
            issue_rows.append({
                "file": report["file"],
                "level": "WARNING",
                "message": warning,
            })

    if issue_rows:
        issues_df = pd.DataFrame(issue_rows)
        issues_path = QUALITY_DIR / "validation_issues.csv"
        issues_df.to_csv(issues_path, index=False)
        logger.info(f"Saved {len(issue_rows)} issues to {issues_path}")

    # Log summary
    logger.info(
        f"Validation complete: {total_errors} errors, {total_warnings} warnings"
    )

    if fail_on_error and total_errors > 0:
        raise ValueError(f"Validation failed with {total_errors} errors")

    return summary


def generate_symbol_coverage_report(
    input_root: Path = NORMALIZED_DIR,
) -> pd.DataFrame:
    """Generate symbol coverage report showing trading dates per symbol.
    
    Args:
        input_root: Root directory with normalized files
    
    Returns:
        DataFrame with symbol coverage statistics
    """
    files = sorted(input_root.glob("*/*/*.csv"))
    
    coverage = {}
    for file in files:
        df = pd.read_csv(file)
        for symbol in df["symbol"].unique():
            if symbol not in coverage:
                coverage[symbol] = {"first_date": None, "last_date": None, "days": 0}
            
            symbol_df = df[df["symbol"] == symbol]
            date = symbol_df["date"].iloc[0] if len(symbol_df) > 0 else None
            
            if date:
                if coverage[symbol]["first_date"] is None:
                    coverage[symbol]["first_date"] = date
                coverage[symbol]["last_date"] = date
                coverage[symbol]["days"] += len(symbol_df)
    
    coverage_df = pd.DataFrame(coverage).T.reset_index()
    coverage_df.columns = ["symbol", "first_date", "last_date", "trading_days"]
    coverage_df = coverage_df.sort_values("trading_days", ascending=False)
    
    # Save
    report_path = QUALITY_DIR / "symbol_coverage.csv"
    coverage_df.to_csv(report_path, index=False)
    logger.info(f"Saved symbol coverage to {report_path}")
    
    return coverage_df
