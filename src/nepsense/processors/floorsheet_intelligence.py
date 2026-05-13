"""
Full Floorsheet Intelligence Engine (Production V1).
Analyzes daily NEPSE floorsheet data to detect accumulation, distribution, 
and operator-like activity patterns using transaction sequence analysis.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def sanitize_floorsheet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize floorsheet data.
    - Normalize column names
    - Clean broker codes (strip, zfill)
    - Parse transaction numbers
    - Ensure amount exists
    """
    if df.empty:
        return df
        
    # Column mapping
    mapping = {
        'buyer': 'buyer_broker',
        'seller': 'seller_broker',
        'qty': 'quantity',
        'price': 'rate',
        'amt': 'amount',
        'txn_no': 'transaction_no'
    }
    df = df.rename(columns=mapping)
    
    # Required columns
    required = ['symbol', 'buyer_broker', 'seller_broker', 'quantity', 'rate']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required floorsheet column: {col}")
            
    # Clean broker codes
    for col in ['buyer_broker', 'seller_broker']:
        df[col] = df[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(2)
        
    # Transaction order - fixed regex for mixed IDs
    if 'transaction_no' in df.columns:
        df['txn_order'] = df['transaction_no'].astype(str).str.extract(r"(\d+)$")[0].astype(float)
    else:
        df['txn_order'] = range(len(df))
        
    # Amount calculation
    if 'amount' not in df.columns:
        df['amount'] = df['quantity'] * df['rate']
        
    return df.dropna(subset=['symbol', 'buyer_broker', 'seller_broker'])

def detect_sliced_runs(df: pd.DataFrame, side: str = "buy") -> float:
    """
    Detects sliced buying/selling patterns based on transaction sequence.
    If the same broker appears 3+ times within a transaction gap <= 3, it's a sliced run.
    Returns a normalized score 0-100.
    """
    broker_col = 'buyer_broker' if side == "buy" else 'seller_broker'
    if df.empty:
        return 0.0
        
    # Group by broker and find sequences
    total_sliced_vol = 0
    total_vol = df['quantity'].sum()
    
    for broker, group in df.groupby(broker_col):
        if len(group) < 3:
            continue
            
        group = group.sort_values('txn_order')
        group['txn_diff'] = group['txn_order'].diff()
        
        # A 'run' is where txn_diff <= 3 for 3+ consecutive rows
        # We simplify: what percentage of broker's volume is in 'close' transactions
        runs = group[group['txn_diff'] <= 3]
        if len(runs) >= 2: # At least 3 transactions involved
            total_sliced_vol += runs['quantity'].sum()
            
    score = (total_sliced_vol / total_vol) * 100 if total_vol > 0 else 0
    return min(score * 2, 100) # Boost multiplier for sensitivity

def detect_repeated_pairs(df: pd.DataFrame) -> float:
    """
    Calculates the share of the top 3 repeating broker pairs.
    Returns a score 0-100.
    """
    if len(df) < 5:
        return 0.0
        
    df['pair'] = df['buyer_broker'] + "-" + df['seller_broker']
    pair_counts = df.groupby('pair')['quantity'].sum()
    total_vol = df['quantity'].sum()
    
    top_3_vol = pair_counts.nlargest(3).sum()
    pair_share = top_3_vol / total_vol if total_vol > 0 else 0
    
    # Score: if top 3 pairs are 25% of volume, score = 100
    return min(pair_share / 0.25, 1) * 100

def calculate_normalized_hhi(shares: pd.Series) -> float:
    """Calculates normalized HHI (0 to 1)."""
    if shares.empty:
        return 0.0
    n = len(shares)
    if n <= 1:
        return 1.0
    raw_hhi = (shares**2).sum()
    return (raw_hhi - (1/n)) / (1 - (1/n))

def compute_symbol_flow(df: pd.DataFrame, symbol: str, date: str) -> Dict[str, Any]:
    """
    Computes detailed intelligence for a single symbol.
    Now with hardened 8-factor scoring model.
    """
    total_qty = df['quantity'].sum()
    total_amt = df['amount'].sum()
    trade_count = len(df)
    vwap = total_amt / total_qty if total_qty > 0 else 0
    
    # concentration
    buyer_shares = df.groupby('buyer_broker')['quantity'].sum() / total_qty
    seller_shares = df.groupby('seller_broker')['quantity'].sum() / total_qty
    
    buyer_hhi = calculate_normalized_hhi(buyer_shares)
    seller_hhi = calculate_normalized_hhi(seller_shares)
    
    # Top Players
    top_buyers_df = df.groupby('buyer_broker')['quantity'].sum().nlargest(5)
    top_sellers_df = df.groupby('seller_broker')['quantity'].sum().nlargest(5)
    
    top_buyers = [{"broker": b, "qty": q, "share": q/total_qty} for b, q in top_buyers_df.items()]
    top_sellers = [{"broker": b, "qty": q, "share": q/total_qty} for b, q in top_sellers_df.items()]
    
    # Pattern Scores
    sliced_buy = detect_sliced_runs(df, "buy")
    sliced_sell = detect_sliced_runs(df, "sell")
    repeated_pair = detect_repeated_pairs(df)
    
    cross_trade_df = df[df['buyer_broker'] == df['seller_broker']]
    cross_trade_ratio = cross_trade_df['amount'].sum() / total_amt if total_amt > 0 else 0
    
    chunk_trade_pct = (df['quantity'].max() / total_qty) * 100 if total_qty > 0 else 0
    chunk_score = min(chunk_trade_pct / 25, 1) * 100
    
    # Strength Components
    top_5_buyer_share = top_buyers_df.sum() / total_qty if total_qty > 0 else 0
    top_5_seller_share = top_sellers_df.sum() / total_qty if total_qty > 0 else 0
    
    # Net buy strength: How much more concentrated is the buy side vs sell side
    net_buy_strength = max(0, (top_5_buyer_share - top_5_seller_share)) * 100
    net_sell_strength = max(0, (top_5_seller_share - top_5_buyer_share)) * 100

    # New Accumulation/Distribution formulas
    acc_score = (
        0.30 * net_buy_strength +
        0.20 * buyer_hhi * 100 +
        0.15 * sliced_buy +
        0.15 * chunk_score +
        0.10 * repeated_pair +
        0.10 * cross_trade_ratio * 100
    )
    
    dist_score = (
        0.30 * net_sell_strength +
        0.20 * seller_hhi * 100 +
        0.15 * sliced_sell +
        0.15 * chunk_score +
        0.10 * repeated_pair +
        0.10 * cross_trade_ratio * 100
    )
    
    churn_score = min(buyer_hhi * 100, seller_hhi * 100)
    
    # Advanced Components (Real calculations or warnings)
    warnings = []
    
    # 1. Concentration Surprise
    # In V1, we use a simple heuristic: if HHI > 0.4, it's a surprise
    conc_surprise = max(0, (buyer_hhi - 0.2)) * 100
    # Note: Real surprise needs historical HHI baseline.
    warnings.append("missing_historical_baseline")
    
    # 2. Volume Spike
    # Real spike needs avg_volume_20.
    vol_spike_score = 0
    warnings.append("missing_volume_baseline")
    
    # 3. Settlement Followthrough
    settlement_score = 0
    warnings.append("missing_settlement_baseline")

    # Operator-Like Score (8-Factor Model)
    op_score = (
        0.18 * conc_surprise +
        0.16 * buyer_hhi * 100 +
        0.14 * churn_score +
        0.14 * max(acc_score, dist_score) +
        0.12 * repeated_pair +
        0.10 * cross_trade_ratio * 100 +
        0.08 * vol_spike_score +
        0.08 * settlement_score
    )
    
    # Data Quality & Guards
    active_brokers = pd.concat([df["buyer_broker"], df["seller_broker"]]).nunique()
    
    if trade_count < 10:
        op_score = min(op_score, 50)
        warnings.append("low_trade_count")
    if active_brokers < 5:
        op_score = min(op_score, 55)
        warnings.append("few_active_brokers")
        
    # Flags
    flags = []
    if sliced_buy > 40: flags.append("Sliced buy pattern")
    if sliced_sell > 40: flags.append("Sliced sell pattern")
    if repeated_pair > 60: flags.append("Repeated broker pair activity")
    if cross_trade_ratio > 0.05: flags.append("Cross-trade watch")
    if chunk_score > 70: flags.append("Large chunk trade")
    if net_buy_strength > 20: flags.append("Concentrated accumulation")
    
    return {
        "symbol": symbol,
        "date": date,
        "total_qty": int(total_qty),
        "total_amt": float(total_amt),
        "trade_count": trade_count,
        "vwap": round(vwap, 2),
        "accumulation_score": round(acc_score, 1),
        "distribution_score": round(dist_score, 1),
        "operator_like_score": round(op_score, 1),
        "churn_score": round(churn_score, 1),
        "sliced_buy_score": round(sliced_buy, 1),
        "sliced_sell_score": round(sliced_sell, 1),
        "repeated_pair_score": round(repeated_pair, 1),
        "cross_trade_ratio": round(cross_trade_ratio, 3),
        "chunk_score": round(chunk_score, 1),
        "net_buy_strength": round(net_buy_strength, 1),
        "top_buyer": top_buyers[0]['broker'] if top_buyers else None,
        "top_seller": top_sellers[0]['broker'] if top_sellers else None,
        "flags": flags,
        "data_quality": {"warnings": warnings, "score": 100 if not warnings else 60}
    }

def analyze_daily_floorsheet(df: pd.DataFrame, date: str) -> List[Dict[str, Any]]:
    """Analyzes a full floorsheet day by day and returns list of metrics."""
    df = sanitize_floorsheet(df)
    results = []
    for symbol, group in df.groupby('symbol'):
        results.append(compute_symbol_flow(group, symbol, date))
    return results
