# NEPSE Open Data Engine

Open-source NEPSE historical data collector, cleaner, validator, and exporter.

## Features

- Daily NEPSE data collection
- Historical archive import
- Daily CSV folder structure
- Cleaned data generation
- Experimental adjusted-price generation
- Master CSV export
- Master Parquet export
- DuckDB export
- Data validation reports
- CircleCI automation

## Folder Format

```text
data/raw/YYYY/MM/YYYY-MM-DD.csv
data/clean/YYYY/MM/YYYY-MM-DD.csv
data/adjusted/YYYY/MM/YYYY-MM-DD.csv
data/master/nepse_all_companies_daily.csv
data/master/nepse_all_companies_daily.parquet
data/master/nepse_all_companies_daily.duckdb
```

## Install

```bash
pip install -e .
```

## Commands

Collect today's data:

```bash
nepse-data collect-daily
```

Clean today's data:

```bash
nepse-data clean --date today
```

Import old CSV archive:

```bash
nepse-data import-archive --archive-dir path/to/archive
```

Clean all raw files:

```bash
nepse-data clean-all
```

Generate adjusted files:

```bash
nepse-data adjust-all
```

Build master dataset:

```bash
nepse-data build-master
```

Validate data:

```bash
nepse-data validate
```

Full daily run:

```bash
nepse-data daily-run
```

## Data Status

* Raw data: source snapshot
* Clean data: normalized daily OHLCV-style format
* Adjusted data: experimental unless corporate actions are verified

## Important

Corporate-action adjustment needs verified bonus/right/dividend data.

Put verified actions inside:

```text
data/corporate_actions/corporate_actions.csv
```

Format:

```csv
symbol,book_close_date,action_type,bonus_percent,cash_dividend_percent,right_ratio,issue_price,notes
NABIL,2024-12-10,bonus,10,0,,,10 percent bonus
```

