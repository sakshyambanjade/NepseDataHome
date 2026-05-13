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
    """Calculates normalized HHI (0 to 1) with robust normalization."""
    shares = shares.dropna()
    shares = shares[shares > 0]
    if shares.empty:
        return 0.0
    shares = shares / shares.sum()
    
    n = len(shares)
    if n <= 1:
        return 1.0
    raw_hhi = (shares**2).sum()
    norm_hhi = (raw_hhi - (1/n)) / (1 - (1/n))
    return float(np.clip(norm_hhi, 0, 1))

def compute_symbol_flow(df: pd.DataFrame, symbol: str, date: str, baseline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Computes detailed intelligence for a single symbol.
    Upgraded for Production V2 with True Net Flow and 7-Factor Weighted Model.
    """
    total_qty = df['quantity'].sum()
    total_amt = df['amount'].sum()
    trade_count = len(df)
    vwap = total_amt / total_qty if total_qty > 0 else 0
    
    # 1. Broker-Level Aggregation (True Net Flow)
    buy_by_broker = df.groupby('buyer_broker')['quantity'].sum()
    sell_by_broker = df.groupby('seller_broker')['quantity'].sum()
    
    broker_stats = pd.DataFrame({'buy': buy_by_broker, 'sell': sell_by_broker}).fillna(0)
    broker_stats['net_qty'] = broker_stats['buy'] - broker_stats['sell']
    
    # Concentration (Using Buy/Sell totals for HHI)
    buyer_hhi = calculate_normalized_hhi(broker_stats['buy'])
    seller_hhi = calculate_normalized_hhi(broker_stats['sell'])
    
    # Top Players (Based on Net Flow)
    top_net_buyers_df = broker_stats[broker_stats['net_qty'] > 0].nlargest(5, 'net_qty')
    top_net_sellers_df = broker_stats[broker_stats['net_qty'] < 0].nsmallest(5, 'net_qty')
    
    top_net_buyers = [{"broker": b, "net_qty": q, "share": q/total_qty} for b, q in top_net_buyers_df['net_qty'].items()]
    top_net_sellers = [{"broker": b, "net_qty": abs(q), "share": abs(q)/total_qty} for b, q in top_net_sellers_df['net_qty'].items()]
    
    # 2. Pattern Scores
    sliced_buy = detect_sliced_runs(df, "buy")
    sliced_sell = detect_sliced_runs(df, "sell")
    repeated_pair = detect_repeated_pairs(df)
    
    cross_trade_df = df[df['buyer_broker'] == df['seller_broker']]
    cross_trade_ratio = cross_trade_df['amount'].sum() / total_amt if total_amt > 0 else 0
    
    chunk_trade_pct = (df['quantity'].max() / total_qty) * 100 if total_qty > 0 else 0
    chunk_score = min(chunk_trade_pct / 25, 1) * 100
    
    # 3. Strength Components (True Net Flow)
    # net_buy_strength = top 3 positive net_qty / total_qty * 100
    net_buy_strength = (top_net_buyers_df['net_qty'].nlargest(3).sum() / total_qty * 100) if total_qty > 0 else 0
    net_sell_strength = (abs(top_net_sellers_df['net_qty'].nsmallest(3).sum()) / total_qty * 100) if total_qty > 0 else 0

    # 4. Scoring Formulas
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
    
    # 5. Production Operator Score (7-Factor Model)
    # Rescaled for better sensitivity (normal 0-30, flags 40-70+)
    op_score = (
        0.20 * max(acc_score, dist_score) +
        0.18 * repeated_pair +
        0.16 * max(buyer_hhi, seller_hhi) * 100 +
        0.14 * churn_score +
        0.12 * chunk_score +
        0.10 * cross_trade_ratio * 100 +
        0.10 * max(sliced_buy, sliced_sell)
    )
    
    # 6. Surprise Scores (Baseline Comparison)
    concentration_surprise_score = 0.0
    volume_spike_score = 0.0
    unusual_net_buy_score = 0.0
    unusual_net_sell_score = 0.0
    baseline_available = False
    
    if baseline:
        baseline_available = True
        # Concentration Surprise: repeated_pair_score today vs baseline
        repeated_pair_baseline = baseline.get("avg_repeated_pair_score_20", 0)
        if repeated_pair_baseline > 0:
            concentration_surprise_score = max(0, repeated_pair - repeated_pair_baseline)
            
        # Volume Spike: total_qty today vs avg_volume_20
        volume_baseline = baseline.get("avg_volume_20", 0)
        if volume_baseline > 0:
            volume_spike_score = max(0, (total_qty / volume_baseline - 1) * 50) # 2x volume = 50 pts
            
        # Unusual Net Buy/Sell: today strength vs baseline
        buy_strength_baseline = baseline.get("avg_net_buy_strength_20", 0)
        if buy_strength_baseline > 0:
            unusual_net_buy_score = max(0, net_buy_strength - buy_strength_baseline)
            
        sell_strength_baseline = baseline.get("avg_net_sell_strength_20", 0)
        if sell_strength_baseline > 0:
            unusual_net_sell_score = max(0, net_sell_strength - sell_strength_baseline)
            
        # Adjust operator score based on surprise
        op_score += (concentration_surprise_score * 0.2 + volume_spike_score * 0.2)
        op_score = min(op_score, 100)

    # 7. Data Quality & Warnings
    warnings = []
    if not baseline_available:
        warnings.append("missing_historical_baseline")
    
    if not baseline or baseline.get("avg_volume_20", 0) == 0:
        warnings.append("missing_volume_baseline")
        
    warnings.append("missing_settlement_baseline")
    
    active_brokers = broker_stats.index.nunique()
    if trade_count < 10:
        op_score = min(op_score, 50)
        warnings.append("low_trade_count")
    if active_brokers < 5:
        op_score = min(op_score, 55)
        warnings.append("few_active_brokers")
        
    # 8. Stronger Intelligence Flags
    flags = []
    if acc_score >= 40: flags.append("Accumulation pressure")
    if dist_score >= 40: flags.append("Distribution pressure")
    if op_score >= 40: flags.append("Broker-flow watch")
    if net_buy_strength >= 20: flags.append("Net broker accumulation")
    if net_sell_strength >= 20: flags.append("Net broker distribution")
    
    if concentration_surprise_score > 20: flags.append("Unusual concentration")
    if volume_spike_score > 30: flags.append("Volume spike detected")
    
    if sliced_buy > 40: flags.append("Sliced buy pattern")
    if sliced_sell > 40: flags.append("Sliced sell pattern")
    if repeated_pair > 60: flags.append("Repeated broker pair activity")
    if cross_trade_ratio > 0.05: flags.append("Cross-trade watch")
    if chunk_score > 70: flags.append("Large chunk trade")
    
    # 9. Detailed Drilldown Data
    pair_counts = df.groupby(['buyer_broker', 'seller_broker'])['quantity'].sum().reset_index()
    pair_counts['pair'] = pair_counts['buyer_broker'] + " → " + pair_counts['seller_broker']
    broker_pairs = pair_counts.nlargest(10, 'quantity').to_dict(orient="records")
    
    cross_trades = cross_trade_df.nlargest(10, 'amount')[['buyer_broker', 'quantity', 'rate', 'amount', 'txn_order']].to_dict(orient="records")
    largest_trades = df.nlargest(10, 'amount')[['buyer_broker', 'seller_broker', 'quantity', 'rate', 'amount', 'txn_order']].to_dict(orient="records")
    
    # Identify sliced run samples
    # (Simple approach: return brokers with highest sliced volume)
    # This is already somewhat reflected in sliced_buy_score but we could add more.

    return {
        "symbol": symbol,
        "date": date,
        "total_qty": int(total_qty),
        "total_amt": float(total_amt),
        "trade_count": trade_count,
        "vwap": round(vwap, 2),
        "buyer_hhi": round(buyer_hhi, 3),
        "seller_hhi": round(seller_hhi, 3),
        "net_flow": float(broker_stats['net_qty'].sum()),
        "accumulation_score": round(acc_score, 1),
        "distribution_score": round(dist_score, 1),
        "operator_like_score": round(op_score, 1),
        "concentration_surprise_score": round(concentration_surprise_score, 1),
        "volume_spike_score": round(volume_spike_score, 1),
        "unusual_net_buy_score": round(unusual_net_buy_score, 1),
        "unusual_net_sell_score": round(unusual_net_sell_score, 1),
        "baseline_available": baseline_available,
        "churn_score": round(churn_score, 1),
        "sliced_buy_score": round(sliced_buy, 1),
        "sliced_sell_score": round(sliced_sell, 1),
        "repeated_pair_score": round(repeated_pair, 1),
        "cross_trade_ratio": round(cross_trade_ratio, 3),
        "chunk_score": round(chunk_score, 1),
        "net_buy_strength": round(net_buy_strength, 1),
        "net_sell_strength": round(net_sell_strength, 1),
        "top_net_buyers": top_net_buyers,
        "top_net_sellers": top_net_sellers,
        "drilldown": {
            "broker_pairs": broker_pairs,
            "cross_trades": cross_trades,
            "largest_trades": largest_trades
        },
        "flags": flags,
        "data_quality": {"warnings": warnings, "score": 100 if len(warnings) < 2 else 60}
    }

def analyze_daily_floorsheet(df: pd.DataFrame, date: str, baselines: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Analyzes a full floorsheet day by day and returns list of metrics."""
    df = sanitize_floorsheet(df)
    results = []
    baselines = baselines or {}
    for symbol, group in df.groupby('symbol'):
        symbol_baseline = baselines.get(symbol)
        results.append(compute_symbol_flow(group, symbol, date, baseline=symbol_baseline))
    return results
