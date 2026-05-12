"""Corporate action adjustments (bonus, right, dividend, split, merger)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from nepsense.config import ADJUSTED_DIR, METADATA_DIR, NORMALIZED_DIR

logger = logging.getLogger(__name__)

CORPORATE_ACTIONS_FILE = METADATA_DIR / "corporate_actions.csv"


def ensure_corporate_actions_template() -> None:
    """Create empty corporate actions CSV if it doesn't exist."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    if CORPORATE_ACTIONS_FILE.exists():
        return

    template = pd.DataFrame(
        columns=[
            "symbol",
            "book_close_date",
            "announcement_date",
            "action_type",
            "bonus_percent",
            "cash_dividend_percent",
            "right_ratio",
            "right_price",
            "source_url",
            "verified",
        ]
    )
    template.to_csv(CORPORATE_ACTIONS_FILE, index=False)
    logger.info(f"Created corporate actions template at {CORPORATE_ACTIONS_FILE}")


def load_corporate_actions() -> pd.DataFrame:
    """Load and validate corporate actions data.
    
    Returns:
        DataFrame with verified corporate actions
    """
    ensure_corporate_actions_template()

    actions = pd.read_csv(CORPORATE_ACTIONS_FILE)

    if actions.empty:
        logger.warning("No corporate actions defined")
        return actions

    # Clean and validate
    actions["symbol"] = actions["symbol"].astype(str).str.strip().str.upper()
    actions["book_close_date"] = pd.to_datetime(
        actions["book_close_date"], errors="coerce"
    )
    actions["announcement_date"] = pd.to_datetime(
        actions["announcement_date"], errors="coerce"
    )

    # Convert numeric columns
    for col in [
        "bonus_percent",
        "cash_dividend_percent",
        "right_ratio",
        "right_price",
    ]:
        if col in actions.columns:
            actions[col] = pd.to_numeric(actions[col], errors="coerce").fillna(0)

    # Filter to verified actions only
    if "verified" in actions.columns:
        actions = actions[actions["verified"].astype(str).str.lower() == "true"]

    actions = actions.dropna(subset=["symbol", "book_close_date"])
    logger.info(f"Loaded {len(actions)} verified corporate actions")
    return actions


def calculate_adjustment_factor(
    df: pd.DataFrame,
    actions: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate cumulative adjustment factors for all stocks.
    
    Adjustment factor accounts for Bonus, Split, Right, and Cash Dividends (Total Return).
    
    Args:
        df: Price data
        actions: Corporate actions
    
    Returns:
        DataFrame with adjustment_factor column
    """
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["symbol", "date_dt"])
    df["adjustment_factor"] = 1.0

    if actions.empty:
        return df

    # Sort actions by date
    actions = actions.copy()
    actions["book_close_date"] = pd.to_datetime(actions["book_close_date"])
    actions = actions.sort_values("book_close_date")

    for _, action in actions.iterrows():
        symbol = str(action["symbol"]).upper()
        book_close_date = action["book_close_date"]
        action_type = str(action.get("action_type", "")).upper()

        # Find the price on the day before book close to calculate dividend/right factor
        symbol_df = df[df["symbol"] == symbol]
        pre_event_df = symbol_df[symbol_df["date_dt"] < book_close_date]
        
        if pre_event_df.empty:
            continue
            
        pre_event_price = pre_event_df.iloc[-1]["close"]
        mask = (df["symbol"] == symbol) & (df["date_dt"] < book_close_date)

        factor = 1.0
        
        if action_type == "BONUS":
            bonus_pct = float(action.get("bonus_percent", 0) or 0)
            if bonus_pct > 0:
                factor = 1.0 + bonus_pct / 100.0
                
        elif action_type == "SPLIT" or action_type == "FACE_VALUE_CHANGE":
            # Ratio of old face value to new face value
            # Or reused right_ratio for split ratio
            split_ratio = float(action.get("right_ratio", 1) or 1)
            if split_ratio > 0 and split_ratio != 1:
                factor = split_ratio

        elif action_type == "RIGHT":
            right_ratio = float(action.get("right_ratio", 0) or 0)
            right_price = float(action.get("right_price", 0) or 0)
            if right_ratio > 0:
                # Theoretical Ex-Right Price (TERP) adjustment
                # factor = (Price_before + ratio * subscription_price) / (Price_before * (1 + ratio))
                # This makes the price series continuous
                factor = (pre_event_price + right_ratio * right_price) / (pre_event_price * (1 + right_ratio))
                # Note: This factor is usually < 1, so we multiply to adjust historical prices DOWN
                # or divide to adjust them UP. Our convention is dividing by adjustment_factor.

        elif action_type == "CASH_DIVIDEND":
            # Standard Total Return adjustment: (Price - Dividend) / Price
            cash_div_pct = float(action.get("cash_dividend_percent", 0) or 0)
            # NEPSE dividends are usually % of face value (100)
            dividend_amount = cash_div_pct # Assuming face value 100 for now if not specified
            if dividend_amount > 0 and pre_event_price > dividend_amount:
                factor = (pre_event_price - dividend_amount) / pre_event_price

        elif action_type == "MERGER_SWAP":
            swap_ratio = float(action.get("right_ratio", 1) or 1)
            if swap_ratio > 0:
                factor = swap_ratio

        if factor != 1.0:
            df.loc[mask, "adjustment_factor"] *= factor
            logger.debug(f"Applied {action_type} factor {factor:.4f} to {symbol} before {book_close_date}")

    df = df.drop(columns=["date_dt"])
    return df


def apply_adjustments(
    df: pd.DataFrame,
    actions: pd.DataFrame,
) -> pd.DataFrame:
    """Apply all corporate action adjustments to OHLCV data.
    
    Args:
        df: Normalized price data
        actions: Corporate actions
    
    Returns:
        DataFrame with adjusted prices
    """
    # Ensure columns exist
    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            logger.warning(f"Missing column {col} in input dataframe")
            return df

    df = calculate_adjustment_factor(df, actions)

    # Calculate adjusted prices
    # We DIVIDE historical prices by the factor to get adjusted prices in today's terms
    # e.g. if 1:1 bonus, factor was 2.0 for historical rows. 
    # Price 1000 / 2.0 = 500 adjusted close.
    for col in ["open", "high", "low", "close"]:
        df[f"adjusted_{col}"] = (df[col] / df["adjustment_factor"]).round(2)

    # Volume adjustment: historical volume * adjustment_factor
    if "volume" in df.columns:
        df["adjusted_volume"] = (df["volume"] * df["adjustment_factor"]).round(0)

    logger.info(f"Applied adjustments to {len(df)} rows")
    return df


def adjust_all(
    input_root: Path = NORMALIZED_DIR,
    output_root: Path = ADJUSTED_DIR,
) -> int:
    """Adjust all normalized CSV files.
    
    Args:
        input_root: Where to find normalized files
        output_root: Where to save adjusted files
    
    Returns:
        Count of adjusted files
    """
    actions = load_corporate_actions()
    files = sorted(input_root.rglob("*.csv"))
    logger.info(f"Found {len(files)} normalized files to adjust")

    adjusted = 0
    for input_file in files:
        try:
            df = pd.read_csv(input_file)
            adjusted_df = apply_adjustments(df, actions)

            # Save with same date structure
            date_str = input_file.stem
            year, month, _ = date_str.split("-")
            output_dir = output_root / year / month
            output_file = output_dir / f"{date_str}.csv"

            output_dir.mkdir(parents=True, exist_ok=True)
            adjusted_df.to_csv(output_file, index=False)

            adjusted += 1
        except Exception as e:
            logger.error(f"Failed to adjust {input_file}: {e}")
            continue

    logger.info(f"Successfully adjusted {adjusted} files")
    return adjusted
