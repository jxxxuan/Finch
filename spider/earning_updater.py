import yfinance as yf
import pandas as pd
import os

nl = pd.read_csv(r"D:\predictor\stock.csv",index_col=0,low_memory=False)

for name in nl[nl['balance_sheet_record']].index:
    print(name)
    ticker = yf.Ticker(name)
    balance_sheet = ticker.balance_sheet
    ticker.earnings

    path = os.path.join(r'D:\predictor\stock_balance_sheet',name[0].upper())
    if(not os.path.exists(path)):
        os.mkdir(path)

    if not balance_sheet.empty:
        balance_sheet.to_csv(os.path.join(path,name+'.csv'))
    nl.loc[name,'balance_sheet_record'] = len(balance_sheet) > 0
    nl.loc[name,'balance_sheet_last_update'] = pd.Timestamp.now()

nl.to_csv(r"D:\predictor\stock.csv")
