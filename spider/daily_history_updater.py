import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd
import numpy as np
import os
import logging
from constants import FILE_DIRS
import traceback
from database.symbol_metadata import update_symbol_by_symbol
from utils import wait_until_online
import time
from .update_main import manually_run_spider
import random

def update_database(conn, name, data):
    data_dict = {"history_record":len(data) > 0,
                    "history_last_update":pd.Timestamp.now(),
                    "history_first_day":data.first_valid_index(),
                    "history_last_day":data.last_valid_index()}
    update_symbol_by_symbol(conn, name,data_dict)

def get_history(name, start, interval, max_retries=3):
    new_data = pd.DataFrame()  # 初始化，防止没有赋值报错

    for attempt in range(max_retries):
        try:
            wait_until_online()
            ticker = yf.Ticker(name)
            
            if start == None:
                new_data = ticker.history(period='max', interval=interval, auto_adjust=False)
            else:
                new_data = ticker.history(start=start, end=pd.Timestamp.now(), interval=interval, auto_adjust=False)
            
            new_data.loc[new_data['Close'] == new_data['Adj Close'],'Adj Close'] = np.nan
            if not new_data.empty:
                #drop incomplete data
                if new_data['Dividends'].dtypes == 'O':
                    new_data['Dividends'] = new_data['Dividends'].str.replace(r'[^\d\.]', '', regex=True).astype(float)
                new_data = new_data.iloc[:-1]
                break  # 成功就不继续 retry 啦
            
            time.sleep(random.random())
        except IndexError as e:
            logging.error(f"{name} IndexError: {e}")
            new_data = pd.DataFrame()
        except YFRateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"🌐 {name} RateLimit attempt {attempt+1}, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        except Exception as e:
            print(f"{name} unknown exception occured: {e}\n",end="")
            logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
            new_data = pd.DataFrame()
        
    return new_data

def update_history(name,db_pool,interval,**kwargs):
    try:
        conn = db_pool.getconn()
        
        file_dir = os.path.join(FILE_DIRS['history'], name[0].upper())
        file_path = os.path.join(file_dir, name + '.parquet')

        if os.path.exists(file_path):
            try:
                existing_data = pd.read_parquet(file_path, engine='fastparquet')

                # 找到最早的 NaN 
                start = existing_data[existing_data['Adj Close'].isna()].index.min()
                if pd.isna(start):
                    start = None

                new_data = get_history(name, start, interval)
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
            new_data = pd.DataFrame()
            data = get_history(name, None, interval)
        
        if not data.empty:
            os.makedirs(file_dir, exist_ok=True)
            data["Adj Close"] = pd.to_numeric(data["Adj Close"], errors="coerce")
            data.to_parquet(file_path, compression='zstd', engine='fastparquet')

        update_database(conn, name, data)
    except Exception as e:
        print(f"{name} unknown exception occurred: {e}")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_spider(update_history, "history", "history", interval="1d")
