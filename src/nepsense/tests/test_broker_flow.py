"""Tests for Broker Flow engine."""

import pytest
import pandas as pd
import numpy as np
from nepsense.processors.broker_flow import (
    compute_symbol_broker_flow, 
    calculate_normalized_hhi,
    batch_compute_broker_flow
)

def test_empty_floorsheet():
    df = pd.DataFrame(columns=["date", "transaction_no", "symbol", "buyer_broker", "seller_broker", "quantity", "rate", "amount"])
    with pytest.raises(ValueError):
        batch_compute_broker_flow(df, "2026-05-12")

def test_data_quality_capping():
    # Single trade
    df = pd.DataFrame([{
        "date": "2026-05-12",
        "transaction_no": "T1",
        "symbol": "TEST",
        "buyer_broker": "01",
        "seller_broker": "02",
        "quantity": 100,
        "rate": 100,
        "amount": 10000
    }])
    
    metrics = compute_symbol_broker_flow(df, "TEST", "2026-05-12")
    # trade_count = 1 (< 10), so score should be capped at 50
    assert metrics["operator_like_score"] <= 50
    assert "low_trade_count" in metrics["data_quality"]["warnings"]

def test_normalized_hhi():
    # Even distribution: 10 brokers with 10% each
    shares = pd.Series([0.1] * 10)
    hhi = calculate_normalized_hhi(shares)
    assert hhi == pytest.approx(0.0)
    
    # Total concentration: 1 broker with 100%
    shares_conc = pd.Series([1.0])
    hhi_conc = calculate_normalized_hhi(shares_conc)
    assert hhi_conc == 1.0

def test_cross_trade_score():
    # Same broker buy and sell
    df = pd.DataFrame([{
        "date": "2026-05-12",
        "transaction_no": "T1",
        "symbol": "TEST",
        "buyer_broker": "01",
        "seller_broker": "01", # Cross trade
        "quantity": 100,
        "rate": 100,
        "amount": 10000
    }] * 20) # 20 trades to avoid quality cap
    
    metrics = compute_symbol_broker_flow(df, "TEST", "2026-05-12")
    assert metrics["cross_trade_ratio"] == 1.0

def test_accumulation_distribution():
    # High net buying
    data = []
    for i in range(20):
        data.append({
            "date": "2026-05-12",
            "transaction_no": f"T{i}",
            "symbol": "BUY",
            "buyer_broker": "01",
            "seller_broker": f"{i+10}",
            "quantity": 1000,
            "rate": 100,
            "amount": 100000
        })
    df_buy = pd.DataFrame(data)
    metrics_buy = compute_symbol_broker_flow(df_buy, "BUY", "2026-05-12")
    
    # High net selling
    data = []
    for i in range(20):
        data.append({
            "date": "2026-05-12",
            "transaction_no": f"T{i}",
            "symbol": "SELL",
            "buyer_broker": f"{i+10}",
            "seller_broker": "01",
            "quantity": 1000,
            "rate": 100,
            "amount": 100000
        })
    df_sell = pd.DataFrame(data)
    metrics_sell = compute_symbol_broker_flow(df_sell, "SELL", "2026-05-12")
    
    assert metrics_buy["accumulation_score"] > metrics_sell["accumulation_score"]
    assert metrics_sell["distribution_score"] > metrics_buy["distribution_score"]

if __name__ == "__main__":
    # Simple manual run
    test_normalized_hhi()
    print("Tests passed!")
