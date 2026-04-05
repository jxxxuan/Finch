from utils import send_mail, wait_until_online
from spider.update_main import run_spider
from spider.info_updater import update_info
from spider.minute_history_updater import update_history as update_mhistory
from spider.daily_history_updater import update_history
from spider.recommendations_updater import update_recommendations
from spider.cash_flow_updater import update_cash_flow
from spider.balance_sheet_updater import update_balance_sheet
from spider.income_statement_updater import update_income_statement
from spider.news_updater import update_news
from processor.process_main import run_process
from processor.next_update_updater import update_by_interval, update_by_frequency
from processor.delisted_updater import update_by_last_day
from backuper.backup_main import run_backup
from backuper.stock_backuper import backup as backup_stock
# from backuper.database_backuper import backup as backup_database
from datetime import datetime

if __name__ == '__main__':
    #while True:
    wait_until_online()
    today = datetime.now().strftime("%Y-%m-%d")
    send_mail(today+" Predictor start running","")
    sql = "today AND ready for update"
    run_spider(update_mhistory, sql, task_name="minute_history", type="minute_history", interval="1m")
    run_spider(update_history, sql, task_name="history", type="history", interval="1d")
    
    run_spider(update_cash_flow, sql, task_name="cash_flow", type="cash_flow",num_worker=3)
    run_spider(update_balance_sheet, sql, task_name="balance_sheet", type="balance_sheet",num_worker=3)
    run_spider(update_income_statement, sql, task_name="income_statement", type="income_stmt",num_worker=3)
    run_spider(update_info, sql, task_name="info", type="info")
    run_spider(update_recommendations, sql, task_name="recommendations", type="recommendations",num_worker=3)
    run_spider(update_news, sql, task_name="news", type="news",num_worker=2)

    run_process(update_by_frequency, task_name='update_next_update(frequency)',type='news')
    run_process(update_by_interval, task_name='update_next_update(interval)',type='INTV')
    #run_process(update_by_last_day, task_name='delisted_updater', type = '')

    run_backup(backup_stock, task_name='backup_stock', type='*')
    # run_backup(backup_database, task_name='backup_database', type='*')
    #wait_until_next_task()