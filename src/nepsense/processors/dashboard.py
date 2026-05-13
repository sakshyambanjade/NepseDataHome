"""Generate dashboard JSON artifacts for the frontend."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from nepsense.config import DATA_DIR, DASHBOARD_DIR

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

    # Sector performance
    latest_df["sector"] = latest_df["sector"].fillna("Others").replace("", "Others")
    sector_perf = latest_df.groupby("sector")["ret_1d"].mean().reset_index()
    sector_perf["ret_1d"] = sector_perf["ret_1d"].round(4)
    
    # helper to clean NaNs for JSON serialization
    def clean_json(data):
        if isinstance(data, list):
            return [clean_json(x) for x in data]
        if isinstance(data, dict):
            return {k: clean_json(v) for k, v in data.items()}
        if isinstance(data, float) and np.isnan(data):
            return None
        return data

    # 1. Market Overview
    market_overview = {
        "generated_at": datetime.now().isoformat(),
        "date": latest_date.strftime("%Y-%m-%d"),
        "active_symbols": len(latest_df),
        "total_volume": int(latest_df["volume"].sum()) if not np.isnan(latest_df["volume"].sum()) else 0,
        "total_turnover": float(latest_df["turnover"].sum()) if not np.isnan(latest_df["turnover"].sum()) else 0.0,
        "total_transactions": int(latest_df["transactions"].sum()) if "transactions" in latest_df.columns and not np.isnan(latest_df["transactions"].sum()) else 0,
        "advancers": int((latest_df["ret_1d"] > 0).sum()),
        "decliners": int((latest_df["ret_1d"] < 0).sum()),
        "unchanged": int((latest_df["ret_1d"] == 0).sum()),
        "market_regime": int(latest_df["market_regime"].mode()[0]) if "market_regime" in latest_df.columns and not latest_df["market_regime"].empty else 0,
        "sector_performance": sector_perf.to_dict(orient="records"),
        "top_gainers": latest_df.nlargest(10, "ret_1d")[["symbol", "close", "ret_1d"]].to_dict(orient="records"),
        "top_losers": latest_df.nsmallest(10, "ret_1d")[["symbol", "close", "ret_1d"]].to_dict(orient="records"),
        "top_turnover": latest_df.nlargest(10, "turnover")[["symbol", "close", "turnover"]].to_dict(orient="records"),
    }
    
    with open(output_dir / "market_overview.json", "w") as f:
        json.dump(clean_json(market_overview), f, indent=2)
        
    # 2. Symbols Index (Lightweight list for screener)
    # Filter columns to keep index small
    index_cols = [
        "symbol", "date", "close", "adjusted_close", "ret_1d", "ret_5d", "ret_20d",
        "rsi_14", "macd_hist", "adx_14", "atr_pct", "vol_20", "drawdown",
        "liquidity_score", "sma_20_gap", "sma_50_gap", "vwap", "market_regime",
        "watch_score", "score_trend", "score_momentum", "score_liquidity", "score_risk",
        "p_up_5d"
    ]
    # Filter to only columns that exist
    index_cols = [c for c in index_cols if c in latest_df.columns]
    
    symbols_index = latest_df[index_cols].to_dict(orient="records")
    # Convert dates to strings
    for item in symbols_index:
        item["date"] = item["date"].strftime("%Y-%m-%d")

    with open(output_dir / "symbols_index.json", "w") as f:
        json.dump(clean_json(symbols_index), f, indent=2)
        
        # 3. Individual Symbol Details (Full History)
    for symbol, group in indicators_df.groupby("symbol"):
        group = group.sort_values("date")
        
        # Sanitize symbol for filename (e.g. GBILD84/85 -> GBILD84-85)
        safe_symbol = str(symbol).replace("/", "-")
        
        # Limit history for symbol detail if needed, or keep all
        # Converting to dict with list for each column (better for charts)
        history = {}
        for col in group.columns:
            if col == "date":
                history[col] = group[col].dt.strftime("%Y-%m-%d").tolist()
            else:
                history[col] = group[col].tolist()
        
        symbol_detail = {
            "symbol": symbol,
            "last_updated": latest_date.strftime("%Y-%m-%d"),
            "history": history,
            "latest": history["close"][-1] if history["close"] else None,
        }
        
        with open(output_dir / "symbols" / f"{safe_symbol}.json", "w") as f:
            json.dump(clean_json(symbol_detail), f)


def generate_dashboard_artifacts(output_dir: Path = DASHBOARD_DIR):
    """Convenience wrapper for generating artifacts using the default output directory."""
    from nepsense.config import DATA_DIR
    indicators_path = DATA_DIR / "features" / "indicators_all.csv"
    if not indicators_path.exists():
        logger.error(f"Indicators not found at {indicators_path}")
        return
    
    df = pd.read_csv(indicators_path)
    generate_dashboard_json(df, output_dir)
