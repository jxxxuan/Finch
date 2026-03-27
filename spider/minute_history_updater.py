import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd
import numpy as np
import os
from datetime import datetime
import logging
from constants import FILE_DIRS, TEMP_FILE_DIRS
import traceback
from database.symbol_metadata import update_symbol_by_symbol, get_by_condition
from utils import wait_until_online, write_parquet
import time
from .update_main import manually_run_spider
import random

def update_database(conn, name, data):
    data_dict = {"minute_history_record":len(data) > 0,
                    "minute_history_last_update":pd.Timestamp.now(),
                    "minute_history_first_day":data.first_valid_index(),
                    "minute_history_last_day":data.last_valid_index(),
                    "minute_history_frequency":len(data)}
    update_symbol_by_symbol(conn, name,data_dict)

def get_history(name, start, conn, interval, max_retries=3):
    new_data = pd.DataFrame()  # 初始化，防止没有赋值报错

    for attempt in range(max_retries):
        try:
            wait_until_online()
            ticker = yf.Ticker(name)

            if start is None:
                new_data = ticker.history(period='8d', interval=interval)
            else:
                days_diff = (datetime.now().date() - start.date()).days
                if days_diff >= 8:
                    new_data = ticker.history(period='8d', interval=interval)
                else:
                    new_data = ticker.history(start=start, interval=interval)
            
            if not new_data.empty:
                #drop incomplete data
                if new_data.index[-1].date() >= datetime.now().date():
                    new_data = new_data.iloc[:-1]
                if new_data['Dividends'].dtypes == 'O':
                    new_data['Dividends'] = new_data['Dividends'].str.replace(r'[^\d\.]', '', regex=True).astype(float)
                break  # 成功就不继续 retry 啦
            
            df = get_by_condition(conn, cols=['delisted'], where='symbol = %s', params=(name,))
            # 如果是空的，看是不是退市了（不要 retry）
            if not df.empty and df.iloc[0]['delisted']:
                break  # 不要 retry 了，确实没数据
            time.sleep(random.random())
        except IndexError as e:
            logging.error(f"{name} IndexError: {e}")
            new_data = pd.DataFrame()
        except YFRateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"🌐 {name} RateLimit attempt {attempt+1}, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        except Exception as e:
            logging.error(f"{name} unknown exception: {traceback.format_exc()}")
            print(f"{name} unknown exception occured: {e}\n",end="")
            new_data = pd.DataFrame()

    return new_data

def update_history(name, db_pool, interval, **kwargs):
    try:
        conn = db_pool.getconn()

        file_dir = os.path.join(FILE_DIRS['minute_history'], name[0].upper())
        file_path = os.path.join(file_dir, name + '.parquet')
        
        if os.path.exists(file_path):
            try:
                existing_data = pd.read_parquet(file_path, engine='fastparquet')
                start = existing_data[existing_data['Close'].isna()].index.max()
                if pd.isna(start):
                    start = None
                new_data = get_history(name, start,conn, interval)
                if not new_data.empty:
                    data = pd.concat([existing_data, new_data])
                    data = data[~data.index.duplicated(keep='last')]
                else:
                    data = existing_data
                
            except Exception as e:
                print(f"⚠️ {name}: parquet file damaged, redownloading...")
                logging.warning(f"{name}: parquet damaged -> {e}")
                data = get_history(name, None, interval)
                new_data = data.copy()
        else:
            data = get_history(name, None,conn, interval)

        if not data.empty:
            # write_parquet()
            os.makedirs(file_dir, exist_ok=True)
            data.to_parquet(file_path, compression='zstd', engine='fastparquet')

        update_database(conn,name,data)
    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_spider(update_history, "minute_history", "minute_history", interval="1m")