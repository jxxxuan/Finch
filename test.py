import time
from datetime import datetime
import os

if __name__ == '__main__':
    print('Start testing')
    now = datetime.now()
    log_datetime = now.strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join('/home/jxxxuan/gdrive/stock/logs', str(now.year), str(now.month).zfill(2), str(now.day).zfill(2))
    os.makedirs(log_dir,exist_ok=True)
    log_path = os.path.join(log_dir,'test.log')
    with open(log_path, 'a') as f:
        print('Start testing')
        f.write('Start testing\n')
        time.sleep(5)
        print('End testing')
        f.write('End testing\n')
    print('End testing')