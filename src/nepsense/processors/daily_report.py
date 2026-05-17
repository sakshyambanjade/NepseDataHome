import json
import os
from typing import List, Dict, Any

JSON_OUT_DIR = "web/public/data/reports"
MD_OUT_DIR = "reports"

def generate_daily_report(results: List[Dict[str, Any]], date: str):
    os.makedirs(JSON_OUT_DIR, exist_ok=True)
    os.makedirs(MD_OUT_DIR, exist_ok=True)
    
    # Process market summary
    total_volume = sum(r["total_qty"] for r in results)
    total_amount = sum(r["total_amt"] for r in results)
    active_symbols = len(results)
    
    # Sort for report
    top_accumulated = sorted(results, key=lambda x: x.get("accumulation_score", 0), reverse=True)[:10]
    top_distributed = sorted(results, key=lambda x: x.get("distribution_score", 0), reverse=True)[:10]
    
    # Top volume
    top_volume = sorted(results, key=lambda x: x.get("total_amt", 0), reverse=True)[:5]
    
    report_data = {
        "date": date,
        "summary": {
            "total_volume": total_volume,
            "total_amount": total_amount,
            "active_symbols": active_symbols
        },
        "top_accumulation": [
            {
                "symbol": r["symbol"], 
                "score": r.get("accumulation_score", 0),
                "volume": r.get("total_qty", 0)
            } for r in top_accumulated
        ],
        "top_distribution": [
            {
                "symbol": r["symbol"], 
                "score": r.get("distribution_score", 0),
                "volume": r.get("total_qty", 0)
            } for r in top_distributed
        ],
        "top_volume": [
            {
                "symbol": r["symbol"],
                "amount": r.get("total_amt", 0)
            } for r in top_volume
        ],
        "data_quality_notes": [
            "Baseline data was successfully loaded." if any(r.get("baseline_available") for r in results) else "Warning: No historical baseline available.",
            f"{active_symbols} symbols processed with valid transaction streams."
        ]
    }
    
    # JSON Outputs
    with open(os.path.join(JSON_OUT_DIR, f"{date}.json"), "w") as f:
        json.dump(report_data, f, indent=2)
        
    with open(os.path.join(JSON_OUT_DIR, "latest.json"), "w") as f:
        json.dump(report_data, f, indent=2)
        
    # MD Output
    md_content = f"""# NepSense Daily Flow Report
**Date:** {date}

## Market Summary
- **Total Flow Amount:** Rs. {total_amount / 10000000:.2f} Cr
- **Total Volume:** {total_volume:,} shares
- **Active Symbols:** {active_symbols}

## Top Accumulation
"""
    for r in top_accumulated:
        md_content += f"- **{r['symbol']}**: Score {r.get('accumulation_score', 0):.1f} ({r.get('total_qty', 0):,} shares)\n"

    md_content += "\n## Top Distribution\n"
    for r in top_distributed:
        md_content += f"- **{r['symbol']}**: Score {r.get('distribution_score', 0):.1f} ({r.get('total_qty', 0):,} shares)\n"
        
    with open(os.path.join(MD_OUT_DIR, f"{date}.md"), "w") as f:
        f.write(md_content)
