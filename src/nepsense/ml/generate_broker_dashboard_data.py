"""Bridge for Broker Intelligence static JSON generation."""

import logging
import json
from pathlib import Path
import pandas as pd
from nepsense.config import DASHBOARD_DIR, DATA_DIR
from nepsense.processors.broker_flow import process_daily_broker_flow, calculate_concentration
from nepsense.processors.broker_scores import calculate_accumulation_score, calculate_smart_money_score, detect_operator_patterns

logger = logging.getLogger(__name__)

def generate_broker_artifacts(date: str):
    """Generate all broker-related JSON for the dashboard."""
    floorsheet_path = DATA_DIR / "floorsheet" / "normalized" / f"{date}.csv"
    if not floorsheet_path.exists():
        logger.error(f"Floorsheet not found for {date}")
        return
        
    # 1. Process Flow
    flow_df = process_daily_broker_flow(floorsheet_path)
    
    # 2. Calculate Stats & Scores
    conc_df = calculate_concentration(flow_df)
    acc_df = calculate_accumulation_score(flow_df, conc_df)
    smart_df = calculate_smart_money_score(acc_df, flow_df)
    op_df = detect_operator_patterns(flow_df)
    
    print(f"conc_df columns: {conc_df.columns.tolist()}")
    print(f"acc_df columns: {acc_df.columns.tolist()}")
    
    # Merge all scores
    scores_df = conc_df.merge(acc_df, on="symbol").merge(smart_df, on="symbol").merge(op_df, on="symbol")
    print(f"Scores columns: {scores_df.columns.tolist()}")
    
    # 3. Generate Overview JSON
    overview = {
        "date": date,
        "most_accumulated": scores_df.nlargest(10, "accumulation_score")[["symbol", "accumulation_score"]].to_dict(orient="records"),
        "smart_money_ranking": scores_df.nlargest(10, "smart_money_score")[["symbol", "smart_money_score"]].to_dict(orient="records"),
        "unusual_activity": op_df[op_df["operator_like_score"] > 50].to_dict(orient="records")
    }
    
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    with open(DASHBOARD_DIR / "broker_overview.json", "w") as f:
        json.dump(overview, f, indent=2)
        
    # 4. Generate Symbol Broker Flow JSON
    (DASHBOARD_DIR / "symbols").mkdir(exist_ok=True)
    for symbol, group in flow_df.groupby("symbol"):
        symbol_scores = scores_df[scores_df["symbol"] == symbol].iloc[0].to_dict()
        
        flow_data = {
            "symbol": symbol,
            "date": date,
            "total_quantity": int(group["buy_qty"].sum()),
            "total_amount": float(group["buy_amount"].sum()),
            "top_buyers": group.nlargest(5, "buy_qty")[["broker", "buy_qty", "buy_amount", "buy_share"]].to_dict(orient="records"),
            "top_sellers": group.nlargest(5, "sell_qty")[["broker", "sell_qty", "sell_amount", "sell_share"]].to_dict(orient="records"),
            "scores": {k: v for k, v in symbol_scores.items() if k != "symbol"}
        }
        
        with open(DASHBOARD_DIR / "symbols" / f"{symbol}_broker_flow.json", "w") as f:
            json.dump(flow_data, f, indent=2)
            
    logger.info("Broker artifacts generated successfully.")

if __name__ == "__main__":
    # Mock run for demo
    from nepsense.collectors.floorsheet import generate_mock_floorsheet
    date = "2026-05-12"
    generate_mock_floorsheet(date, ["NABIL", "GBIME", "NTC", "PCBL", "HRL"])
    generate_broker_artifacts(date)
