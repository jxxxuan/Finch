import pandas as pd
import os
from constants import FILE_DIRS
import logging
import traceback
from database.symbol_metadata import update_symbol_by_symbol
from utils import safe_type_input, safe_field_input
import time
from .run_script import manually_run_script
import sys
from pandas.errors import ParserError
target = 'balance_sheet'

def func(name, db_pool):
    try:
        file_dir = os.path.join(FILE_DIRS[target], name[0].upper())
        file_path = os.path.join(file_dir, name + '.parquet')

        #conn = db_pool.getconn()

        if os.path.exists(file_path):
            data = pd.read_parquet(file_path, engine='fastparquet')
            try:
                data.index = pd.to_datetime(data.index, format="%Y-%m-%d")
            except (ParserError, ValueError):
                data = data.T
                data.index = pd.to_datetime(data.index, format="%Y-%m-%d")
            data.sort_index(ascending=True, inplace=True)
            data.to_parquet(file_path, compression='zstd', engine='fastparquet')
            print(name)
        else:
            pass
            #data_dict = {f"{type_}_record":False,}
        #update_symbol_by_symbol(conn,name,data_dict)

    except Exception as e:
        print(f"{name} unknown exception occured: {e}\n",end="")
        logging.error(f"{name} unknown exception occured: {traceback.format_exc()}")
    finally:
        #db_pool.putconn(conn)
        pass

if __name__ == '__main__':
    manually_run_script(func, target, target+"_transpose")