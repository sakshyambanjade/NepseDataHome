from __future__ import annotations

from pathlib import Path
import pandas as pd

from nepse_data_engine.config import CLEAN_DIR, ADJUSTED_DIR, CORPORATE_ACTIONS_DIR
from nepse_data_engine.utils.dates import dated_output_path

CORPORATE_ACTIONS_FILE = CORPORATE_ACTIONS_DIR / "corporate_actions.csv"

def ensure_corporate_action_template() -> None:
    CORPORATE_ACTIONS_DIR.mkdir(parents=True, exist_ok=True)

    if CORPORATE_ACTIONS_FILE.exists():
        return

    template = pd.DataFrame(
        columns=[
            "symbol",
            "book_close_date",
            "action_type",
            "bonus_percent",
            "cash_dividend_percent",
            "right_ratio",
            "issue_price",
            "notes",
        ]
    )
    template.to_csv(CORPORATE_ACTIONS_FILE, index=False)

def load_corporate_actions() -> pd.DataFrame:
    ensure_corporate_action_template()

    actions = pd.read_csv(CORPORATE_ACTIONS_FILE)

    if actions.empty:
        return actions

    actions["symbol"] = actions["symbol"].astype(str).str.strip().str.upper()
    actions["book_close_date"] = pd.to_datetime(actions["book_close_date"], errors="coerce")

    for col in ["bonus_percent", "cash_dividend_percent", "issue_price"]:
        if col in actions.columns:
            actions[col] = pd.to_numeric(actions[col], errors="coerce").fillna(0)

    return actions.dropna(subset=["symbol", "book_close_date"])

def apply_adjustments(df: pd.DataFrame, actions: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    df["adjustment_factor"] = 1.0

    if not actions.empty:
        for _, action in actions.iterrows():
            symbol = str(action["symbol"]).upper()
            book_close_date = action["book_close_date"]
            bonus_percent = float(action.get("bonus_percent", 0) or 0)

            if bonus_percent <= 0:
                continue

            factor = 1.0 + bonus_percent / 100.0

            mask = (df["symbol"] == symbol) & (df["date_dt"] < book_close_date)
            df.loc[mask, "adjustment_factor"] *= factor

    price_cols = ["open", "high", "low", "close"]

    for col in price_cols:
        df[f"adjusted_{col}"] = df[col] / df["adjustment_factor"]

    df = df.drop(columns=["date_dt"])

    return df

def adjust_file(input_file: Path, output_file: Path, actions: pd.DataFrame) -> Path:
    df = pd.read_csv(input_file)
    adjusted = apply_adjustments(df, actions)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    adjusted.to_csv(output_file, index=False)

    return output_file

def adjust_all() -> int:
    actions = load_corporate_actions()
    files = sorted(CLEAN_DIR.glob("*/*/*.csv"))

    adjusted_count = 0

    for input_file in files:
        date_str = input_file.stem
        output_file = dated_output_path(ADJUSTED_DIR, date_str)
        adjust_file(input_file, output_file, actions)
        adjusted_count += 1

    return adjusted_count
