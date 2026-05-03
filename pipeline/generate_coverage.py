"""Generate coverage reports for the NEPSE dataset."""

from __future__ import annotations

from nepsense.processors.coverage_report import generate_coverage_report, save_coverage_report


def main() -> None:
    metrics = generate_coverage_report()
    save_coverage_report(metrics)


if __name__ == "__main__":
    main()

