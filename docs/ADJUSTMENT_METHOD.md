# Adjustment Method

Detailed explanation of how NepSense adjusts historical prices for corporate actions.

## Overview

Stock prices need to be adjusted for certain corporate actions to create a fair historical comparison:

- **Bonus shares** → More shares at lower prices
- **Right shares** → Dilution from new share issuance
- **Splits** → Change in par value
- **Mergers** → Swap to new company's stock
- **Dividends** → Cash paid out (in adjusted prices, dividends not in price)

Without adjustment, it looks like a stock crashed on bonus date or spiked on merger date.

## Adjustment Factor

NepSense calculates a cumulative `adjustment_factor` per symbol:

```
adjusted_price = raw_price / adjustment_factor
```

### Starting State
```
adjustment_factor = 1.0  (no adjustment)
```

### After 10% Bonus
```
new_factor = 1.0 + 10/100 = 1.1
adjusted_price = raw_price / 1.1
```

Example:
```
Raw price before bonus:     1000
Raw price after bonus:      909 (lower because more shares)
Adjusted price (both):      909.09 (uniform)
```

## Bonus Shares Adjustment

### Theory
When a company issues a 10% bonus:
- Each shareholder gets 10 extra shares for every 100 owned
- Total shares increase by 10%
- Price per share drops roughly 10%

**Formula:**
```
factor = 1 + bonus_percent / 100
adjusted_price = raw_price / factor
```

### Example: NABIL 10% Bonus on 2024-12-10

```
Dates       Raw_Price  Factor   Adjusted_Price  Effect
2024-12-09  1460.00    1.0      1460.00         Before bonus
2024-12-10  1318.18    1.1      1198.34 ← Looks like crash
            (adjusted) (1.1)    (1198.34)       But adjusted uniform
2024-12-11  1320.00    1.1      1200.00         After bonus
```

**Without adjustment:** Looks like 10% drop on bonus date  
**With adjustment:** Uniform price movement

## Right Share Adjustment

### Theory
Right shares dilute existing shareholders unless the price rises proportionally.

**Formula:**
```
TERP = ((old_price × old_shares) + (right_price × right_shares)) / total_shares_after
```

Example: TERP = 2:1 right at 400 NPR

```
Old: 100 shares @ 1000 NPR = 100,000 NPR value
Right: 50 shares @ 400 NPR = 20,000 NPR added value
Total value: 120,000 NPR
New shares: 150
TERP: 120,000 / 150 = 800 NPR
```

Adjustment applied to dates before right record date:
```
adjustment_factor = old_price / TERP
                  = 1000 / 800 = 1.25
adjusted_price = raw_price / 1.25
```

## Stock Split Adjustment

### Theory
Stock split changes par value but not company value.

2:1 split = Par value halves, price halves, shares double

**Formula:**
```
factor = new_par_value / old_par_value
(or for 2:1 split: factor = 0.5)
```

Applied backwards in time:
```
adjustment_factor = factor
adjusted_price = raw_price / factor
```

Example: 2:1 split
```
Before: 100 shares @ 1000 NPR = 100,000 total value
After:  200 shares @ 500 NPR = 100,000 total value

Adjusted: 500 / 0.5 = 1000 (uniform)
```

## Merger Swap Adjustment

### Theory
When NCCB merged into KBL at 100:85 ratio:
- 100 NCCB shares → 85 KBL shares
- Price should adjust to reflect new exchange rate

**Formula:**
```
adjustment_factor = swap_ratio
adjusted_price = raw_price × (new_par / old_par) / swap_ratio
```

Example: NCCB → KBL at 100:85

```
NCCB old price:     1000 NPR
KBL equivalent:     1000 × (85/100) = 850 NPR

Applied to NCCB dates before merger:
adjustment_factor = 100/85 = 1.176
adjusted_price = 1000 / 1.176 = 850 NPR

Result: NCCB prices converted to KBL equivalent
```

## Cumulative Adjustments

If a stock has multiple actions, they compound:

```
Example: 10% bonus on date1, 2:1 split on date2

Date      Raw   Factor_1  Factor_2  Final_Factor  Adjusted
before1   1000  1.0       1.0       1.0           1000
after1    909   1.1       1.0       1.1           909 (adj: 826)
after2    454   1.1       2.0       2.2           454 (adj: 206)

Applied backwards (oldest to newest):
Price on date1 (before both): 1000 / 2.2 = 454.55
Price on date2 (before split): 909 / 2.0 = 454.55
Price on date3 (after all):   454 / 2.0 = 227 (uniform)
```

## Cash Dividend

Cash dividends are **not** adjusted in price (different treatment).

They represent cash paid to shareholders, not restructuring:
```
Value before dividend: 1000 shares @ 1000 = 1,000,000
Cash dividend: 15% = 150,000
Value after dividend: 1000 shares @ 1000 - 15 per share = 985 per share
(but this is recorded separately, not in adjusted prices)
```

For backtesting, you may want:
- **Unadjusted prices** - For trading simulation
- **Adjusted prices** - For long-term analysis, comparison

## Implementation in NepSense

### Code Structure

```python
def calculate_adjustment_factor(df, actions):
    """Calculate cumulative adjustment per symbol."""
    df["adjustment_factor"] = 1.0
    
    for action in actions_sorted_by_date:
        if action_type == "BONUS":
            factor = 1 + bonus_percent / 100
            df.loc[before_date & symbol] *= factor
            
        elif action_type == "SPLIT":
            factor = split_ratio
            df.loc[before_date & symbol] *= factor
            
        # etc...
```

### Application

```python
def apply_adjustments(df, actions):
    """Apply adjustment factors to OHLCV."""
    df = calculate_adjustment_factor(df, actions)
    
    for col in ["open", "high", "low", "close"]:
        df[f"adjusted_{col}"] = df[col] / df["adjustment_factor"]
```

## Quality Checks

Validation rules:
- ✅ All actions must have book_close_date
- ✅ Bonus_percent must be 0-2000
- ✅ Right_ratio must be > 0
- ✅ Merger must have both old and new symbol
- ✅ All verified actions must have source_url

## Known Limitations

- ⚠️  **Right adjustment** uses TERP model (theoretical, not actual)
- ⚠️  **Incomplete data** - Many historical actions not documented
- ⚠️  **Dividend impact** - Not in adjusted prices, tracked separately
- ⚠️  **Face value** - Changes tracked but not automatically adjusted
- ⚠️  **Mergers** - Require manual symbol mapping

## Example Dataset

See `data/corporate_actions/corporate_actions.csv` for examples.

## Further Reading

- [Corporate Actions](https://en.wikipedia.org/wiki/Corporate_action)
- [Adjusted Close](https://en.wikipedia.org/wiki/Adjusted_closing_price)
- [NEPSE Historical Data](https://www.nepse.com.np/)

---

**Last Updated:** May 2, 2026  
**Status:** Experimental - Use with caution
