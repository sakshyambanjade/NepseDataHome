from pathlib import Path

import pandas as pd

import nepsense.collectors.archive_importer as archive_importer


def test_import_archive_partitions_raw_and_normalized_files(
    tmp_path: Path, monkeypatch
):
    input_dir = tmp_path / "archive"
    raw_dir = tmp_path / "raw"
    normalized_dir = tmp_path / "normalized"
    input_dir.mkdir()

    pd.DataFrame(
        {
            "Symbol": ["NABIL"],
            "LTP": [100],
            "Qty": [1000],
        }
    ).to_csv(input_dir / "market_2024_01_02.csv", index=False)

    monkeypatch.setattr(archive_importer, "RAW_DIR", raw_dir)
    monkeypatch.setattr(archive_importer, "NORMALIZED_DIR", normalized_dir)

    stats = archive_importer.import_archive(
        input_dir=input_dir,
        source="testarchive",
        source_confidence=0.7,
    )

    raw_file = raw_dir / "source=testarchive" / "2024" / "01" / "2024-01-02.csv"
    normalized_file = (
        normalized_dir / "source=testarchive" / "2024" / "01" / "2024-01-02.csv"
    )

    assert stats["imported"] == 1
    assert stats["normalized"] == 1
    assert raw_file.exists()
    assert normalized_file.exists()

    normalized = pd.read_csv(normalized_file)
    assert normalized.loc[0, "symbol"] == "NABIL"
    assert normalized.loc[0, "close"] == 100
    assert normalized.loc[0, "source"] == "testarchive"
    assert normalized.loc[0, "source_confidence"] == 0.7
