import pandas as pd

from nepse_data_engine.processors.adjust_prices import apply_adjustments

def test_bonus_adjustment():
    prices = pd.DataFrame(
        {
            "date": ["2024-01-01", "2025-01-01"],
            "symbol": ["NABIL", "NABIL"],
            "open": [1000, 600],
            "high": [1100, 650],
            "low": [900, 550],
            "close": [1000, 600],
        }
    )

    actions = pd.DataFrame(
        {
            "symbol": ["NABIL"],
            "book_close_date": [pd.Timestamp("2024-06-01")],
            "bonus_percent": [100],
        }
    )

    adjusted = apply_adjustments(prices, actions)

    assert adjusted.loc[0, "adjusted_close"] == 500
    assert adjusted.loc[1, "adjusted_close"] == 600
