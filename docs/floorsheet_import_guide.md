# NEPSE Floorsheet Import & Intelligence Guide

This guide explains how to import raw NEPSE floorsheet data and generate production-grade broker intelligence artifacts.

## 1. Prepare Raw Data
Ensure your daily floorsheet is in CSV format. The filename should contain the date in `YYYY-MM-DD` format (e.g., `2026-05-13.csv`).

Required columns (or variants like 'buyer', 'qty'):
- `symbol`
- `buyer_broker`
- `seller_broker`
- `quantity`
- `rate`
- `transaction_no` (optional, but recommended for sequence analysis)

## 2. Import and Normalize
Run the following command to normalize the raw CSV and store it in the NepSense data lake:

```bash
nepsense floorsheet import data/floorsheet/raw/2026-05-13.csv
```

This command will:
1. Sanitize column names.
2. Normalize broker codes (e.g., `58.0` -> `58`).
3. Calculate missing `amount` and `txn_order` fields.
4. Save the result to `data/floorsheet/normalized/2026-05-13.csv`.

## 3. Generate Intelligence Artifacts
Generate the dashboard JSONs, including historical baseline comparisons and broker-specific profiles:

```bash
python3 src/nepsense/ml/generate_broker_dashboard_data.py --date 2026-05-13
```

This script performs:
- **Baseline Comparison**: Compares today's activity against the last 20 trading days.
- **Scoring**: Calculates Accumulation, Distribution, and Operator-flow scores.
- **Drilldowns**: Generates detailed data for Symbol and Broker detail pages.

## 4. View Results
Once generated, the following files are updated:
- `web/public/data/broker_overview.json` (Main rankings)
- `web/public/data/flowsheet_table.json` (Full market table)
- `web/public/data/symbols/{SYMBOL}_broker_flow.json` (Symbol drilldown)
- `web/public/data/brokers/{BROKER_ID}.json` (Broker profile)

Refresh your dashboard to see the latest intelligence.
