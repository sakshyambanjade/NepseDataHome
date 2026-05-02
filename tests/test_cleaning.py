from pathlib import Path
import pandas as pd

from nepse_data_engine.processors.clean_daily import clean_price_file

def test_clean_price_file(tmp_path: Path):
    raw = tmp_path / "raw.csv"
    clean = tmp_path / "clean.csv"

    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "Symbol": [" nabil "],
            "Open": ["1,000"],
            "High": ["1,100"],
            "Low": ["950"],
            "LTP": ["1,050"],
            "Qty": ["10,000"],
            "Turnover": ["10,500,000"],
        }
    )

    df.to_csv(raw, index=False)

    clean_price_file(raw, clean)

    output = pd.read_csv(clean)

    assert output.loc[0, "symbol"] == "NABIL"
    assert output.loc[0, "close"] == 1050
    assert output.loc[0, "volume"] == 10000
