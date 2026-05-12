"""Generate dashboard JSON artifacts for the frontend."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

def generate_dashboard_json(
    indicators_df: pd.DataFrame,
    output_dir: Path,
):
    """Generate all JSON artifacts for the React dashboard.
    
    Files generated:
    - market_overview.json
    - symbols_index.json
    - symbols/[SYMBOL].json
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "symbols").mkdir(exist_ok=True)
    
    # Ensure date is datetime
    indicators_df["date"] = pd.to_datetime(indicators_df["date"])
    latest_date = indicators_df["date"].max()
    latest_df = indicators_df[indicators_df["date"] == latest_date]
    
    # Load ML predictions if available
    predictions_path = DATA_DIR / "features" / "predictions_latest.csv"
    if predictions_path.exists():
        preds_df = pd.read_csv(predictions_path)
        latest_df = latest_df.merge(preds_df[["symbol", "p_up_5d"]], on="symbol", how="left")
        logger.info("Merged ML predictions into dashboard")

    # 1. Market Overview
    market_overview = {
        "generated_at": datetime.now().isoformat(),
        "date": latest_date.strftime("%Y-%m-%d"),
        "active_symbols": len(latest_df),
        "total_volume": int(latest_df["volume"].sum()),
        "total_turnover": float(latest_df["turnover"].sum()),
        "total_transactions": int(latest_df["transactions"].sum()) if "transactions" in latest_df.columns else 0,
        "advancers": int((latest_df["ret_1d"] > 0).sum()),
        "decliners": int((latest_df["ret_1d"] < 0).sum()),
        "unchanged": int((latest_df["ret_1d"] == 0).sum()),
        "top_gainers": latest_df.nlargest(10, "ret_1d")[["symbol", "close", "ret_1d"]].to_dict(orient="records"),
        "top_losers": latest_df.nsmallest(10, "ret_1d")[["symbol", "close", "ret_1d"]].to_dict(orient="records"),
        "top_turnover": latest_df.nlargest(10, "turnover")[["symbol", "close", "turnover"]].to_dict(orient="records"),
    }
    
    with open(output_dir / "market_overview.json", "w") as f:
        json.dump(market_overview, f, indent=2)
        
    # 2. Symbols Index (Lightweight list for screener)
    # Filter columns to keep index small
    index_cols = [
        "symbol", "date", "close", "adjusted_close", "ret_1d", "ret_5d", "ret_20d",
        "rsi_14", "macd_hist", "adx_14", "atr_pct", "vol_20", "drawdown",
        "liquidity_score", "sma_20_gap", "sma_50_gap",
        "watch_score", "score_trend", "score_momentum", "score_liquidity", "score_risk",
        "p_up_5d"
    ]
    # Filter to only columns that exist
    index_cols = [c for c in index_cols if c in latest_df.columns]
    
    symbols_index = latest_df[index_cols].to_dict(orient="records")
    # Convert dates to strings
    for item in symbols_index:
        item["date"] = item["date"].strftime("%Y-%m-%d")
        # Handle NaNs
        for k, v in item.items():
            if isinstance(v, float) and np.isnan(v):
                item[k] = None

    with open(output_dir / "symbols_index.json", "w") as f:
        json.dump(symbols_index, f, indent=2)
        
    # 3. Individual Symbol Details (Full History)
    for symbol, group in indicators_df.groupby("symbol"):
        group = group.sort_values("date")
        
        # Limit history for symbol detail if needed, or keep all
        # Converting to dict with list for each column (better for charts)
        history = {}
        for col in group.columns:
            if col == "date":
                history[col] = group[col].dt.strftime("%Y-%m-%d").tolist()
            else:
                # Replace NaN with None for JSON
                history[col] = [None if isinstance(x, float) and np.isnan(x) else x for x in group[col].tolist()]
        
        symbol_detail = {
            "symbol": symbol,
            "last_updated": latest_date.strftime("%Y-%m-%d"),
            "history": history,
            "latest": history["close"][-1] if history["close"] else None,
        }
        
        with open(output_dir / "symbols" / f"{symbol}.json", "w") as f:
            json.dump(symbol_detail, f)

    logger.info(f"Generated dashboard artifacts in {output_dir}")
