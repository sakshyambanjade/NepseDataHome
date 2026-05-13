import pandas as pd
from nepsense.processors.floorsheet_intelligence import compute_symbol_flow, sanitize_floorsheet

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
