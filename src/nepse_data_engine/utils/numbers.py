from __future__ import annotations

import pandas as pd

def to_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.replace("रु", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace("-", "", regex=False)
        .replace({"": None, "nan": None, "None": None})
    )
    return pd.to_numeric(cleaned, errors="coerce")
