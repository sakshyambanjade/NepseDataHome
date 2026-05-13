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

def test_net_buy_strength():
    # One broker net buying heavily should raise net_buy_strength
    data = []
    # Broker 01 buys 1000 from 10 different sellers
    for i in range(10):
        data.append({
            "symbol": "NETBUY",
            "buyer_broker": "01",
            "seller_broker": f"{i+10}",
            "quantity": 100,
            "rate": 100,
            "transaction_no": i
        })
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "NETBUY", "2026-05-12")
    assert metrics["net_buy_strength"] >= 90
    assert "Net broker accumulation" in metrics["flags"]

def test_net_sell_strength():
    # One broker net selling heavily should raise net_sell_strength
    data = []
    # Broker 01 sells 1000 to 10 different buyers
    for i in range(10):
        data.append({
            "symbol": "NETSELL",
            "buyer_broker": f"{i+10}",
            "seller_broker": "01",
            "quantity": 100,
            "rate": 100,
            "transaction_no": i
        })
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "NETSELL", "2026-05-12")
    assert metrics["net_sell_strength"] >= 90
    assert "Net broker distribution" in metrics["flags"]

def test_mixed_transaction_ids():
    # Transaction IDs like TXN-2026-05-12-NABIL-775 should parse correctly
    data = [{
        "symbol": "TXN",
        "buyer_broker": "01",
        "seller_broker": "02",
        "quantity": 100,
        "rate": 100,
        "transaction_no": "TXN-2026-05-12-NABIL-775"
    }]
    df = sanitize_floorsheet(pd.DataFrame(data))
    assert df["txn_order"].iloc[0] == 775

def test_balanced_broker_activity():
    # Balanced broker activity should give low operator_like_score
    data = []
    # 20 trades between different random brokers
    for i in range(20):
        data.append({
            "symbol": "BALANCED",
            "buyer_broker": f"{i+10}",
            "seller_broker": f"{i+40}",
            "quantity": 100,
            "rate": 100,
            "transaction_no": i
        })
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "BALANCED", "2026-05-12")
    assert metrics["operator_like_score"] < 25
    assert len(metrics["flags"]) == 0

def test_low_trade_count_warning():
    # Low trade count should add low_trade_count warning and cap score
    data = [{
        "symbol": "LOW",
        "buyer_broker": "01",
        "seller_broker": "02",
        "quantity": 100,
        "rate": 100,
        "transaction_no": 1
    }]
    df = sanitize_floorsheet(pd.DataFrame(data))
    metrics = compute_symbol_flow(df, "LOW", "2026-05-12")
    assert "low_trade_count" in metrics["data_quality"]["warnings"]
    assert metrics["operator_like_score"] <= 50

def test_baseline_removes_warning():
    """Verify that providing a baseline removes the missing_historical_baseline warning."""
    df = pd.DataFrame({
        'symbol': ['NABIL']*10,
        'buyer_broker': ['58']*10,
        'seller_broker': ['45']*10,
        'quantity': [100]*10,
        'rate': [500]*10,
        'transaction_no': range(10)
    })
    df = sanitize_floorsheet(df)
    
    # Case 1: No baseline
    res_no_base = compute_symbol_flow(df, 'NABIL', '2026-05-13')
    assert "missing_historical_baseline" in res_no_base["data_quality"]["warnings"]
    
    # Case 2: With baseline
    baseline = {
        "avg_volume_20": 1000, 
        "avg_repeated_pair_score_20": 20,
        "avg_net_buy_strength_20": 10
    }
    res_with_base = compute_symbol_flow(df, 'NABIL', '2026-05-13', baseline=baseline)
    assert "missing_historical_baseline" not in res_with_base["data_quality"]["warnings"]
    assert res_with_base["baseline_available"] is True

def test_surprise_scores_elevation():
    """Verify that scores are elevated when today's activity exceeds historical averages."""
    # Today's activity: 10 transactions, all same pair, total volume 1000
    df = pd.DataFrame({
        'symbol': ['NABIL']*10,
        'buyer_broker': ['58']*10,
        'seller_broker': ['45']*10,
        'quantity': [100]*10,
        'rate': [500]*10,
        'transaction_no': range(10)
    })
    df = sanitize_floorsheet(df)
    
    # Baseline: Low historical activity
    baseline = {
        "avg_volume_20": 200,                # Today is 1000 (5x spike)
        "avg_repeated_pair_score_20": 10,    # Today will be ~100
        "avg_net_buy_strength_20": 5         # Today will be ~100
    }
    
    res = compute_symbol_flow(df, 'NABIL', '2026-05-13', baseline=baseline)
    
    assert res["concentration_surprise_score"] > 50
    assert res["volume_spike_score"] > 100
    assert res["unusual_net_buy_score"] > 50
    assert "Volume spike detected" in res["flags"]
    assert "Unusual concentration" in res["flags"]

def test_missing_volume_baseline_warning():
    """Verify that missing volume baseline specifically keeps its warning."""
    df = pd.DataFrame({
        'symbol': ['NABIL']*5,
        'buyer_broker': ['58']*5,
        'seller_broker': ['45']*5,
        'quantity': [100]*5,
        'rate': [500]*5,
        'transaction_no': range(5)
    })
    df = sanitize_floorsheet(df)
    
    # Baseline exists but avg_volume is 0 or missing
    baseline = {"avg_repeated_pair_score_20": 20}
    res = compute_symbol_flow(df, 'NABIL', '2026-05-13', baseline=baseline)
    
    assert "missing_volume_baseline" in res["data_quality"]["warnings"]
    assert "missing_historical_baseline" not in res["data_quality"]["warnings"]

if __name__ == "__main__":
    print("Running manual tests...")
    test_net_buy_strength()
    test_mixed_transaction_ids()
    test_low_trade_count_warning()
    test_baseline_removes_warning()
    print("All tests passed!")
