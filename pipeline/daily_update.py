"""Daily update entry point for Cloud Scheduler/Cloud Run jobs."""

from __future__ import annotations

from typer.main import get_command

from nepsense.cli import app


def main() -> None:
    get_command(app).main(args=["daily-run"], prog_name="nepsense")


if __name__ == "__main__":
    main()
