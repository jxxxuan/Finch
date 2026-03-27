import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd
import numpy as np
import os
import logging
from constants import FILE_DIRS
import traceback
from database.symbol_metadata import update_symbol_by_symbol, get_by_condition
from utils import wait_until_online
import time
from .update_main import manually_run_spider
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

def update_database(conn, name, data):
    data_dict = {"recommendations_record":len(data) > 0,
                    "recommendations_last_update":pd.Timestamp.now(),
                    "recommendations_first_month":data.first_valid_index(),
                    "recommendations_last_month":data.last_valid_index()}
    update_symbol_by_symbol(conn, name, data_dict)

def get_recommendations(name, conn, max_retries=3):
    new_data = pd.DataFrame()  # 初始化，防止没有赋值报错

    for attempt in range(max_retries):
        try:
            wait_until_online()
            ticker = yf.Ticker(name)
            new_data = ticker.recommendations
            
            if "period" in new_data.columns:
                now = datetime.now()
                # period 如 '0m', '-1m', '-2m' ...
                def period_to_date(p):
                    try:
                        months = int(p.replace('m', ''))
                        dt = now + relativedelta(months=months)
                        dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                        return dt
                    except:
                        return None
                new_data["date"] = new_data["period"].apply(period_to_date)
                new_data.set_index("date", inplace=True)
                new_data.drop(columns=["period"], inplace=True)
            
                break

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

def update_recommendations(name,db_pool,**kwargs):
    try:
        conn = db_pool.getconn()
        
        file_dir = os.path.join(FILE_DIRS['recommendations'], name[0].upper())
        file_path = os.path.join(file_dir, name + '.parquet')

        if os.path.exists(file_path):
            try:
                existing_data = pd.read_parquet(file_path, engine='fastparquet')

                new_data = get_recommendations(name, conn)
                if not new_data.empty:
                    data = pd.concat([existing_data, new_data])
                    data = data[~data.index.duplicated(keep='last')]
                else:
                    data = existing_data

            except Exception as e:
                print(f"⚠️ {name}: parquet file damaged, redownloading...")
                logging.warning(f"{name}: parquet damaged -> {e}")
                data = get_recommendations(name, conn)
        else:
            data = get_recommendations(name, conn)
        
        if not data.empty:
            os.makedirs(file_dir, exist_ok=True)
            data.to_parquet(file_path, compression='zstd', engine='fastparquet')

        update_database(conn, name, data)
    except Exception as e:
        print(f"{name} unknown exception occurred: {e}")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_spider(update_recommendations, "recommendations", "recommendations")


#   period  strongBuy  buy  hold  sell  strongSell
# 0     0m         12   45     0     0           0
# 1    -1m         12   45     0     0           0
# 2    -2m         13   44     1     0           0
# 3    -3m         12   43     1     0           0