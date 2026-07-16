import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import create_conn

tickers = ["SPY", "TLT", "SHY", "GLD"]

conn = create_conn()
cur = conn.cursor()

try:
    for ticker in tickers:
        print(f"Registering {ticker} in database...")
        
        # 1. Handle symbol table
        cur.execute("SELECT symbol FROM symbol WHERE symbol = %s", (ticker,))
        exists = cur.fetchone()
        if exists:
            cur.execute(
                """
                UPDATE symbol 
                SET delisted = FALSE, exchange = 'NYSE Arca', country = 'United States', asset_type = 'etf'
                WHERE symbol = %s
                """,
                (ticker,)
            )
        else:
            cur.execute(
                """
                INSERT INTO symbol (symbol, delisted, exchange, country, asset_type)
                VALUES (%s, FALSE, 'NYSE Arca', 'United States', 'etf')
                """,
                (ticker,)
            )
            
        # 2. Handle symbol_metadata table
        cur.execute("SELECT symbol FROM symbol_metadata WHERE symbol = %s", (ticker,))
        exists_meta = cur.fetchone()
        if exists_meta:
            cur.execute(
                """
                UPDATE symbol_metadata 
                SET delisted = FALSE, history_next_update = %s, history_record = TRUE
                WHERE symbol = %s
                """,
                (datetime(2000, 1, 1), ticker)
            )
        else:
            cur.execute(
                """
                INSERT INTO symbol_metadata (symbol, delisted, history_next_update, history_record)
                VALUES (%s, FALSE, %s, TRUE)
                """,
                (ticker, datetime(2000, 1, 1))
            )
            
    conn.commit()
    print("\n[SUCCESS] SPY, TLT, SHY, and GLD registered successfully in PostgreSQL.")
    print("Now you can run Finch's crawler (e.g. main.py) to fetch their daily historical data.")
except Exception as e:
    conn.rollback()
    print(f"\n[ERROR] Failed to register symbols: {e}")
finally:
    conn.close()
