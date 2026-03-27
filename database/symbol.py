import re
import psycopg2
import os
import pandas as pd
from typing import Union, Optional
from database import *
from dotenv import load_dotenv

load_dotenv()

PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

table_name = "symbol" if PRODUCTION else "symbol_test"

def update_symbol_by_symbol(conn, symbol, data_dict):
    condition = "symbol = %s"
    update_symbol_by_condition(conn, condition, data_dict, (symbol,))

def update_symbol_by_condition(conn, condition, data_dict, condition_values=()):
    columns = list(data_dict.keys())
    values = list(data_dict.values())

    set_clause = ", ".join([f"{col} = %s" for col in columns])
    sql = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {condition}
    """

    with conn.cursor() as cur:
        cur.execute(sql, values + list(condition_values))
    conn.commit()

def get_by_condition(conn, 
                       cols: Union[str, list[str]] = '*', 
                       where: str = '', 
                       limit: int = 100,
                       params: Optional[Union[tuple, list]] = None):

    # 构造 SELECT 的列部分
    if isinstance(cols, str) and cols == "*":
        str_cols = "*"
    elif isinstance(cols, list):
        if 'symbol' not in cols:
            cols = cols + ['symbol']
        str_cols = ", ".join(cols)
    else:
        raise ValueError("cols should be '*' or list[str]")

    base_sql = f"SELECT {str_cols} FROM {table_name}"
    
    where_sql = f"WHERE {where}" if where else ""
    final_sql = f"{base_sql} {where_sql} LIMIT {limit};"

    with create_pandas_conn() as c:
        df = pd.read_sql(final_sql, c, params=params)
    df.set_index('symbol',inplace=True)
    return df

def get_by_rule(conn, 
                selected_rule: str = '',
                cols: Union[str, list[str]] = '*', 
                limit: int = 999999,
                ):
    
    rules2sql = {'malaysia':"country = 'Malaysia'",
                 '*':"TRUE"
                 }

    pattern = re.compile(r"(" + "|".join(map(re.escape, rules2sql.keys())) + r")")
    translated_sql = pattern.sub(lambda m: rules2sql[m.group(0)], selected_rule)

    return get_by_condition(conn, cols, translated_sql, limit)

def get_by_symbol(conn, 
                  symbol,
                  cols: Union[str, list[str]],
                  limit: int = 999999):
    where = 'symbol = %s'
    result = get_by_condition(conn, cols, where, limit, params=[symbol])

    return result.iloc[0] if not result.empty else None

if __name__ == '__main__':
    conn = create_conn()
    get_by_rule(conn,"history","delisted AND ready for update")