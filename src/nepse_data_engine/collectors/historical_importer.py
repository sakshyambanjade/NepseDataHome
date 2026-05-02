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
