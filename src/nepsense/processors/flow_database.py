import duckdb
import os
import glob
from pathlib import Path

DB_PATH = "data/db/nepsense.duckdb"

def build_flow_database(date=None):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    
    load_normalized_floorsheets(conn, date)
    create_floorsheet_trades_table(conn)
    create_broker_symbol_daily_table(conn)
    create_broker_pair_daily_table(conn)
    create_symbol_flow_daily_table(conn)
    
    conn.close()

def load_normalized_floorsheets(conn, date=None):
    # Load CSVs directly into a staging view or table
    if date:
        csv_pattern = f"data/floorsheet/normalized/{date}.csv"
    else:
        csv_pattern = "data/floorsheet/normalized/*.csv"
    
    if not glob.glob(csv_pattern):
        print(f"Warning: No normalized data found for pattern {csv_pattern}")
        return

    # Create temporary table/view for source data
    conn.execute(f"""
        CREATE OR REPLACE VIEW raw_floorsheet AS 
        SELECT 
            date::DATE as date,
            transaction_no,
            symbol,
            buyer_broker::VARCHAR as buyer_broker,
            seller_broker::VARCHAR as seller_broker,
            quantity::DOUBLE as quantity,
            rate::DOUBLE as rate,
            amount::DOUBLE as amount
        FROM read_csv_auto('{csv_pattern}')
    """)

def create_floorsheet_trades_table(conn):
    conn.execute("""
        CREATE OR REPLACE TABLE floorsheet_trades AS
        SELECT 
            date,
            transaction_no,
            row_number() OVER (PARTITION BY date ORDER BY transaction_no) as txn_order,
            symbol,
            buyer_broker,
            seller_broker,
            quantity,
            rate,
            amount
        FROM raw_floorsheet
    """)

def create_broker_symbol_daily_table(conn):
    conn.execute("""
        CREATE OR REPLACE TABLE broker_symbol_daily AS
        WITH buys AS (
            SELECT date, buyer_broker as broker, symbol, 
                   sum(quantity) as buy_qty, sum(amount) as buy_amount
            FROM floorsheet_trades GROUP BY date, buyer_broker, symbol
        ),
        sells AS (
            SELECT date, seller_broker as broker, symbol, 
                   sum(quantity) as sell_qty, sum(amount) as sell_amount
            FROM floorsheet_trades GROUP BY date, seller_broker, symbol
        )
        SELECT 
            COALESCE(b.date, s.date) as date,
            COALESCE(b.broker, s.broker) as broker,
            COALESCE(b.symbol, s.symbol) as symbol,
            COALESCE(b.buy_qty, 0) as buy_qty,
            COALESCE(s.sell_qty, 0) as sell_qty,
            COALESCE(b.buy_qty, 0) - COALESCE(s.sell_qty, 0) as net_qty,
            COALESCE(b.buy_amount, 0) as buy_amount,
            COALESCE(s.sell_amount, 0) as sell_amount,
            COALESCE(b.buy_amount, 0) - COALESCE(s.sell_amount, 0) as net_amount
        FROM buys b
        FULL OUTER JOIN sells s ON b.date = s.date AND b.broker = s.broker AND b.symbol = s.symbol
    """)

def create_broker_pair_daily_table(conn):
    conn.execute("""
        CREATE OR REPLACE TABLE broker_pair_daily AS
        SELECT 
            date,
            symbol,
            buyer_broker,
            seller_broker,
            sum(quantity) as quantity,
            sum(amount) as amount,
            count(*) as trade_count
        FROM floorsheet_trades
        GROUP BY date, symbol, buyer_broker, seller_broker
    """)

def create_symbol_flow_daily_table(conn):
    conn.execute("""
        CREATE OR REPLACE TABLE symbol_flow_daily AS
        WITH daily_totals AS (
            SELECT date, symbol, sum(quantity) as total_qty, sum(amount) as total_amount
            FROM floorsheet_trades GROUP BY date, symbol
        ),
        top_buyers AS (
            SELECT date, symbol, broker, net_qty,
                   row_number() OVER (PARTITION BY date, symbol ORDER BY net_qty DESC) as r_buy
            FROM broker_symbol_daily WHERE net_qty > 0
        ),
        top_sellers AS (
            SELECT date, symbol, broker, net_qty,
                   row_number() OVER (PARTITION BY date, symbol ORDER BY net_qty ASC) as r_sell
            FROM broker_symbol_daily WHERE net_qty < 0
        ),
        cross_trades AS (
            SELECT date, symbol, sum(quantity) as cross_qty
            FROM floorsheet_trades WHERE buyer_broker = seller_broker
            GROUP BY date, symbol
        ),
        pair_metrics AS (
            SELECT date, symbol, max(quantity) as top_pair_qty
            FROM broker_pair_daily
            GROUP BY date, symbol
        )
        SELECT 
            t.date,
            t.symbol,
            t.total_qty,
            t.total_amount,
            tb.broker as top_buyer,
            ts.broker as top_seller,
            COALESCE(pm.top_pair_qty / NULLIF(t.total_qty, 0) * 100, 0) as repeated_pair_score,
            COALESCE(ct.cross_qty / NULLIF(t.total_qty, 0), 0) as cross_trade_ratio,
            0.0 as accumulation_score,
            0.0 as distribution_score,
            0.0 as pattern_score
        FROM daily_totals t
        LEFT JOIN top_buyers tb ON t.date = tb.date AND t.symbol = tb.symbol AND tb.r_buy = 1
        LEFT JOIN top_sellers ts ON t.date = ts.date AND t.symbol = ts.symbol AND ts.r_sell = 1
        LEFT JOIN cross_trades ct ON t.date = ct.date AND t.symbol = ct.symbol
        LEFT JOIN pair_metrics pm ON t.date = pm.date AND t.symbol = pm.symbol
    """)

if __name__ == "__main__":
    build_flow_database("2026-05-12")
