import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.symbol_metadata import create_db_pool
from spider.daily_history_updater import update_history

tickers = ["SPY", "TLT", "SHY", "GLD"]

db_pool = create_db_pool(5)

try:
    for ticker in tickers:
        print(f"\n==================================================")
        print(f"Starting crawl for {ticker}...")
        print(f"==================================================")
        update_history(ticker, db_pool, interval="1d")
    print("\n[SUCCESS] Historical daily prices for SPY, TLT, SHY, and GLD have been successfully downloaded!")
except Exception as e:
    print(f"\n[ERROR] Failed to run crawl: {e}")
finally:
    db_pool.closeall()
