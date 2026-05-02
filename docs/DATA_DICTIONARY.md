# Data Dictionary

Complete reference for all columns in NepSense datasets.

## Standard OHLCV Data

Used in `data/raw/`, `data/normalized/`, and `data/adjusted/` files.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | DATE | Trading date in YYYY-MM-DD format | 2026-05-02 |
| `symbol` | STRING | Stock symbol, uppercase | NABIL |
| `open` | FLOAT | Opening price | 1450.00 |
| `high` | FLOAT | Daily high price | 1465.00 |
| `low` | FLOAT | Daily low price | 1445.00 |
| `close` | FLOAT | Closing price (Last Traded Price) | 1460.00 |
| `volume` | INT | Quantity of shares traded | 50000 |
| `turnover` | INT | Total value traded in NPR | 73000000 |
| `transactions` | INT | Number of transactions on day | 250 |
| `source` | STRING | Source URL or origin | https://www.sharesansar.com/... |

## Adjusted Data Only

Additional columns in `data/adjusted/` files when corporate actions applied.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `adjusted_open` | FLOAT | Open price adjusted for corporate actions | 1409.09 |
| `adjusted_high` | FLOAT | High price adjusted | 1422.73 |
| `adjusted_low` | FLOAT | Low price adjusted | 1404.55 |
| `adjusted_close` | FLOAT | Close price adjusted | 1418.18 |
| `adjustment_factor` | FLOAT | Cumulative adjustment multiplier | 1.1 |

### Adjustment Factor Interpretation

- `1.0` = No corporate actions
- `> 1.0` = Bonus shares, split, or merger applied (prices divided by factor)
- `< 1.0` = Reverse split or merger (rare)

**Example:** adjustment_factor = 1.1 means 10% bonus → prices divided by 1.1

## Company Master

File: `data/metadata/company_master.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `symbol` | STRING | Stock symbol | NABIL |
| `company_name` | STRING | Full company name | Nabil Bank Limited |
| `sector` | STRING | Industry sector | Finance |
| `listed_shares` | INT | Number of listed shares | 3500000 |
| `paidup_value` | FLOAT | Paid-up value per share in NPR | 100 |
| `total_paidup` | INT | Total paid-up capital | 350000000 |
| `status` | STRING | ACTIVE, INACTIVE, DELISTED, SUSPENDED | ACTIVE |
| `first_seen` | DATE | First trading date | 2000-01-01 |
| `last_seen` | DATE | Most recent trading date | 2026-05-02 |

## Symbol Events

File: `data/metadata/symbol_events.csv`

Tracks changes: mergers, renames, delistings, IPOs, etc.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `old_symbol` | STRING | Previous symbol (before event) | NCCB |
| `new_symbol` | STRING | New symbol (after event) | KBL |
| `event_type` | STRING | IPO, MERGER, DELISTED, RENAMED, SUSPENDED, SECTOR_CHANGED, etc. | MERGER |
| `event_date` | DATE | Date event took effect | 2017-07-31 |
| `notes` | STRING | Additional details and swap ratios | Merged at 100:85 ratio |

### Event Types

- **IPO** - Initial public offering
- **MERGER** - Merged with another company
- **RENAMED** - Symbol or name changed
- **DELISTED** - Removed from exchange
- **SUSPENDED** - Temporarily suspended from trading
- **SECTOR_CHANGED** - Sector classification changed
- **PROMOTER_TO_PUBLIC** - Ownership structure changed

## Corporate Actions

File: `data/corporate_actions/corporate_actions.csv`

Defines adjustments to historical prices.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `symbol` | STRING | Stock symbol | NABIL |
| `book_close_date` | DATE | Book closure date when action takes effect | 2024-12-10 |
| `announcement_date` | DATE | When action was announced | 2024-11-15 |
| `action_type` | STRING | BONUS, RIGHT, CASH_DIVIDEND, SPLIT, MERGER_SWAP, FACE_VALUE_CHANGE | BONUS |
| `bonus_percent` | FLOAT | Bonus share percentage (0-1000) | 10 |
| `cash_dividend_percent` | FLOAT | Dividend as percentage of par value | 15 |
| `right_ratio` | FLOAT | Right shares ratio OR split ratio OR merger ratio | 2 |
| `right_price` | FLOAT | Issue price of right shares in NPR | 400 |
| `source_url` | STRING | Source of information | https://www.sharesansar.com |
| `verified` | BOOLEAN | Is this action verified and reliable? | true |

### Action Types

- **BONUS** - Bonus share issuance (bonus_percent required)
- **RIGHT** - Right share offering (right_ratio, right_price required)
- **CASH_DIVIDEND** - Cash dividend (cash_dividend_percent required)
- **SPLIT** - Stock split (right_ratio = new:old ratio)
- **MERGER_SWAP** - Merger with swap ratio (right_ratio = new:old ratio)
- **FACE_VALUE_CHANGE** - Par value change (right_ratio = new:old ratio)

### Verification Status

Only actions with `verified = true` are applied in official adjustments.

## Validation Report

File: `data/quality/validation_report.json`

```json
{
  "files_checked": 100,
  "total_errors": 2,
  "total_warnings": 15,
  "reports": [
    {
      "file": "data/normalized/2026/05/2026-05-02.csv",
      "rows": 250,
      "errors": [],
      "warnings": ["Extreme price movement (>90%) in 1 rows"]
    }
  ]
}
```

## Validation Issues

File: `data/quality/validation_issues.csv`

```csv
file,level,message
data/normalized/2026/05/2026-05-01.csv,ERROR,High < Low in 2 rows
data/normalized/2026/05/2026-05-01.csv,WARNING,Close outside High-Low range in 1 rows
```

## Symbol Coverage

File: `data/quality/symbol_coverage.csv`

```csv
symbol,first_date,last_date,trading_days
NABIL,2000-01-01,2026-05-02,6500
HBL,2000-01-04,2026-05-02,6498
TRH,2010-06-15,2026-05-02,4000
```

---

**Last Updated:** May 2, 2026
