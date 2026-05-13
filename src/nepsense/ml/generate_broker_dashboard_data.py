"""Bridge for Broker Intelligence static JSON generation (Production V2)."""

import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from nepsense.config import DASHBOARD_DIR, DATA_DIR
from nepsense.processors.floorsheet_intelligence import analyze_daily_floorsheet

logger = logging.getLogger(__name__)

def generate_broker_artifacts(date: str):
    """
    Generate all floorsheet-related JSON artifacts for the dashboard.
    
    Reads from data/floorsheet/normalized/{date}.csv
    Writes to:
    - web/public/data/broker_overview.json
    - web/public/data/flowsheet_table.json
    - web/public/data/symbols/{SYMBOL}_broker_flow.json
    """
    floorsheet_path = DATA_DIR / "floorsheet" / "normalized" / f"{date}.csv"
    if not floorsheet_path.exists():
        # Try to find any file in the directory if exact date not found (fallback for demo)
        files = list((DATA_DIR / "floorsheet" / "normalized").glob("*.csv"))
        if not files:
            logger.error(f"No floorsheet CSVs found in {DATA_DIR / 'floorsheet' / 'normalized'}")
            return
        floorsheet_path = files[-1]
        date = floorsheet_path.stem
        logger.warning(f"Exact date {date} not found. Using latest: {floorsheet_path}")
        
    logger.info(f"Processing Full Floorsheet Intelligence for {date}...")
    df = pd.read_csv(floorsheet_path)
    
    # Compute all metrics using the intelligence engine
    results = analyze_daily_floorsheet(df, date)
    if not results:
        logger.warning(f"No results generated for {date}")
        return
        
    results_df = pd.DataFrame(results)
    
    # 1. Broker Overview JSON
    overview = {
      "generated_at": datetime.now().isoformat(),
      "date": date,
      "most_accumulated": results_df.nlargest(15, "accumulation_score").to_dict(orient="records"),
      "most_distributed": results_df.nlargest(15, "distribution_score").to_dict(orient="records"),
      "smart_money_ranking": results_df.nlargest(15, "operator_like_score").to_dict(orient="records"),
      "operator_watchlist": results_df.nlargest(20, "operator_like_score").to_dict(orient="records")
    }
    
    # Ensure DASHBOARD_DIR exists
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save overview
    with open(DASHBOARD_DIR / "broker_overview.json", "w") as f:
        json.dump(overview, f, indent=2)
    
    # 2. Flowsheet Table JSON (for the new table page)
    with open(DASHBOARD_DIR / "flowsheet_table.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # 3. Individual Symbol JSONs
    symbol_dir = DASHBOARD_DIR / "symbols"
    symbol_dir.mkdir(exist_ok=True)
    for res in results:
        symbol = res["symbol"]
        with open(symbol_dir / f"{symbol}_broker_flow.json", "w") as f:
            json.dump(res, f, indent=2)
            
    logger.info(f"Generated {len(results)} intelligence artifacts for {date}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()
    
    # Default to a known date if not provided
    date = args.date or "2026-05-12"
    generate_broker_artifacts(date)
