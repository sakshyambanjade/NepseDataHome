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
