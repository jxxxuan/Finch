import os
from database import *
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

table_name = "news" if PRODUCTION else "news_test"

def insert_news(conn, df):
    """
    批量插入 DataFrame，每行一条新闻
    """
    if df.empty:
        return

    cols = [f'"{col}"' for col in df.columns]
    columns_str = "(" + ", ".join(cols) + ")"
    placeholders = "(" + ", ".join(["%s"] * len(cols)) + ")"

    sql = f"""
        INSERT INTO {table_name} {columns_str}
        VALUES {placeholders}
        ON CONFLICT (id) DO NOTHING;
    """

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            # 转成普通 Python 类型，避免 numpy 类型报错
            values = [None if pd.isna(v) else v for v in row.tolist()]
            cur.execute(sql, values)

    conn.commit()
