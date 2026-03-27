import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd
import os
from constants import FILE_DIRS
from .update_main import manually_run_spider
from database.symbol_metadata import update_symbol_by_symbol, get_by_condition
from utils import wait_until_online, safe_type_input
import logging
import traceback
import time
import random

def update_database(name, conn, type, data):
    data_dict = {f"{type}_record":len(data) > 0,
                    f"{type}_last_update":pd.Timestamp.now(),
                    f"{type}_last_day":data.last_valid_index(),
                    f"{type}_first_day":data.first_valid_index()}
    update_symbol_by_symbol(name, conn, data_dict)

def get_financial_statement(name, conn, max_retries=3):
    new_data = pd.DataFrame()

    for attempt in range(max_retries):
        try:
            wait_until_online()
            ticker = yf.Ticker(name)
            new_data = ticker.quarterly_balance_sheet.T
            if not new_data.empty:
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
            print(f"{name} unknown exception occured: {e}\n",end="")
            logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
            new_data = pd.DataFrame()
        
    return new_data

def update_financial_statement(name, conn, type):
    try:
        file_dir = os.path.join(FILE_DIRS[type], name[0].upper())
        file_path = os.path.join(file_dir, name + '.parquet')
        
        if os.path.exists(file_path):
            try:
                existing_data = pd.read_parquet(file_path, engine='fastparquet')
                new_data = get_financial_statement(name, conn)
                if not new_data.empty:
                    data = pd.concat([existing_data, new_data])
                    data = data[~data.index.duplicated(keep='last')]
                    data.sort_index(inplace=True)
                else:
                    data = existing_data
                    
            except Exception as e:
                print(f"⚠️ {name}: parquet file damaged, redownloading...")
                logging.warning(f"{name}: parquet damaged -> {e}")
                data = get_financial_statement(name, conn)
        else:
            data = get_financial_statement(name, conn)

        if not data.empty:
            os.makedirs(file_dir, exist_ok=True)
            data.to_parquet(file_path, compression='zstd', engine='fastparquet')
        return data
    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")

if __name__ == '__main__':
    type = safe_type_input('type to update', 'balance_sheet')
    manually_run_spider(update_financial_statement, type, type)
