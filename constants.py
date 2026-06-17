import os
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

load_dotenv()

BACKUP_PATH = os.getenv("BACKUP_PATH")
# GOOGLE_DRIVE_PATH = os.getenv("GOOGLE_DRIVE_PATH")
LOCAL_DRIVE_PATH = os.getenv("LOCAL_DRIVE_PATH")
TEST_PATH = os.getenv("TEST_PATH")
PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

# SYMBOL_LIST_PATH = os.path.join(GOOGLE_DRIVE_PATH,"symbol.csv")
# SYMBOL_CORRELATION_PATH = os.path.join(GOOGLE_DRIVE_PATH,"corr.csv")
# CURRENCY_LIST_PATH = os.path.join(GOOGLE_DRIVE_PATH,"currencies.csv")
LOG_DIR = os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'logs')
TYPE_OPTIONS = ['history','minute_history','balance_sheet','cash_flow','income_stmt','info','currency','recommendations','news']
# FILE_DIRS = {t: os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH, t) for t in TYPE_OPTIONS}
FILE_DIRS = {'history':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'history'),
             'minute_history':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'minute_history'),
             'balance_sheet':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'balance_sheet'),
             'cash_flow':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'cash_flow'),
             'income_stmt':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'income_stmt'),
             'info':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'info'),
             'currency':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'currency'),
             'recommendations':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'recommendations'),
             'news':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'news')}

TEMP_FILE_DIRS = {'temp_history':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','history'),
             'temp_minute_history':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','minute_history'),
             'temp_balance_sheet':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','balance_sheet'),
             'temp_cash_flow':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','cash_flow'),
             'temp_income_stmt':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','income_stmt'),
             'temp_info':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','info'),
             'temp_currency':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','currency'),
             'temp_recommendations':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','recommendations'),
             'temp_news':os.path.join(LOCAL_DRIVE_PATH if PRODUCTION else TEST_PATH,'tmp','news')}

FIELD_OPTIONS = ['record','last_update','first_day','last_day']
INTERVAL_OPTIONS = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1d', '5d', '1wk', '1mo', '3mo']
RULE_OPTIONS = ['exist', 'malaysia', 'delisted', 'today', 'ready for update', '*']
UPDATE_INTERVAL = {"news": relativedelta(days=1),
                   "minute_history": relativedelta(days=6),
                   "history": relativedelta(months=2),
                   "recommendations": relativedelta(months=2),
                   "cash_flow": relativedelta(months=2),
                   "balance_sheet": relativedelta(months=2),
                   "income_stmt": relativedelta(months=2),
                   "info": relativedelta(months=1)
                   }

UPDATE_FREQUENCY = {"news": 10000,"minute_history": 10000,}

TASK_SCHEDULED_TIME = {"day":"*","hour":"00","minute":"00","second":"00"}