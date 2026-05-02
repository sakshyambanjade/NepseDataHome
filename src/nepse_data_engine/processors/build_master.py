from __future__ import annotations

from pathlib import Path
import pandas as pd
import duckdb

from nepse_data_engine.config import CLEAN_DIR, ADJUSTED_DIR, MASTER_DIR

def _read_all_csv(root: Path) -> pd.DataFrame:
    files = sorted(root.glob("*/*/*.csv"))

    if not files:
        raise RuntimeError(f"No CSV files found in {root}")

    frames = []

    for file in files:
        df = pd.read_csv(file)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    if "date" in combined.columns and "symbol" in combined.columns:
        combined = combined.drop_duplicates(subset=["date", "symbol"])
        combined = combined.sort_values(["date", "symbol"])

    return combined

def build_master(use_adjusted: bool = False) -> dict[str, str]:
    source_root = ADJUSTED_DIR if use_adjusted else CLEAN_DIR
    MASTER_DIR.mkdir(parents=True, exist_ok=True)

    master = _read_all_csv(source_root)

    name = "nepse_all_companies_adjusted_daily" if use_adjusted else "nepse_all_companies_daily"

    csv_path = MASTER_DIR / f"{name}.csv"
    parquet_path = MASTER_DIR / f"{name}.parquet"
    duckdb_path = MASTER_DIR / f"{name}.duckdb"

    master.to_csv(csv_path, index=False)
    master.to_parquet(parquet_path, index=False)

    con = duckdb.connect(str(duckdb_path))
    con.execute("CREATE OR REPLACE TABLE daily_prices AS SELECT * FROM master")
    con.close()

    return {
        "csv": str(csv_path),
        "parquet": str(parquet_path),
        "duckdb": str(duckdb_path),
        "rows": str(len(master)),
    }
