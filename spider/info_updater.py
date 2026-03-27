import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd
import os
from constants import FILE_DIRS
import logging
import json
import traceback
from database.symbol_metadata import update_symbol_by_symbol, get_by_condition
from utils import wait_until_online
import time
import random
from .update_main import manually_run_spider

def update_database(conn, name, data):
    data_dict = {"info_record":len(data) > 0,
                    "info_last_update":pd.Timestamp.now(),}
    update_symbol_by_symbol(conn, name, data_dict)

def get_info(name, conn, max_retries=3):
    new_data = dict()

    for attempt in range(max_retries):
        try:
            wait_until_online()
            ticker = yf.Ticker(name)
            new_data = ticker.info

            if len(new_data) > 0:
                break  # 成功就不继续 retry 啦
            
            df = get_by_condition(conn, cols=['delisted'], where='symbol = %s', params=(name,))
            # 如果是空的，看是不是退市了（不要 retry）
            if not df.empty and df.iloc[0]['delisted']:
                break  # 不要 retry 了，确实没数据
            time.sleep(random.random())
        except YFRateLimitError as e:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"🌐 {name} RateLimit attempt {attempt+1}, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        except Exception as e:
            print(f"{name} unknown exception occured: {e}\n",end="")
            logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
            new_data = dict()
    
    return new_data

def update_info(name, db_pool):
    try:
        conn = db_pool.getconn()

        file_dir = os.path.join(FILE_DIRS[type], name[0].upper())
        file_path = os.path.join(file_dir, name + '.json')
        
        data = get_info(name)

        if len(data) > 0:
            os.makedirs(file_dir,exist_ok=True)
            with open(file_path,'w') as f:
                json.dump(data,f)

        update_database(conn, name, data)
    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_spider(update_info, "info", "info")