import pandas as pd

from nepsense.collectors.companywise_importer import _normalise_company_history


def test_normalise_company_history_filters_and_maps_columns():
    raw = pd.DataFrame(
        {
            "published_date": ["2006-12-31", "2007-01-01"],
            "open": ["10", "10"],
            "high": ["12", "12"],
            "low": ["9", "9"],
            "close": ["11", "11"],
            "traded_quantity": ["100", "100"],
            "traded_amount": ["1100", "1100"],
            "status": ["1", "1"],
        }
    )

    normalized = _normalise_company_history(
        symbol="NABIL",
        frame=raw,
        source="test_source",
        source_confidence=0.7,
        start_date="2007-01-01",
    )

    assert len(normalized) == 1
    assert normalized.iloc[0]["date"].isoformat() == "2007-01-01"
    assert normalized.iloc[0]["symbol"] == "NABIL"
    assert normalized.iloc[0]["volume"] == 100
    assert normalized.iloc[0]["turnover"] == 1100
    assert normalized.iloc[0]["source"] == "test_source"
    assert normalized.iloc[0]["source_confidence"] == 0.7
