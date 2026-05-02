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
