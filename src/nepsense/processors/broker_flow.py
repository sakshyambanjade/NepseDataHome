"""Process floorsheet data to extract broker-level flow metrics."""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

BROKER_DATA_DIR = DATA_DIR / "broker"

def process_daily_broker_flow(floorsheet_path: Path):
    """Aggregate daily floorsheet into broker-symbol net flows."""
    df = pd.read_csv(floorsheet_path)
    date = df["date"].iloc[0]
    
    # 1. Buyer aggregation
    buyers = df.groupby(["symbol", "buyer_broker"]).agg(
        buy_qty=("quantity", "sum"),
        buy_amount=("amount", "sum"),
        buy_trades=("transaction_no", "count")
    ).reset_index().rename(columns={"buyer_broker": "broker"})
    
    # 2. Seller aggregation
    sellers = df.groupby(["symbol", "seller_broker"]).agg(
        sell_qty=("quantity", "sum"),
        sell_amount=("amount", "sum"),
        sell_trades=("transaction_no", "count")
    ).reset_index().rename(columns={"seller_broker": "broker"})
    
    # 3. Merge to get Net Flow
    flow = pd.merge(buyers, sellers, on=["symbol", "broker"], how="outer").fillna(0)
    
    flow["net_qty"] = flow["buy_qty"] - flow["sell_qty"]
    flow["net_amount"] = flow["buy_amount"] - flow["sell_amount"]
    flow["total_qty"] = flow["buy_qty"] + flow["sell_qty"]
    flow["total_amount"] = flow["buy_amount"] + flow["sell_amount"]
    flow["date"] = date
    
    # 4. Symbol level stats
    symbol_stats = df.groupby("symbol").agg(
        market_qty=("quantity", "sum"),
        market_amount=("amount", "sum")
    ).reset_index()
    
    flow = flow.merge(symbol_stats, on="symbol")
    flow["buy_share"] = flow["buy_qty"] / flow["market_qty"]
    flow["sell_share"] = flow["sell_qty"] / flow["market_qty"]
    
    # 5. Cross trade detection
    cross = df[df["buyer_broker"] == df["seller_broker"]]
    cross_stats = cross.groupby(["symbol", "buyer_broker"])["amount"].sum().reset_index()
    cross_stats.columns = ["symbol", "broker", "cross_amount"]
    
    flow = flow.merge(cross_stats, on=["symbol", "broker"], how="left").fillna(0)
    flow["cross_ratio"] = flow["cross_amount"] / flow["market_amount"]
    
    BROKER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BROKER_DATA_DIR / f"flow_{date}.csv"
    flow.to_csv(output_path, index=False)
    logger.info(f"Saved broker flow to {output_path}")
    return flow

def calculate_concentration(flow_df: pd.DataFrame):
    """Calculate concentration metrics (HHI, Top 3 share)."""
    # Group by symbol
    stats = []
    for symbol, group in flow_df.groupby("symbol"):
        # Top 3 Buy Concentration
        top3_buy = group.nlargest(3, "buy_qty")["buy_share"].sum()
        top3_sell = group.nlargest(3, "sell_qty")["sell_share"].sum()
        
        # HHI
        buy_hhi = (group["buy_share"] ** 2).sum()
        sell_hhi = (group["sell_share"] ** 2).sum()
        
        stats.append({
            "symbol": symbol,
            "buy_concentration_3": top3_buy,
            "sell_concentration_3": top3_sell,
            "buy_hhi": buy_hhi,
            "sell_hhi": sell_hhi,
            "dominance_score": max(top3_buy, top3_sell) * 100
        })
        
    return pd.DataFrame(stats)
