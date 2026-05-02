# Historical Data Completeness

NepSense aims to become a backtesting-ready NEPSE data lake from 2000 to today.
The first broad historical import now covers 2007 onward from a public
MIT-licensed company-wise archive, plus the project daily sample data.

## Current Local Coverage

As of the latest local coverage run:

| Metric | Value |
|--------|-------|
| Rows | 265,426 |
| Symbols | 125 |
| Date range | 2007-01-01 to 2026-05-02 |
| Trading days | 4,369 |
| Primary historical source | Aabishkar2/nepse-data (`MIT`) |
| Historical source confidence | 0.70 |

This is a major historical data baseline, but it is not yet a fully verified
official/licensed dataset. Adjusted prices and corporate-action completeness
still require additional verification.

## Required For 2000-To-Today Coverage

1. **Licensed or otherwise reliable historical source**
   - Prefer NEPSE-authorized historical data access for production-grade
     completeness.
   - Public scrapers can bootstrap development, but they should carry explicit
     source confidence and provenance.

2. **Daily market-wide historical ingestion**
   - The current ShareSansar collector is suitable for current market data.
   - Historical backfill must use a true historical endpoint or import archive,
     not the current-day page replayed across old dates.
   - `nepsense import-archive /path/to/csvs --source <name>` is the preferred
     path for verified bulk CSV archives today.
   - `nepsense import-companywise /path/to/company-wise-csvs --source <name>`
     imports `SYMBOL.csv` archives into daily files.

3. **Company universe reconstruction**
   - Track IPOs, delistings, mergers, symbol changes, sector changes, and
     inactive companies.

4. **Corporate action verification**
   - Bonus shares, rights, cash dividends, mergers, splits, and face-value
     changes must be verified before adjusted prices are treated as
     backtesting-grade.

5. **Coverage gate**
   - A release is complete only if `nepsense coverage` reports:
     - start date on or before 2000-01-01,
     - end date equal to the latest expected trading day,
     - broad active and inactive symbol coverage,
     - zero duplicate date-symbol pairs,
     - no unreviewed critical validation errors.

## Two Complementary Systems

### 1. Daily Collector

Run `nepsense daily-run` after each market day. It collects the full market
snapshot, normalizes it, rebuilds master data, validates quality, and publishes
the public data book.

### 2. Historical Importer

Run `nepsense import-archive /path/to/historical-csvs --source verified_archive`
whenever older daily market files are found or licensed. Files are partitioned
by source and date so provenance remains visible:

```text
data/raw/source=verified_archive/YYYY/MM/YYYY-MM-DD.csv
data/normalized/source=verified_archive/YYYY/MM/YYYY-MM-DD.csv
```

The public data book then exposes:

```text
data/history/nepse_all_prices.csv
data/history/by_symbol/NABIL.csv
data/history/by_date/2024-01-02.csv
```

## Near-Term Project Priorities

1. Add a historical source adapter with retries, rate limiting, and raw response
   snapshots.
2. Add an archive-import path for verified CSV/Parquet backfills.
3. Add source confidence and provenance to every row.
4. Replace the approximate holiday list with a versioned NEPSE trading calendar.
5. Add CI checks that fail when master data products exclude available
   normalized partitions.
