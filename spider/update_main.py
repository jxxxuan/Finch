from utils import safe_int_input, safe_rule_input, init_logging, safe_float_input, batch_iterable, wait_until_online
from database.symbol_metadata import create_db_pool, get_by_rule
from database.task_status import log_task_end, log_task_start
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import traceback
from datetime import datetime
from constants import LOG_DIR
import os

def run_spider(update_function, selected_rule, task_name, type, num_to_update=999999, num_worker=1, max_run_time_minutes=999999, **kwargs):

    try:
        wait_until_online()

        db_pool = create_db_pool(num_worker+1)
        
        conn = db_pool.getconn()

        now = datetime.now()
        log_datetime = now.strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.join(LOG_DIR, str(now.year), str(now.month).zfill(2), str(now.day).zfill(2))
        log_id = f"spider_{task_name}_{log_datetime}.log"
        task_id = log_task_start(conn, f"spider_{task_name}", log_id)
        
        init_logging(log_dir, log_id)

        df = get_by_rule(conn, type, selected_rule, cols=['symbol'], limit=num_to_update)

        indexes = df.index
        total = len(indexes)
        print(f"updating {task_name} {total} symbols")
        logging.info(f"updating {task_name} {total} symbols")

        start_time = time.time()
        max_run_time = max_run_time_minutes * 60

        with ThreadPoolExecutor(max_workers=num_worker) as executor:
            with tqdm(total=total, desc=task_name, smoothing=0.9, ncols=120) as pbar:
                for batch in batch_iterable(indexes, batch_size=num_worker * 10):
                    futures = [executor.submit(update_function, name, db_pool, **kwargs) for name in batch]

                    for f in as_completed(futures):
                        if time.time() - start_time > max_run_time:
                            print(f"\n⏰ exceed max run time {max_run_time/60:.2f} minute")
                            raise KeyboardInterrupt

                        try:
                            f.result()
                        except Exception as e:
                            print(f"任务失败: {e}")

                        pbar.update(1)  # ✅ 更新全局进度条

        log_task_end(conn, task_id, "success")
    except KeyboardInterrupt:
        print("❗ KeyboardInterrupt, terminating program")
        logging.info("❗ KeyboardInterrupt, terminating program")
    except Exception as e:
        print(f"unknown exception occured: {e}\n",end="")
        logging.error(f"unknown exception occured: {traceback.format_exc()}")
        log_task_end(conn, task_id, "failed", traceback.format_exc())
        raise
    finally:
        db_pool.putconn(conn)
        db_pool.closeall()
        logging.shutdown()
        print("✅ shut down safely")
    print("✅ done update")

def manually_run_spider(update_function, type, task_name, **kwargs):
    num_to_update = safe_int_input('num to update', 999999)
    num_worker = safe_int_input('num worker', 1)
    selected_rule = safe_rule_input('rules', '*')
    max_run_time_minutes = safe_float_input('max run time (minute, default endless)', 60)

    run_spider(update_function, selected_rule, task_name, type, num_to_update, num_worker, max_run_time_minutes, **kwargs)