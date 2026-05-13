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

if __name__ == "__main__":
    print("Running manual tests...")
    test_net_buy_strength()
    test_mixed_transaction_ids()
    print("Basic tests passed!")
