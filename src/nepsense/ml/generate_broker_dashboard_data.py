"""Bridge for Broker Intelligence static JSON generation (V2)."""

import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
from nepsense.config import DASHBOARD_DIR, DATA_DIR
from nepsense.processors.broker_flow import process_daily_broker_flow, calculate_concentration_v2
from nepsense.processors.broker_scores import (
    calculate_accumulation_score, 
    calculate_distribution_score, 
    calculate_operator_score_v2
)

logger = logging.getLogger(__name__)

def generate_broker_artifacts_v2(date: str):
    """Generate all broker-related JSON using V2 scoring logic."""
    floorsheet_path = DATA_DIR / "floorsheet" / "normalized" / f"{date}.csv"
    if not floorsheet_path.exists():
        logger.error(f"Floorsheet not found for {date}")
        return
        
    # 1. Process Flow & Pairs
    flow_df, pairs_df = process_daily_broker_flow(floorsheet_path)
    
    # 2. Base Concentration & Metrics
    metrics_df = calculate_concentration_v2(flow_df, pairs_df)
    
    # 3. Acc/Dist Scores
    acc_df = calculate_accumulation_score(flow_df, metrics_df)
    dist_df = calculate_distribution_score(flow_df, metrics_df)
    
    # Merge for easier looping
    merged_metrics = metrics_df.merge(acc_df, on="symbol").merge(dist_df, on="symbol")
    
    # 4. Final Operator Score V2
    operator_results = []
    for _, row in merged_metrics.iterrows():
        symbol = row["symbol"]
        
        # Mock historical context for demo
        # In production, this would be loaded from previous runs
        historical = {
            "rolling_avg_conc": 35.0, # Default avg
            "persistence_score": np.random.randint(20, 60) # Random demo
        }
        
        metrics_dict = row.to_dict()
        res = calculate_operator_score_v2(symbol, metrics_dict, historical)
        res["symbol"] = symbol
        operator_results.append(res)
        
    op_df = pd.DataFrame(operator_results)
    
    # Final consolidated scores
    final_scores = merged_metrics.merge(op_df, on="symbol")
    
    # 5. Generate Overview JSON
    overview = {
        "date": date,
        "operator_watchlist": final_scores.nlargest(15, "operator_like_score")[
            ["symbol", "operator_like_score", "operator_pattern", "churn_score"]
        ].to_dict(orient="records"),
        "unusual_activity": final_scores.nlargest(10, "operator_like_score")[
            ["symbol", "operator_like_score", "operator_pattern"]
        ].to_dict(orient="records"), # Compatibility alias
        "most_accumulated": final_scores.nlargest(10, "accumulation_score")[["symbol", "accumulation_score"]].to_dict(orient="records"),
        "smart_money_ranking": final_scores.nlargest(10, "pressure_score")[
            ["symbol", "pressure_score"]
        ].rename(columns={"pressure_score": "smart_money_score"}).to_dict(orient="records"),
    }
    
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_DIR / "broker_overview.json", "w") as f:
        json.dump(overview, f, indent=2)
        
    # 6. Symbol Specific Flow
    (DASHBOARD_DIR / "symbols").mkdir(exist_ok=True)
    for symbol, group in flow_df.groupby("symbol"):
        symbol_scores = final_scores[final_scores["symbol"] == symbol].iloc[0].to_dict()
        
        flow_data = {
            "symbol": symbol,
            "date": date,
            "total_quantity": int(group["market_qty"].iloc[0]),
            "total_amount": float(group["market_amount"].iloc[0]),
            "top_buyers": group.nlargest(5, "buy_qty")[["broker", "buy_qty", "buy_amount", "buy_share"]].to_dict(orient="records"),
            "top_sellers": group.nlargest(5, "sell_qty")[["broker", "sell_qty", "sell_amount", "sell_share"]].to_dict(orient="records"),
            "scores": {k: v for k, v in symbol_scores.items() if k != "symbol"}
        }
        
        with open(DASHBOARD_DIR / "symbols" / f"{symbol}_broker_flow.json", "w") as f:
            json.dump(flow_data, f, indent=2)
            
    logger.info("Broker V2 artifacts generated.")

if __name__ == "__main__":
    from nepsense.collectors.floorsheet import generate_mock_floorsheet
    date = "2026-05-12"
    # Ensure symbols match previous runs or are broad enough
    symbols = ["NABIL", "GBIME", "NTC", "PCBL", "HRL", "UPPER", "HDL", "SHL", "STC", "NICL"]
    generate_mock_floorsheet(date, symbols)
    generate_broker_artifacts_v2(date)
