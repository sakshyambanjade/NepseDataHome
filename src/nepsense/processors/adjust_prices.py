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
    
    Adjustment factor = 1 / (cumulative bonus factor * cumulative split factor)
    
    Args:
        df: Price data
        actions: Corporate actions
    
    Returns:
        DataFrame with adjustment_factor column
    """
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df["adjustment_factor"] = 1.0

    if actions.empty:
        return df

    # Sort actions by date
    actions = actions.sort_values("book_close_date")

    for _, action in actions.iterrows():
        symbol = str(action["symbol"]).upper()
        book_close_date = action["book_close_date"]
        action_type = str(action.get("action_type", "")).upper()

        # Mask for dates before book close (adjustment applies before book close)
        mask = (df["symbol"] == symbol) & (df["date_dt"] < book_close_date)

        if not mask.any():
            continue

        if action_type == "BONUS":
            bonus_pct = float(action.get("bonus_percent", 0) or 0)
            if bonus_pct > 0:
                factor = 1.0 + bonus_pct / 100.0
                df.loc[mask, "adjustment_factor"] *= factor
                logger.debug(
                    f"Applied {bonus_pct}% bonus to {symbol} before {book_close_date}"
                )

        elif action_type == "SPLIT":
            # Split factor: old_price = new_price * split_factor
            split_ratio = float(action.get("right_ratio", 1) or 1)  # right_ratio reused
            if split_ratio > 0:
                df.loc[mask, "adjustment_factor"] *= split_ratio
                logger.debug(f"Applied {split_ratio} split to {symbol} before {book_close_date}")

        elif action_type == "MERGER_SWAP":
            # Merger swap factor
            swap_ratio = float(action.get("right_ratio", 1) or 1)
            if swap_ratio > 0:
                df.loc[mask, "adjustment_factor"] *= swap_ratio
                logger.debug(f"Applied {swap_ratio} merger swap to {symbol} before {book_close_date}")

        # Note: RIGHT and CASH_DIVIDEND don't directly adjust prices
        # They are informational or handled separately

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
    df = calculate_adjustment_factor(df, actions)

    # Calculate adjusted prices
    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        if col in df.columns:
            df[f"adjusted_{col}"] = (
                df[col] / df["adjustment_factor"]
            ).round(2)

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
    files = sorted(input_root.glob("*/*/*.csv"))
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
