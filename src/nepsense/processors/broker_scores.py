"""Intelligence scores based on broker flow patterns (V2)."""

import pandas as pd
import numpy as np
from typing import Optional, Dict

def calculate_accumulation_score(flow_df: pd.DataFrame, symbol_stats: pd.DataFrame):
    """
    Accumulation Score (0-100):
    Detects strong buying by concentrated brokers with minimal sell-side presence.
    """
    scores = []
    for symbol, group in flow_df.groupby("symbol"):
        # Top 3 Net Buyers
        net_buyers = group[group["net_qty"] > 0]
        if net_buyers.empty:
            scores.append({"symbol": symbol, "accumulation_score": 0.0})
            continue
            
        market_qty = group["market_qty"].iloc[0]
        net_buy_strength = net_buyers.nlargest(3, "net_qty")["net_qty"].sum() / market_qty
        
        # Concentration
        sym_stat = symbol_stats[symbol_stats["symbol"] == symbol].iloc[0]
        buy_conc = sym_stat["buy_concentration_3"]
        
        # Volume Spike (Mock or passed in, default 0 for raw calculation)
        vol_spike = 0 
        
        # Scoring V2
        score = (
            np.clip(net_buy_strength * 2, 0, 1) * 30 +
            np.clip(buy_conc, 0, 1) * 20 +
            # Other components will be added in aggregate
            0
        )
        
        scores.append({
            "symbol": symbol,
            "accumulation_score": round(score, 1),
            "net_buy_strength_score": np.clip(net_buy_strength * 100, 0, 100)
        })
        
    return pd.DataFrame(scores)

def calculate_distribution_score(flow_df: pd.DataFrame, symbol_stats: pd.DataFrame):
    """
    Distribution Score (0-100):
    Detects strong selling by concentrated brokers.
    """
    scores = []
    for symbol, group in flow_df.groupby("symbol"):
        net_sellers = group[group["net_qty"] < 0]
        if net_sellers.empty:
            scores.append({"symbol": symbol, "distribution_score": 0.0})
            continue
            
        market_qty = group["market_qty"].iloc[0]
        net_sell_strength = abs(net_sellers.nsmallest(3, "net_qty")["net_qty"].sum()) / market_qty
        
        sym_stat = symbol_stats[symbol_stats["symbol"] == symbol].iloc[0]
        sell_conc = sym_stat["sell_concentration_3"]
        
        score = (
            np.clip(net_sell_strength * 2, 0, 1) * 30 +
            np.clip(sell_conc, 0, 1) * 20
        )
        
        scores.append({
            "symbol": symbol,
            "distribution_score": round(score, 1),
            "net_sell_strength_score": np.clip(net_sell_strength * 100, 0, 100)
        })
        
    return pd.DataFrame(scores)

def calculate_operator_score_v2(
    symbol: str,
    metrics: Dict,
    historical_stats: Optional[Dict] = None
):
    """
    Implements the Operator-Like Broker Activity Score V2.
    """
    # 1. Normalized Concentration
    # metrics['buy_hhi'] should be pre-calculated in broker_flow.py
    raw_hhi = metrics.get('buy_hhi', 0.1)
    active_brokers = metrics.get('active_brokers', 1)
    
    if active_brokers > 1:
        norm_hhi = (raw_hhi - 1/active_brokers) / (1 - 1/active_brokers)
    else:
        norm_hhi = 1.0
    norm_conc_score = np.clip(norm_hhi * 100, 0, 100)
    
    # 2. Concentration Surprise
    # Needs historical context
    rolling_avg_conc = historical_stats.get('rolling_avg_conc', 40) if historical_stats else 40
    conc_surprise = norm_conc_score - rolling_avg_conc
    conc_surprise_score = np.clip((conc_surprise / 40) * 100, 0, 100)
    
    # 3. Churn and Pressure
    acc = metrics.get('accumulation_score', 0)
    dist = metrics.get('distribution_score', 0)
    churn_score = min(acc, dist)
    pressure_score = (acc + dist) / 2
    
    # 4. Repeated Pair
    repeated_pair_score = metrics.get('top_3_pair_share', 0.1) * 100
    
    # 5. Cross Trade
    cross_trade_ratio = metrics.get('cross_trade_ratio', 0)
    cross_trade_score = np.clip((cross_trade_ratio / 0.15) * 100, 0, 100)
    
    # 6. Volume Spike
    vol_spike_score = metrics.get('volume_spike_score', 0)
    
    # 7. Persistence
    persistence_score = historical_stats.get('persistence_score', 0) if historical_stats else 0
    
    # 8. Price Impact
    price_impact_score = metrics.get('price_impact_score', 0)
    
    # Weighted Raw Score
    raw_score = (
        0.16 * conc_surprise_score +
        0.14 * norm_conc_score +
        0.14 * churn_score +
        0.12 * pressure_score +
        0.12 * persistence_score +
        0.10 * repeated_pair_score +
        0.08 * cross_trade_score +
        0.08 * vol_spike_score +
        0.06 * price_impact_score
    )
    
    # Data Quality Multiplier
    trade_count = metrics.get('trade_count', 0)
    turnover = metrics.get('turnover', 0)
    liquidity_threshold = 1000000 # 10 Lakhs
    
    trade_count_score = min(trade_count / 30, 1)
    active_broker_score = min(active_brokers / 10, 1)
    turnover_score = min(turnover / liquidity_threshold, 1)
    
    quality_mult = min(1, 0.4*trade_count_score + 0.3*active_broker_score + 0.3*turnover_score)
    
    final_score = raw_score * quality_mult
    
    # Caps
    if trade_count < 10: final_score = min(final_score, 50)
    if active_brokers < 5: final_score = min(final_score, 55)
    
    # Pattern Label
    pattern = "Normal broker flow"
    if final_score > 85: pattern = "Extreme broker-flow anomaly"
    elif final_score > 70: pattern = "Strong operator-like pattern"
    elif final_score > 50: pattern = "Unusual broker concentration"
    elif final_score > 30: pattern = "Watch"
    
    return {
        "operator_like_score": round(final_score, 1),
        "operator_pattern": pattern,
        "churn_score": round(churn_score, 1),
        "pressure_score": round(pressure_score, 1),
        "conc_surprise": round(conc_surprise_score, 1)
    }
