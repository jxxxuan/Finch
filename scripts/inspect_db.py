import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import create_conn

conn = create_conn()
cur = conn.cursor()

for table in ["symbol", "symbol_metadata"]:
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'")
    cols = cur.fetchall()
    print(f"\nTable: {table}")
    for col in cols:
        print(f"  {col[0]}: {col[1]}")
        
conn.close()
