"""Archive importer for historical NEPSE data drops."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from nepsense.config import NORMALIZED_DIR, RAW_DIR, SOURCE_CONFIDENCE_SCALE
from nepsense.processors import normalize_file
from nepsense.utils import extract_date_from_filename

logger = logging.getLogger(__name__)


def _partitioned_path(root: Path, source: str, date_str: str) -> Path:
    year, month, _ = date_str.split("-")
    output_dir = root / f"source={source}" / year / month
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{date_str}.csv"


def import_archive(
    input_dir: Path,
    source: str = "archive",
    source_confidence: float = SOURCE_CONFIDENCE_SCALE["archive"],
    normalize: bool = True,
) -> dict[str, object]:
    """Import a folder of dated CSV files into raw and normalized history.

    The importer expects each filename to contain a date such as
    `2024-01-02.csv`, `20240102.csv`, or `2024_01_02.csv`.
    """
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Archive directory not found: {input_dir}")

    csv_files = sorted(input_dir.rglob("*.csv"))
    stats: dict[str, object] = {
        "source": source,
        "input_dir": str(input_dir),
        "files_found": len(csv_files),
        "imported": 0,
        "normalized": 0,
        "skipped": [],
        "failed": [],
    }

    for csv_file in csv_files:
        date_str = extract_date_from_filename(csv_file)
        if date_str is None:
            stats["skipped"].append({"file": str(csv_file), "reason": "no date in filename"})
            continue

        raw_path = _partitioned_path(RAW_DIR, source, date_str)
        normalized_path = _partitioned_path(NORMALIZED_DIR, source, date_str)

        try:
            df = pd.read_csv(csv_file, low_memory=False)
            if "date" not in df.columns:
                df["date"] = date_str
            if "source" not in df.columns:
                df["source"] = source
            if "source_confidence" not in df.columns:
                df["source_confidence"] = source_confidence

            df.to_csv(raw_path, index=False)
            stats["imported"] = int(stats["imported"]) + 1

            if normalize:
                normalize_file(raw_path, normalized_path)
                stats["normalized"] = int(stats["normalized"]) + 1

        except Exception as exc:
            logger.exception("Failed to import archive file %s", csv_file)
            stats["failed"].append({"file": str(csv_file), "reason": str(exc)})

    return stats
