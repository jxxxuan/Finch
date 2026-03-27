from database.symbol_metadata import update_symbol_by_condition
from processor.process_main import manually_run_process
from utils import safe_type_input

def update_by_last_day(db_pool, type):
    try:
        conn = db_pool.getconn()
        
        condition = f"""
            NOT delisted
            AND (history_last_day IS NOT NULL AND NOW() - history_last_day > interval '1 month')
            """
        data_dict = {'delisted':True}
        update_symbol_by_condition(conn, condition, data_dict)
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    type = safe_type_input("Type to update",'')
    manually_run_process(update_by_last_day, type)