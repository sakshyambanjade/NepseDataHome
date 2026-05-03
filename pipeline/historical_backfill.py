"""Historical backfill entry point."""

from __future__ import annotations

from typer.main import get_command

from nepsense.cli import app


def main() -> None:
    get_command(app).main(
        args=["backfill", "--start", "2007-01-01", "--end", "today", "--build"],
        prog_name="nepsense",
    )


if __name__ == "__main__":
    main()
