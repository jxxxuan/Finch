import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd
import os
from datetime import datetime
from constants import FILE_DIRS
import logging
import json
import traceback
from database.symbol_metadata import update_symbol_by_symbol, get_by_condition
from database.news import insert_news
from utils import wait_until_online
import time
from .update_main import manually_run_spider
import random

def update_database(conn, name, data):
    data_dict = {"news_record":len(data) > 0,
                    "news_last_update":pd.Timestamp.now(),}
    update_symbol_by_symbol(conn, name, data_dict)
    insert_news(conn,data)

def get_news(name, conn, max_retries=3):
    new_data = pd.DataFrame()

    for attempt in range(max_retries):
        try:
            wait_until_online()
            ticker = yf.Ticker(name)
            news = ticker.news or []
            
            if len(news) > 0:
                rows = [pd.Series(flatten('', n['content'])) for n in news]
                new_data = pd.DataFrame(rows)
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
            new_data = pd.DataFrame
    
    return new_data

def merge_name(prefix, k, sep='_'):
    return f"{prefix}{sep}{k}" if prefix else str(k)

def flatten(prefix, d):
    flat = {}
    skip_keys = {
        'isHosted', 'bypassModal',
        'metadata_editorsPick',
        'thumbnail_originalWidth', 'thumbnail_originalHeight',
        'thumbnail_resolutions_0_width', 'thumbnail_resolutions_0_height',
        'thumbnail_resolutions_0_tag',
        'storyline'
    }

    if isinstance(d, dict):
        # 如果 dict 为空，直接跳过
        if not d:
            return flat
        for k, v in d.items():
            new_key = f"{prefix}_{k}" if prefix else k
            if new_key not in skip_keys:
                flat.update(flatten(new_key, v))
    elif isinstance(d, list):
        if d:  # 只处理非空 list
            for i, v in enumerate(d[:1]):  # 只取第一个元素
                new_key = f"{prefix}_{i}"
                flat.update(flatten(new_key, v))
    else:
        # 过滤 None
        if d not in (None, '') and prefix not in skip_keys:
            flat[prefix] = d

    return flat

def update_news(name, db_pool):
    try:
        conn = db_pool.getconn()

        file_dir = os.path.join(FILE_DIRS['news'], name[0].upper())
        file_path = os.path.join(file_dir, name + '.csv')
        
        news = get_news(name, conn)

        if not news.empty:
            if os.path.exists(file_path):
                existing_ids = pd.read_csv(file_path,index_col=0)
                ids = pd.concat([existing_ids, news['id']])
                ids = ids.drop_duplicates(keep='first')
            else:
                ids = news['id']

            os.makedirs(file_dir,exist_ok=True)
            ids.to_csv(file_path)

        update_database(conn,name,news)

    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_spider(update_news, "news", "news")
