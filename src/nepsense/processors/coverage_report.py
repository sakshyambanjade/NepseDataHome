"""
Data Coverage Report Generator

Generates comprehensive coverage and quality reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from rich.console import Console

from nepsense.config import NORMALIZED_DIR, ADJUSTED_DIR, PROJECT_ROOT, NEPAL_TZ

console = Console()


def generate_coverage_report() -> Dict[str, Any]:
    """
    Generate comprehensive data coverage report.
    
    Returns:
        Dictionary with coverage metrics
    """
    # Load all normalized data
    csv_files = list(NORMALIZED_DIR.rglob("*.csv"))
    
    if not csv_files:
        console.print("[red]✗ No normalized data files found[/red]")
        return {}
    
    # Read all files
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
        except Exception as e:
            console.print(f"[yellow]⚠  Error reading {csv_file}: {e}[/yellow]")
    
    if not dfs:
        console.print("[red]✗ Could not read any data files[/red]")
        return {}
    
    # Combine
    combined = pd.concat(dfs, ignore_index=True)
    
    # Calculate metrics
    metrics = {
        "generated_at": datetime.now(NEPAL_TZ).isoformat(),
        "total_rows": len(combined),
        "total_files": len(csv_files),
        "total_symbols": combined["symbol"].nunique(),
        "active_symbols": len(combined[combined["symbol"].str.isupper()]),
        "date_range": {
            "start": combined["date"].min(),
            "end": combined["date"].max(),
        },
        "trading_days": combined["date"].nunique(),
        "columns": list(combined.columns),
        "missing_values": combined.isnull().sum().to_dict(),
        "source_distribution": combined["source"].value_counts().to_dict() if "source" in combined.columns else {},
        "symbols_list": sorted(combined["symbol"].unique().tolist()),
    }
    
    # Calculate source confidence distribution if available
    if "source_confidence" in combined.columns:
        metrics["source_confidence_distribution"] = {
            "high (>0.80)": len(combined[combined["source_confidence"] > 0.80]),
            "medium (0.50-0.80)": len(combined[(combined["source_confidence"] >= 0.50) & (combined["source_confidence"] <= 0.80)]),
            "low (<0.50)": len(combined[combined["source_confidence"] < 0.50]),
        }
        metrics["average_source_confidence"] = float(combined["source_confidence"].mean())
    
    # Calculate adjustment coverage
    if "adjustment_factor" in combined.columns:
        adjusted_rows = len(combined[combined["adjustment_factor"] != 1.0])
        metrics["adjusted_coverage"] = {
            "adjusted_rows": adjusted_rows,
            "percentage": round((adjusted_rows / len(combined)) * 100, 1),
        }
    
    # Check for duplicates
    duplicates = combined.duplicated(subset=["date", "symbol"]).sum()
    metrics["data_quality"] = {
        "duplicate_date_symbol_pairs": int(duplicates),
        "null_counts": combined.isnull().sum().to_dict(),
    }
    
    return metrics


def save_coverage_report(metrics: Dict[str, Any]) -> None:
    """Save coverage report to CSV and Markdown."""
    quality_dir = PROJECT_ROOT / "data" / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    json_path = quality_dir / "coverage_metrics.json"
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    console.print(f"[green]✓ Coverage metrics saved to {json_path}[/green]")
    
    # Save as CSV summary
    csv_path = quality_dir / "coverage_report.csv"
    
    summary_rows = [
        ["Metric", "Value"],
        ["Generated At", metrics.get("generated_at", "N/A")],
        ["Total Rows", metrics.get("total_rows", 0)],
        ["Total Files", metrics.get("total_files", 0)],
        ["Total Symbols", metrics.get("total_symbols", 0)],
        ["Active Symbols", metrics.get("active_symbols", 0)],
        ["Date Range", f"{metrics.get('date_range', {}).get('start', 'N/A')} to {metrics.get('date_range', {}).get('end', 'N/A')}"],
        ["Trading Days", metrics.get("trading_days", 0)],
    ]
    
    if "adjusted_coverage" in metrics:
        summary_rows.append([
            "Adjusted Records", 
            f"{metrics['adjusted_coverage']['adjusted_rows']} ({metrics['adjusted_coverage']['percentage']}%)"
        ])
    
    if "average_source_confidence" in metrics:
        summary_rows.append([
            "Average Source Confidence",
            f"{metrics['average_source_confidence']:.2f}"
        ])
    
    summary_df = pd.DataFrame(summary_rows[1:], columns=summary_rows[0])
    summary_df.to_csv(csv_path, index=False)
    console.print(f"[green]✓ Coverage report saved to {csv_path}[/green]")
    
    # Save as Markdown
    md_path = quality_dir / "coverage_report.md"
    
    with open(md_path, "w") as f:
        f.write("# NepSense Data Coverage Report\n\n")
        f.write(f"**Generated:** {metrics.get('generated_at', 'N/A')}\n\n")
        
        f.write("## Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        
        for row in summary_rows[1:]:
            f.write(f"| {row[0]} | {row[1]} |\n")
        
        f.write("\n## Data Quality\n\n")
        quality = metrics.get("data_quality", {})
        f.write(f"- **Duplicate Date-Symbol Pairs:** {quality.get('duplicate_date_symbol_pairs', 0)}\n")
        
        if quality.get("null_counts"):
            f.write("\n### Missing Values by Column\n\n")
            for col, count in quality["null_counts"].items():
                if count > 0:
                    f.write(f"- {col}: {count}\n")
        
        f.write("\n## Source Distribution\n\n")
        sources = metrics.get("source_distribution", {})
        if sources:
            for source, count in sources.items():
                pct = round((count / metrics.get("total_rows", 1)) * 100, 1)
                f.write(f"- {source}: {count} ({pct}%)\n")
        else:
            f.write("- No source information available\n")
        
        f.write("\n## Symbol Universe\n\n")
        f.write(f"**Total Symbols:** {metrics.get('total_symbols', 0)}\n\n")
        
        symbols = metrics.get("symbols_list", [])
        if symbols:
            f.write("**Listed Symbols:**\n\n")
            for i, symbol in enumerate(symbols, 1):
                if i % 5 == 0:
                    f.write(f"{symbol}  \n")
                else:
                    f.write(f"{symbol}, ")
            f.write("\n")
    
    console.print(f"[green]✓ Coverage report saved to {md_path}[/green]")


if __name__ == "__main__":
    metrics = generate_coverage_report()
    save_coverage_report(metrics)
    console.print("[bold cyan]Coverage report generation complete[/bold cyan]")
