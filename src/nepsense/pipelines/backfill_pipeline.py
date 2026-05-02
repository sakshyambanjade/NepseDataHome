"""
Backfill Pipeline

Orchestrates collection and processing of historical NEPSE data.
"""

import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from zoneinfo import ZoneInfo

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from nepsense.config import (
    PROJECT_ROOT, RAW_DIR, NORMALIZED_DIR, ADJUSTED_DIR, METADATA_DIR,
    NEPAL_TZ, SHARESANSAR_TODAY_URL
)
from nepsense.collectors import collect_daily
from nepsense.processors import normalize_file
from nepsense.processors.validate_data import validate_file
from nepsense.storage import build_master

console = Console()


def build_trading_calendar(start_date: str, end_date: str) -> List[str]:
    """
    Build list of trading dates (Nepal timezone, business days).
    
    Excludes weekends and standard Nepal holidays.
    """
    trading_dates = []
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # Nepal holidays (approximate)
    nepal_holidays = {
        (1, 26),   # Republic Day
        (3, 8),    # Women's Day
        (4, 13),   # New Year
        (9, 16),   # National Day
        (9, 29),   # Dashain
        (10, 19),  # Deepavali
        (12, 25),  # Christmas
    }
    
    current = start
    while current <= end:
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5:
            # Skip holidays (rough approximation, not Nepal calendar)
            if (current.month, current.day) not in nepal_holidays:
                trading_dates.append(current.isoformat())
        
        current += timedelta(days=1)
    
    return trading_dates


def backfill_date_range(
    start_date: str,
    end_date: str,
    sources: Optional[List[str]] = None,
    skip_existing: bool = True,
) -> Dict[str, Any]:
    """
    Backfill data for a date range.
    
    Args:
        start_date: "YYYY-MM-DD" format
        end_date: "YYYY-MM-DD" format
        sources: List of source priorities, default ["sharesansar"]
        skip_existing: Skip dates that already have normalized files
    
    Returns:
        Dictionary with backfill statistics
    """
    if sources is None:
        sources = ["sharesansar"]
    
    # Create backfill report directory
    quality_dir = PROJECT_ROOT / "data" / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    
    # Build trading calendar
    trading_dates = build_trading_calendar(start_date, end_date)
    
    # Initialize report
    report_path = quality_dir / "backfill_report.csv"
    report_exists = report_path.exists()
    
    report_file = open(report_path, "a", newline="")
    writer = csv.DictWriter(report_file, fieldnames=[
        "date", "source", "status", "raw_file", "normalized_file", 
        "error_message", "records_collected", "timestamp"
    ])
    
    if not report_exists:
        writer.writeheader()
    
    # Statistics
    stats = {
        "total_dates": len(trading_dates),
        "successful": 0,
        "skipped_existing": 0,
        "failed": 0,
        "errors": [],
        "start_date": start_date,
        "end_date": end_date,
        "timestamp": datetime.now(NEPAL_TZ).isoformat(),
    }
    
    # Progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"[cyan]Backfilling {start_date} to {end_date}...",
            total=len(trading_dates),
        )
        
        for date_str in trading_dates:
            progress.update(task, advance=1)
            
            # Check if normalized file exists
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            normalized_path = (
                NORMALIZED_DIR / f"{date_obj.year}/{date_obj.month:02d}/"
                f"{date_str}.csv"
            )
            
            if skip_existing and normalized_path.exists():
                stats["skipped_existing"] += 1
                writer.writerow({
                    "date": date_str,
                    "source": "N/A",
                    "status": "skipped_existing",
                    "raw_file": "",
                    "normalized_file": str(normalized_path),
                    "error_message": "",
                    "records_collected": 0,
                    "timestamp": datetime.now(NEPAL_TZ).isoformat(),
                })
                report_file.flush()
                continue
            
            # Try each source
            collected = False
            for source in sources:
                try:
                    if source == "sharesansar":
                        raw_file = collect_daily(date_str, RAW_DIR)
                        
                        # Normalize
                        normalize_file(raw_file, normalized_path)
                        
                        # Count records
                        df = pd.read_csv(normalized_path)
                        record_count = len(df)
                        
                        writer.writerow({
                            "date": date_str,
                            "source": source,
                            "status": "success",
                            "raw_file": str(raw_file),
                            "normalized_file": str(normalized_path),
                            "error_message": "",
                            "records_collected": record_count,
                            "timestamp": datetime.now(NEPAL_TZ).isoformat(),
                        })
                        
                        stats["successful"] += 1
                        collected = True
                        break
                        
                except Exception as e:
                    writer.writerow({
                        "date": date_str,
                        "source": source,
                        "status": "failed",
                        "raw_file": "",
                        "normalized_file": "",
                        "error_message": str(e),
                        "records_collected": 0,
                        "timestamp": datetime.now(NEPAL_TZ).isoformat(),
                    })
                    report_file.flush()
            
            if not collected:
                stats["failed"] += 1
                stats["errors"].append({
                    "date": date_str,
                    "reason": "All sources failed",
                })
    
    report_file.close()
    
    console.print(f"\n[bold]Backfill Summary[/bold]")
    console.print(f"  Successful: {stats['successful']}")
    console.print(f"  Skipped (existing): {stats['skipped_existing']}")
    console.print(f"  Failed: {stats['failed']}")
    console.print(f"  Report saved to: {report_path}")
    
    return stats


def backfill(
    start_date: str,
    end_date: str,
    sources: Optional[List[str]] = None,
    skip_existing: bool = True,
    build_after: bool = False,
) -> Dict[str, Any]:
    """
    Complete backfill pipeline.
    
    1. Collect raw data from sources
    2. Normalize each file
    3. Validate
    4. Optionally build master dataset
    
    Args:
        start_date: "YYYY-MM-DD"
        end_date: "YYYY-MM-DD"
        sources: Collection sources
        skip_existing: Skip dates with normalized files
        build_after: Build master dataset after backfill
    
    Returns:
        Backfill statistics
    """
    console.print(f"[bold cyan]Starting backfill: {start_date} to {end_date}[/bold cyan]")
    
    # Step 1: Backfill raw + normalized
    stats = backfill_date_range(start_date, end_date, sources, skip_existing)
    
    # Step 2: Optionally build master
    if build_after and stats["successful"] > 0:
        console.print("[bold]Building master dataset...[/bold]")
        try:
            result = build_master(NORMALIZED_DIR, use_adjusted=False)
            console.print(f"[green]✓ Master dataset built: {result['csv_path']}[/green]")
            stats["master_result"] = result
        except Exception as e:
            console.print(f"[red]✗ Failed to build master: {e}[/red]")
            stats["master_error"] = str(e)
    
    return stats
