'''
        stock.loc[name, 'average_volume'] = data.Volume.mean()
        stock.loc[name, 'last_day'] = data.last_valid_index()
        stock.loc[name, 'first_day'] = data.first_valid_index()
        stock.loc[name, 'close_std'] = data.Close.std()
        stock.loc[name, 'volume_std'] = data.Volume.std()
        stock.loc[name, 'droped_na_count'] = len(data.dropna())
        stock.loc[name, 'count'] = len(data)
        stock.loc[name, 'contains_negative'] = (data[['Open','High','Low','Close']] < 0).any().any()
        '''