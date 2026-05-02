"""ShareSansar daily data collector."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import requests

from nepsense.config import RAW_DIR, SHARESANSAR_TODAY_URL
from nepsense.utils import dated_output_path, resolve_date

logger = logging.getLogger(__name__)


def _choose_market_table(tables: list[pd.DataFrame]) -> pd.DataFrame:
    """Select the correct market data table from HTML tables.
    
    Args:
        tables: List of DataFrames from pd.read_html()
    
    Returns:
        DataFrame with market data
    """
    for table in tables:
        cols = [str(c).lower().strip() for c in table.columns]

        has_symbol = any("symbol" in c for c in cols)
        has_price = any(c in cols for c in ["ltp", "close", "last traded price"])

        if has_symbol and has_price:
            logger.debug(f"Selected table with columns: {cols}")
            return table

    if not tables:
        raise RuntimeError("No HTML tables found in page")

    logger.warning(f"No ideal table found, using first of {len(tables)} tables")
    return tables[0]


def collect_daily(
    date: str | None = None,
    output_root: Path = RAW_DIR,
    timeout: int = 40,
) -> Path:
    """Collect today's NEPSE data from ShareSansar.
    
    Args:
        date: Date to collect (default: today)
        output_root: Where to save CSV
        timeout: Request timeout in seconds
    
    Returns:
        Path to saved CSV file
    """
    date_str = resolve_date(date)
    output_file = dated_output_path(output_root, date_str)

    logger.info(f"Collecting NEPSE data for {date_str} from ShareSansar...")

    try:
        response = requests.get(
            SHARESANSAR_TODAY_URL,
            timeout=timeout,
            headers={
                "User-Agent": "nepsense/0.2 (+https://github.com/sakshyambanjade/NepSense)"
            },
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch ShareSansar: {e}")
        raise

    try:
        tables = pd.read_html(response.text)
        df = _choose_market_table(tables)
    except Exception as e:
        logger.error(f"Failed to parse HTML tables: {e}")
        raise

    # Add metadata
    df["date"] = date_str
    df["source"] = SHARESANSAR_TODAY_URL

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(df)} rows to {output_file}")

    return output_file
