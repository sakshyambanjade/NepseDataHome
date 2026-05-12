"""Baseline ML model for NEPSE forward returns."""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc

from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

def prepare_ml_data(indicators_df: pd.DataFrame, horizon: int = 5):
    """Generate targets and features for ML.
    
    Target: 1 if forward_return > 0 else 0
    """
    df = indicators_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["symbol", "date"])
    
    # Target: 5-day forward return
    df["fwd_ret"] = df.groupby("symbol")["adjusted_close"].shift(-horizon) / df["adjusted_close"] - 1
    df["target"] = (df["fwd_ret"] > 0).astype(int)
    
    # Features
    features = [
        "ret_1d", "ret_5d", "ret_20d", "rsi_14", "macd_hist", "adx_14", 
        "atr_pct", "vol_20", "drawdown", "liquidity_score", "sma_20_gap", "sma_50_gap"
    ]
    
    # Optional: fill NaNs with zero or mean for demo purposes
    df[features] = df[features].fillna(0)
    
    # Only drop rows where we have absolutely no data (e.g. all features are zero)
    # but for now let's keep it and drop only in train_baseline
    
    return df, features

def train_baseline(df: pd.DataFrame, features: list):
    """Train a baseline Logistic Regression model using TimeSeriesSplit."""
    # Drop rows with missing targets or features only for training
    train_df = df.dropna(subset=features + ["target"])
    
    if train_df.empty:
        logger.info("No rows with targets found. Skipping training.")
        return None, None

    X = train_df[features]
    y = train_df["target"]
    dates = train_df["date"]
    
    # Time-based split (simplified)
    # Train on everything before the last 60 days
    cutoff = dates.max() - pd.Timedelta(days=60)
    train_mask = dates < cutoff
    test_mask = dates >= cutoff
    
    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]
    
    # Fallback to random split if time-based split is too small
    if len(X_train) < 10 or len(X_test) < 5:
        logger.info("Dataset too small for 60-day time split, falling back to random split")
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if len(X_train) < 2:
        logger.warning("Not enough data to train even a baseline model")
        return None, None
        
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = LogisticRegression(C=0.1)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    probs = model.predict_proba(X_test_scaled)[:, 1]
    auc_score = roc_auc_score(y_test, probs)
    
    precision, recall, _ = precision_recall_curve(y_test, probs)
    pr_auc = auc(recall, precision)
    
    logger.info(f"Baseline AUC: {auc_score:.4f}, PR-AUC: {pr_auc:.4f}")
    
    return model, scaler

def run_ml_pipeline():
    """Load indicators, train model, and save predictions."""
    indicators_path = DATA_DIR / "features" / "indicators_all.csv"
    if not indicators_path.exists():
        logger.error("Indicators file not found")
        return
        
    df = pd.read_csv(indicators_path)
    ml_df, features = prepare_ml_data(df)
    
    model, scaler = train_baseline(ml_df, features)
    
    # Generate predictions for the latest data
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date].copy()
    
    if model and scaler:
        # Real predictions
        latest_df_valid = latest_df.dropna(subset=features)
        if not latest_df_valid.empty:
            X_latest = scaler.transform(latest_df_valid[features])
            latest_df_valid["p_up_5d"] = model.predict_proba(X_latest)[:, 1]
        else:
            latest_df_valid = latest_df
            latest_df_valid["p_up_5d"] = np.nan
    else:
        # Mock predictions for demo purposes when data is scarce
        logger.info("Using mock predictions for demo (insufficient data for training)")
        # Simple heuristic: positive watch score -> higher probability
        if "watch_score" in latest_df.columns:
            latest_df["p_up_5d"] = (latest_df["watch_score"] / 100 * 0.4 + np.random.random(len(latest_df)) * 0.2 + 0.4).clip(0, 1)
        else:
            latest_df["p_up_5d"] = np.random.uniform(0.4, 0.6, size=len(latest_df))
        latest_df_valid = latest_df
    
    # Save predictions
    output_path = DATA_DIR / "features" / "predictions_latest.csv"
    latest_df_valid[["symbol", "date", "p_up_5d"]].to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")
    
    return latest_df_valid
