"""Technical indicators for NEPSE data."""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import List, Optional

logger = logging.getLogger(__name__)

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all standard indicators for a symbol's price history.
    
    Expected columns: date, symbol, adjusted_open, adjusted_high, adjusted_low, adjusted_close, volume, turnover, transactions
    
    Returns:
        DataFrame with indicators appended
    """
    df = df.copy()
    df = df.sort_values("date")
    
    # Use adjusted close for most price-based indicators
    price = df["adjusted_close"]
    high = df["adjusted_high"]
    low = df["adjusted_low"]
    
    # SMA (20, 50, 200)
    for n in [20, 50, 200]:
        df[f"sma_{n}"] = price.rolling(window=n).mean()
        df[f"sma_{n}_gap"] = (price / df[f"sma_{n}"]) - 1
        
    # EMA (12, 26, 20, 50)
    for n in [12, 20, 26, 50]:
        df[f"ema_{n}"] = price.ewm(span=n, adjust=False).mean()
        
    # MACD (12, 26, 9)
    df["macd"] = df["ema_12"] - df["ema_26"]
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    
    # RSI (14)
    delta = price.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi_14"] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands (20, 2)
    df["bb_mid"] = df["sma_20"]
    df["bb_std"] = price.rolling(window=20).std()
    df["bb_upper"] = df["bb_mid"] + (2 * df["bb_std"])
    df["bb_lower"] = df["bb_mid"] - (2 * df["bb_std"])
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
    
    # True Range and ATR (14)
    df["prev_close"] = price.shift(1)
    df["tr"] = pd.concat([
        high - low,
        (high - df["prev_close"]).abs(),
        (low - df["prev_close"]).abs()
    ], axis=1).max(axis=1)
    df["atr_14"] = df["tr"].ewm(alpha=1/14, adjust=False).mean()
    df["atr_pct"] = df["atr_14"] / price
    
    # ADX / DMI (14) - Wilder's Smoothing
    n = 14
    df["up_move"] = high.diff()
    df["down_move"] = low.diff().abs()
    
    df["plus_dm"] = np.where((df["up_move"] > df["down_move"]) & (df["up_move"] > 0), df["up_move"], 0)
    df["minus_dm"] = np.where((df["down_move"] > df["up_move"]) & (df["down_move"] > 0), df["down_move"], 0)
    
    df["plus_di"] = 100 * (df["plus_dm"].ewm(alpha=1/n, adjust=False).mean() / df["atr_14"])
    df["minus_di"] = 100 * (df["minus_dm"].ewm(alpha=1/n, adjust=False).mean() / df["atr_14"])
    df["dx"] = 100 * (df["plus_di"] - df["minus_di"]).abs() / (df["plus_di"] + df["minus_di"])
    df["adx_14"] = df["dx"].ewm(alpha=1/n, adjust=False).mean()
    
    # OBV
    df["obv"] = (np.sign(delta).fillna(0) * df["volume"]).cumsum()
    
    # MFI (14)
    tp = (high + low + price) / 3
    mf = tp * df["volume"]
    pos_mf = mf.where(tp > tp.shift(1), 0).rolling(window=14).sum()
    neg_mf = mf.where(tp < tp.shift(1), 0).rolling(window=14).sum()
    mfr = pos_mf / neg_mf
    df["mfi_14"] = 100 - (100 / (1 + mfr))
    
    # Momentum (1, 5, 10, 20, 60)
    for n in [1, 5, 10, 20, 60]:
        df[f"ret_{n}d"] = price.pct_change(n)
        
    # Volatility (20)
    df["vol_20"] = df["ret_1d"].rolling(window=20).std() * np.sqrt(252) # Annualized
    
    # Drawdown
    df["cum_max"] = price.cummax()
    df["drawdown"] = (price / df["cum_max"]) - 1
    
    # Liquidity Scores
    df["avg_turnover_20"] = df["turnover"].rolling(window=20).mean()
    df["avg_volume_20"] = df["volume"].rolling(window=20).mean()
    df["avg_trades_20"] = df["transactions"].rolling(window=20).mean()
    df["liquidity_score"] = np.log1p(df["avg_turnover_20"]) # Simplified log-based score
    
    # Cleanup temporary columns
    temp_cols = ["prev_close", "tr", "up_move", "down_move", "plus_dm", "minus_dm", "plus_di", "minus_di", "dx", "cum_max"]
    df = df.drop(columns=[c for c in temp_cols if c in df.columns])
    
    return df

def compute_all_indicators(input_root: Path, output_root: Path):
    """Iterate through all adjusted files and compute indicators."""
    files = sorted(input_root.glob("*/*/*.csv"))
    logger.info(f"Computing indicators for {len(files)} files...")
    
    # Since indicators need historical context, we should group by symbol
    # This might require loading all data or processing in chunks
    # For now, let's assume we can load by symbol or we have a consolidated file
    
    # A better approach for EOD indicators:
    # 1. Load all adjusted files into one massive DF (or use a database/parquet)
    # 2. Group by symbol
    # 3. Apply compute_indicators
    # 4. Save results
    
    # Implementation depends on the scale. For NEPSE, all history is manageable in memory.
    all_data = []
    for file in files:
        all_data.append(pd.read_csv(file))
        
    if not all_data:
        logger.warning("No adjusted data found.")
        return
        
    df = pd.concat(all_data, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    
    processed_dfs = []
    for symbol, group in df.groupby("symbol"):
        logger.info(f"Processing indicators for {symbol}")
        processed_dfs.append(compute_indicators(group))
        
    final_df = pd.concat(processed_dfs, ignore_index=True)
    
    # Save back to a feature store or updated adjusted files
    # For MVP, let's save to a feature store in data/features
    output_root.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_root / "indicators_all.csv", index=False)
    logger.info(f"Saved indicators to {output_root / 'indicators_all.csv'}")
