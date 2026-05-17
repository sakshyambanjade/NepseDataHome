"""Bridge for Broker Intelligence static JSON generation (Production V2)."""

import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from nepsense.config import DASHBOARD_DIR, DATA_DIR
from nepsense.processors.floorsheet_intelligence import analyze_daily_floorsheet
from nepsense.processors.floorsheet_baseline import load_previous_floorsheet_tables, compute_symbol_baselines
from nepsense.processors.broker_detail import build_all_broker_details
from nepsense.processors.flow_database import build_flow_database
from nepsense.processors.flow_map import generate_flow_artifacts
from nepsense.processors.alerts import generate_alerts
from nepsense.processors.daily_report import generate_daily_report
from nepsense.processors.data_health import generate_data_health

logger = logging.getLogger(__name__)

# Directory for persistent intelligence history
INTELLIGENCE_DIR = DATA_DIR / "floorsheet" / "intelligence"

def clean_json(data):
    """Recursively clean dictionary/list of NaNs, Infinities for JSON compatibility."""
    import numpy as np
    if isinstance(data, list):
        return [clean_json(x) for x in data]
    if isinstance(data, dict):
        return {k: clean_json(v) for k, v in data.items()}
    if isinstance(data, (float, np.floating)):
        if np.isnan(data) or np.isinf(data):
            return None
    if pd.isna(data):
        return None
    return data

def generate_broker_artifacts(date: str):
    """
    Generate all floorsheet-related JSON artifacts for the dashboard.
    
    Reads from data/floorsheet/normalized/{date}.csv
    Writes to:
    - data/floorsheet/intelligence/{date}.json (Persistent History)
    - web/public/data/broker_overview.json
    - web/public/data/flowsheet_table.json
    - web/public/data/symbols/{SYMBOL}_broker_flow.json
    """
    floorsheet_path = DATA_DIR / "floorsheet" / "normalized" / f"{date}.csv"
    if not floorsheet_path.exists():
        files = sorted(list((DATA_DIR / "floorsheet" / "normalized").glob("*.csv")))
        if not files:
            logger.error(f"No floorsheet CSVs found in {DATA_DIR / 'floorsheet' / 'normalized'}")
            return
        floorsheet_path = files[-1]
        date = floorsheet_path.stem
        logger.warning(f"Exact date {date} not found. Using latest: {floorsheet_path}")
        
    logger.info(f"Loading historical baselines (last 20 days)...")
    history_df = load_previous_floorsheet_tables(days=20)
    baselines = compute_symbol_baselines(history_df)
    
    logger.info(f"Processing Full Floorsheet Intelligence for {date}...")
    df = pd.read_csv(floorsheet_path)
    
    # Compute all metrics using the intelligence engine
    results = analyze_daily_floorsheet(df, date, baselines=baselines)
    if not results:
        logger.warning(f"No results generated for {date}")
        return
        
    results_df = pd.DataFrame(results)
    
    # 0. Save Persistent Intelligence History (before any UI-specific filtering)
    INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(INTELLIGENCE_DIR / f"{date}.json", "w") as f:
        json.dump(clean_json(results), f, indent=2)
    
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
        json.dump(clean_json(overview), f, indent=2)
    
    # 2. Flowsheet Table JSON (for the new table page)
    with open(DASHBOARD_DIR / "flowsheet_table.json", "w") as f:
        json.dump(clean_json(results), f, indent=2)
    
    # 3. Individual Symbol JSONs
    symbol_dir = DASHBOARD_DIR / "symbols"
    symbol_dir.mkdir(exist_ok=True)
    for res in results:
        symbol = res["symbol"]
        safe_symbol = str(symbol).replace("/", "-")
        with open(symbol_dir / f"{safe_symbol}_broker_flow.json", "w") as f:
            json.dump(clean_json(res), f, indent=2)

    # 4. Individual Broker JSONs
    broker_details = build_all_broker_details(df, date)
    
    broker_dir = DASHBOARD_DIR / "brokers"
    broker_dir.mkdir(parents=True, exist_ok=True)
    
    for broker, detail in broker_details.items():
        with open(broker_dir / f"{broker}.json", "w") as f:
            json.dump(clean_json(detail), f, indent=2)
            
    # 5. Build Flow Database & Generate Flow Artifacts
    logger.info(f"Building DuckDB Flow Database for {date}...")
    build_flow_database(date)
    logger.info(f"Generating Flow Map Artifacts for {date}...")
    generate_flow_artifacts(date)

    # 6. Trust Layer: Alerts and Daily Report
    logger.info(f"Generating Flow Alerts for {date}...")
    generate_alerts(results, date)
    
    logger.info(f"Generating Daily Report for {date}...")
    generate_daily_report(results, date)
    
    logger.info(f"Generating Data Health Metrics for {date}...")
    generate_data_health(df, date, bool(baselines))

    logger.info(f"Generated {len(results)} intelligence artifacts for {date}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()
    
    # Default to a known date if not provided
    date = args.date or "2026-05-12"
    generate_broker_artifacts(date)
