"""Process floorsheet data to extract broker-level flow metrics."""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

BROKER_DATA_DIR = DATA_DIR / "broker"

def process_daily_broker_flow(floorsheet_path: Path):
    """Aggregate daily floorsheet into broker-symbol net flows with V2 metrics."""
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
    flow["avg_buy_price"] = np.where(flow["buy_qty"] > 0, flow["buy_amount"] / flow["buy_qty"], 0)
    flow["avg_sell_price"] = np.where(flow["sell_qty"] > 0, flow["sell_amount"] / flow["sell_qty"], 0)
    flow["date"] = date
    
    # 4. Symbol level stats
    symbol_stats = df.groupby("symbol").agg(
        market_qty=("quantity", "sum"),
        market_amount=("amount", "sum"),
        trade_count=("transaction_no", "count"),
        active_brokers=("buyer_broker", "nunique") # Rough estimate
    ).reset_index()
    
    flow = flow.merge(symbol_stats, on="symbol")
    flow["buy_share"] = flow["buy_qty"] / flow["market_qty"]
    flow["sell_share"] = flow["sell_qty"] / flow["market_qty"]
    flow["vwap"] = flow["market_amount"] / flow["market_qty"]
    
    # Price Impact
    flow["buy_vwap_dev"] = np.maximum(0, (flow["avg_buy_price"] / flow["vwap"]) - 1)
    flow["sell_vwap_dev"] = np.maximum(0, 1 - (flow["avg_sell_price"] / flow["vwap"]))
    
    # 5. Cross trade detection
    cross = df[df["buyer_broker"] == df["seller_broker"]]
    cross_stats = cross.groupby(["symbol", "buyer_broker"])["amount"].sum().reset_index()
    cross_stats.columns = ["symbol", "broker", "cross_amount"]
    
    flow = flow.merge(cross_stats, on=["symbol", "broker"], how="left").fillna(0)
    flow["cross_ratio"] = flow["cross_amount"] / flow["market_amount"]
    
    # 6. Broker Pairs (Repeated Pair Score)
    df["pair"] = df["buyer_broker"].astype(str) + "-" + df["seller_broker"].astype(str)
    pairs = df.groupby(["symbol", "pair"])["quantity"].sum().reset_index()
    
    BROKER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BROKER_DATA_DIR / f"flow_{date}.csv"
    flow.to_csv(output_path, index=False)
    
    return flow, pairs

def calculate_concentration_v2(flow_df: pd.DataFrame, pairs_df: pd.DataFrame):
    """V2 Concentration and Pattern metrics."""
    stats = []
    for symbol, group in flow_df.groupby("symbol"):
        # Basic concentration
        top3_buy = group.nlargest(3, "buy_qty")["buy_share"].sum()
        top3_sell = group.nlargest(3, "sell_qty")["sell_share"].sum()
        buy_hhi = (group["buy_share"] ** 2).sum()
        
        # Pairs
        sym_pairs = pairs_df[pairs_df["symbol"] == symbol]
        market_qty = group["market_qty"].iloc[0]
        top3_pair_share = sym_pairs.nlargest(3, "quantity")["quantity"].sum() / market_qty
        
        # Max Price Impact
        max_buy_impact = group["buy_vwap_dev"].max()
        max_sell_impact = group["sell_vwap_dev"].max()
        price_impact_score = np.clip(max(max_buy_impact, max_sell_impact) / 0.02 * 100, 0, 100)

        stats.append({
            "symbol": symbol,
            "buy_concentration_3": top3_buy,
            "sell_concentration_3": top3_sell,
            "buy_hhi": buy_hhi,
            "top_3_pair_share": top3_pair_share,
            "price_impact_score": price_impact_score,
            "trade_count": group["trade_count"].iloc[0],
            "active_brokers": group["active_brokers"].iloc[0],
            "turnover": group["market_amount"].iloc[0]
        })
        
    return pd.DataFrame(stats)
