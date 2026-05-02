from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console

from nepsense import __version__
from nepsense.collectors import collect_daily
from nepsense.collectors.archive_importer import import_archive
from nepsense.config import QUALITY_DIR
from nepsense.databook import build_data_book
from nepsense.processors import normalize_all
from nepsense.processors.adjust_prices import adjust_all
from nepsense.processors.coverage_report import generate_coverage_report, save_coverage_report
from nepsense.processors.validate_data import (
    generate_symbol_coverage_report,
    validate_all,
)
from nepsense.pipelines import backfill
from nepsense.storage import build_master, create_manifest
from nepsense.utils.logging import setup_logger

app = typer.Typer(
    help="NepSense - NEPSE historical market data engine",
    no_args_is_help=True,
)
console = Console()

# Setup logging
logger = setup_logger(__name__)


@app.callback(invoke_without_command=True)
@app.command()
def version(ctx: typer.Context) -> None:
    """Show version."""
    if ctx.invoked_subcommand is None:
        console.print(f"NepSense v{__version__}")


@app.command()
def collect_daily_cmd(date: str = typer.Option("today", help="Date to collect")) -> None:
    """Collect today's NEPSE data from ShareSansar.
    
    Example:
        nepse-data collect-daily
        nepse-data collect-daily --date 2026-05-02
    """
    try:
        output = collect_daily(date=date)
        console.print(f"[green]✓ Raw data saved:[/green] {output}")
    except Exception as e:
        console.print(f"[red]✗ Collection failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def normalize_cmd() -> None:
    """Normalize all raw data to standard schema.
    
    Converts raw HTML scrapes to clean CSV with standard column names.
    """
    try:
        count = normalize_all()
        console.print(f"[green]✓ Normalized files:[/green] {count}")
    except Exception as e:
        console.print(f"[red]✗ Normalization failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def adjust_cmd() -> None:
    """Apply corporate-action adjustments (bonus, right, dividend, split).
    
    Reads corporate_actions.csv and adjusts historical prices accordingly.
    """
    try:
        count = adjust_all()
        console.print(f"[green]✓ Adjusted files:[/green] {count}")
    except Exception as e:
        console.print(f"[red]✗ Adjustment failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def build_master_cmd(
    adjusted: bool = typer.Option(False, help="Use adjusted prices")
) -> None:
    """Build master dataset in CSV, Parquet, and DuckDB formats.
    
    Creates combined dataset from all daily files.
    """
    try:
        result = build_master(use_adjusted=adjusted)
        console.print("[green]✓ Master dataset created[/green]")
        console.print(f"  Type: {result['dataset_type']}")
        console.print(f"  Rows: {result['rows']}")
        console.print(f"  CSV: {result['csv']}")
        console.print(f"  Parquet: {result['parquet']}")
        console.print(f"  DuckDB: {result['duckdb']}")
    except Exception as e:
        console.print(f"[red]✗ Master build failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def validate_cmd(
    fail_on_error: bool = typer.Option(False, help="Exit with error if validation fails")
) -> None:
    """Validate all data files for quality issues.
    
    Checks for:
    - Missing columns
    - Duplicate rows
    - OHLC integrity
    - Unusual price movements
    """
    try:
        result = validate_all(fail_on_error=fail_on_error)
        console.print("[green]✓ Validation complete[/green]")
        console.print(f"  Files: {result['files_checked']}")
        console.print(f"  Errors: {result['total_errors']}")
        console.print(f"  Warnings: {result['total_warnings']}")
        
        if result['total_errors'] > 0:
            console.print(f"  [red]See {QUALITY_DIR}/validation_report.json for details[/red]")
        
        # Generate coverage report
        coverage = generate_symbol_coverage_report()
        console.print(f"\n[bold]Symbol Coverage:[/bold]")
        console.print(f"  Active symbols: {len(coverage)}")
        console.print(f"  Oldest trading date: {coverage['first_date'].min()}")
        console.print(f"  Newest trading date: {coverage['last_date'].max()}")
        console.print(f"  Total trading days: {coverage['trading_days'].sum()}")
        
    except Exception as e:
        console.print(f"[red]✗ Validation failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def daily_run() -> None:
    """Run complete daily pipeline.
    
    Steps:
    1. Collect today's data
    2. Normalize
    3. Adjust
    4. Build master datasets
    5. Validate
    """
    console.print("[bold]Starting daily NEPSE data pipeline...[/bold]\n")
    
    try:
        # Step 1: Collect
        console.print("[blue]1. Collecting daily data...[/blue]")
        raw = collect_daily(date="today")
        console.print(f"   [green]✓[/green] Raw: {raw}\n")

        # Step 2: Normalize
        console.print("[blue]2. Normalizing all data...[/blue]")
        normalize_count = normalize_all()
        console.print(f"   [green]✓[/green] Normalized: {normalize_count} files\n")

        # Step 3: Adjust
        console.print("[blue]3. Applying corporate adjustments...[/blue]")
        adjust_count = adjust_all()
        console.print(f"   [green]✓[/green] Adjusted: {adjust_count} files\n")

        # Step 4: Build masters
        console.print("[blue]4. Building master datasets...[/blue]")
        master_norm = build_master(use_adjusted=False)
        console.print(f"   [green]✓[/green] Normalized: {master_norm['rows']} rows")
        master_adj = build_master(use_adjusted=True)
        console.print(f"   [green]✓[/green] Adjusted: {master_adj['rows']} rows\n")

        # Step 5: Validate
        console.print("[blue]5. Validating...[/blue]")
        validation = validate_all()
        console.print(f"   [green]✓[/green] {validation['files_checked']} files checked")
        console.print(f"   [green]✓[/green] {validation['total_errors']} errors, {validation['total_warnings']} warnings\n")

        # Manifest
        console.print("[blue]6. Building public data book...[/blue]")
        data_book = build_data_book(rebuild_master=False)
        console.print(
            f"   [green]✓[/green] Data book: {data_book['rows']} rows, "
            f"{data_book['symbols']} symbols\n"
        )

        console.print("[blue]7. Creating manifest...[/blue]")
        create_manifest()
        console.print(f"   [green]✓[/green] Manifest created\n")

        console.print("[bold green]✓ Daily pipeline completed successfully![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]✗ Pipeline failed: {e}[/bold red]")
        logger.exception("Daily pipeline failed")
        raise typer.Exit(1)



@app.command()
def backfill_cmd(
    start: str = typer.Option("2010-01-01", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option("today", help="End date (YYYY-MM-DD)"),
    skip_existing: bool = typer.Option(True, help="Skip dates with existing normalized files"),
    build: bool = typer.Option(False, help="Build master dataset after backfill"),
) -> None:
    """Backfill historical NEPSE data from sources.
    
    Downloads and processes historical data for the specified date range.
    
    Examples:
        nepsense backfill  # Default: 2010 to today
        nepsense backfill --start 2015-01-01 --end 2020-12-31
        nepsense backfill --start 2000-01-01 --end today --build
    """
    try:
        console.print(f"[bold cyan]Backfilling {start} to {end}...[/bold cyan]")
        stats = backfill(
            start_date=start,
            end_date=end,
            skip_existing=skip_existing,
            build_after=build,
        )
        
        console.print(f"\n[bold green]✓ Backfill complete[/bold green]")
        console.print(f"  Successful: {stats['successful']}")
        console.print(f"  Skipped: {stats['skipped_existing']}")
        console.print(f"  Failed: {stats['failed']}")
        
    except Exception as e:
        console.print(f"[red]✗ Backfill failed:[/red] {e}")
        logger.exception("Backfill failed")
        raise typer.Exit(1)


@app.command()
def import_archive_cmd(
    input_dir: Path = typer.Argument(..., help="Folder containing dated historical CSV files"),
    source: str = typer.Option("archive", help="Source label for provenance"),
    source_confidence: float = typer.Option(0.70, help="Confidence score from 0.0 to 1.0"),
    normalize: bool = typer.Option(True, help="Normalize imported raw files"),
    build: bool = typer.Option(True, help="Rebuild the public data book after import"),
) -> None:
    """Import historical CSV archives into NepSense daily history.

    Filenames must contain dates, for example:
    2024-01-02.csv, 20240102.csv, or market_2024_01_02.csv.
    """
    try:
        console.print(f"[bold cyan]Importing archive from {input_dir}...[/bold cyan]")
        stats = import_archive(
            input_dir=input_dir,
            source=source,
            source_confidence=source_confidence,
            normalize=normalize,
        )
        console.print("[green]✓ Archive import complete[/green]")
        console.print(f"  Files found: {stats['files_found']}")
        console.print(f"  Imported raw files: {stats['imported']}")
        console.print(f"  Normalized files: {stats['normalized']}")
        console.print(f"  Skipped: {len(stats['skipped'])}")
        console.print(f"  Failed: {len(stats['failed'])}")

        if build:
            manifest = build_data_book()
            console.print(
                f"  Data book rebuilt: {manifest['rows']} rows, "
                f"{manifest['symbols']} symbols"
            )
    except Exception as e:
        console.print(f"[red]✗ Archive import failed:[/red] {e}")
        logger.exception("Archive import failed")
        raise typer.Exit(1)


@app.command()
def coverage_cmd() -> None:
    """Generate data coverage and quality report.
    
    Creates:
    - coverage_metrics.json
    - coverage_report.csv
    - coverage_report.md
    """
    try:
        console.print("[bold cyan]Generating coverage report...[/bold cyan]")
        metrics = generate_coverage_report()
        save_coverage_report(metrics)
        
        console.print(f"\n[bold green]✓ Coverage report generated[/bold green]")
        console.print(f"  Total rows: {metrics.get('total_rows', 0):,}")
        console.print(f"  Total symbols: {metrics.get('total_symbols', 0)}")
        console.print(f"  Date range: {metrics.get('date_range', {}).get('start', 'N/A')} to {metrics.get('date_range', {}).get('end', 'N/A')}")
        console.print(f"  Trading days: {metrics.get('trading_days', 0)}")
        
        if "average_source_confidence" in metrics:
            console.print(f"  Avg source confidence: {metrics['average_source_confidence']:.2f}")
        
        console.print(f"\n[blue]Reports saved to: data/quality/[/blue]")
        
    except Exception as e:
        console.print(f"[red]✗ Coverage report failed:[/red] {e}")
        logger.exception("Coverage report generation failed")
        raise typer.Exit(1)


@app.command()
def databook_cmd() -> None:
    """Build public all-market and per-symbol history files.

    Outputs:
    - data/history/nepse_all_prices.csv
    - data/history/by_symbol/SYMBOL.csv
    - data/history/by_date/YYYY-MM-DD.csv
    - data/history/manifest.json
    """
    try:
        console.print("[bold cyan]Building NepSense data book...[/bold cyan]")
        manifest = build_data_book()
        console.print("[green]✓ Data book created[/green]")
        console.print(f"  Rows: {manifest['rows']}")
        console.print(f"  Symbols: {manifest['symbols']}")
        console.print(f"  Trading days: {manifest['trading_days']}")
        console.print(
            "  Date range: "
            f"{manifest['date_range']['start']} to {manifest['date_range']['end']}"
        )
        console.print(f"  Output: {manifest['outputs']['all_prices_csv']}")
    except Exception as e:
        console.print(f"[red]✗ Data book build failed:[/red] {e}")
        logger.exception("Data book build failed")
        raise typer.Exit(1)


# Add command aliases
app.command(name="collect")(collect_daily_cmd)
app.command(name="normalize")(normalize_cmd)
app.command(name="adjust")(adjust_cmd)
app.command(name="build")(build_master_cmd)
app.command(name="validate")(validate_cmd)
app.command(name="backfill")(backfill_cmd)
app.command(name="import-archive")(import_archive_cmd)
app.command(name="coverage")(coverage_cmd)
app.command(name="databook")(databook_cmd)


if __name__ == "__main__":
    app()
