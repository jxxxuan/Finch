

import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd
import numpy as np
import os
from datetime import datetime
import logging
from constants import FILE_DIRS
import traceback
from database.symbol_metadata import update_symbol_by_symbol, get_by_condition
from utils import wait_until_online
import time
from .check_main import manually_run_check
import random

def update_database(conn, name, status):
    data_dict = {"minute_history_last_check": pd.Timestamp.now(),
                 "minute_history_check_status": status}
    update_symbol_by_symbol(conn, name, data_dict)

def check_history(name, interval="1D"):
    file_dir = os.path.join(FILE_DIRS['minute_history'], name[0].upper())
    file_path = os.path.join(file_dir, name + '.parquet')
    
    # check file readable
    try:
        data = pd.read_parquet(file_path, engine='fastparquet')
    except Exception as e:
        print(f"⚠️ {name}: parquet file damaged")
        logging.warning(f"{name}: parquet file damaged -> {e}")
        return "DAMAGED"
        
    # check index dtype
    try:
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
    except Exception as e:
        print(f"⚠️ {name}: wrong index format")
        logging.warning(f"{name}: wrong index format -> {e}")
        return "WRONG FORMAT"
        
    # check time continuity
    # 按照 interval 生成完整日期范围
    full_range = pd.date_range(start=data.index.min(),
                                end=data.index.max(),
                                freq=interval)  # interval = "1D" for daily
    
    # 找缺失的日期
    missing = full_range.difference(data.index)
    if len(missing) > 0:
        print(f"⚠️ {name}: missing {len(missing)} timestamps, e.g. {missing[:5]}.")
        logging.warning(f"{name}: missing data -> missing {len(missing)} timestamps, e.g. {missing[:5]}.")
        return "MISSING"
    
    #check duplicated timestamps
    if data.index.duplicated().any():
        print(f"⚠️ {name}: duplicated timestamps found.")
        logging.warning(f"{name}: duplicated timestamps")
        return "DUPLICATE"

    #check requiored columns
    required_cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for col in required_cols:
        if col not in data.columns:
            print(f"⚠️ {name}: missing column {col}")
            logging.warning(f"{name}: missing column {col}")
            return "MISSING COL"
    
    #check negative
    if (data["Adj Close"] < 0).any():
        print(f"⚠️ {name}: negative price detected")
        logging.warning(f"{name}: negative price detected")
        return "INVALID PRICE"

    if (data["Volume"] < 0).any():
        print(f"⚠️ {name}: negative volume detected")
        logging.warning(f"{name}: negative volume detected")
        return "INVALID VOLUME"
    
    return "GOOD"

def update_history(name, db_pool, interval, **kwargs):
    try:
        conn = db_pool.getconn()
        
        status = check_history(name, interval)

        update_database(conn,name,status)
    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_check(update_history, "minute_history", "minute_history", interval="1m")