"""Advanced scoring engine for NEPSE symbols."""

import numpy as np
import pandas as pd
from typing import Dict

def calculate_trend_score(df: pd.DataFrame) -> pd.Series:
    """Trend Score (0-100): Based on price vs SMAs and MACD."""
    price = df["adjusted_close"]
    trend_sma20 = (price > df["sma_20"]).astype(int)
    trend_sma50 = (price > df["sma_50"]).astype(int)
    trend_macd = (df["macd_hist"] > 0).astype(int)
    return (trend_sma20 * 0.4 + trend_sma50 * 0.3 + trend_macd * 0.3) * 100

def calculate_momentum_score(df: pd.DataFrame) -> pd.Series:
    """Momentum Score (0-100): Weighted returns over multiple timeframes."""
    return ((df["ret_5d"] > 0).astype(int) * 0.2 + 
            (df["ret_20d"] > 0).astype(int) * 0.3 + 
            (df["ret_60d"] > 0).astype(int) * 0.5) * 100

def calculate_liquidity_score(df: pd.DataFrame) -> pd.Series:
    """Liquidity Score (0-100): Based on turnover vs benchmark."""
    # Simplified bounded log-based score
    score = np.log1p(df["turnover"].rolling(20).mean())
    return np.clip((score / 15) * 100, 0, 100)

def calculate_risk_score(df: pd.DataFrame) -> pd.Series:
    """Risk Score (0-100): Inverse of volatility and drawdown."""
    # High score means low risk
    risk = (df["vol_20"] * 100) + (df["drawdown"].abs() * 100)
    return 100 - np.clip(risk, 0, 100)

def compute_watch_score(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate all scores into a single watch score."""
    df = df.copy()
    
    df["score_trend"] = calculate_trend_score(df)
    df["score_momentum"] = calculate_momentum_score(df)
    df["score_liquidity"] = calculate_liquidity_score(df)
    df["score_risk"] = calculate_risk_score(df)
    
    df["watch_score"] = (
        df["score_trend"] * 0.4 + 
        df["score_momentum"] * 0.3 + 
        df["score_liquidity"] * 0.2 + 
        df["score_risk"] * 0.1
    ).round(1)
    
    return df
