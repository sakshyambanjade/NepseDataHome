"""Storage and export utilities."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import duckdb
import pandas as pd

from nepsense.config import ADJUSTED_DIR, MASTER_DIR, NORMALIZED_DIR

logger = logging.getLogger(__name__)


def _read_all_csv(root: Path) -> pd.DataFrame:
    """Read and concatenate all CSV files from directory tree.
    
    Args:
        root: Root directory with year/month/date structure
    
    Returns:
        Combined DataFrame
    """
    files = sorted(root.glob("*/*/*.csv"))

    if not files:
        raise RuntimeError(f"No CSV files found in {root}")

    logger.info(f"Reading {len(files)} files from {root}")
    frames = []

    for file in files:
        try:
            df = pd.read_csv(file)
            frames.append(df)
        except Exception as e:
            logger.warning(f"Failed to read {file}: {e}")
            continue

    combined = pd.concat(frames, ignore_index=True)

    # Remove duplicates and sort
    if "date" in combined.columns and "symbol" in combined.columns:
        combined = combined.drop_duplicates(subset=["date", "symbol"])
        combined = combined.sort_values(["date", "symbol"])

    logger.info(f"Combined {len(combined)} rows from {len(files)} files")
    return combined


def build_master(use_adjusted: bool = False) -> dict[str, str]:
    """Build master dataset in all formats.
    
    Creates:
    - CSV (full dataset)
    - Parquet (compressed, faster)
    - DuckDB (queryable database)
    
    Args:
        use_adjusted: If True, use adjusted data; else use normalized
    
    Returns:
        Dict with paths to created files
    """
    source_root = ADJUSTED_DIR if use_adjusted else NORMALIZED_DIR
    MASTER_DIR.mkdir(parents=True, exist_ok=True)

    master = _read_all_csv(source_root)
    dataset_type = "adjusted" if use_adjusted else "normalized"
    logger.info(f"Building master {dataset_type} dataset...")

    # Determine output filenames
    if use_adjusted:
        base_name = "nepsense_adjusted_prices"
    else:
        base_name = "nepsense_prices"

    csv_path = MASTER_DIR / f"{base_name}.csv"
    parquet_path = MASTER_DIR / f"{base_name}.parquet"
    duckdb_path = MASTER_DIR / f"{base_name}.duckdb"

    # Save CSV
    master.to_csv(csv_path, index=False)
    logger.info(f"Saved CSV: {csv_path} ({csv_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # Save Parquet
    master.to_parquet(parquet_path, index=False)
    logger.info(f"Saved Parquet: {parquet_path} ({parquet_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # Save DuckDB
    con = duckdb.connect(str(duckdb_path))
    con.execute(f"CREATE OR REPLACE TABLE {base_name} AS SELECT * FROM master")
    con.close()
    logger.info(f"Saved DuckDB: {duckdb_path} ({duckdb_path.stat().st_size / 1024 / 1024:.2f} MB)")

    return {
        "csv": str(csv_path),
        "parquet": str(parquet_path),
        "duckdb": str(duckdb_path),
        "rows": str(len(master)),
        "dataset_type": dataset_type,
    }


def create_manifest() -> dict:
    """Create manifest of all data products.
    
    Returns:
        Manifest dict
    """
    MASTER_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": "0.2.0",
        "generated": pd.Timestamp.now().isoformat(),
        "datasets": {
            "prices": {
                "file": "nepsense_prices.csv",
                "parquet": "nepsense_prices.parquet",
                "duckdb": "nepsense.duckdb",
                "description": "Normalized daily OHLCV data",
            },
            "adjusted_prices": {
                "file": "nepsense_adjusted_prices.csv",
                "parquet": "nepsense_adjusted_prices.parquet",
                "duckdb": "nepsense_adjusted.duckdb",
                "description": "Corporate-action adjusted daily prices",
            },
        },
    }

    manifest_path = MASTER_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Created manifest at {manifest_path}")
    return manifest
