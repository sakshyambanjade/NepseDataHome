from pathlib import Path

import pandas as pd

from nepsense.storage import _read_all_csv


def test_read_all_csv_includes_source_partitioned_files(tmp_path: Path):
    standard_dir = tmp_path / "2026" / "05"
    source_dir = tmp_path / "source=sharesansar" / "2024" / "01"
    hidden_dir = tmp_path / ".scratch" / "2024" / "01"

    standard_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    hidden_dir.mkdir(parents=True)

    pd.DataFrame(
        {
            "date": ["2026-05-02"],
            "symbol": ["NABIL"],
            "close": [1460],
        }
    ).to_csv(standard_dir / "2026-05-02.csv", index=False)

    pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "symbol": ["HBL"],
            "close": [428],
        }
    ).to_csv(source_dir / "2024-01-02.csv", index=False)

    pd.DataFrame(
        {
            "date": ["2024-01-03"],
            "symbol": ["IGNORED"],
            "close": [1],
        }
    ).to_csv(hidden_dir / "ignored.csv", index=False)

    combined = _read_all_csv(tmp_path)

    assert len(combined) == 2
    assert list(combined["symbol"]) == ["HBL", "NABIL"]
