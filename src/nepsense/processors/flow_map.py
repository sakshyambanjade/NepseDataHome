import duckdb
import json
import os
from pathlib import Path

DB_PATH = "data/db/nepsense.duckdb"
OUT_DIR = "web/public/data/flow"

def generate_flow_artifacts(date):
    os.makedirs(f"{OUT_DIR}/symbols", exist_ok=True)
    os.makedirs(f"{OUT_DIR}/brokers", exist_ok=True)
    
    conn = duckdb.connect(DB_PATH)
    
    generate_flow_overview(conn, date)
    generate_broker_pairs(conn, date)
    generate_rotation_map(conn, date)
    generate_transaction_replay(conn, date)
    generate_all_symbols_flow(conn, date)
    generate_all_brokers_flow(conn, date)
    
    conn.close()

def generate_flow_overview(conn, date):
    # Total trades & amount
    totals = conn.execute(f"SELECT count(*), sum(amount) FROM floorsheet_trades WHERE date = '{date}'").fetchone()
    
    top_symbols = conn.execute(f"SELECT symbol, sum(quantity), sum(amount) FROM floorsheet_trades WHERE date = '{date}' GROUP BY symbol ORDER BY sum(amount) DESC LIMIT 5").fetchall()
    top_pairs = conn.execute(f"SELECT buyer_broker, seller_broker, sum(amount) FROM broker_pair_daily WHERE date = '{date}' GROUP BY buyer_broker, seller_broker ORDER BY sum(amount) DESC LIMIT 5").fetchall()
    
    # Highest rotation
    rot = conn.execute(f"""
        WITH bs AS (SELECT broker, sum(abs(net_amount)) as amt FROM broker_symbol_daily WHERE date='{date}' GROUP BY broker)
        SELECT broker, amt FROM bs ORDER BY amt DESC LIMIT 5
    """).fetchall()

    cross_trades = conn.execute(f"SELECT symbol, sum(amount) as amt FROM floorsheet_trades WHERE date = '{date}' AND buyer_broker = seller_broker GROUP BY symbol ORDER BY amt DESC LIMIT 5").fetchall()

    overview = {
        "date": date,
        "total_trades": int(totals[0]) if totals[0] else 0,
        "total_amount": float(totals[1]) if totals[1] else 0.0,
        "top_flow_symbols": [{"symbol": s[0], "amount": float(s[2])} for s in top_symbols],
        "top_broker_pairs": [{"buyer": p[0], "seller": p[1], "amount": float(p[2])} for p in top_pairs],
        "top_rotating_brokers": [{"broker": r[0], "score": float(r[1])} for r in rot],
        "cross_trade_watch": [{"symbol": c[0], "amount": float(c[1])} for c in cross_trades],
        "largest_transfers": []
    }
    
    with open(f"{OUT_DIR}/flow_overview.json", "w") as f:
        json.dump(overview, f, indent=2)

def generate_broker_pairs(conn, date):
    pairs = conn.execute(f"""
        SELECT buyer_broker, seller_broker, sum(quantity) as qty, sum(amount) as amt, count(*) as trades
        FROM broker_pair_daily
        WHERE date = '{date}'
        GROUP BY buyer_broker, seller_broker
        ORDER BY amt DESC
        LIMIT 100
    """).fetchall()
    
    res = [{"buyer": p[0], "seller": p[1], "quantity": p[2], "amount": p[3], "trade_count": p[4]} for p in pairs]
    with open(f"{OUT_DIR}/broker_pairs.json", "w") as f:
        json.dump(res, f, indent=2)

def generate_rotation_map(conn, date):
    rotations = conn.execute(f"""
        WITH broker_stats AS (
            SELECT 
                broker,
                sum(CASE WHEN net_amount > 0 THEN 1 ELSE 0 END) as net_buy_symbols,
                sum(CASE WHEN net_amount < 0 THEN 1 ELSE 0 END) as net_sell_symbols,
                sum(abs(net_amount)) as total_abs_net_amount
            FROM broker_symbol_daily
            WHERE date = '{date}'
            GROUP BY broker
        )
        SELECT 
            broker, net_buy_symbols, net_sell_symbols, total_abs_net_amount,
            (net_buy_symbols * 0.3 + net_sell_symbols * 0.3 + log(total_abs_net_amount + 1) * 0.4) as rotation_score
        FROM broker_stats
        ORDER BY rotation_score DESC
    """).fetchall()
    
    res = [{"broker": r[0], "net_buy_symbols": r[1], "net_sell_symbols": r[2], "rotation_score": float(r[4])} for r in rotations]
    with open(f"{OUT_DIR}/rotation_map.json", "w") as f:
        json.dump(res, f, indent=2)

def generate_transaction_replay(conn, date, limit=5000):
    txns = conn.execute(f"""
        SELECT seller_broker, buyer_broker, symbol, quantity, rate, amount, transaction_no
        FROM floorsheet_trades
        WHERE date = '{date}'
        ORDER BY txn_order ASC
        LIMIT {limit}
    """).fetchall()
    
    res = [{"from": t[0], "to": t[1], "symbol": t[2], "quantity": t[3], "rate": t[4], "amount": t[5], "transaction_no": t[6]} for t in txns]
    with open(f"{OUT_DIR}/transactions_{date}.json", "w") as f:
        json.dump(res, f, indent=2)

def generate_all_symbols_flow(conn, date):
    symbols = conn.execute(f"SELECT DISTINCT symbol FROM floorsheet_trades WHERE date = '{date}'").fetchall()
    
    for (sym,) in symbols:
        # summary
        summary = conn.execute(f"SELECT total_qty, total_amount, total_amount/NULLIF(total_qty,0) FROM symbol_flow_daily WHERE date='{date}' AND symbol='{sym}'").fetchone()
        
        # pairs
        edges = conn.execute(f"SELECT seller_broker, buyer_broker, quantity, amount, trade_count FROM broker_pair_daily WHERE date='{date}' AND symbol='{sym}' ORDER BY amount DESC LIMIT 20").fetchall()
        edges_list = [{"source": e[0], "target": e[1], "quantity": e[2], "amount": e[3], "trade_count": e[4]} for e in edges]
        
        # nodes
        nodes = set()
        for e in edges_list:
            nodes.add(e["source"])
            nodes.add(e["target"])
        nodes_list = [{"id": n} for n in nodes]
        
        # timeline
        timeline = conn.execute(f"SELECT transaction_no, seller_broker, buyer_broker, quantity, rate, amount FROM floorsheet_trades WHERE date='{date}' AND symbol='{sym}' ORDER BY txn_order ASC LIMIT 50").fetchall()
        timeline_list = [{"transaction_no": t[0], "from": t[1], "to": t[2], "quantity": t[3], "rate": t[4], "amount": t[5]} for t in timeline]
        
        out = {
            "symbol": sym,
            "date": date,
            "summary": {
                "total_quantity": summary[0] if summary else 0,
                "total_amount": summary[1] if summary else 0,
                "vwap": summary[2] if summary else 0
            },
            "nodes": nodes_list,
            "edges": edges_list,
            "timeline": timeline_list
        }
        
        safe_sym = sym.replace("/", "-")
        with open(f"{OUT_DIR}/symbols/{safe_sym}_flow.json", "w") as f:
            json.dump(out, f, indent=2)

def generate_all_brokers_flow(conn, date):
    brokers = conn.execute(f"SELECT DISTINCT buyer_broker FROM floorsheet_trades WHERE date = '{date}' UNION SELECT DISTINCT seller_broker FROM floorsheet_trades WHERE date = '{date}'").fetchall()
    
    for (brk,) in brokers:
        buys = conn.execute(f"SELECT symbol, buy_qty, buy_amount, sell_qty, sell_amount, net_qty, net_amount FROM broker_symbol_daily WHERE date='{date}' AND broker='{brk}'").fetchall()
        
        out = {
            "broker": brk,
            "date": date,
            "symbols": [{"symbol": b[0], "buy_qty": b[1], "buy_amount": b[2], "sell_qty": b[3], "sell_amount": b[4], "net_qty": b[5], "net_amount": b[6]} for b in buys]
        }
        
        with open(f"{OUT_DIR}/brokers/{brk}_flow.json", "w") as f:
            json.dump(out, f, indent=2)

if __name__ == "__main__":
    generate_flow_artifacts("2026-05-12")
