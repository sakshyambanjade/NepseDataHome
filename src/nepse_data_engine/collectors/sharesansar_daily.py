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
