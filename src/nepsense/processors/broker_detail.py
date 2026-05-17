from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def build_broker_detail(df: pd.DataFrame, broker: str, date: str) -> Dict[str, Any]:
    broker = str(broker).zfill(2)

    buy_df = df[df["buyer_broker"].astype(str).str.zfill(2) == broker].copy()
    sell_df = df[df["seller_broker"].astype(str).str.zfill(2) == broker].copy()

    buy_by_symbol = (
        buy_df.groupby("symbol")
        .agg(
            buy_qty=("quantity", "sum"),
            buy_amt=("amount", "sum"),
            buy_trades=("transaction_no", "count"),
        )
        .reset_index()
    )

    sell_by_symbol = (
        sell_df.groupby("symbol")
        .agg(
            sell_qty=("quantity", "sum"),
            sell_amt=("amount", "sum"),
            sell_trades=("transaction_no", "count"),
        )
        .reset_index()
    )

    symbol_flow = buy_by_symbol.merge(sell_by_symbol, on="symbol", how="outer").fillna(0)

    symbol_flow["net_qty"] = symbol_flow["buy_qty"] - symbol_flow["sell_qty"]
    symbol_flow["net_amt"] = symbol_flow["buy_amt"] - symbol_flow["sell_amt"]

    symbol_flow["avg_buy_price"] = symbol_flow.apply(
        lambda r: r["buy_amt"] / r["buy_qty"] if r["buy_qty"] > 0 else None,
        axis=1,
    )
    symbol_flow["avg_sell_price"] = symbol_flow.apply(
        lambda r: r["sell_amt"] / r["sell_qty"] if r["sell_qty"] > 0 else None,
        axis=1,
    )

    symbol_totals = (
        df.groupby("symbol")
        .agg(symbol_total_qty=("quantity", "sum"), symbol_total_amt=("amount", "sum"))
        .reset_index()
    )

    symbol_flow = symbol_flow.merge(symbol_totals, on="symbol", how="left")

    symbol_flow["broker_participation_pct"] = (
        (symbol_flow["buy_qty"] + symbol_flow["sell_qty"])
        / symbol_flow["symbol_total_qty"]
        * 100
    )

    def classify_direction(net_qty: float) -> str:
        if net_qty > 0:
            return "Accumulating"
        if net_qty < 0:
            return "Distributing"
        return "Neutral"

    symbol_flow["direction"] = symbol_flow["net_qty"].apply(classify_direction)

    net_buy_stocks = (
        symbol_flow[symbol_flow["net_qty"] > 0]
        .sort_values("net_qty", ascending=False)
        .to_dict(orient="records")
    )

    net_sell_stocks = (
        symbol_flow[symbol_flow["net_qty"] < 0]
        .assign(abs_net_qty=lambda x: x["net_qty"].abs())
        .sort_values("abs_net_qty", ascending=False)
        .drop(columns=["abs_net_qty"])
        .to_dict(orient="records")
    )

    # Counterparties
    buy_counterparties = (
        buy_df.groupby("seller_broker")
        .agg(quantity=("quantity", "sum"), amount=("amount", "sum"))
        .reset_index()
        .rename(columns={"seller_broker": "broker"})
    )

    sell_counterparties = (
        sell_df.groupby("buyer_broker")
        .agg(quantity=("quantity", "sum"), amount=("amount", "sum"))
        .reset_index()
        .rename(columns={"buyer_broker": "broker"})
    )

    counterparties = (
        pd.concat([buy_counterparties, sell_counterparties], ignore_index=True)
        .groupby("broker")
        .agg(quantity=("quantity", "sum"), amount=("amount", "sum"))
        .reset_index()
        .sort_values("quantity", ascending=False)
        .head(15)
    )

    counterparties["relationship"] = broker + " ↔ " + counterparties["broker"].astype(str)

    # Largest trades involving this broker
    buy_trades = buy_df.copy()
    buy_trades["side"] = "BUY"
    buy_trades["counterparty_broker"] = buy_trades["seller_broker"]

    sell_trades = sell_df.copy()
    sell_trades["side"] = "SELL"
    sell_trades["counterparty_broker"] = sell_trades["buyer_broker"]

    largest_trades = (
        pd.concat([buy_trades, sell_trades], ignore_index=True)
        .sort_values("amount", ascending=False)
        .head(20)
    )

    largest_trade_cols = [
        "transaction_no",
        "symbol",
        "side",
        "counterparty_broker",
        "quantity",
        "rate",
        "amount",
    ]

    flags: List[str] = []

    total_buy_qty = float(buy_df["quantity"].sum())
    total_sell_qty = float(sell_df["quantity"].sum())
    total_net_qty = total_buy_qty - total_sell_qty

    if total_net_qty > 0:
        flags.append("Net accumulation")
    elif total_net_qty < 0:
        flags.append("Net distribution")

    if not symbol_flow.empty:
        max_participation = symbol_flow["broker_participation_pct"].max()
        if max_participation >= 20:
            flags.append("High symbol participation")

    if not counterparties.empty and counterparties["quantity"].iloc[0] >= 0.2 * (
        total_buy_qty + total_sell_qty
    ):
        flags.append("Repeated counterparty activity")

    return {
        "broker": broker,
        "date": date,
        "summary": {
            "total_buy_qty": total_buy_qty,
            "total_sell_qty": total_sell_qty,
            "total_net_qty": total_net_qty,
            "total_buy_amt": float(buy_df["amount"].sum()) if not buy_df.empty else 0.0,
            "total_sell_amt": float(sell_df["amount"].sum()) if not sell_df.empty else 0.0,
            "total_net_amt": float((buy_df["amount"].sum() if not buy_df.empty else 0.0) - (sell_df["amount"].sum() if not sell_df.empty else 0.0)),
            "buy_symbols_count": int((symbol_flow["buy_qty"] > 0).sum()) if not symbol_flow.empty else 0,
            "sell_symbols_count": int((symbol_flow["sell_qty"] > 0).sum()) if not symbol_flow.empty else 0,
            "net_accumulation_symbols": int((symbol_flow["net_qty"] > 0).sum()) if not symbol_flow.empty else 0,
            "net_distribution_symbols": int((symbol_flow["net_qty"] < 0).sum()) if not symbol_flow.empty else 0,
        },
        "net_buy_stocks": net_buy_stocks,
        "net_sell_stocks": net_sell_stocks,
        "top_counterparties": counterparties.to_dict(orient="records"),
        "largest_trades": largest_trades[largest_trade_cols].to_dict(orient="records") if not largest_trades.empty else [],
        "flags": flags,
    }


def build_all_broker_details(df: pd.DataFrame, date: str) -> Dict[str, Dict[str, Any]]:
    brokers = sorted(
        set(df["buyer_broker"].astype(str).str.zfill(2))
        | set(df["seller_broker"].astype(str).str.zfill(2))
    )

    return {
        broker: build_broker_detail(df, broker, date)
        for broker in brokers
    }
