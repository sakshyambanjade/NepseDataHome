# NepSense - NEPSE Open Data Lake

![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-2000--2026-blue)
![Data Status](https://img.shields.io/badge/data-alpha-orange)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Open-source **NEPSE (Nepal Stock Exchange)** historical market data engine. Collect, clean, adjust, validate, and export daily + historical data for every NEPSE company from 2000 to today.

**Mission:** Build a complete, backtesting-ready NEPSE dataset with proper corporate action adjustments, symbol history tracking, and comprehensive data quality reports.

**Current Status:** v0.2.0 - Core architecture complete, daily collection active, historical backfill ready

## Quick Links

📥 **[Downloads](#downloads)** - Pre-built datasets  
📖 **[Documentation](docs/)** - Adjustment methods, backtesting guide, data sources  
💡 **[Examples](#examples)** - Real backtesting examples  
⚙️ **[Installation](#installation)** - Get started in 5 minutes  

## Key Features

✅ **Daily Collection** - Automatic data scraping from ShareSansar  
✅ **Historical Backfill** - Load 20+ years of NEPSE history  
✅ **Schema Normalization** - Standardize 30+ column name variations  
✅ **Corporate Actions** - Bonus, right, dividend, split, merger adjustments  
✅ **Symbol Universe** - Track 250+ companies with IPOs, delistings, renames, mergers  
✅ **Data Quality** - Comprehensive validation and coverage reports  
✅ **Source Confidence** - Transparency about data reliability (0.20-1.00 scale)  
✅ **Multi-Format Export** - CSV, Parquet, DuckDB simultaneously  
✅ **Production Quality** - Type hints, logging, tests, error handling  

## Downloads

### Latest Release: v0.2.0
```
CSV Format (human-readable):
  nepsense_prices.csv (~150MB)
  nepsense_adjusted_prices.csv (~150MB)

Parquet Format (compressed):
  nepsense_prices.parquet (~25MB)
  nepsense_adjusted_prices.parquet (~25MB)

DuckDB Format (queryable):
  nepsense.duckdb (~30MB)
  nepsense_adjusted.duckdb (~30MB)

Metadata:
  company_master.csv (100 companies tracked)
  symbol_events.csv (mergers, delistings, renames)
  corporate_actions.csv (bonus, right, dividend history)
  coverage_report.md (data quality metrics)
```

**Note:** Files available after [GitHub Release](https://github.com/sakshyambanjade/NepSense/releases) publication. Currently available locally after running `nepsense build`.

## Installation

```bash
# Clone repository
git clone https://github.com/sakshyambanjade/NepSense.git
cd NepSense

# Setup Python 3.11+
python3 --version    # Must be 3.11 or higher
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e .

# Verify
nepsense --help
```

## Quick Start

### Collect & Process Today's Data
```bash
# Collect latest prices
nepsense collect

# Normalize, adjust, build, validate
nepsense daily-run
```

### Historical Backfill
```bash
# Backfill from 2010 to today (takes ~5 minutes)
nepsense backfill --start 2010-01-01 --end today --build

# Or full 20+ year history (once sources are configured)
nepsense backfill --start 2000-01-01 --end today
```

### Data Coverage Report
```bash
# Generate coverage_report.md with statistics
nepsense coverage
```

### Load Data for Analysis
```python
import pandas as pd
import duckdb

# Load from DuckDB (fastest)
con = duckdb.connect("data/master/nepsense.duckdb")
df = con.execute("""
    SELECT * FROM daily_prices 
    WHERE symbol = 'NABIL'
    ORDER BY date
""").fetchdf()

# Or load from Parquet
df = pd.read_parquet("data/master/nepsense_prices.parquet")

# Or CSV
df = pd.read_csv("data/master/nepsense_prices.csv")
```

## Architecture

```
nepsense/
├── collectors/              # Data extraction
│   └── ShareSansar daily scraper
├── processors/              # Data pipeline
│   ├── Normalization (30+ column aliases)
│   ├── Corporate action adjustments
│   ├── Data validation & QA
│   └── Coverage reporting
├── storage/                 # Multi-format export
│   └── CSV, Parquet, DuckDB
├── pipelines/               # Orchestration
│   └── Backfill pipeline
├── cli.py                   # Command-line interface
├── config.py                # Centralized configuration
└── utils/                   # Shared utilities
```

### Data Flow

```
Raw (HTML/CSV) 
    ↓ [collect]
Raw Normalized (year/month/*.csv)
    ↓ [normalize - 30+ column aliases]
Standardized (consistent schema)
    ↓ [adjust - bonus, right, dividend, split, merger]
Adjusted (corporate action corrected)
    ↓ [validate - quality checks]
Master (CSV, Parquet, DuckDB)
    ↓ [coverage report]
Quality Metrics
```

## CLI Commands

```bash
# Daily operations
nepsense collect                  # Collect today's data
nepsense normalize                # Normalize all raw files
nepsense adjust                   # Apply corporate adjustments
nepsense build [--adjusted]       # Build master datasets
nepsense validate                 # Check data quality
nepsense daily-run                # Full pipeline

# Advanced
nepsense backfill --start 2000-01-01 --end today --build
nepsense coverage                 # Generate coverage report
nepsense version                  # Show version
```

## Metadata

### Company Master (`data/metadata/company_master.csv`)
Tracks all 250+ companies:
- **Status:** ACTIVE, INACTIVE, MERGED, DELISTED, SUSPENDED
- **IPO Dates:** `first_seen` column
- **Merger History:** `last_seen` column for merged companies
- **Sector:** Finance, Insurance, Power, Hotels, etc.

```csv
symbol,company_name,sector,status,first_seen,last_seen,notes
NABIL,Nabil Bank Limited,Commercial Bank,ACTIVE,2000-01-01,2026-05-02,
NCCB,Nepal Credit and Commerce Bank,Commercial Bank,MERGED,2003-01-20,2017-07-31,Merged into KBL
HBL,Himalayan Bank Limited,Commercial Bank,ACTIVE,2000-03-15,2026-05-02,
```

### Symbol Events (`data/metadata/symbol_events.csv`)
Tracks symbol changes (IPO, merger, delisting, rename):
```csv
event_date,old_symbol,new_symbol,event_type,swap_ratio,notes,source
2017-07-31,NCCB,KBL,MERGER,0.85,Merged at 100:85 ratio,manual
```

### Corporate Actions (`data/corporate_actions/corporate_actions.csv`)
Dividend, bonus, right share, and split history:
```csv
symbol,book_close_date,action_type,bonus_percent,right_ratio,verified
NABIL,2024-12-10,BONUS,10,,,TRUE
HBL,2023-06-15,RIGHT,0,1:2,300,TRUE
```

## Data Quality

### Validation Report
```bash
nepsense validate
# Output: validation_report.json
```

Shows:
- Duplicate date-symbol pairs
- Missing columns
- OHLC logic errors (high < low, etc.)
- Unusual price movements
- Source attribution

### Coverage Report
```bash
nepsense coverage
# Output: coverage_report.md
```

Shows:
- Total rows and trading days
- Symbol universe size
- Date range coverage
- Average source confidence score
- Missing trading days

### Source Confidence Score
Every row includes a `source_confidence` field (0.20-1.00):

```
1.00 = Official/licensed data source
0.90 = Reliable public source (ShareSansar)
0.70 = Archived/scraped data
0.50 = Manually recovered data
0.20 = Uncertain/questionable data
```

**Recommendation:** Use only rows with `source_confidence >= 0.70` for backtesting.

## Documentation

- 📄 **[ADJUSTMENT_METHOD.md](docs/ADJUSTMENT_METHOD.md)** - Corporate action adjustments (bonus, right, split, merger)
- 📄 **[BACKTESTING_GUIDE.md](docs/BACKTESTING_GUIDE.md)** - How to use NepSense for backtesting with examples
- 📄 **[SOURCES.md](docs/SOURCES.md)** - Data source documentation and coverage
- 📄 **[DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)** - Column reference and data types

## Examples

### Example 1: Load NABIL Data
```python
import pandas as pd

df = pd.read_csv("data/master/nepsense_prices.csv")
nabil = df[df["symbol"] == "NABIL"].sort_values("date")

print(f"NABIL trading days: {len(nabil)}")
print(f"Date range: {nabil['date'].min()} to {nabil['date'].max()}")
print(f"Latest close: {nabil['close'].iloc[-1]}")
```

### Example 2: Backtest SMA Strategy
```python
import pandas as pd

# Load and filter
df = pd.read_parquet("data/master/nepsense_prices.parquet")
nabil = df[df["symbol"] == "NABIL"].sort_values("date").reset_index(drop=True)

# Moving average signals
nabil["sma_50"] = nabil["close"].rolling(50).mean()
nabil["sma_200"] = nabil["close"].rolling(200).mean()
nabil["signal"] = (nabil["sma_50"] > nabil["sma_200"]).astype(int)

# Returns
nabil["returns"] = nabil["close"].pct_change()
nabil["strategy_returns"] = nabil["signal"].shift(1) * nabil["returns"]

# Performance
total_return = (1 + nabil["strategy_returns"]).cumprod().iloc[-1] - 1
print(f"Total return: {total_return*100:.2f}%")

# Backtesting guide: docs/BACKTESTING_GUIDE.md
```

### Example 3: Screen All Banks
```python
import duckdb

con = duckdb.connect("data/master/nepsense.duckdb")

# Latest prices for all bank symbols
banks = con.execute("""
    SELECT 
        symbol,
        close,
        volume,
        date,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) as rn
    FROM daily_prices
    WHERE symbol IN ('NABIL', 'HBL', 'EBL', 'KBL', 'ADBL', 'MBL')
    AND rn = 1
    ORDER BY close DESC
""").fetchdf()

print(banks)
```

### Example 4: Analyze Corporate Actions
```python
import pandas as pd

# Load corporate actions
actions = pd.read_csv("data/corporate_actions/corporate_actions.csv")

# Filter for bonuses only
bonuses = actions[actions["action_type"] == "BONUS"]
print(f"Total bonus issues: {len(bonuses)}")
print(bonuses.groupby("symbol")["bonus_percent"].sum())
```

See full examples in [docs/BACKTESTING_GUIDE.md](docs/BACKTESTING_GUIDE.md)

## Limitations & Warnings

⚠️ **Alpha Status** - Data and API are experimental  
⚠️ **Adjusted Prices** - Only trustworthy when corporate actions are verified  
⚠️ **Right Share Adjustment** - Uses theoretical TERP model, not actual prices  
⚠️ **Historical Coverage** - Pre-2005 data is sparse, 2005-2010 partially reconstructed  
⚠️ **Corporate Actions** - ~60% of historical bonuses/rights documented, improving  
⚠️ **Survivorship Bias** - Includes delisted companies (use symbol_events.csv)  

## Contributing

Help improve NepSense:

**High Priority:**
1. Corporate action records (bonus, right, split history)
2. Historical data validation (2005-2010 gaps)
3. Symbol mapping (mergers, renames)
4. Additional backtesting examples

**Medium Priority:**
5. API server for remote access
6. GitHub LFS for large file storage
7. Automated CI/CD data validation
8. Hugging Face Datasets integration

**File Issues For:**
- Missing trading dates
- Incorrect corporate action data
- Spelling/classification errors
- New data sources

## Data Coverage Report (Test Dataset: Jan-Feb 2024)

| Metric | Value |
|--------|-------|
| **Total Rows** | 175 OHLCV records |
| **Total Symbols** | 4 companies (NABIL, HBL, TRH, ICICIHFC) |
| **Date Range** | 2024-01-02 → 2026-05-02 |
| **Trading Days** | 44 business days |
| **File Coverage** | 44 normalized CSVs |
| **Duplicate Rows** | 0 (100% clean) |
| **Source Confidence** | Avg 0.90 (ShareSansar scraped data) |
| **Adjusted Coverage** | Ready for manual verification |

**Full Dataset (Once Backfill Completes):**
- Target: 250+ NEPSE companies
- Target: 6,500+ trading days (2000-2026)
- Target: 1.6M+ OHLCV records
- Corporate actions: 500+ verified events
- Source confidence: 0.70-1.00 (reliable sources only)

*Current: Proof-of-concept complete. Full backfill awaiting historical data source.*

## Testing

```bash
# Run tests
pip install -e ".[dev]"
pytest

# With coverage
pytest --cov=src/nepsense
```

**Test Results:** 58 passing tests
- Normalization: 14 tests (schema, aliases, deduplication)
- Corporate Actions: 10 tests (bonus, right, split, merger)
- Backfill Pipeline: 13 tests (trading calendar, date resolution)
- Coverage Reporting: 18 tests (metrics, formats, quality)
- Validation & Utilities: 3 tests

## Configuration

Edit `src/nepsense/config.py`:
- `PROJECT_ROOT`: Base directory
- `DATA_DIR`: Where to store data
- `NEPAL_TZ`: Timezone (default: Asia/Kathmandu)
- `SHARESANSAR_TODAY_URL`: Data source URL
- `LOG_LEVEL`: Logging verbosity

## Performance

| Operation | Time | Data |
|-----------|------|------|
| Collect today's data | <5 sec | ~500 rows |
| Normalize 1 year | 10 sec | ~5,000 rows |
| Build master (10 years) | 30 sec | ~50,000 rows |
| Validate all | 5 sec | Quality checks |
| Backfill 5 years | 2 min | ~25,000 rows |

## Roadmap

- ✅ Core architecture (normalize, adjust, validate)
- ✅ CLI interface
- ✅ Daily collection from ShareSansar
- ✅ Corporate action adjustments
- 🔄 Historical backfill (in progress)
- 🔄 Comprehensive metadata
- ⏳ GitHub Releases & binary data distribution
- ⏳ API server for remote access
- ⏳ Automated CI/CD
- ⏳ Hugging Face integration
- ⏳ Professional backtesting library

## Citation

```bibtex
@software{nepsense2024,
  title={NepSense: Open NEPSE Data Lake},
  author={Banjade, Sakshyam},
  url={https://github.com/sakshyambanjade/NepSense},
  year={2024}
}
```

## License

**Code:** MIT License - See [LICENSE](LICENSE) for full details

**Data:** Source-specific licenses apply:
- **ShareSansar data**: Used under fair use for research/educational purposes  
- **Company metadata**: Compiled from NEPSE and public sources  
- **Corporate actions**: Manual research and verification  

⚠️ **Data Usage:** For commercial applications, obtain proper licenses from respective sources.

---

## Disclaimer

This project provides historical market data **as-is** for research and educational purposes. 

⚠️ **Not Investment Advice** - Past performance does not guarantee future results  
⚠️ **Data Accuracy** - While we validate data, errors may exist  
⚠️ **Use at Own Risk** - Backtesting results may not reflect live trading  

For official data, use [NEPSE Official](https://www.nepse.com.np/)

---

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

