"""Floorsheet data collector for NEPSE."""

import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

FLOORSHEET_RAW_DIR = DATA_DIR / "floorsheet" / "raw"
FLOORSHEET_NORM_DIR = DATA_DIR / "floorsheet" / "normalized"

def normalize_floorsheet(raw_path: Path) -> pd.DataFrame:
    """Normalize raw floorsheet CSV to standard schema."""
    df = pd.read_csv(raw_path)
    
    # Expected standard columns: date, symbol, buyer_broker, seller_broker, quantity, rate, amount
    # (Mapping logic would go here based on the source)
    
    # Ensure numeric types
    for col in ["quantity", "rate", "amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    df["amount"] = df["quantity"] * df["rate"]
    return df

def generate_mock_floorsheet(date: str, symbols: list):
    """Generate mock floorsheet data for development/demo."""
    data = []
    import random
    
    for symbol in symbols:
        num_trades = random.randint(50, 200)
        for i in range(num_trades):
            qty = random.choice([10, 50, 100, 500, 1000, 5000])
            rate = random.uniform(200, 1500)
            buyer = str(random.randint(1, 60))
            seller = str(random.randint(1, 60))
            
            data.append({
                "date": date,
                "transaction_no": f"TXN-{date}-{symbol}-{i}",
                "symbol": symbol,
                "buyer_broker": buyer,
                "seller_broker": seller,
                "quantity": qty,
                "rate": round(rate, 2),
                "amount": round(qty * rate, 2)
            })
            
    df = pd.DataFrame(data)
    FLOORSHEET_NORM_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FLOORSHEET_NORM_DIR / f"{date}.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Generated mock floorsheet at {output_path}")
    return output_path
