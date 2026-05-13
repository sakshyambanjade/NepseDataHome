"""Process floorsheet data to extract broker-level flow metrics and scores (Production V1)."""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

def validate_floorsheet(df: pd.DataFrame) -> bool:
    """Validate if floorsheet has required columns."""
    required = ["date", "transaction_no", "symbol", "buyer_broker", "seller_broker", "quantity", "rate", "amount"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Floorsheet missing columns: {missing}")
        return False
    return True

def sanitize_floorsheet(df: pd.DataFrame) -> pd.DataFrame:
    """Clean broker codes and numeric fields."""
    df = df.copy()
    
    def clean_broker(val):
        s = str(val).strip()
        if s.endswith(".0"):
            s = s[:-2]
        return s.zfill(2)
        
    df["buyer_broker"] = df["buyer_broker"].apply(clean_broker)
    df["seller_broker"] = df["seller_broker"].apply(clean_broker)
    
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce").fillna(0)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    
    return df

def calculate_normalized_hhi(shares: pd.Series) -> float:
    """
    Calculate Normalized Herfindahl-Hirschman Index.
    HHI ranges from 1/N to 1. Normalized HHI ranges from 0 to 1.
    """
    n = len(shares)
    if n <= 1:
        return 1.0
    
    raw_hhi = (shares ** 2).sum()
    norm_hhi = (raw_hhi - (1/n)) / (1 - (1/n))
    return float(np.clip(norm_hhi, 0, 1))

def calculate_accumulation_score(metrics: Dict) -> float:
    """
    Accumulation Score (0-100):
    0.30 * net_buy_strength
    + 0.20 * buy_concentration
    + 0.15 * buy_vwap_pressure
    + 0.15 * volume_spike
    + 0.10 * price_stability
    + 0.10 * persistence
    """
    score = (
        0.30 * metrics.get("net_buy_strength", 0) +
        0.20 * metrics.get("top3_buy_share", 0) * 100 +
        0.15 * metrics.get("buy_vwap_pressure", 0) +
        0.15 * metrics.get("volume_spike_score", 0) +
        0.10 * metrics.get("price_stability_score", 50) +
        0.10 * metrics.get("persistence_score", 50)
    )
    return round(float(np.clip(score, 0, 100)), 1)

def calculate_distribution_score(metrics: Dict) -> float:
    """
    Distribution Score (0-100):
    0.30 * net_sell_strength
    + 0.20 * sell_concentration
    + 0.15 * sell_vwap_pressure
    + 0.15 * volume_spike
    + 0.10 * price_weakness
    + 0.10 * persistence
    """
    score = (
        0.30 * metrics.get("net_sell_strength", 0) +
        0.20 * metrics.get("top3_sell_share", 0) * 100 +
        0.15 * metrics.get("sell_vwap_pressure", 0) +
        0.15 * metrics.get("volume_spike_score", 0) +
        0.10 * metrics.get("price_weakness_score", 50) +
        0.10 * metrics.get("persistence_score", 50)
    )
    return round(float(np.clip(score, 0, 100)), 1)

def calculate_operator_like_score(metrics: Dict) -> Tuple[float, str]:
    """
    Operator-Like Score (0-100):
    0.18 * concentration_surprise
    + 0.16 * normalized_hhi
    + 0.14 * churn_score
    + 0.14 * max(accumulation_score, distribution_score)
    + 0.12 * repeated_pair_score
    + 0.10 * cross_trade_score
    + 0.08 * volume_spike
    + 0.08 * settlement_followthrough_score
    """
    acc = metrics.get("accumulation_score", 0)
    dist = metrics.get("distribution_score", 0)
    churn = min(acc, dist)
    
    score = (
        0.18 * metrics.get("concentration_surprise", 40) +
        0.16 * metrics.get("normalized_buyer_hhi", 0) * 100 +
        0.14 * churn +
        0.14 * max(acc, dist) +
        0.12 * metrics.get("repeated_pair_score", 0) +
        0.10 * metrics.get("cross_trade_ratio", 0) * 100 +
        0.08 * metrics.get("volume_spike_score", 0) +
        0.08 * metrics.get("settlement_followthrough_score", 0)
    )
    
    # Data quality guards
    if metrics.get("trade_count", 0) < 10:
        score = min(score, 50)
    if metrics.get("active_brokers", 0) < 5:
        score = min(score, 55)
        
    final_score = round(float(np.clip(score, 0, 100)), 1)
    
    # Pattern Label
    pattern = "Normal broker flow"
    if final_score > 85: pattern = "Extreme broker-flow anomaly"
    elif final_score > 70: pattern = "Strong operator-like pattern"
    elif final_score > 50: pattern = "Unusual broker concentration"
    elif final_score > 30: pattern = "Watch"
    
    return final_score, pattern

def calculate_settlement_followthrough(symbol: str, date: str, historical_df: Optional[pd.DataFrame]) -> float:
    """
    Calculate Settlement Follow-through Score (T+1, T+2 focus).
    """
    if historical_df is None or historical_df.empty:
        return 0.0
    
    # Formula:
    # 0.40 * same_broker_net_buy_continuation_t1
    # + 0.35 * same_broker_net_buy_continuation_t2
    # + 0.25 * price_hold_after_accumulation
    
    # Mock for now as historical flow is complex to compute in one pass
    # In production, this would look back at previous flow CSVs
    return 45.0 

def compute_symbol_broker_flow(
    df: pd.DataFrame, 
    symbol: str, 
    date: str, 
    historical_df: Optional[pd.DataFrame] = None,
    price_meta: Optional[Dict] = None
) -> Dict:
    """Compute detailed broker flow metrics for a single symbol."""
    sym_df = df[df["symbol"] == symbol]
    if sym_df.empty:
        return {}
        
    total_qty = sym_df["quantity"].sum()
    total_amount = sym_df["amount"].sum()
    trade_count = len(sym_df)
    vwap = total_amount / total_qty if total_qty > 0 else 0
    
    # Buyer aggregation
    buyers = sym_df.groupby("buyer_broker").agg(
        buy_qty=("quantity", "sum"),
        buy_amount=("amount", "sum")
    ).reset_index().rename(columns={"buyer_broker": "broker"})
    buyers["buy_share"] = buyers["buy_qty"] / total_qty
    buyers["avg_buy_price"] = buyers["buy_amount"] / buyers["buy_qty"]
    
    # Seller aggregation
    sellers = sym_df.groupby("seller_broker").agg(
        sell_qty=("quantity", "sum"),
        sell_amount=("amount", "sum")
    ).reset_index().rename(columns={"seller_broker": "broker"})
    sellers["sell_share"] = sellers["sell_qty"] / total_qty
    sellers["avg_sell_price"] = sellers["sell_amount"] / sellers["sell_qty"]
    
    # Net Flow
    flow = pd.merge(buyers, sellers, on="broker", how="outer").fillna(0)
    flow["net_qty"] = flow["buy_qty"] - flow["sell_qty"]
    
    active_brokers = flow["broker"].nunique()
    
    # Concentration
    top3_buy_share = buyers.nlargest(3, "buy_qty")["buy_share"].sum()
    top3_sell_share = sellers.nlargest(3, "sell_qty")["sell_share"].sum()
    buyer_hhi = (buyers["buy_share"] ** 2).sum()
    seller_hhi = (sellers["sell_share"] ** 2).sum()
    
    # VWAP Pressure
    # If top buyers bought significantly above VWAP, it's pressure
    buy_vwap_dev = np.maximum(0, (buyers["avg_buy_price"] / vwap) - 1).mean() * 100
    sell_vwap_dev = np.maximum(0, 1 - (sellers["avg_sell_price"] / vwap)).mean() * 100
    
    # Cross trade
    cross_trades = sym_df[sym_df["buyer_broker"] == sym_df["seller_broker"]]
    cross_trade_ratio = cross_trades["amount"].sum() / total_amount if total_amount > 0 else 0
    
    # Repeated Pairs
    sym_df = sym_df.copy()
    sym_df["pair"] = sym_df["buyer_broker"] + "-" + sym_df["seller_broker"]
    pairs = sym_df.groupby("pair")["quantity"].sum().reset_index()
    top3_pair_share = pairs.nlargest(3, "quantity")["quantity"].sum() / total_qty
    repeated_pair_score = top3_pair_share * 100
    
    metrics = {
        "symbol": symbol,
        "date": date,
        "total_quantity": int(total_qty),
        "total_amount": float(total_amount),
        "trade_count": int(trade_count),
        "active_brokers": int(active_brokers),
        "vwap": float(vwap),
        "net_buy_strength": float(np.clip(flow[flow["net_qty"] > 0]["net_qty"].sum() / total_qty * 100, 0, 100)),
        "net_sell_strength": float(np.clip(abs(flow[flow["net_qty"] < 0]["net_qty"].sum()) / total_qty * 100, 0, 100)),
        "top3_buy_share": float(top3_buy_share),
        "top3_sell_share": float(top3_sell_share),
        "buyer_hhi": float(buyer_hhi),
        "seller_hhi": float(seller_hhi),
        "normalized_buyer_hhi": calculate_normalized_hhi(buyers["buy_share"]),
        "normalized_seller_hhi": calculate_normalized_hhi(sellers["sell_share"]),
        "buy_vwap_pressure": float(np.clip(buy_vwap_dev * 5, 0, 100)),
        "sell_vwap_pressure": float(np.clip(sell_vwap_dev * 5, 0, 100)),
        "cross_trade_ratio": float(cross_trade_ratio),
        "repeated_pair_score": float(repeated_pair_score),
        "volume_spike_score": 30.0, # Placeholder for now
        "concentration_surprise": 35.0, # Placeholder
        "persistence_score": 40.0, # Placeholder
    }
    
    # Calculate scores
    metrics["settlement_followthrough_score"] = calculate_settlement_followthrough(symbol, date, historical_df)
    metrics["accumulation_score"] = calculate_accumulation_score(metrics)
    metrics["distribution_score"] = calculate_distribution_score(metrics)
    metrics["churn_score"] = min(metrics["accumulation_score"], metrics["distribution_score"])
    
    score, pattern = calculate_operator_like_score(metrics)
    metrics["operator_like_score"] = score
    metrics["operator_pattern"] = pattern
    
    # Top 3 lists for UI
    metrics["top_buyers"] = buyers.nlargest(3, "buy_qty")[["broker", "buy_qty", "buy_share"]].to_dict(orient="records")
    metrics["top_sellers"] = sellers.nlargest(3, "sell_qty")[["broker", "sell_qty", "sell_share"]].to_dict(orient="records")
    metrics["net_flow"] = float(flow["net_qty"].sum()) # Should be 0 for a closed system, but useful if externalized
    
    # Quality flags
    warnings = []
    if trade_count < 10: warnings.append("low_trade_count")
    if active_brokers < 5: warnings.append("few_active_brokers")
    if historical_df is None: warnings.append("missing_historical_data")
    metrics["data_quality"] = {"warnings": warnings}
    
    return metrics

def batch_compute_broker_flow(df: pd.DataFrame, date: str, price_meta: Optional[pd.DataFrame] = None) -> List[Dict]:
    """Compute broker flow for all symbols in a floorsheet."""
    if not validate_floorsheet(df):
        raise ValueError("Invalid floorsheet schema")
        
    if df.empty:
        raise ValueError("Floorsheet is empty")
        
    df = sanitize_floorsheet(df)
    results = []
    
    for symbol, group in df.groupby("symbol"):
        res = compute_symbol_broker_flow(df, symbol, date)
        if res:
            results.append(res)
            
    return results
