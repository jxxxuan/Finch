from utils import safe_int_input, safe_rule_input, init_logging, safe_float_input, batch_iterable
from database.symbol_metadata import create_db_pool, get_by_rule
import pandas as pd
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait, FIRST_COMPLETED
import traceback
from datetime import datetime
from constants import LOG_DIR
import os
from database.task_status import log_task_end, log_task_start

def run_script(update_function, selected_rule, task_name, type, num_to_update=999999, num_worker=1, max_run_time_minutes=999999, **kwargs):
    try:
        db_pool = create_db_pool(num_worker)

        conn = db_pool.getconn()

        now = datetime.now()
        log_datetime = now.strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.join(LOG_DIR, str(now.year), str(now.month).zfill(2), str(now.day).zfill(2))
        log_id = f"spider_{task_name}_{log_datetime}.log"
        task_id = log_task_start(conn, f"spider_{task_name}", log_id)

        init_logging(log_dir, log_id)

        df = get_by_rule(conn, type, selected_rule, cols=['symbol'], limit=num_to_update)

        indexes = df.index
        print(f"updating {len(indexes)} symbols")
        logging.info(f"updating {len(indexes)} symbols")

        start_time = time.time()
        max_run_time = max_run_time_minutes * 60

        with ThreadPoolExecutor(max_workers=num_worker) as executor:
            for batch in batch_iterable(indexes, batch_size=num_worker * 10):
                futures = set(executor.submit(update_function, name, db_pool, **kwargs) for name in batch)

                while futures: 
                    done, not_done = wait(futures, timeout=1, return_when=FIRST_COMPLETED)
                    futures.difference_update(done)

                    if time.time() - start_time > max_run_time:
                        print(f"⏰ exceed max run time {max_run_time/60:.2f} minute")
                        raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("❗ KeyboardInterrupt, program stopped")
        logging.info("❗ KeyboardInterrupt, program stopped")
        executor.shutdown(wait=False, cancel_futures=True)
    except Exception as e:
        print(f"unknown exception occured: {e}\n",end="")
        logging.error(f"unknown exception occured: {traceback.format_exc()}")
        log_task_end(conn, task_id, "failed", traceback.format_exc())
        raise
    finally:
        db_pool.putconn(conn)
        db_pool.closeall()
        logging.shutdown()
        print("✅ 程序已安全退出")
    print("✅ DONE！")

def manually_run_script(update_function, type, task_name, **kwargs):
    num_to_update = safe_int_input('num to update', 999999)
    num_worker = safe_int_input('num worker', 1)
    selected_rule = safe_rule_input('rules', '*')
    max_run_time_minutes = safe_float_input('max run time (minute, default endless)', 60)

    run_script(update_function, selected_rule, task_name, type, num_to_update, num_worker, max_run_time_minutes, **kwargs)