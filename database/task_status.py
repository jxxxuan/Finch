from datetime import datetime
import traceback
import psycopg2
from database import *

def log_task_start(conn, task_name, log_id):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO monitor.task_status (task_name, status, log_id)
            VALUES (%s, 'running', %s)
            RETURNING task_id
        """, (task_name, log_id))
        task_id = cur.fetchone()[0]
        conn.commit()
        return task_id

def log_task_end(conn, task_id, status, message=None):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE monitor.task_status
            SET end_time = %s, status = %s, message = %s
            WHERE task_id = %s
        """, (datetime.now(), status, message, task_id))
        conn.commit()
