import yfinance as yf
import pandas as pd
import os
from constants import FILE_DIRS
import logging
import traceback
from utils import safe_type_input, check_internet
import time
import sys
from spider.update_main import run_update
import numpy as np
from datetime import datetime, timedelta

def calc_end_from_start(start_str, days=1):
    start_dt = pd.Timestamp(start_str)
    end_dt = start_dt + pd.Timedelta(days=days)
    return end_dt.date()

def history(name,start):
    if not check_internet():
        print("❌ 没有网络，程序即将退出")
        logging.error("❌ 没有网络，程序即将退出")
        sys.exit(1)  # 退出程序，返回状态码 1（错误

    try:
        ticker = yf.Ticker(name)
        end = calc_end_from_start(start)
        new_data = ticker.history(start=start, end=end, auto_adjust=False)
        new_data.loc[new_data['Close'] == new_data['Adj Close'],'Adj Close'] = np.nan

    except IndexError as e:
        print(f"{name} IndexError: {e}\n",end="")
        logging.error(f"{name} IndexError: {e}")
        new_data = pd.DataFrame()
    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
        new_data = pd.DataFrame()
    return new_data

def fill_zero(name, start_time, max_run_time, db_pool):
    try:
        if time.time() - start_time > max_run_time:
            print(f"⏰ 超过最大运行时间 {max_run_time/60:.2f} 分钟，程序结束")
            return

        file_dir = os.path.join(FILE_DIRS[type_], name[0].upper())
        file_path = os.path.join(file_dir, name + '.parquet')
        existing_data = pd.read_parquet(file_path, engine='fastparquet')
        missing_times = existing_data[existing_data['Close'] == 0].index

        for missing_time in missing_times:
            missing_time_str = missing_time.date().isoformat()

            new_data = history(name, missing_time_str)

            if missing_time_str in new_data.index:
                existing_data.loc[missing_time] = new_data.loc[missing_time_str]
                print(name,':',missing_time_str)
            else:
                print(name,':',f'{missing_time_str} not found')

        existing_data = existing_data.drop_duplicates(keep='last')
        existing_data.to_parquet(file_path, compression='zstd', engine='fastparquet')
        
    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")


if __name__ == '__main__':
    while True:
        type_ = safe_type_input('type to update')
        if type_ in ['history','minute_history','balance_sheet','income_stmt','cash_flow']:
            break
        print(['history','minute_history','balance_sheet','income_stmt','cash_flow'])
    run_update(fill_zero, "fill_history_zero", type_, 14)