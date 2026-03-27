from .update_main import manually_run_spider
from .financial_statement_updater import update_database, get_financial_statement, update_financial_statement
import logging
import traceback

def update_balance_sheet_database(conn, name, data):
    update_database(conn, name, 'balance_sheet', data)

def get_balance_sheet(name, conn, max_retries=3):
    return get_financial_statement(name, conn, max_retries)

def update_balance_sheet(name, db_pool):
    try:
        conn = db_pool.getconn()
        data = update_financial_statement(name, conn, 'balance_sheet')
        update_balance_sheet_database(conn, name, data)
    finally:
        db_pool.putconn(conn)

if __name__ == '__main__':
    manually_run_spider(update_balance_sheet, "balance_sheet", "balance_sheet")
