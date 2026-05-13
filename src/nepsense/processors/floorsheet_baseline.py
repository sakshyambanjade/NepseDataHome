"""
Historical Baseline Engine for Floorsheet Intelligence.
Computes 20-day rolling averages for symbol-level broker flow metrics.
"""

import logging
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

# Directory where daily intelligence results are stored for baseline calculation
INTELLIGENCE_HISTORY_DIR = DATA_DIR / "floorsheet" / "intelligence"

def load_previous_floorsheet_tables(days: int = 20) -> pd.DataFrame:
    """
    Loads historical intelligence results from data/floorsheet/intelligence/*.json
    """
    if not INTELLIGENCE_HISTORY_DIR.exists():
        logger.warning(f"Intelligence history directory {INTELLIGENCE_HISTORY_DIR} does not exist.")
        return pd.DataFrame()
        
    files = sorted(list(INTELLIGENCE_HISTORY_DIR.glob("*.json")), reverse=True)
    historical_data = []
    
    # We take the most recent 'days' files
    for f in files[:days]:
        try:
            with open(f, 'r') as j:
                day_results = json.load(j)
                # Each file is a list of symbol result dicts
                historical_data.extend(day_results)
        except Exception as e:
            logger.error(f"Failed to load historical file {f}: {e}")
            continue
            
    if not historical_data:
        return pd.DataFrame()
        
    return pd.DataFrame(historical_data)

def compute_symbol_baselines(history_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Computes per-symbol averages for baseline metrics.
    """
    if history_df.empty:
        return {}
        
    # Define metrics to average
    metrics_to_avg = {
        "total_qty": "avg_volume_20",
        "total_amt": "avg_turnover_20",
        "operator_like_score": "avg_operator_score_20",
        "repeated_pair_score": "avg_repeated_pair_score_20",
        "net_buy_strength": "avg_net_buy_strength_20",
        "net_sell_strength": "avg_net_sell_strength_20",
        "buyer_hhi": "avg_buyer_hhi_20",
        "seller_hhi": "avg_seller_hhi_20"
    }
    
    baselines = {}
    
    # Group by symbol and calculate means
    for symbol, group in history_df.groupby("symbol"):
        symbol_baseline = {}
        for col, label in metrics_to_avg.items():
            if col in group.columns:
                symbol_baseline[label] = float(group[col].mean())
            else:
                symbol_baseline[label] = 0.0
        baselines[symbol] = symbol_baseline
        
    return baselines

def get_symbol_baseline(symbol: str, days: int = 20) -> Optional[Dict[str, float]]:
    """
    Convenience function to get baseline for a single symbol.
    """
    history_df = load_previous_floorsheet_tables(days)
    if history_df.empty:
        return None
        
    symbol_history = history_df[history_df["symbol"] == symbol]
    if symbol_history.empty:
        return None
        
    baselines = compute_symbol_baselines(symbol_history)
    return baselines.get(symbol)
