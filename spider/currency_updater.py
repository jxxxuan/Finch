import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import concurrent.futures
from constants import BASE_PATH,CURRENCY_LIST_PATH,FILE_PATHS

period_date = pd.Timestamp(datetime.now() - timedelta(days=5)).date()
currency = pd.read_csv(CURRENCY_LIST_PATH, index_col=0,low_memory=False)
currency.last_update = pd.to_datetime(currency.last_update,format='mixed',utc=True)
currency.last_day = pd.to_datetime(currency.last_day,format='mixed',utc=True)
rules = (currency.record) & (currency.last_update.dt.date < period_date)
# rules = ~(currency.record) & (currency.last_update.dt.date < period_date)
# rules = ~(currency.record) & (currency.last_update.isna())
indexes = currency.index.drop_duplicates()
print(len(indexes))

def history(name,start):
    name = name+'=X'
    ticker = yf.Ticker(name)
    try:
        if start == None:
            new_data = ticker.history(period='max')
        else:
            new_data = ticker.history(start=start)
    except IndexError as e:
        print(e)
        new_data = pd.DataFrame()
    except Exception as e:
        print(e)
        new_data = pd.DataFrame()
    return new_data[:-1]

def update_currency(name):
    print(name)
    data = history(name, None)

    if os.path.exists(os.path.join(BASE_PATH,FILE_PATHS['currency'], name[0].upper(), name + '.csv')):
        data = pd.read_csv(os.path.join(BASE_PATH,FILE_PATHS['currency'], name[0].upper(), name + '.csv'),index_col=0)
        new_data = history(name,currency.loc[name].last_day)

        if not new_data.empty:
            new_data.loc[new_data.index[0], 'historical_max_ohlc'] = max([new_data.iloc[0][['Open', 'High', 'Low', 'Close']].max().max(),data.iloc[-1,-2]])
            new_data.loc[new_data.index[0], 'historical_min_ohlc'] = min([new_data.iloc[0][['Open', 'High', 'Low', 'Close']].min().min(),data.iloc[-1,-1]])
            new_data = get_hist_ohlc_min_max(new_data)
            data = pd.concat([data, new_data])
            data = data[~data.index.duplicated()]
    else:
        data = history(name,None)
        if not data.empty:
            data.loc[data.index[0], 'historical_max_ohlc'] = data.iloc[0][['Open', 'High', 'Low', 'Close']].max().max()
            data.loc[data.index[0], 'historical_min_ohlc'] = data.iloc[0][['Open', 'High', 'Low', 'Close']].min().min()
            data = get_hist_ohlc_min_max(data)

    if len(data) > 100:
        data.to_csv(os.path.join(BASE_PATH,FILE_PATHS['currency'], name[0].upper(), name + '.csv'))
        currency.loc[name, 'record'] = True

    currency.loc[name, 'count'] = len(data)
    currency.loc[name, 'droped_na_count'] = len(data.dropna())
    currency.loc[name, 'last_day'] = data.last_valid_index()
    currency.loc[name, 'first_day'] = data.first_valid_index()
    currency.loc[name, 'last_update'] = pd.Timestamp.now()
    currency.loc[name, 'close_std'] = data.Close.std()

def get_hist_ohlc_min_max(data):
    columns = data.columns
    indexes = data.index
    ndata = data.values
    for i in range(1, len(ndata)):
        ndata[i, -2] = ndata[i - 1, -2]
        ndata[i, -2] = ndata[i - 1:i + 1, [0, 1, 2, 3, -2]].max()
        ndata[i, -1] = ndata[i - 1, -1]
        ndata[i, -1] = ndata[i - 1:i + 1, [0, 1, 2, 3, -1]].min()
    data = pd.DataFrame(index=indexes, columns=columns, data=ndata)
    return data

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    executor.map(update_currency, indexes[:5000])
currency.to_csv(CURRENCY_LIST_PATH)
