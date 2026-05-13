import pytest
import pandas as pd
import numpy as np
from nepsense.processors.floorsheet_intelligence import (
    compute_symbol_flow,
    calculate_normalized_hhi,
    sanitize_floorsheet
)

def test_sliced_buy_pattern():
    # Repeated transaction sequence should trigger sliced_buy_score
    data = []
    # 5 trades by broker 01 with small txn_no gaps
    for i in range(5):
        data.append({
            "symbol": "TEST",
            "buyer_broker": "01",
            "seller_broker": f"{i+10}",
            "quantity": 1000,
            "rate": 100,
            "transaction_no": f"TXN-{i*2}" # Gaps of 2
        })
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "TEST", "2026-05-12")
    assert metrics["sliced_buy_score"] > 0
    assert "Sliced buy pattern" in metrics["flags"]

def test_repeated_pair_pattern():
    # Repeated broker pair should trigger repeated_pair_score
    data = []
    for i in range(10):
        data.append({
            "symbol": "PAIR",
            "buyer_broker": "01",
            "seller_broker": "02",
            "quantity": 1000,
            "rate": 100,
            "transaction_no": i
        })
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "PAIR", "2026-05-12")
    assert metrics["repeated_pair_score"] >= 80
    assert "Repeated broker pair activity" in metrics["flags"]

def test_cross_trade_watch():
    # Same buyer and seller broker should trigger cross_trade_ratio
    data = []
    for i in range(10):
        data.append({
            "symbol": "CROSS",
            "buyer_broker": "05",
            "seller_broker": "05",
            "quantity": 1000,
            "rate": 100,
            "transaction_no": i
        })
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "CROSS", "2026-05-12")
    assert metrics["cross_trade_ratio"] == 1.0
    assert "Cross-trade watch" in metrics["flags"]

def test_quality_guards():
    # Low trade count should cap operator_like_score
    data = [{
        "symbol": "LOW",
        "buyer_broker": "01",
        "seller_broker": "02",
        "quantity": 1000,
        "rate": 100,
        "transaction_no": 1
    }]
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "LOW", "2026-05-12")
    assert metrics["operator_like_score"] <= 55
    assert "low_trade_count" in metrics["data_quality"]["warnings"]

def test_hhi_calculation():
    # Balanced brokers produce low normalized HHI
    shares = pd.Series([0.1] * 10)
    hhi = calculate_normalized_hhi(shares)
    assert hhi == pytest.approx(0.0)
    
    # Concentrated broker produces high HHI
    shares_conc = pd.Series([1.0])
    hhi_conc = calculate_normalized_hhi(shares_conc)
    assert hhi_conc == 1.0

if __name__ == "__main__":
    print("Running manual tests...")
    test_hhi_calculation()
    test_quality_guards()
    print("Basic tests passed!")
