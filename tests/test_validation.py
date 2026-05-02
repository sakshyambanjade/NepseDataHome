from pathlib import Path
import pandas as pd

from nepse_data_engine.processors.validate_data import validate_file

def test_validate_high_low_error(tmp_path: Path):
    file = tmp_path / "bad.csv"

    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "symbol": ["NABIL"],
            "open": [100],
            "high": [90],
            "low": [110],
            "close": [100],
            "volume": [1000],
        }
    )

    df.to_csv(file, index=False)

    report = validate_file(file)

    assert len(report["errors"]) > 0
