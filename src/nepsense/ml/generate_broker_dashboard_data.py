"""Bridge for Broker Intelligence static JSON generation (Production V2)."""

import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from nepsense.config import DASHBOARD_DIR, DATA_DIR
from nepsense.processors.floorsheet_intelligence import analyze_daily_floorsheet
from nepsense.processors.floorsheet_baseline import load_previous_floorsheet_tables, compute_symbol_baselines

logger = logging.getLogger(__name__)

# Directory for persistent intelligence history
INTELLIGENCE_DIR = DATA_DIR / "floorsheet" / "intelligence"

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
        json.dump(results, f, indent=2)
    
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

    # 4. Individual Broker JSONs
    # We need to aggregate across all symbols for each broker
    broker_stats = {}
    
    # Process raw df for total buy/sell volume and counterparty info
    for _, row in df.iterrows():
        b = row['buyer_broker']
        s = row['seller_broker']
        
        # Initialize
        for brk in [b, s]:
            if brk not in broker_stats:
                broker_stats[brk] = {
                    "broker": brk,
                    "buy_qty": 0, "sell_qty": 0,
                    "buy_amt": 0, "sell_amt": 0,
                    "symbols": {},
                    "counterparties": {}
                }
        
        # Buy side
        broker_stats[b]["buy_qty"] += row['quantity']
        broker_stats[b]["buy_amt"] += row['amount']
        sym = row['symbol']
        broker_stats[b]["symbols"][sym] = broker_stats[b]["symbols"].get(sym, {"buy": 0, "sell": 0})
        broker_stats[b]["symbols"][sym]["buy"] += row['quantity']
        broker_stats[b]["counterparties"][s] = broker_stats[b]["counterparties"].get(s, 0) + row['quantity']
        
        # Sell side
        broker_stats[s]["sell_qty"] += row['quantity']
        broker_stats[s]["sell_amt"] += row['amount']
        broker_stats[s]["symbols"][sym] = broker_stats[s]["symbols"].get(sym, {"buy": 0, "sell": 0})
        broker_stats[s]["symbols"][sym]["sell"] += row['quantity']
        broker_stats[s]["counterparties"][b] = broker_stats[s]["counterparties"].get(b, 0) + row['quantity']

    broker_dir = DASHBOARD_DIR / "brokers"
    broker_dir.mkdir(exist_ok=True)
    
    for brk, stats in broker_stats.items():
        # Finalize stats
        net_buy_stocks = []
        net_sell_stocks = []
        for sym, q in stats["symbols"].items():
            net = q["buy"] - q["sell"]
            if net > 0: net_buy_stocks.append({"symbol": sym, "net_qty": net})
            elif net < 0: net_sell_stocks.append({"symbol": sym, "net_qty": abs(net)})
            
        top_counterparties = sorted(stats["counterparties"].items(), key=lambda x: x[1], reverse=True)[:10]
        
        broker_data = {
            "broker": brk,
            "date": date,
            "total_buy_qty": int(stats["buy_qty"]),
            "total_sell_qty": int(stats["sell_qty"]),
            "total_net_qty": int(stats["buy_qty"] - stats["sell_qty"]),
            "total_buy_amt": float(stats["buy_amt"]),
            "total_sell_amt": float(stats["sell_amt"]),
            "net_buy_stocks": sorted(net_buy_stocks, key=lambda x: x["net_qty"], reverse=True),
            "net_sell_stocks": sorted(net_sell_stocks, key=lambda x: x["net_qty"], reverse=True),
            "top_counterparties": [{"broker": c[0], "qty": int(c[1])} for c in top_counterparties]
        }
        
        # Match with intelligence results to find exposure
        # (This helps find which symbols this broker was most dominant in)
        exposure = []
        for res in results:
            # Check if this broker is in top_net_buyers or sellers
            for b_info in res.get("top_net_buyers", []):
                if b_info["broker"] == brk:
                    exposure.append({"symbol": res["symbol"], "type": "accumulation", "score": res["accumulation_score"]})
            for s_info in res.get("top_net_sellers", []):
                if s_info["broker"] == brk:
                    exposure.append({"symbol": res["symbol"], "type": "distribution", "score": res["distribution_score"]})
        
        broker_data["exposure"] = sorted(exposure, key=lambda x: x["score"], reverse=True)
        
        with open(broker_dir / f"{brk}.json", "w") as f:
            json.dump(broker_data, f, indent=2)
            
    logger.info(f"Generated {len(results)} intelligence artifacts for {date}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()
    
    # Default to a known date if not provided
    date = args.date or "2026-05-12"
    generate_broker_artifacts(date)
