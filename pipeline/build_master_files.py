"""Build master CSV, Parquet, DuckDB, and public history files."""

from __future__ import annotations

from nepsense.databook import build_data_book


def main() -> None:
    build_data_book(rebuild_master=True)


if __name__ == "__main__":
    main()

