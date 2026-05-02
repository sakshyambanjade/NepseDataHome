# Backtesting Guide

How to use NepSense data for backtesting trading strategies on NEPSE.

## Quick Start

Load adjusted historical prices and run a simple strategy:

```python
import pandas as pd
import duckdb

# Load data
con = duckdb.connect("data/master/daily_prices.duckdb")
df = con.execute("""
    SELECT * FROM daily_prices
    WHERE symbol = 'NABIL'
    ORDER BY date
""").fetchdf()

# Calculate moving averages
df["sma_50"] = df["close"].rolling(50).mean()
df["sma_200"] = df["close"].rolling(200).mean()

# Generate signals
df["signal"] = (df["sma_50"] > df["sma_200"]).astype(int)
df["position"] = df["signal"].diff()  # 1=BUY, -1=SELL

# Calculate returns
df["daily_return"] = df["close"].pct_change()
df["strategy_return"] = df["position"].shift(1) * df["daily_return"]

# Performance
cumulative_return = (1 + df["strategy_return"]).cumprod()
print(f"Final return: {(cumulative_return.iloc[-1] - 1) * 100:.2f}%")
```

## Data Access

### Method 1: DuckDB (Recommended for large datasets)

```python
import duckdb

con = duckdb.connect("data/master/daily_prices.duckdb")

# All data
df = con.execute("SELECT * FROM daily_prices ORDER BY date").fetchdf()

# Filter by symbol
df = con.execute("""
    SELECT * FROM daily_prices
    WHERE symbol = 'NABIL'
    ORDER BY date
""").fetchdf()

# Filter by date range
df = con.execute("""
    SELECT * FROM daily_prices
    WHERE symbol = 'NABIL'
    AND date BETWEEN '2020-01-01' AND '2023-12-31'
    ORDER BY date
""").fetchdf()

# Aggregate by month
monthly = con.execute("""
    SELECT 
        date_trunc('month', date) AS month,
        symbol,
        first(close) AS open,
        max(high) AS high,
        min(low) AS low,
        last(close) AS close,
        sum(volume) AS volume
    FROM daily_prices
    WHERE symbol IN ('NABIL', 'HBL')
    GROUP BY month, symbol
    ORDER BY month, symbol
""").fetchdf()
```

### Method 2: Parquet (Good for pandas)

```python
import pandas as pd

df = pd.read_parquet("data/master/daily_prices.parquet")

# Filter
nabil = df[df["symbol"] == "NABIL"].sort_values("date").reset_index(drop=True)

# Check date coverage
print(f"Date range: {nabil['date'].min()} to {nabil['date'].max()}")
print(f"Trading days: {len(nabil)}")
```

### Method 3: CSV (Portable, larger file)

```python
import pandas as pd

df = pd.read_csv("data/master/daily_prices.csv", parse_dates=["date"])
```

## Data Schema

All formats include these columns:

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| date | DATE | 2024-01-15 | Trading date |
| symbol | STRING | NABIL | Company ticker |
| open | FLOAT | 1456.50 | Opening price (NPR) |
| high | FLOAT | 1480.00 | Daily high |
| low | FLOAT | 1450.00 | Daily low |
| close | FLOAT | 1475.00 | Closing price (adjusted) |
| volume | INT | 125000 | Shares traded |
| turnover | FLOAT | 185000000 | Value traded (NPR) |
| transactions | INT | 2500 | Number of transactions |
| source | STRING | sharesansar | Data source |
| adjustment_factor | FLOAT | 1.1 | Applied to get adjusted price |

## Adjusted vs. Unadjusted

NepSense provides **adjusted prices** (corrected for bonuses, splits, mergers):

```python
import pandas as pd

df = pd.read_parquet("data/master/daily_prices.parquet")

# Adjusted price (recommended for backtesting)
adjusted = df["close"]

# Unadjusted price (for historical comparison)
unadjusted = df["close"] * df["adjustment_factor"]

# See what happened
nabil = df[df["symbol"] == "NABIL"]
print(nabil[["date", "close", "adjustment_factor"]].tail(10))
```

If `adjustment_factor > 1.0`, a bonus occurred recently. Without adjustment, returns would be distorted.

## Common Backtests

### 1. Buy & Hold

```python
def backtest_buy_hold(symbol, start_date, end_date):
    con = duckdb.connect("data/master/daily_prices.duckdb")
    df = con.execute(f"""
        SELECT * FROM daily_prices
        WHERE symbol = '{symbol}'
        AND date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY date
    """).fetchdf()
    
    buy_price = df.iloc[0]["close"]
    sell_price = df.iloc[-1]["close"]
    return_pct = ((sell_price - buy_price) / buy_price) * 100
    
    return {
        "symbol": symbol,
        "buy_date": df.iloc[0]["date"],
        "buy_price": buy_price,
        "sell_date": df.iloc[-1]["date"],
        "sell_price": sell_price,
        "return_pct": return_pct,
        "days": len(df)
    }

result = backtest_buy_hold("NABIL", "2020-01-01", "2023-12-31")
print(f"NABIL: {result['return_pct']:.2f}% over {result['days']} days")
```

### 2. Moving Average Crossover

```python
def backtest_sma_cross(symbol, fast=50, slow=200):
    con = duckdb.connect("data/master/daily_prices.duckdb")
    df = con.execute(f"""
        SELECT * FROM daily_prices
        WHERE symbol = '{symbol}'
        ORDER BY date
    """).fetchdf()
    
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()
    
    # Generate signals
    df["signal"] = (df["sma_fast"] > df["sma_slow"]).astype(int)
    df["position"] = df["signal"].diff()  # 1=BUY, -1=SELL, 0=HOLD
    
    # Returns
    df["returns"] = df["close"].pct_change()
    df["strategy_returns"] = df["position"].shift(1) * df["returns"]
    
    cumulative = (1 + df["strategy_returns"]).cumprod()
    
    return {
        "symbol": symbol,
        "total_return": (cumulative.iloc[-1] - 1) * 100,
        "trades": (df["position"] != 0).sum(),
        "sharpe": df["strategy_returns"].mean() / df["strategy_returns"].std() * (252 ** 0.5)
    }

result = backtest_sma_cross("NABIL")
print(result)
```

### 3. Multi-Symbol Portfolio

```python
def backtest_portfolio(symbols, weights, start_date, end_date):
    con = duckdb.connect("data/master/daily_prices.duckdb")
    
    portfolio = {}
    for symbol, weight in zip(symbols, weights):
        df = con.execute(f"""
            SELECT date, close
            FROM daily_prices
            WHERE symbol = '{symbol}'
            AND date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY date
        """).fetchdf()
        portfolio[symbol] = df.set_index("date")["close"]
    
    df_portfolio = pd.DataFrame(portfolio)
    
    # Normalized prices (for equal weighting)
    normalized = df_portfolio / df_portfolio.iloc[0]
    
    # Portfolio return
    weighted_prices = (normalized * weights).sum(axis=1)
    portfolio_return = ((weighted_prices.iloc[-1] - 1) * 100)
    
    return {
        "symbols": symbols,
        "weights": weights,
        "return_pct": portfolio_return,
        "start_date": start_date,
        "end_date": end_date
    }

result = backtest_portfolio(
    ["NABIL", "HBL", "EBL"],
    [0.5, 0.3, 0.2],
    "2022-01-01",
    "2023-12-31"
)
print(f"Portfolio return: {result['return_pct']:.2f}%")
```

### 4. Momentum Strategy

```python
def backtest_momentum(symbol, lookback=20, threshold=0.02):
    """Buy if >20-day momentum > 2%"""
    con = duckdb.connect("data/master/daily_prices.duckdb")
    df = con.execute(f"""
        SELECT * FROM daily_prices
        WHERE symbol = '{symbol}'
        ORDER BY date
    """).fetchdf()
    
    df["momentum"] = (df["close"] / df["close"].shift(lookback)) - 1
    df["signal"] = (df["momentum"] > threshold).astype(int)
    df["position"] = df["signal"].diff()
    
    df["returns"] = df["close"].pct_change()
    df["strategy_returns"] = df["position"].shift(1) * df["returns"]
    
    cumulative = (1 + df["strategy_returns"]).cumprod()
    
    trades = len(df[df["position"] != 0])
    win_rate = len(df[(df["strategy_returns"] > 0) & (df["signal"] == 1)]) / trades if trades > 0 else 0
    
    return {
        "symbol": symbol,
        "total_return": (cumulative.iloc[-1] - 1) * 100,
        "trades": trades,
        "win_rate": win_rate * 100
    }

result = backtest_momentum("NABIL")
print(result)
```

## Performance Metrics

### Returns

```python
# Daily return
daily_return = df["close"].pct_change()

# Cumulative return
cumulative_return = (1 + daily_return).cumprod()
total_return = (cumulative_return.iloc[-1] - 1) * 100

# Average daily return
avg_daily = daily_return.mean() * 100

# Annual return (approximate)
annual_return = daily_return.mean() * 252 * 100
```

### Risk

```python
# Daily volatility
daily_vol = daily_return.std() * 100

# Annual volatility
annual_vol = daily_return.std() * (252 ** 0.5) * 100

# Maximum drawdown
cumulative = (1 + daily_return).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max
max_drawdown = drawdown.min() * 100
```

### Sharpe Ratio

```python
# Assuming 3% annual risk-free rate
risk_free_rate = 0.03
annual_return = daily_return.mean() * 252
annual_vol = daily_return.std() * (252 ** 0.5)

sharpe = (annual_return - risk_free_rate) / annual_vol
```

## Pitfalls to Avoid

### 1. Survivorship Bias
NepSense data includes delisted companies (with `last_seen` date).

```python
# Check if stock was listed on backtest date
if df.iloc[0]["date"] > backtest_start:
    print("⚠️  Stock was not listed at start of period")
```

### 2. Look-Ahead Bias
Don't use future data to make today's decisions.

```python
# WRONG
for i in range(100, len(df)):
    signal = df.iloc[i+1]["close"] > df.iloc[i]["close"]  # ← Uses future!

# CORRECT
for i in range(100, len(df)):
    signal = df.iloc[i]["close"] > df.iloc[i-1]["close"]  # Uses past
```

### 3. Incomplete Adjustment
Some corporate actions may be missing.

```python
# Check adjustment_factor to see if something changed
adj = df[df["symbol"] == "NABIL"]["adjustment_factor"]
print(f"Max adjustment: {adj.max()}")  # > 1 means bonuses/splits
```

### 4. Gap Data
NEPSE is closed some days.

```python
# Don't assume consecutive trading days
df["date_gap"] = df["date"].diff()
large_gaps = df[df["date_gap"] > pd.Timedelta(days=7)]
print(f"Gaps > 1 week: {len(large_gaps)}")
```

## Running Backtests at Scale

Use DuckDB for efficient filtering:

```python
import duckdb

con = duckdb.connect("data/master/daily_prices.duckdb")

# Test 250+ symbols at once
symbols = con.execute(
    "SELECT DISTINCT symbol FROM daily_prices ORDER BY symbol"
).fetchall()

results = []
for (symbol,) in symbols:
    try:
        result = backtest_sma_cross(symbol)
        results.append(result)
    except Exception as e:
        print(f"Error with {symbol}: {e}")

# Find best performers
df_results = pd.DataFrame(results)
top_10 = df_results.nlargest(10, "total_return")
print(top_10)
```

## Advanced: Walk-Forward Analysis

Test parameters on expanding windows:

```python
def walkforward_test(symbol, test_window=252, train_window=504):
    """Rolling window backtest."""
    con = duckdb.connect("data/master/daily_prices.duckdb")
    df = con.execute(f"""
        SELECT * FROM daily_prices
        WHERE symbol = '{symbol}'
        ORDER BY date
    """).fetchdf()
    
    results = []
    for i in range(train_window, len(df) - test_window, test_window):
        train = df.iloc[i-train_window:i]
        test = df.iloc[i:i+test_window]
        
        # Train on train period
        params = optimize_params(train)
        
        # Test on test period
        perf = evaluate_params(test, params)
        results.append(perf)
    
    return pd.DataFrame(results)
```

## See Also

- [ADJUSTMENT_METHOD.md](ADJUSTMENT_METHOD.md) - How prices are adjusted
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) - Column definitions
- [SOURCES.md](SOURCES.md) - Data source documentation

---

**Last Updated:** May 2, 2026  
**Status:** Beta - Feedback welcome
