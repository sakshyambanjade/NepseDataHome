"""Validate the normalized NEPSE dataset."""

from __future__ import annotations

from nepsense.processors.validate_data import validate_all


def main() -> None:
    validate_all(fail_on_error=True)


if __name__ == "__main__":
    main()

