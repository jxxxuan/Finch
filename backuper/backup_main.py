from utils import safe_int_input, init_logging
from database.symbol_metadata import create_db_pool, create_conn
from database.task_status import log_task_end, log_task_start
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from constants import LOG_DIR, FILE_DIRS
from datetime import datetime
import os
from tqdm import tqdm

def run_backup(backup_function, task_name, type, num_worker=2, **kwargs):
    try:
        conn = create_conn()
        db_pool = create_db_pool(num_worker)

        now = datetime.now()
        log_datetime = now.strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.join(LOG_DIR, str(now.year), str(now.month).zfill(2), str(now.day).zfill(2))
        log_id = f"backup_{task_name}_{log_datetime}.log"
        task_id = log_task_start(conn, f"backup_{task_name}", log_id)

        init_logging(log_dir, log_id)

        types_to_process = FILE_DIRS if type == '*' else [type]
        with ThreadPoolExecutor(max_workers=num_worker) as executor:
            with tqdm(total=len(types_to_process), desc=task_name, smoothing=0.9, ncols=120) as pbar:
                futures = [executor.submit(backup_function, t, **kwargs) for t in types_to_process]

                for f in as_completed(futures):
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
        conn.close()
        db_pool.closeall()
        logging.shutdown()
        print("✅ shut down safely")
    print("✅ done update")

def manually_run_backup(backup_function, type):
    #selected_rule = safe_rule_input('选择规则', 'need_update')

    run_backup(backup_function, type, type)
