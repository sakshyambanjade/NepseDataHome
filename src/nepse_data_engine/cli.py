from __future__ import annotations

import typer
from rich.console import Console

from nepse_data_engine.collectors.sharesansar_daily import collect_daily as collect_daily_func
from nepse_data_engine.collectors.historical_importer import import_archive as import_archive_func
from nepse_data_engine.processors.clean_daily import clean_daily as clean_daily_func
from nepse_data_engine.processors.clean_daily import clean_all as clean_all_func
from nepse_data_engine.processors.adjust_prices import adjust_all as adjust_all_func
from nepse_data_engine.processors.build_master import build_master as build_master_func
from nepse_data_engine.processors.validate_data import validate_all as validate_all_func

app = typer.Typer(help="NEPSE Open Data Engine")
console = Console()

@app.command()
def collect_daily(date: str = "today"):
    output = collect_daily_func(date=date)
    console.print(f"[green]Raw daily data saved:[/green] {output}")

@app.command()
def import_archive(archive_dir: str):
    count = import_archive_func(archive_dir)
    console.print(f"[green]Imported raw archive files:[/green] {count}")

@app.command()
def clean(date: str = "today"):
    output = clean_daily_func(date=date)
    console.print(f"[green]Clean data saved:[/green] {output}")

@app.command()
def clean_all():
    count = clean_all_func()
    console.print(f"[green]Cleaned files:[/green] {count}")

@app.command()
def adjust_all():
    count = adjust_all_func()
    console.print(f"[green]Adjusted files generated:[/green] {count}")

@app.command()
def build_master(adjusted: bool = False):
    result = build_master_func(use_adjusted=adjusted)
    console.print("[green]Master dataset created[/green]")
    console.print(result)

@app.command()
def validate(fail_on_error: bool = True):
    result = validate_all_func(fail_on_error=fail_on_error)
    console.print("[green]Validation complete[/green]")
    console.print(
        {
            "files_checked": result["files_checked"],
            "total_errors": result["total_errors"],
            "total_warnings": result["total_warnings"],
        }
    )

@app.command()
def daily_run():
    raw = collect_daily_func(date="today")
    console.print(f"[green]Collected:[/green] {raw}")

    clean = clean_daily_func(date="today")
    console.print(f"[green]Cleaned:[/green] {clean}")

    adjusted_count = adjust_all_func()
    console.print(f"[green]Adjusted files:[/green] {adjusted_count}")

    master = build_master_func(use_adjusted=False)
    console.print(f"[green]Master clean dataset:[/green] {master}")

    adjusted_master = build_master_func(use_adjusted=True)
    console.print(f"[green]Master adjusted dataset:[/green] {adjusted_master}")

    validation = validate_all_func(fail_on_error=True)
    console.print(
        f"[green]Validation passed. Files checked:[/green] {validation['files_checked']}"
    )

if __name__ == "__main__":
    app()
