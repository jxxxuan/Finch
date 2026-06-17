import re
import psycopg2
import os
import pandas as pd
from typing import Union, Optional
from database import *
from dotenv import load_dotenv

load_dotenv()

PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

table_name = "symbol_metadata"

def update_symbols_by_symbols(conn, col, df):
    # 优先根据列名后缀推断 SQL 类型，避免 pandas object 类型转换偏差导致的错误
    if col.endswith('_update') or col.endswith('_check'):
        sql_type = 'TIMESTAMP'
    elif col.endswith('_day') or col.endswith('_month'):
        sql_type = 'TIMESTAMPTZ'
    elif col.endswith('_record') or col.endswith('delisted'):
        sql_type = 'BOOLEAN'
    elif col.endswith('_count') or col.endswith('_frequency'):
        sql_type = 'INTEGER'
    elif col.endswith('_status'):
        sql_type = 'VARCHAR(20)'
    else:
        dtype_map = {
            'datetime64[ns]': 'TIMESTAMP',
            'datetime64[ns, UTC]': 'TIMESTAMPTZ',
            'int64': 'INTEGER',
            'float64': 'DOUBLE PRECISION',
            'bool': 'BOOLEAN',
            'object': 'VARCHAR(20)'
        }
        sql_type = dtype_map.get(str(df[col].dtype), 'TEXT')

    temp_table = "temp_update"

    # 准备数据：只用一次 iterrows
    update_data = [
        (symbol, row[f"{col}"])
        for symbol, row in df.iterrows()
    ]

    with conn.cursor() as cursor:
        # 1. 创建临时表
        cursor.execute(f"""
            CREATE TEMP TABLE {temp_table} (
                symbol TEXT PRIMARY KEY,
                {col} {sql_type}
            ) ON COMMIT DROP
        """)

        # 2. 批量插入到临时表
        psycopg2.extras.execute_batch(
            cursor,
            f"""
            INSERT INTO {temp_table} (symbol, {col})
            VALUES (%s, %s)
            """,
            update_data
        )

        # 3. 更新主表
        cursor.execute(f"""
            UPDATE {table_name} AS t
            SET {col} = tmp.{col}
            FROM {temp_table} AS tmp
            WHERE t.symbol = tmp.symbol
        """)

    conn.commit()

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

    if params is not None:
        params = tuple(params)

    with create_pandas_conn() as c:
        df = pd.read_sql(final_sql, c, params=params)
    df.set_index('symbol',inplace=True)
    return df

def get_by_rule(conn, 
                type,
                selected_rule: str = '',
                cols: Union[str, list[str]] = '*', 
                limit: int = 999999,
                ):
    record = type+"_record"
    last_update = type+"_last_update"
    next_update = type+'_next_update'
    last_check = type+"_last_check"
    next_check = type+'_next_check'

    # 构造 SELECT 的列部分
    if isinstance(cols, str) and cols == "*":
        str_cols = "*"
    elif isinstance(cols, list):
        str_cols = ", ".join(cols)
    else:
        raise ValueError("cols should be '*' or list[str]")
    
    rules2sql = {'ready for update':f"{last_update} < {next_update} OR ({next_update} IS NOT NULL AND {last_update} IS NULL)",
                 'ready for check':f"{last_check} < {next_check} OR ({next_check} IS NOT NULL AND {last_check} IS NULL)",
                 'exist':f"{record}",
                 'malaysia':"country = 'Malaysia'",
                 'today':f"{next_update} <= NOW()",
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