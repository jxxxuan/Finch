from .update_main import manually_run_spider
from .financial_statement_updater import update_database, get_financial_statement, update_financial_statement

def update_income_stmt_database(conn, name, data):
    update_database(conn, name, 'income_stmt', data)

def get_income_statement(name, conn, max_retries=3):
    return get_financial_statement(name, conn, max_retries)

def update_income_statement(name, db_pool):
    try:
        conn = db_pool.getconn()
        data = update_financial_statement(name, conn, 'income_stmt')
        update_income_stmt_database(conn, name, data)
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_spider(update_income_statement, "income_stmt", "income_stmt")
