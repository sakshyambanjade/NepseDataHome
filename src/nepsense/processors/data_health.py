import json
import os
import glob
from datetime import datetime
import pandas as pd

OUT_DIR = "web/public/data"

def generate_data_health(df: pd.DataFrame, date: str, baselines_available: bool):
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Calculate counts
    transaction_count = len(df)
    symbol_count = df['symbol'].nunique() if 'symbol' in df else 0
    
    # Unique brokers across buyer and seller columns
    if 'buyer_broker' in df and 'seller_broker' in df:
        broker_count = len(set(df['buyer_broker'].unique()).union(set(df['seller_broker'].unique())))
    else:
        broker_count = 0
        
    # Check for invalid rows (missing essential data)
    invalid_row_count = df[['symbol', 'buyer_broker', 'seller_broker', 'quantity', 'rate']].isnull().any(axis=1).sum()
    
    # Check for duplicate transactions
    if 'transaction_no' in df:
        duplicate_transaction_count = df['transaction_no'].duplicated().sum()
    else:
        duplicate_transaction_count = 0

    # Count generated JSON artifacts
    generated_files = []
    for root, dirs, files in os.walk(OUT_DIR):
        for file in files:
            if file.endswith('.json'):
                generated_files.append(os.path.relpath(os.path.join(root, file), OUT_DIR))

    health_data = {
        "latest_floorsheet_date": date,
        "transaction_count": int(transaction_count),
        "symbol_count": int(symbol_count),
        "broker_count": int(broker_count),
        "duplicate_transaction_count": int(duplicate_transaction_count),
        "invalid_row_count": int(invalid_row_count),
        "baseline_available": baselines_available,
        "generated_files": len(generated_files),
        "generated_at": datetime.now().isoformat()
    }
    
    with open(os.path.join(OUT_DIR, "data_health.json"), "w") as f:
        json.dump(health_data, f, indent=2)
