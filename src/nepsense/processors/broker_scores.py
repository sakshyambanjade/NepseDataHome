"""Intelligence scores based on broker flow patterns."""

import pandas as pd
import numpy as np

def calculate_accumulation_score(flow_df: pd.DataFrame, symbol_stats: pd.DataFrame):
    """
    Accumulation Score (0-100):
    Detects strong buying by concentrated brokers with minimal sell-side presence.
    """
    # Merge concentration stats
    df = flow_df.merge(symbol_stats, on="symbol")
    
    # Net Buy Strength: Net Qty / Total Market Qty
    df["net_buy_strength"] = df["net_qty"] / df["market_qty"]
    
    # We aggregate to symbol level
    scores = []
    for symbol, group in df.groupby("symbol"):
        top_net_buyer = group.nlargest(1, "net_qty").iloc[0]
        
        # Scoring components
        net_buy_strength = max(0, top_net_buyer["net_buy_strength"])
        buy_concentration = group.iloc[0]["buy_concentration_3"] if "buy_concentration_3" in group.columns else 0
        
        # Accumulation Score Formula
        score = (
            np.clip(net_buy_strength * 3, 0, 1) * 40 +
            np.clip(buy_concentration, 0, 1) * 40 +
            (1 - np.clip(group.iloc[0]["sell_concentration_3"], 0, 1)) * 20
        )
        
        scores.append({
            "symbol": symbol,
            "accumulation_score": round(score, 1)
        })
        
    return pd.DataFrame(scores)

def calculate_smart_money_score(acc_df: pd.DataFrame, flow_df: pd.DataFrame):
    """Smart Money Flow Score (0-100)."""
    # Placeholder for more complex logic (e.g., historical persistence)
    df = acc_df.copy()
    # High accumulation + high concentration = smart money
    df["smart_money_score"] = np.clip(df["accumulation_score"] * 1.1, 0, 100).round(1)
    return df[["symbol", "smart_money_score"]]

def detect_operator_patterns(flow_df: pd.DataFrame):
    """Detect unusual concentration patterns."""
    # This matches the user's requirement for careful wording
    stats = []
    for symbol, group in flow_df.groupby("symbol"):
        max_cross = group["cross_ratio"].max()
        max_dominance = (group["buy_share"].max() + group["sell_share"].max()) / 2
        
        score = (max_cross * 50 + max_dominance * 50) * 100
        
        pattern = "Normal"
        if score > 85: pattern = "Extreme concentration pattern"
        elif score > 70: pattern = "Strong operator-like pattern"
        elif score > 50: pattern = "Unusual broker concentration"
        elif score > 30: pattern = "Watch"
        
        stats.append({
            "symbol": symbol,
            "operator_like_score": round(np.clip(score, 0, 100), 1),
            "operator_pattern": pattern
        })
        
    return pd.DataFrame(stats)
