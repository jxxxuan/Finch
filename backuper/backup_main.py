from utils import safe_int_input, init_logging
from database.symbol_metadata import create_db_pool, create_conn
from database.task_status import log_task_end, log_task_start
import logging
import concurrent.futures
import traceback
from constants import LOG_DIR
from datetime import datetime
import os

def run_backup(update_function, task_name, type, num_to_update=999999, num_worker=1, max_run_time_minutes=99):
    try:
        conn = create_conn()
        db_pool = create_db_pool(num_worker)

        now = datetime.now()
        log_datetime = now.strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.join(LOG_DIR, str(now.year), str(now.month).zfill(2), str(now.day).zfill(2))
        log_id = f"processor_{task_name}_{log_datetime}.log"
        task_id = log_task_start(conn, f"processor_{task_name}", log_id)

        init_logging(log_dir, log_id)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_worker) as executor:
            executor.map(
                update_function(db_pool, type),  # 传入 db_pool
            )
        log_task_end(conn, task_id, "success")
    except KeyboardInterrupt:
        print("❗ KeyboardInterrupt, terminating program")
        logging.info("❗ KeyboardInterrupt, terminating program")
        executor.shutdown(wait=False, cancel_futures=True)
    except Exception as e:
        print(f"unknown exception occured: {e}\n",end="")
        logging.error(f"unknown exception occured: {traceback.format_exc()}")
        log_task_end(conn, task_id, "failed", traceback.format_exc())
        raise
    finally:
        conn.close()
        db_pool.closeall()
        logging.shutdown()
        print("✅ shut down safely")
    print("✅ done update")

def manually_run_process(update_function, type):
    num_worker = safe_int_input('num worker', 1)
    max_run_time_minutes = safe_int_input('max run time (minute, default endless)', 60)
    #selected_rule = safe_rule_input('选择规则', 'need_update')

    run_process(update_function, type, type, num_worker, max_run_time_minutes)