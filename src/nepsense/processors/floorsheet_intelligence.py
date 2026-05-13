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
        
    # Transaction order
    if 'transaction_no' in df.columns:
        df['txn_order'] = pd.to_numeric(df['transaction_no'], errors='coerce')
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
    """
    total_qty = df['quantity'].sum()
    total_amt = df['amount'].sum()
    trade_count = len(df)
    vwap = total_amt / total_qty if total_qty > 0 else 0
    
    # Concentration
    buyer_shares = df.groupby('buyer_broker')['quantity'].sum() / total_qty
    seller_shares = df.groupby('seller_broker')['quantity'].sum() / total_qty
    
    buyer_hhi = calculate_normalized_hhi(buyer_shares)
    seller_hhi = calculate_normalized_hhi(seller_shares)
    
    # Top Players
    top_buyers = [{"broker": b, "qty": q, "share": q/total_qty} 
                  for b, q in df.groupby('buyer_broker')['quantity'].sum().nlargest(3).items()]
    top_sellers = [{"broker": b, "qty": q, "share": q/total_qty} 
                   for b, q in df.groupby('seller_broker')['quantity'].sum().nlargest(3).items()]
    
    # Patterns
    sliced_buy = detect_sliced_runs(df, "buy")
    sliced_sell = detect_sliced_runs(df, "sell")
    repeated_pair = detect_repeated_pairs(df)
    
    cross_trade_df = df[df['buyer_broker'] == df['seller_broker']]
    cross_trade_ratio = cross_trade_df['amount'].sum() / total_amt if total_amt > 0 else 0
    
    chunk_trade = (df['quantity'].max() / total_qty) * 100 if total_qty > 0 else 0
    chunk_score = min(chunk_trade / 25, 1) * 100
    
    # Net Flow
    net_buy = 0
    net_sell = 0
    # Simplistic daily net for top broker
    top_b = top_buyers[0]['broker'] if top_buyers else None
    top_s = top_sellers[0]['broker'] if top_sellers else None
    
    # Basic direction scores
    # Accumulation = Concentration * Buyer Concentration * Net Buy Strength
    acc_score = min(buyer_hhi * 100 * 1.5, 100)
    dist_score = min(seller_hhi * 100 * 1.5, 100)
    churn_score = min(acc_score, dist_score)
    
    # Operator-Like Score (8-Factor Model)
    # 0.18 * surprise + 0.16 * hhi + 0.14 * churn + 0.14 * max(acc, dist) + 0.12 * pair + 0.10 * cross + 0.08 * spike + 0.08 * settlement
    op_score = (
        0.18 * 40 + # surprise placeholder
        0.16 * buyer_hhi * 100 +
        0.14 * churn_score +
        0.14 * max(acc_score, dist_score) +
        0.12 * repeated_pair +
        0.10 * cross_trade_ratio * 100 +
        0.08 * 35 + # spike placeholder
        0.08 * 30   # settlement placeholder
    )
    
    # Data Quality & Guards
    warnings = []
    if trade_count < 10:
        op_score = min(op_score, 50)
        warnings.append("low_trade_count")
    if len(df['buyer_broker'].unique()) < 5:
        op_score = min(op_score, 55)
        warnings.append("few_active_brokers")
        
    # Flags
    flags = []
    if sliced_buy > 40: flags.append("Sliced buy pattern")
    if repeated_pair > 60: flags.append("Repeated broker pair activity")
    if cross_trade_ratio > 0.05: flags.append("Cross-trade watch")
    if chunk_score > 70: flags.append("Large chunk trade")
    
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
        "repeated_pair_score": round(repeated_pair, 1),
        "cross_trade_ratio": round(cross_trade_ratio, 3),
        "chunk_score": round(chunk_score, 1),
        "top_buyer": top_b,
        "top_seller": top_s,
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
