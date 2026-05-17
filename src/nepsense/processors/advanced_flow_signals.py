import json
import os
import glob
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Directories
OUT_DIR = Path("web/public/data")
INTELLIGENCE_DIR = Path("data/floorsheet/intelligence")
NORMALIZED_DIR = Path("data/floorsheet/normalized")

def load_historical_intelligence(days: int = 20) -> pd.DataFrame:
    files = sorted(list(INTELLIGENCE_DIR.glob("*.json")), reverse=True)
    historical_data = []
    for f in files[:days]:
        try:
            with open(f, 'r') as j:
                historical_data.extend(json.load(j))
        except Exception as e:
            continue
    if not historical_data:
        return pd.DataFrame()
    return pd.DataFrame(historical_data)

def load_historical_flow(days: int = 20) -> pd.DataFrame:
    files = sorted(list(NORMALIZED_DIR.glob("*.csv")), reverse=True)
    df_list = []
    for f in files[:days]:
        try:
            df = pd.read_csv(f)
            # Add date column if needed based on filename
            df['date'] = f.stem
            df_list.append(df)
        except Exception as e:
            continue
    if not df_list:
        return pd.DataFrame()
    return pd.concat(df_list, ignore_index=True)

def safe_z_score(val, mean, std):
    if std == 0 or pd.isna(std):
        return 0.0
    return (val - mean) / std

def get_anomaly_label(z_score: float) -> str:
    if abs(z_score) > 2.5: return "extreme"
    if abs(z_score) > 1.5: return "unusual"
    return "normal"

def generate_advanced_signals(today_results: List[Dict[str, Any]], date: str):
    os.makedirs(OUT_DIR / "symbols", exist_ok=True)
    os.makedirs(OUT_DIR / "brokers", exist_ok=True)
    
    signals = []
    
    # 1. Load History
    hist_df = load_historical_intelligence(days=20)
    
    # Precompute symbol level stats if history exists
    symbol_stats = {}
    if not hist_df.empty:
        for symbol, group in hist_df.groupby('symbol'):
            symbol_stats[symbol] = {
                'net_buy_strength_mean': group['net_buy_strength'].mean() if 'net_buy_strength' in group else 0,
                'net_buy_strength_std': group['net_buy_strength'].std() if 'net_buy_strength' in group else 0,
                'net_sell_strength_mean': group['net_sell_strength'].mean() if 'net_sell_strength' in group else 0,
                'net_sell_strength_std': group['net_sell_strength'].std() if 'net_sell_strength' in group else 0,
                'repeated_pair_score_mean': group['repeated_pair_score'].mean() if 'repeated_pair_score' in group else 0,
                'repeated_pair_score_std': group['repeated_pair_score'].std() if 'repeated_pair_score' in group else 0,
                'cross_trade_ratio_mean': group['cross_trade_ratio'].mean() if 'cross_trade_ratio' in group else 0,
                'cross_trade_ratio_std': group['cross_trade_ratio'].std() if 'cross_trade_ratio' in group else 0,
                'operator_like_score_mean': group['operator_like_score'].mean() if 'operator_like_score' in group else 0,
                'operator_like_score_std': group['operator_like_score'].std() if 'operator_like_score' in group else 0,
                'volume_mean': group['total_qty'].mean() if 'total_qty' in group else 0,
                'volume_std': group['total_qty'].std() if 'total_qty' in group else 0,
            }

    for r in today_results:
        symbol = r["symbol"]
        
        # 1. Flow Anomaly Z-Score
        if symbol in symbol_stats:
            stats = symbol_stats[symbol]
            anomalies = []
            
            metrics_to_check = [
                ('net_buy_strength', r.get('net_buy_strength', 0), stats['net_buy_strength_mean'], stats['net_buy_strength_std']),
                ('net_sell_strength', r.get('net_sell_strength', 0), stats['net_sell_strength_mean'], stats['net_sell_strength_std']),
                ('repeated_pair_score', r.get('repeated_pair_score', 0), stats['repeated_pair_score_mean'], stats['repeated_pair_score_std']),
                ('operator_like_score', r.get('operator_like_score', 0), stats['operator_like_score_mean'], stats['operator_like_score_std']),
                ('volume', r.get('total_qty', 0), stats['volume_mean'], stats['volume_std'])
            ]
            
            max_z = 0
            primary_anomaly = ""
            for m_name, val, mean, std in metrics_to_check:
                z = safe_z_score(val, mean, std)
                if abs(z) > 1.5:
                    anomalies.append(f"{m_name} is unusual (Z: {z:.1f})")
                if abs(z) > abs(max_z):
                    max_z = z
                    primary_anomaly = m_name
                    
            if abs(max_z) > 1.5:
                signals.append({
                    "date": date,
                    "symbol": symbol,
                    "signal_type": "Flow Anomaly",
                    "score": min(abs(max_z) * 20, 100),
                    "confidence_score": min(len(hist_df[hist_df['symbol'] == symbol]) * 5, 100),
                    "confidence_label": get_anomaly_label(max_z),
                    "reasons": anomalies,
                    "related_brokers": [b["broker"] for b in r.get("top_net_buyers", [])[:2]],
                    "related_metrics": [primary_anomaly],
                    "link": f"/flowsheet/{symbol}"
                })
        
        # 3. Silent Accumulation
        net_buy = r.get("net_buy_strength", 0)
        vol_spike = r.get("volume_spike_score", 0)
        
        if net_buy > 20 and vol_spike > 10:
            score = (
                0.30 * min(net_buy * 2, 100) +
                0.20 * 80 + # proxy price stability
                0.15 * min(vol_spike * 2, 100)
            )
            if score > 50:
                signals.append({
                    "date": date,
                    "symbol": symbol,
                    "signal_type": "Silent Accumulation",
                    "score": score,
                    "confidence_score": r.get("confidence", {}).get("score", 70),
                    "confidence_label": r.get("confidence", {}).get("label", "Medium confidence"),
                    "reasons": ["High net buy strength", "Volume above baseline"],
                    "related_brokers": [b["broker"] for b in r.get("top_net_buyers", [])[:2]],
                    "related_metrics": ["net_buy_strength", "volume_spike_score"],
                    "link": f"/flowsheet/{symbol}"
                })
                
        # 4. Distribution Exit
        net_sell = r.get("net_sell_strength", 0)
        if net_sell > 20 and vol_spike > 10:
            score = (
                0.30 * min(net_sell * 2, 100) +
                0.15 * min(vol_spike * 2, 100)
            )
            if score > 50:
                signals.append({
                    "date": date,
                    "symbol": symbol,
                    "signal_type": "Distribution Exit",
                    "score": score,
                    "confidence_score": r.get("confidence", {}).get("score", 70),
                    "confidence_label": r.get("confidence", {}).get("label", "Medium confidence"),
                    "reasons": ["High net sell strength", "Volume above baseline"],
                    "related_brokers": [b["broker"] for b in r.get("top_net_sellers", [])[:2]],
                    "related_metrics": ["net_sell_strength", "volume_spike_score"],
                    "link": f"/flowsheet/{symbol}"
                })
                
        # 5. Absorption
        # High volume, but price is stable. We proxy this if volume spike is high but net strength is low.
        if vol_spike > 30 and net_buy < 15 and net_sell < 15:
            signals.append({
                "date": date,
                "symbol": symbol,
                "signal_type": "Absorption Pattern",
                "score": vol_spike,
                "confidence_score": 75,
                "confidence_label": "High confidence",
                "reasons": ["High volume with neutral net broker flow"],
                "related_brokers": [],
                "related_metrics": ["volume_spike_score"],
                "link": f"/flowsheet/{symbol}"
            })

    # Sort signals
    signals.sort(key=lambda x: x["score"], reverse=True)
    
    # Export Advanced Signals
    with open(OUT_DIR / "advanced_flow_signals.json", "w") as f:
        json.dump(signals, f, indent=2)
        
    # Group by symbol for specific export
    symbol_signals = {}
    for s in signals:
        sym = s["symbol"]
        if sym not in symbol_signals:
            symbol_signals[sym] = []
        symbol_signals[sym].append(s)
        
    for sym, sigs in symbol_signals.items():
        safe_sym = str(sym).replace("/", "-")
        with open(OUT_DIR / "symbols" / f"{safe_sym}_advanced_signals.json", "w") as f:
            json.dump(sigs, f, indent=2)

    # Broker Fingerprint and Rotation (Simplified based on today's flow map data)
    try:
        with open(OUT_DIR / "rotation_map.json", "r") as f:
            rotation_map = json.load(f)
            
        broker_signals = []
        for broker_id, data in rotation_map.items():
            score = data.get("rotation_score", 0)
            if score > 40:
                broker_signals.append({
                    "date": date,
                    "broker": broker_id,
                    "signal_type": "Broker Rotation",
                    "score": score,
                    "confidence_score": 80,
                    "confidence_label": "High confidence",
                    "reasons": [
                        f"Broker {broker_id} is rotating capital.",
                        f"Net bought {len(data.get('net_buy_symbols', []))} symbols.",
                        f"Net sold {len(data.get('net_sell_symbols', []))} symbols."
                    ],
                    "related_brokers": [broker_id],
                    "related_metrics": ["rotation_score"],
                    "link": f"/broker/{broker_id}"
                })
                
        for s in broker_signals:
            signals.append(s)
            with open(OUT_DIR / "brokers" / f"{s['broker']}_advanced_signals.json", "w") as f:
                json.dump([s], f, indent=2)
                
    except Exception as e:
        pass
        
