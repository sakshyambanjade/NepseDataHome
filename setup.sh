#!/usr/bin/env bash
set -e

PROJECT_NAME="nepse-open-data-engine"

mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

mkdir -p src/nepse_data_engine/collectors
mkdir -p src/nepse_data_engine/processors
mkdir -p src/nepse_data_engine/exporters
mkdir -p src/nepse_data_engine/utils
mkdir -p tests
mkdir -p data/raw
mkdir -p data/clean
mkdir -p data/adjusted
mkdir -p data/master
mkdir -p data/quality
mkdir -p data/corporate_actions
mkdir -p .circleci

touch src/nepse_data_engine/__init__.py
touch src/nepse_data_engine/collectors/__init__.py
touch src/nepse_data_engine/processors/__init__.py
touch src/nepse_data_engine/exporters/__init__.py
touch src/nepse_data_engine/utils/__init__.py

cat > pyproject.toml <<'TOML'
[project]
name = "nepse-open-data-engine"
version = "0.1.0"
description = "Open-source NEPSE historical data collector, cleaner, validator, and exporter."
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
    "html5lib>=1.1",
    "pyarrow>=14.0.0",
    "duckdb>=0.9.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pytest>=7.0.0"
]

[project.scripts]
nepse-data = "nepse_data_engine.cli:app"

[tool.setuptools.packages.find]
where = ["src"]
TOML

cat > requirements.txt <<'REQ'
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
html5lib>=1.1
pyarrow>=14.0.0
duckdb>=0.9.0
typer>=0.9.0
rich>=13.0.0
pytest>=7.0.0
REQ

cat > README.md <<'MD'
# NEPSE Open Data Engine

Open-source NEPSE historical data collector, cleaner, validator, and exporter.

## Features

- Daily NEPSE data collection
- Historical archive import
- Daily CSV folder structure
- Cleaned data generation
- Experimental adjusted-price generation
- Master CSV export
- Master Parquet export
- DuckDB export
- Data validation reports
- CircleCI automation

## Folder Format

```text
data/raw/YYYY/MM/YYYY-MM-DD.csv
data/clean/YYYY/MM/YYYY-MM-DD.csv
data/adjusted/YYYY/MM/YYYY-MM-DD.csv
data/master/nepse_all_companies_daily.csv
data/master/nepse_all_companies_daily.parquet
data/master/nepse_all_companies_daily.duckdb
```

## Install

```bash
pip install -e .
```

## Commands

Collect today's data:

```bash
nepse-data collect-daily
```

Clean today's data:

```bash
nepse-data clean --date today
```

Import old CSV archive:

```bash
nepse-data import-archive --archive-dir path/to/archive
```

Clean all raw files:

```bash
nepse-data clean-all
```

Generate adjusted files:

```bash
nepse-data adjust-all
```

Build master dataset:

```bash
nepse-data build-master
```

Validate data:

```bash
nepse-data validate
```

Full daily run:

```bash
nepse-data daily-run
```

## Data Status

* Raw data: source snapshot
* Clean data: normalized daily OHLCV-style format
* Adjusted data: experimental unless corporate actions are verified

## Important

Corporate-action adjustment needs verified bonus/right/dividend data.

Put verified actions inside:

```text
data/corporate_actions/corporate_actions.csv
```

Format:

```csv
symbol,book_close_date,action_type,bonus_percent,cash_dividend_percent,right_ratio,issue_price,notes
NABIL,2024-12-10,bonus,10,0,,,10 percent bonus
```

MD

cat > src/nepse_data_engine/config.py <<'PY'
from pathlib import Path

PROJECT_ROOT = Path.cwd()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
ADJUSTED_DIR = DATA_DIR / "adjusted"
MASTER_DIR = DATA_DIR / "master"
QUALITY_DIR = DATA_DIR / "quality"
CORPORATE_ACTIONS_DIR = DATA_DIR / "corporate_actions"

TODAY_SHARE_PRICE_URL = "https://www.sharesansar.com/today-share-price"

STANDARD_COLUMNS = [
"date",
"symbol",
"company_name",
"sector",
"open",
"high",
"low",
"close",
"volume",
"turnover",
"transactions",
"source",
]
PY

cat > src/nepse_data_engine/utils/dates.py <<'PY'
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import re

NEPAL_TZ = ZoneInfo("Asia/Kathmandu")

def today_nepal() -> str:
    return datetime.now(NEPAL_TZ).date().isoformat()

def resolve_date(date_value: str | None) -> str:
    if date_value is None or date_value.lower() == "today":
        return today_nepal()
    return date_value

def dated_output_path(root: Path, date_str: str) -> Path:
    year, month, _ = date_str.split("-")
    output_dir = root / year / month
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{date_str}.csv"

def extract_date_from_filename(path: Path) -> str | None:
    text = path.stem

    patterns = [
        r"(\d{4})-(\d{2})-(\d{2})",
        r"(\d{4})_(\d{2})_(\d{2})",
        r"(\d{4})\.(\d{2})\.(\d{2})",
        r"(\d{4})(\d{2})(\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            y, m, d = match.groups()
            return f"{y}-{m}-{d}"

    return None
PY

cat > src/nepse_data_engine/utils/numbers.py <<'PY'
from __future__ import annotations

import pandas as pd

def to_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.replace("रु", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace("-", "", regex=False)
        .replace({"": None, "nan": None, "None": None})
    )
    return pd.to_numeric(cleaned, errors="coerce")
PY

cat > src/nepse_data_engine/collectors/sharesansar_daily.py <<'PY'
from __future__ import annotations

from pathlib import Path
import pandas as pd
import requests

from nepse_data_engine.config import RAW_DIR, TODAY_SHARE_PRICE_URL
from nepse_data_engine.utils.dates import dated_output_path, resolve_date

def _choose_market_table(tables: list[pd.DataFrame]) -> pd.DataFrame:
    for table in tables:
        cols = [str(c).lower().strip() for c in table.columns]

        has_symbol = any("symbol" in c for c in cols)
        has_price = any(c in cols for c in ["ltp", "close", "last traded price"]) or any("ltp" in c for c in cols)

        if has_symbol and has_price:
            return table

    if not tables:
        raise RuntimeError("No HTML tables found.")

    return tables[0]

def collect_daily(date: str | None = None, output_root: Path = RAW_DIR) -> Path:
    date_str = resolve_date(date)
    output_file = dated_output_path(output_root, date_str)

    response = requests.get(
        TODAY_SHARE_PRICE_URL,
        timeout=40,
        headers={
            "User-Agent": "nepse-open-data-engine/0.1 (+https://github.com/yourusername/nepse-open-data-engine)"
        },
    )
    response.raise_for_status()

    tables = pd.read_html(response.text)
    df = _choose_market_table(tables)

    df["date"] = date_str
    df["source"] = TODAY_SHARE_PRICE_URL

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

    return output_file
PY

cat > src/nepse_data_engine/collectors/historical_importer.py <<'PY'
from __future__ import annotations

from pathlib import Path
import pandas as pd

from nepse_data_engine.config import RAW_DIR
from nepse_data_engine.utils.dates import dated_output_path, extract_date_from_filename

def import_archive(archive_dir: str, output_root: Path = RAW_DIR) -> int:
    archive_path = Path(archive_dir)

    if not archive_path.exists():
        raise FileNotFoundError(f"Archive directory not found: {archive_dir}")

    files = sorted(list(archive_path.rglob("*.csv")))
    imported = 0

    for file in files:
        date_str = extract_date_from_filename(file)

        if not date_str:
            continue

        try:
            df = pd.read_csv(file)
        except Exception:
            continue

        df["date"] = date_str

        if "source" not in df.columns:
            df["source"] = str(file)

        output_file = dated_output_path(output_root, date_str)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)

        imported += 1

    return imported
PY

cat > src/nepse_data_engine/processors/clean_daily.py <<'PY'
from __future__ import annotations

from pathlib import Path
import re
import pandas as pd

from nepse_data_engine.config import RAW_DIR, CLEAN_DIR, STANDARD_COLUMNS
from nepse_data_engine.utils.dates import dated_output_path, resolve_date
from nepse_data_engine.utils.numbers import to_number

COLUMN_ALIASES = {
    "symbol": "symbol",
    "stock symbol": "symbol",
    "company": "company_name",
    "company name": "company_name",
    "name": "company_name",
    "security name": "company_name",
    "sector": "sector",
    "open": "open",
    "opening price": "open",
    "high": "high",
    "max price": "high",
    "low": "low",
    "min price": "low",
    "close": "close",
    "closing price": "close",
    "ltp": "close",
    "last traded price": "close",
    "last transaction price": "close",
    "volume": "volume",
    "vol": "volume",
    "qty": "volume",
    "quantity": "volume",
    "traded qty": "volume",
    "traded quantity": "volume",
    "turnover": "turnover",
    "amount": "turnover",
    "total amount": "turnover",
    "transactions": "transactions",
    "trans": "transactions",
    "no of transactions": "transactions",
    "date": "date",
    "source": "source",
}

def normalize_column_name(name: object) -> str:
    text = str(name).strip().lower()
    text = text.replace(".", "")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return COLUMN_ALIASES.get(text, text)

def clean_price_file(input_file: Path, output_file: Path) -> Path:
    df = pd.read_csv(input_file)
    df.columns = [normalize_column_name(c) for c in df.columns]

    if "date" not in df.columns:
        raise ValueError(f"Missing date column in {input_file}")

    if "symbol" not in df.columns:
        raise ValueError(f"Missing symbol column in {input_file}")

    if "close" not in df.columns:
        raise ValueError(f"Missing close/LTP column in {input_file}")

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = None

    numeric_cols = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover",
        "transactions",
    ]

    for col in numeric_cols:
        df[col] = to_number(df[col])

    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df["company_name"] = df["company_name"].astype(str).replace({"nan": None})
    df["sector"] = df["sector"].astype(str).replace({"nan": None})

    df = df[STANDARD_COLUMNS]
    df = df.dropna(subset=["date", "symbol", "close"])
    df = df[df["symbol"].str.len() > 0]
    df = df.drop_duplicates(subset=["date", "symbol"])
    df = df.sort_values(["date", "symbol"])

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

    return output_file

def clean_daily(date: str | None = None) -> Path:
    date_str = resolve_date(date)
    input_file = dated_output_path(RAW_DIR, date_str)
    output_file = dated_output_path(CLEAN_DIR, date_str)

    if not input_file.exists():
        raise FileNotFoundError(f"Raw file not found: {input_file}")

    return clean_price_file(input_file, output_file)

def clean_all() -> int:
    files = sorted(RAW_DIR.glob("*/*/*.csv"))
    cleaned = 0

    for input_file in files:
        date_str = input_file.stem
        output_file = dated_output_path(CLEAN_DIR, date_str)
        clean_price_file(input_file, output_file)
        cleaned += 1

    return cleaned
PY

cat > src/nepse_data_engine/processors/adjust_prices.py <<'PY'
from __future__ import annotations

from pathlib import Path
import pandas as pd

from nepse_data_engine.config import CLEAN_DIR, ADJUSTED_DIR, CORPORATE_ACTIONS_DIR
from nepse_data_engine.utils.dates import dated_output_path

CORPORATE_ACTIONS_FILE = CORPORATE_ACTIONS_DIR / "corporate_actions.csv"

def ensure_corporate_action_template() -> None:
    CORPORATE_ACTIONS_DIR.mkdir(parents=True, exist_ok=True)

    if CORPORATE_ACTIONS_FILE.exists():
        return

    template = pd.DataFrame(
        columns=[
            "symbol",
            "book_close_date",
            "action_type",
            "bonus_percent",
            "cash_dividend_percent",
            "right_ratio",
            "issue_price",
            "notes",
        ]
    )
    template.to_csv(CORPORATE_ACTIONS_FILE, index=False)

def load_corporate_actions() -> pd.DataFrame:
    ensure_corporate_action_template()

    actions = pd.read_csv(CORPORATE_ACTIONS_FILE)

    if actions.empty:
        return actions

    actions["symbol"] = actions["symbol"].astype(str).str.strip().str.upper()
    actions["book_close_date"] = pd.to_datetime(actions["book_close_date"], errors="coerce")

    for col in ["bonus_percent", "cash_dividend_percent", "issue_price"]:
        if col in actions.columns:
            actions[col] = pd.to_numeric(actions[col], errors="coerce").fillna(0)

    return actions.dropna(subset=["symbol", "book_close_date"])

def apply_adjustments(df: pd.DataFrame, actions: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df["adjustment_factor"] = 1.0

    if not actions.empty:
        for _, action in actions.iterrows():
            symbol = str(action["symbol"]).upper()
            book_close_date = action["book_close_date"]
            bonus_percent = float(action.get("bonus_percent", 0) or 0)

            if bonus_percent <= 0:
                continue

            factor = 1.0 + bonus_percent / 100.0

            mask = (df["symbol"] == symbol) & (df["date_dt"] < book_close_date)
            df.loc[mask, "adjustment_factor"] *= factor

    price_cols = ["open", "high", "low", "close"]

    for col in price_cols:
        df[f"adjusted_{col}"] = df[col] / df["adjustment_factor"]

    df = df.drop(columns=["date_dt"])

    return df

def adjust_file(input_file: Path, output_file: Path, actions: pd.DataFrame) -> Path:
    df = pd.read_csv(input_file)
    adjusted = apply_adjustments(df, actions)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    adjusted.to_csv(output_file, index=False)

    return output_file

def adjust_all() -> int:
    actions = load_corporate_actions()
    files = sorted(CLEAN_DIR.glob("*/*/*.csv"))

    adjusted_count = 0

    for input_file in files:
        date_str = input_file.stem
        output_file = dated_output_path(ADJUSTED_DIR, date_str)
        adjust_file(input_file, output_file, actions)
        adjusted_count += 1

    return adjusted_count
PY

cat > src/nepse_data_engine/processors/build_master.py <<'PY'
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
PY

cat > src/nepse_data_engine/processors/validate_data.py <<'PY'
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
PY

cat > src/nepse_data_engine/cli.py <<'PY'
from __future__ import annotations

import typer
from rich.console import Console

from nepse_data_engine.collectors.sharesansar_daily import collect_daily as collect_daily_func
from nepse_data_engine.collectors.historical_importer import import_archive as import_archive_func
from nepse_data_engine.processors.clean_daily import clean_daily as clean_daily_func
from nepse_data_engine.processors.clean_daily import clean_all as clean_all_func
from nepse_data_engine.processors.adjust_prices import adjust_all as adjust_all_func
from nepse_data_engine.processors.build_master import build_master as build_master_func
from nepse_data_engine.processors.validate_data import validate_all as validate_all_func

app = typer.Typer(help="NEPSE Open Data Engine")
console = Console()

@app.command()
def collect_daily(date: str = "today"):
    output = collect_daily_func(date=date)
    console.print(f"[green]Raw daily data saved:[/green] {output}")

@app.command()
def import_archive(archive_dir: str):
    count = import_archive_func(archive_dir)
    console.print(f"[green]Imported raw archive files:[/green] {count}")

@app.command()
def clean(date: str = "today"):
    output = clean_daily_func(date=date)
    console.print(f"[green]Clean data saved:[/green] {output}")

@app.command()
def clean_all():
    count = clean_all_func()
    console.print(f"[green]Cleaned files:[/green] {count}")

@app.command()
def adjust_all():
    count = adjust_all_func()
    console.print(f"[green]Adjusted files generated:[/green] {count}")

@app.command()
def build_master(adjusted: bool = False):
    result = build_master_func(use_adjusted=adjusted)
    console.print("[green]Master dataset created[/green]")
    console.print(result)

@app.command()
def validate(fail_on_error: bool = True):
    result = validate_all_func(fail_on_error=fail_on_error)
    console.print("[green]Validation complete[/green]")
    console.print(
        {
            "files_checked": result["files_checked"],
            "total_errors": result["total_errors"],
            "total_warnings": result["total_warnings"],
        }
    )

@app.command()
def daily_run():
    raw = collect_daily_func(date="today")
    console.print(f"[green]Collected:[/green] {raw}")

    clean = clean_daily_func(date="today")
    console.print(f"[green]Cleaned:[/green] {clean}")

    adjusted_count = adjust_all_func()
    console.print(f"[green]Adjusted files:[/green] {adjusted_count}")

    master = build_master_func(use_adjusted=False)
    console.print(f"[green]Master clean dataset:[/green] {master}")

    adjusted_master = build_master_func(use_adjusted=True)
    console.print(f"[green]Master adjusted dataset:[/green] {adjusted_master}")

    validation = validate_all_func(fail_on_error=True)
    console.print(
        f"[green]Validation passed. Files checked:[/green] {validation['files_checked']}"
    )

if __name__ == "__main__":
    app()
PY

cat > tests/test_cleaning.py <<'PY'
from pathlib import Path
import pandas as pd

from nepse_data_engine.processors.clean_daily import clean_price_file

def test_clean_price_file(tmp_path: Path):
    raw = tmp_path / "raw.csv"
    clean = tmp_path / "clean.csv"

    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "Symbol": [" nabil "],
            "Open": ["1,000"],
            "High": ["1,100"],
            "Low": ["950"],
            "LTP": ["1,050"],
            "Qty": ["10,000"],
            "Turnover": ["10,500,000"],
        }
    )

    df.to_csv(raw, index=False)

    clean_price_file(raw, clean)

    output = pd.read_csv(clean)

    assert output.loc[0, "symbol"] == "NABIL"
    assert output.loc[0, "close"] == 1050
    assert output.loc[0, "volume"] == 10000
PY

cat > tests/test_validation.py <<'PY'
from pathlib import Path
import pandas as pd

from nepse_data_engine.processors.validate_data import validate_file

def test_validate_high_low_error(tmp_path: Path):
    file = tmp_path / "bad.csv"

    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "symbol": ["NABIL"],
            "open": [100],
            "high": [90],
            "low": [110],
            "close": [100],
            "volume": [1000],
        }
    )

    df.to_csv(file, index=False)

    report = validate_file(file)

    assert len(report["errors"]) > 0
PY

cat > tests/test_adjustment.py <<'PY'
import pandas as pd

from nepse_data_engine.processors.adjust_prices import apply_adjustments

def test_bonus_adjustment():
    prices = pd.DataFrame(
        {
            "date": ["2024-01-01", "2025-01-01"],
            "symbol": ["NABIL", "NABIL"],
            "open": [1000, 600],
            "high": [1100, 650],
            "low": [900, 550],
            "close": [1000, 600],
        }
    )

    actions = pd.DataFrame(
        {
            "symbol": ["NABIL"],
            "book_close_date": [pd.Timestamp("2024-06-01")],
            "bonus_percent": [100],
        }
    )

    adjusted = apply_adjustments(prices, actions)

    assert adjusted.loc[0, "adjusted_close"] == 500
    assert adjusted.loc[1, "adjusted_close"] == 600
PY

cat > .circleci/config.yml <<'YAML'
version: 2.1

jobs:
  test:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout

      - run:
          name: Install dependencies
          command: |
            python -m pip install --upgrade pip
            pip install -e .

      - run:
          name: Run tests
          command: pytest -q

  daily_data_update:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout

      - run:
          name: Install dependencies
          command: |
            python -m pip install --upgrade pip
            pip install -e .

      - run:
          name: Run daily NEPSE data pipeline
          command: nepse-data daily-run

      - run:
          name: Commit updated data
          command: |
            git config user.name "nepse-data-bot"
            git config user.email "nepse-data-bot@users.noreply.github.com"

            git add data/
            git diff --cached --quiet || git commit -m "Update NEPSE data $(date +%F)"

            if [ -n "$GH_TOKEN" ]; then
              git push https://$GH_TOKEN@github.com/$CIRCLE_PROJECT_USERNAME/$CIRCLE_PROJECT_REPONAME.git HEAD:main
            else
              echo "GH_TOKEN not set. Skipping push."
            fi

workflows:
  test_on_push:
    jobs:
      - test

  daily_pipeline:
    jobs:
      - daily_data_update:
          filters:
            branches:
              only: main
YAML

cat > .gitignore <<'GIT'
**pycache**/
*.pyc
.pytest_cache/
.venv/
.env
.DS_Store
GIT

cat > data/corporate_actions/corporate_actions.csv <<'CSV'
symbol,book_close_date,action_type,bonus_percent,cash_dividend_percent,right_ratio,issue_price,notes
CSV

cat > LICENSE <<'TXT'
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files to deal in the Software
without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
TXT

echo ""
echo "✅ Project created: $PROJECT_NAME"
echo ""
echo "Next commands:"
echo "cd $PROJECT_NAME"
echo "python -m venv .venv"
echo "source .venv/bin/activate"
echo "pip install -e ."
echo "pytest -q"
echo "nepse-data collect-daily"
echo "nepse-data clean --date today"
echo "nepse-data adjust-all"
echo "nepse-data build-master"
echo "nepse-data validate"
