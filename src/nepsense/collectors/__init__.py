"""ShareSansar daily data collector."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from nepsense.config import RAW_DIR, SHARESANSAR_TODAY_URL, SOURCE_CONFIDENCE_SCALE
from nepsense.utils import dated_output_path, resolve_date

logger = logging.getLogger(__name__)

MARKET_HEADER_TERMS = {
    "symbol",
    "code",
    "ltp",
    "close",
    "last traded price",
    "open",
    "high",
    "low",
    "volume",
    "qty",
    "quantity",
    "turnover",
    "amount",
    "transactions",
}


def _clean_cell_text(cell) -> str:
    """Extract visible cell text without preserving layout whitespace."""
    return re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()


def _dedupe_headers(headers: list[str]) -> list[str]:
    """Create stable, non-empty, unique DataFrame column names."""
    seen: dict[str, int] = {}
    deduped = []

    for index, header in enumerate(headers, start=1):
        name = header or f"col_{index}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        deduped.append(name)

    return deduped


def _direct_rows(table) -> list:
    """Return table rows while ignoring rows inside nested tables."""
    rows = []

    for section_name in ("thead", "tbody", "tfoot"):
        for section in table.find_all(section_name, recursive=False):
            rows.extend(section.find_all("tr", recursive=False))

    rows.extend(table.find_all("tr", recursive=False))

    return rows


def _row_cells(row) -> list:
    """Return a row's direct cells, with a fallback for badly repaired markup."""
    cells = row.find_all(["th", "td"], recursive=False)
    if cells:
        return cells
    return row.find_all(["th", "td"])


def _looks_like_header(cells: list) -> bool:
    texts = [_clean_cell_text(cell).lower() for cell in cells]

    if any(cell.name == "th" for cell in cells):
        return True

    header_hits = sum(
        1
        for text in texts
        if text in MARKET_HEADER_TERMS or any(term in text for term in MARKET_HEADER_TERMS)
    )
    numeric_hits = sum(1 for text in texts if re.fullmatch(r"[-+]?[\d,.]+%?", text or ""))

    return header_hits >= 2 and numeric_hits == 0


def _parse_table_with_bs4(html_content: str) -> list[pd.DataFrame]:
    """Parse HTML tables using BeautifulSoup for better malformed HTML handling.

    Args:
        html_content: Raw HTML content

    Returns:
        List of DataFrames from tables found
    """
    try:
        soup = BeautifulSoup(html_content, "html5lib")
    except Exception:
        soup = BeautifulSoup(html_content, "html.parser")

    tables = []

    table_elements = soup.find_all("table")

    for table in table_elements:
        try:
            table_rows = _direct_rows(table)
            if not table_rows:
                continue

            rows = []
            headers: list[str] = []
            header_row_index: int | None = None

            thead = table.find("thead", recursive=False)
            if thead:
                header_row = thead.find("tr", recursive=False)
                if header_row:
                    header_cells = _row_cells(header_row)
                    headers = [_clean_cell_text(cell) for cell in header_cells]
                    header_row_index = table_rows.index(header_row)

            if not headers:
                for index, row in enumerate(table_rows):
                    cells = _row_cells(row)
                    if cells and _looks_like_header(cells):
                        headers = [_clean_cell_text(cell) for cell in cells]
                        header_row_index = index
                        break

            data_start = (header_row_index + 1) if header_row_index is not None else 0

            if not headers:
                first_cells = _row_cells(table_rows[data_start])
                headers = [f"col_{index + 1}" for index in range(len(first_cells))]

            headers = _dedupe_headers(headers)
            max_cols = len(headers)

            for row in table_rows[data_start:]:
                cells = _row_cells(row)
                if not cells:
                    continue

                row_data = [_clean_cell_text(cell) for cell in cells]
                if row_data and any(cell.strip() for cell in row_data):
                    if len(row_data) < max_cols:
                        row_data.extend([""] * (max_cols - len(row_data)))
                    elif len(row_data) > max_cols:
                        row_data = row_data[:max_cols]
                    rows.append(row_data)

            if headers and rows:
                tables.append(pd.DataFrame(rows, columns=headers))

        except Exception as e:
            logger.warning(f"Failed to parse table: {e}")
            continue

    return tables


def _choose_market_table(tables: list[pd.DataFrame]) -> pd.DataFrame:
    """Select the correct market data table from HTML tables.

    Args:
        tables: List of DataFrames from parsed HTML

    Returns:
        DataFrame with market data
    """
    if not tables:
        raise RuntimeError("No HTML tables found in page")

    # Score tables based on market data characteristics
    best_table = None
    best_score = 0

    for table in tables:
        if table.empty:
            continue

        score = 0
        cols = [str(c).lower().strip() for c in table.columns]

        # Required indicators
        has_symbol = any("symbol" in c or "code" in c for c in cols)
        has_price = any(c in cols for c in ["ltp", "close", "last traded price", "closing price"])
        has_volume = any(c in cols for c in ["volume", "qty", "quantity", "traded qty"])

        if has_symbol:
            score += 3
        if has_price:
            score += 3
        if has_volume:
            score += 2

        # Bonus points for other market data columns
        bonus_cols = ["open", "high", "low", "turnover", "amount", "transactions"]
        for col in bonus_cols:
            if any(col in c for c in cols):
                score += 1

        # Prefer tables with reasonable row counts (not too small, not too large)
        row_count = len(table)
        if 10 <= row_count <= 500:  # NEPSE typically has 100-300 active stocks
            score += 2
        elif row_count > 500:
            score -= 1  # Too many rows, might be detailed data

        logger.debug(f"Table score: {score} for {len(cols)} columns, {row_count} rows")

        if score > best_score:
            best_score = score
            best_table = table

    if best_table is not None:
        logger.info(
            "Selected market data table: "
            f"{len(best_table)} rows, {len(best_table.columns)} columns"
        )
        logger.debug(f"Columns: {list(best_table.columns)}")
        return best_table

    # Fallback to first non-empty table
    for table in tables:
        if not table.empty and len(table) > 5:
            logger.warning(f"Using fallback table selection: {len(table)} rows")
            return table

    raise RuntimeError(f"No suitable market data table found among {len(tables)} tables")


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
        tables = _parse_table_with_bs4(response.text)
        df = _choose_market_table(tables)
    except Exception as e:
        logger.error(f"Failed to parse HTML tables: {e}")
        # Fallback to pandas read_html if BeautifulSoup fails
        try:
            logger.info("Attempting fallback with pandas read_html...")
            tables = pd.read_html(response.text)
            df = _choose_market_table(tables)
        except Exception as fallback_e:
            logger.error(f"Fallback parsing also failed: {fallback_e}")
            raise RuntimeError(f"HTML parsing failed: {e}") from e

    # Add metadata
    df["date"] = date_str
    df["source"] = SHARESANSAR_TODAY_URL
    df["source_confidence"] = SOURCE_CONFIDENCE_SCALE["reliable"]

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(df)} rows to {output_file}")

    return output_file
