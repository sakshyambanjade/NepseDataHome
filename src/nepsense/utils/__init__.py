"""Utility functions for date handling."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

NEPAL_TZ = ZoneInfo("Asia/Kathmandu")


def today_nepal() -> str:
    """Get today's date in Nepal timezone as ISO format string."""
    return datetime.now(NEPAL_TZ).date().isoformat()


def resolve_date(date_value: str | None) -> str:
    """Resolve date value. 'today' or None returns today's date."""
    if date_value is None or date_value.lower() == "today":
        return today_nepal()
    return date_value


def dated_output_path(root: Path, date_str: str) -> Path:
    """Create dated output path: root/year/month/date_str.csv."""
    parts = date_str.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")
    
    year, month, _ = parts
    output_dir = root / year / month
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{date_str}.csv"


def extract_date_from_filename(path: Path) -> str | None:
    """Extract date from filename in various formats."""
    text = path.stem

    patterns = [
        r"(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD
        r"(\d{4})_(\d{2})_(\d{2})",  # YYYY_MM_DD
        r"(\d{4})\.(\d{2})\.(\d{2})",  # YYYY.MM.DD
        r"(\d{4})(\d{2})(\d{2})",  # YYYYMMDD
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            y, m, d = match.groups()
            return f"{y}-{m}-{d}"

    return None


def is_valid_date(date_str: str) -> bool:
    """Check if date string is valid ISO format."""
    try:
        datetime.fromisoformat(date_str)
        return True
    except (ValueError, TypeError):
        return False
