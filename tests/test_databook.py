from pathlib import Path

import pandas as pd

from nepsense.databook import build_data_book


def test_build_data_book_writes_symbol_and_date_history(tmp_path: Path):
    normalized = tmp_path / "normalized"
    output = tmp_path / "history"
    day_dir = normalized / "source=archive" / "2024" / "01"
    day_dir.mkdir(parents=True)

    pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-02", "2024-01-03"],
            "symbol": ["NABIL", "HBL", "NABIL"],
            "close": [100, 200, 110],
            "source": ["archive", "archive", "archive"],
            "source_confidence": [0.7, 0.7, 0.7],
        }
    ).to_csv(day_dir / "2024-01-02.csv", index=False)

    manifest = build_data_book(normalized, output, rebuild_master=False)

    assert manifest["rows"] == 3
    assert manifest["symbols"] == 2
    assert (output / "nepse_all_prices.csv").exists()
    assert (output / "by_symbol" / "NABIL.csv").exists()
    assert (output / "by_symbol" / "HBL.csv").exists()
    assert (output / "by_date" / "2024-01-02.csv").exists()
    assert (output / "manifest.json").exists()

    nabil = pd.read_csv(output / "by_symbol" / "NABIL.csv")
    assert list(nabil["date"]) == ["2024-01-02", "2024-01-03"]


def test_build_data_book_escapes_symbol_filenames(tmp_path: Path):
    normalized = tmp_path / "normalized"
    output = tmp_path / "history"
    day_dir = normalized / "2024" / "01"
    day_dir.mkdir(parents=True)

    pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "symbol": ["GBILD84/85"],
            "close": [100],
            "source": ["archive"],
            "source_confidence": [0.7],
        }
    ).to_csv(day_dir / "2024-01-02.csv", index=False)

    manifest = build_data_book(normalized, output, rebuild_master=False)

    assert (output / "by_symbol" / "GBILD84%2F85.csv").exists()
    assert manifest["symbol_files"][0]["symbol"] == "GBILD84/85"
    assert manifest["symbol_files"][0]["file"] == "by_symbol/GBILD84%2F85.csv"
