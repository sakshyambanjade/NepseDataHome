# Data Sources

Complete documentation of NepSense data sources, collection methods, coverage, and limitations.

## Overview

NepSense aggregates NEPSE data from multiple sources:

| Source | Type | Coverage | Status |
|--------|------|----------|--------|
| ShareSansar | Web Scraping | 2010-Today | ✅ Active Daily |
| NepseAlpha | Historical Export | ~2000-2020 | ⚠️ Manual Import |
| MeroLagani | Company Data | 2010-Today | ⏳ Future |
| NEPSE Official | Direct API | 2020-Today | ⏳ Future |
| Manual Compilation | Historical Records | 2000-2009 | ⏳ Future |

## 1. ShareSansar Daily Data

**Website:** https://www.sharesansar.com/

### Collection Method

NepSense automatically collects daily OHLCV data from ShareSansar's "Today's share price" page:

```python
# From src/nepsense/collectors/__init__.py
collect_daily(date, output_root)
```

### Coverage

- **Start Date:** 2010 (earliest available)
- **Current Date:** Today (automatic)
- **Frequency:** Daily (after market close ~4 PM NPT)
- **Symbols:** All listed companies (~250+)
- **Completeness:** ~99% for listed symbols

### Data Quality

**Strengths:**
- ✅ Most complete public data source
- ✅ Real-time updates daily
- ✅ Includes turnover and transaction counts
- ✅ Covers all current symbols
- ✅ Free and publicly accessible

**Weaknesses:**
- ⚠️  Delisted companies not in daily page
- ⚠️  No adjustments provided
- ⚠️  Historical pages sometimes reset
- ⚠️  No corporate action announcements
- ⚠️  Column names vary across table updates

**Validation Rules:**
- Must have: symbol, close, volume
- volume >= 0
- high >= low
- close between high and low

### Example Data

```csv
date,symbol,open,high,low,close,volume,turnover,transactions,source
2024-05-02,NABIL,1476.50,1485.00,1470.00,1480.00,125000,185000000,2500,sharesansar
2024-05-02,HBL,1520.00,1530.00,1510.00,1525.00,85000,129000000,1800,sharesansar
```

### Using ShareSansar Data

Collect specific date or today:

```bash
nepsense collect  # Today's data
```

Or in code:
```python
from nepsense.collectors import collect_daily
path = collect_daily("2024-05-02", "data/raw")
```

## 2. NepseAlpha Historical Export

**Website:** https://nepsealpha.com/ (no longer active, archived)

### Coverage

- **Period:** ~2005-2020
- **Symbols:** 100-150 companies (historical)
- **Frequency:** Daily
- **Data Type:** OHLCV
- **Access:** Manual download from archived site

### Data Quality

**Strengths:**
- ✅ Only source for pre-2010 data
- ✅ Comprehensive historical coverage
- ✅ Good data quality for its time
- ✅ Includes delisted companies

**Weaknesses:**
- ⚠️  Site no longer active
- ⚠️  Data not continuously updated
- ⚠️  Column naming inconsistent
- ⚠️  Some gaps in 2010-2015
- ⚠️  No dividends/bonus documentation

### Manual Import Process

1. Download historical CSV from archive
2. Place in `data/raw/nepsealpha_historical/`
3. Run importer:

```bash
nepsense import-historical --source nepsealpha
```

## 3. MeroLagani Company Master

**Website:** https://www.merolagani.com/

### Coverage

- **Type:** Company metadata
- **Data:** Company name, sector, listed shares, paid-up capital
- **Symbols:** Current 250+ symbols
- **IPO Data:** First listing date
- **Status:** Active, continuously updated

### Data Quality

**Strengths:**
- ✅ Most accurate company info
- ✅ Includes IPO dates
- ✅ Sector categorization
- ✅ Up-to-date symbol changes

**Weaknesses:**
- ⚠️  Historical IPO dates may be approximate
- ⚠️  Delisted companies eventually removed
- ⚠️  Manual web scraping required

### Usage

Master data merged into `company_master.csv`:

```csv
symbol,company_name,sector,listed_shares,paidup_value,total_paidup,status,first_seen,last_seen
NABIL,Nabil Bank Limited,Finance,3500000,100,350000000,ACTIVE,2000-01-01,2024-05-02
HBL,Himalayan Bank Limited,Finance,2000000,100,200000000,ACTIVE,2000-03-15,2024-05-02
```

## 4. Corporate Action Data

### Coverage

- **Bonus Shares:** 2000-Today
- **Right Shares:** 2000-Today
- **Stock Splits:** 2000-Today
- **Mergers:** 2000-Today
- **Dividends:** 2000-Today
- **Completeness:** ~60% (still being compiled)

### Sources

Data collected from:
- Company websites
- NEPSE announcements
- ShareSansar flash news
- MeroLagani news
- Manual historical records

### Format

```csv
symbol,book_close_date,announcement_date,action_type,bonus_percent,cash_dividend_percent,right_ratio,right_price,source_url,verified
NABIL,2024-12-10,2024-11-25,BONUS,10,0,,,"https://www.nabilbank.com",TRUE
HBL,2023-06-15,2023-05-20,RIGHT,1:2,0,100,300,"https://www.hbl.com",TRUE
```

### Verification

Each action has:
- `verified` flag (TRUE/FALSE)
- `source_url` (link to announcement)

Only verified actions applied in adjustment pipeline.

### Limitation

⚠️ **Many historical actions not documented.** Without complete corporate actions:
- Adjusted prices may be incomplete
- Returns analysis distorted
- Comparisons across adjusted/unadjusted unreliable

**Contributing:** Help compile missing actions by filing issues with:
- Symbol and date
- Action type (bonus %, right ratio, etc.)
- Source link

## 5. NEPSE Official API

**Status:** Planned for future integration

### Potential Coverage

- Live index data
- Sector indices
- Floorsheet data (transaction-level)
- Company announcements
- Corporate action notices
- Trading calendar

### Current Limitations

- No public free API available
- Access requires NEPSE member credentials
- Floorsheet data only via terminal subscriptions

## Data Quality Report

### Validation Checks

Run validation to assess data quality:

```bash
nepsense validate
```

Output: `validation_report.json`

```json
{
  "total_files": 5104,
  "files_with_errors": 3,
  "total_rows": 1245000,
  "error_summary": {
    "missing_columns": 0,
    "duplicate_dates": 3,
    "invalid_ohlc": 0,
    "negative_volume": 0
  },
  "symbol_coverage": {
    "active_symbols": 250,
    "total_trading_days": 3652,
    "date_range": ["2010-01-01", "2024-05-02"]
  }
}
```

### Known Issues

1. **Delisted Companies**
   - ⚠️ Not in ShareSansar daily collection
   - ✅ Included in historical exports
   - → Use `company_master.csv` for dates

2. **Missing Corporate Actions**
   - ⚠️ ~40% of historical actions not documented
   - Impact: Adjusted prices incomplete
   - → Use unadjusted prices or caution with adjustments

3. **Column Name Variations**
   - ⚠️ ShareSansar occasionally changes column names
   - → Handled by normalization (30+ aliases)

4. **Data Gaps**
   - ⚠️ 2000-2010 data from NepseAlpha (limited)
   - ⚠️ Some symbols have gaps 2010-2015
   - → Check symbol_coverage.csv for date ranges

5. **Turnover Calculation**
   - ⚠️ Some sources show turnover, not volume
   - ✅ Normalized to standard OHLCV
   - → Use volume/close for turnover if needed

## Attribution & License

| Source | License | Attribution | Terms |
|--------|---------|-------------|-------|
| ShareSansar | Creative Commons | Required | Educational use free |
| NepseAlpha | Unknown | Unknown | Archive only |
| MeroLagani | Terms of Service | Optional | Personal use free |
| NEPSE | Copyright | Required | Non-commercial |

**When publishing analysis:**
```
Data from ShareSansar.com, MeroLagani.com, and historical NEPSE sources.
Compiled by NepSense: https://github.com/...
```

## Troubleshooting Data Issues

### Problem: Missing data for date X

```python
import duckdb
con = duckdb.connect("data/master/daily_prices.duckdb")

# Check if market was closed
trades = con.execute("""
    SELECT COUNT(*) as count FROM daily_prices WHERE date = '2024-03-15'
""").fetchone()

if trades[0] == 0:
    print("Market was closed (holiday or weekend)")
```

### Problem: Adjusted prices seem wrong

```python
# Check adjustment factor
df = con.execute("""
    SELECT symbol, adjustment_factor 
    FROM daily_prices 
    WHERE symbol = 'NABIL' 
    ORDER BY date DESC LIMIT 20
""").fetchdf()

print(df)  # If > 1.0, bonus/split recently applied
```

### Problem: Old stock not in data

```python
# Check company_master.csv
master = pd.read_csv("data/metadata/company_master.csv")
old_stock = master[master["symbol"] == "OLD_TICKER"]

if len(old_stock) > 0:
    print(f"Last seen: {old_stock.iloc[0]['last_seen']}")
    # Check symbol_events for renames
```

## Contributing Data

Help improve NepSense by:

1. **Reporting Gaps**: File issue with missing dates/symbols
2. **Corporate Actions**: Submit bonus/right/split/merger data with sources
3. **Historical Data**: If you have pre-2010 OHLC data, please share
4. **Company Info**: Updates to company_master.csv

Submit pull request or issue: https://github.com/...

## Data Updates

- **Daily:** ShareSansar prices (automatic)
- **Weekly:** Corporate action compilation (manual)
- **Monthly:** Master dataset release to GitHub
- **Quarterly:** Symbol universe audit (manual)

## See Also

- [ADJUSTMENT_METHOD.md](ADJUSTMENT_METHOD.md) - Corporate action adjustments
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) - Column definitions
- [BACKTESTING_GUIDE.md](BACKTESTING_GUIDE.md) - Using data for analysis

---

**Last Updated:** May 2, 2026  
**Status:** Beta - Data quality improving continuously
