# NepSense - NEPSE Open Data Lake

Open-source NEPSE (Nepal Stock Exchange) historical market data engine. Collect, clean, adjust, validate, and export daily + historical data for every NEPSE company from 2000 to today.

**Goal:** Build a complete, backtesting-ready NEPSE dataset with proper corporate action adjustments, symbol history tracking, and data quality reports.

## Key Features

✅ **Daily Collection** - Scrape latest NEPSE data from ShareSansar  
✅ **Historical Backfill** - Import from multiple sources  
✅ **Schema Normalization** - Standardize diverse data formats  
✅ **Corporate Actions** - Bonus, right, dividend, split, merger adjustments  
✅ **Symbol Universe** - Track IPOs, delistings, renames, mergers  
✅ **Data Quality** - Comprehensive validation and coverage reports  
✅ **Multiple Exports** - CSV, Parquet, DuckDB formats  
✅ **Production Quality** - Logging, type hints, tests, error handling  

## Quick Start

```bash
# Clone and setup
git clone https://github.com/sakshyambanjade/NepSense.git
cd NepSense
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Run pipeline
nepsense collect          # Collect today's data
nepsense normalize        # Normalize all files
nepsense adjust           # Apply corporate adjustments
nepsense build            # Create master datasets
nepsense validate         # Check quality

# Or run everything
nepsense daily-run        # Complete pipeline
```

## Architecture

```
src/nepsense/
├── collectors/          # Data sources (ShareSansar, etc)
├── processors/          # Normalize, adjust, validate
├── storage/            # Export to CSV, Parquet, DuckDB
├── cli.py              # Command-line interface
├── config.py           # Configuration
└── utils/              # Shared utilities
```

## Data Folder Structure

```
data/
├── raw/                        # Raw HTML scrapes
│   └── source=sharesansar/year=2026/month=05/
├── normalized/                 # Standardized schema
│   └── year=2026/month=05/
├── adjusted/                   # Corporate action adjusted
│   └── year=2026/month=05/
├── metadata/                   # Company, events, actions
│   ├── company_master.csv
│   ├── symbol_events.csv
│   └── corporate_actions.csv
├── master/                     # Final datasets
│   ├── nepsense_prices.csv
│   ├── nepsense_prices.parquet
│   ├── nepsense_adjusted_prices.csv
│   └── nepsense.duckdb
└── quality/                    # Validation reports
    ├── validation_report.json
    ├── validation_issues.csv
    └── symbol_coverage.csv
```

## CLI Commands

```bash
nepsense collect              # Collect today's data
nepsense normalize            # Normalize all raw files
nepsense adjust               # Apply corporate adjustments
nepsense build [--adjusted]   # Build master datasets
nepsense validate             # Check data quality
nepsense daily-run            # Full pipeline

# Aliases
nepse-data [command]          # Alternative command name
```

## Metadata Files

### Company Master (`data/metadata/company_master.csv`)
```csv
symbol,company_name,sector,listed_shares,paidup_value,total_paidup,status,first_seen,last_seen
NABIL,Nabil Bank Limited,Finance,3500000,100,350000000,ACTIVE,2000-01-01,2026-05-02
```

### Symbol Events (`data/metadata/symbol_events.csv`)
```csv
old_symbol,new_symbol,event_type,event_date,notes
NCCB,KBL,MERGER,2017-07-31,Merger at 100:85 ratio
```

### Corporate Actions (`data/corporate_actions/corporate_actions.csv`)
```csv
symbol,book_close_date,announcement_date,action_type,bonus_percent,cash_dividend_percent,verified
NABIL,2024-12-10,2024-11-15,BONUS,10,0,true
```

## Corporate Action Adjustments

### Bonus Shares
```
adjusted_price = raw_price / (1 + bonus_percent / 100)
Example: 10% bonus = prices before book close divided by 1.1
```

### Right Shares
```
TERP = ((old_price × old_shares) + (right_price × right_shares)) / total_shares
```

### Mergers
```
adjusted_price = raw_price / swap_ratio
Example: NCCB→KBL 100:85 = prices multiplied by 85/100
```

## Data Quality Checks

Validation checks:
- ✅ Required columns (date, symbol, close)
- ✅ No duplicate date-symbol pairs
- ✅ OHLC integrity (high ≥ low, close between high-low)
- ✅ No future dates
- ✅ No negative volume
- ✅ Unusual price movements documented
- ✅ Complete source attribution

## Backfill from 2000

```bash
# 1. Download historical CSVs from sources
# 2. Place in archive directory
# 3. Import them
nepsense import-archive --archive-dir /path/to/archive

# 4. Process normally
nepsense normalize
nepsense adjust
nepsense build
nepsense validate
```

## Data Sources

- **ShareSansar** (Daily prices) - Primary source
- **MeroLagani** (Company list) - Symbol info
- **NepseAlpha** (Historical) - Future integration
- **Manual imports** - Archive backfill

## Status & Limitations

⚠️  **Alpha Status** - Data is experimental, not production-ready  
⚠️  **Adjusted prices** - Requires verified corporate action data  
⚠️  **Right share adjustment** - Uses theoretical model  
⚠️  **Historical gaps** - Before 2005 data is sparse  

## Testing

```bash
pip install -e ".[dev]"
pytest
pytest --cov        # With coverage
```

## Configuration

Edit `src/nepsense/config.py` to change paths, sources, or logging.

## Contributing

Priority areas:
1. Historical data backfill
2. Corporate action records
3. Symbol mapping documentation
4. Additional tests
5. Documentation examples

## Citation

```bibtex
@software{nepsense2024,
  title={NepSense: Open NEPSE Data},
  author={Banjade, Sakshyam},
  url={https://github.com/sakshyambanjade/NepSense},
  year={2024}
}
```

## License

MIT - See LICENSE file

## Changelog

**v0.2.0** (2026-05-02)
- Package rename to `nepsense`
- Modular architecture
- Enhanced corporate actions (bonus, right, dividend, split, merger)
- Symbol universe tracking
- Comprehensive quality validation
- Improved CLI (11 commands)
- Better documentation

**v0.1.0** (2026-05-02)
- Initial skeleton project

## Links

- 📚 [GitHub](https://github.com/sakshyambanjade/NepSense)
- 🐛 [Issues](https://github.com/sakshyambanjade/NepSense/issues)
- 💬 [Discussions](https://github.com/sakshyambanjade/NepSense/discussions)

---

**Status:** Early Alpha · **Last Updated:** May 2, 2026 · **Maintainer:** [@sakshyambanjade](https://github.com/sakshyambanjade)

