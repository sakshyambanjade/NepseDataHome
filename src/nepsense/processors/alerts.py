import json
import os
import uuid
from typing import List, Dict, Any

OUT_DIR = "web/public/data"

def generate_alerts(results: List[Dict[str, Any]], date: str):
    alerts = []
    
    for r in results:
        symbol = r["symbol"]
        
        # Accumulation Alert
        if r.get("accumulation_score", 0) > 60:
            alerts.append({
                "id": str(uuid.uuid4()),
                "date": date,
                "symbol": symbol,
                "severity": "high",
                "category": "Accumulation Alert",
                "title": f"Strong Accumulation in {symbol}",
                "reason": "High net buy strength and concentration among top buyers.",
                "score": r["accumulation_score"],
                "related_brokers": [b["broker"] for b in r.get("top_net_buyers", [])[:2]],
                "link": f"/flowsheet/{symbol}"
            })
            
        # Distribution Alert
        elif r.get("distribution_score", 0) > 60:
            alerts.append({
                "id": str(uuid.uuid4()),
                "date": date,
                "symbol": symbol,
                "severity": "high",
                "category": "Distribution Alert",
                "title": f"Strong Distribution in {symbol}",
                "reason": "High net sell strength and concentration among top sellers.",
                "score": r["distribution_score"],
                "related_brokers": [b["broker"] for b in r.get("top_net_sellers", [])[:2]],
                "link": f"/flowsheet/{symbol}"
            })
            
        # Cross-Trade Watch
        if r.get("cross_trade_ratio", 0) > 0.10:
            alerts.append({
                "id": str(uuid.uuid4()),
                "date": date,
                "symbol": symbol,
                "severity": "medium",
                "category": "Cross-Trade Watch",
                "title": f"High Cross-Trade Ratio in {symbol}",
                "reason": f"{(r['cross_trade_ratio']*100):.1f}% of volume was traded within the same broker channel.",
                "score": r["cross_trade_ratio"] * 100,
                "related_brokers": [],
                "link": f"/flow?symbol={symbol}"
            })
            
        # Repeated Pair Watch
        if r.get("repeated_pair_score", 0) > 60:
            alerts.append({
                "id": str(uuid.uuid4()),
                "date": date,
                "symbol": symbol,
                "severity": "medium",
                "category": "Repeated Pair Watch",
                "title": f"Repeated Broker-Pairs in {symbol}",
                "reason": "Identified significant repetitive flow between specific broker channels.",
                "score": r["repeated_pair_score"],
                "related_brokers": [],
                "link": f"/flow?symbol={symbol}"
            })
            
        # Volume Spike
        if r.get("volume_spike_score", 0) > 40:
            alerts.append({
                "id": str(uuid.uuid4()),
                "date": date,
                "symbol": symbol,
                "severity": "low",
                "category": "Volume Spike Alert",
                "title": f"Volume Spike in {symbol}",
                "reason": "Volume is significantly higher than the 20-day baseline.",
                "score": r["volume_spike_score"],
                "related_brokers": [],
                "link": f"/flowsheet/{symbol}"
            })
            
    # Sort alerts by severity (high > medium > low) and score
    severity_order = {"high": 3, "medium": 2, "low": 1}
    alerts.sort(key=lambda x: (severity_order.get(x["severity"], 0), x["score"]), reverse=True)
    
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "alerts.json"), "w") as f:
        json.dump(alerts, f, indent=2)
