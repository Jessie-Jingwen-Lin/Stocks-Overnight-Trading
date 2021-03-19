import subprocess
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
from alpaca_v1 import AlpacaV1Downloader
from pytz import timezone

def get_all_tickers():
    subprocess.call('curl ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt > nasdaq_stocknames1', shell = True)
    subprocess.call('curl ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt > nasdaq_stocknames2', shell = True)
    stocknames1 = pd.read_csv('nasdaq_stocknames1', delimiter = '|')
    stocknames2 = pd.read_csv('nasdaq_stocknames2', delimiter = '|')
    stocknames1 = stocknames1.loc[stocknames1['Test Issue']=='N',:] #get rid of Test Issue = Y
    stocknames2 = stocknames2.loc[stocknames2['Test Issue']=='N',:]
    stocknames1 = stocknames1['Symbol']
    stocknames2 = stocknames2['ACT Symbol']
    return sorted(list(set(list(stocknames1) + list(stocknames2)))) #sort alphabetically #set finds unique items in the list, and combine them together

def load_stock_file(tickers, filename):
    from os import path
    import pickle
    if path.exists(filename) == True:
        with open(filename, 'rb') as handle:
            stock_tickers_data = pickle.load(handle)
        if stock_tickers_data['tickers'] == tickers:
            return stock_tickers_data['df']
        else:
            print("new tickers, need to download fresh")
            return None
    else:
        print("no cached data, need to download fresh")
        return None


    # This function needs to:
    # 1. Check if a file at the given filename exists.
    #    If it does not, then return None, so that the rest of the code will have to download everything.
    #    You need to Google search to see how to check if a file exists or not.
    # 2. Load the pickle file into a variable called stock_tickers_data.
    #    See https://docs.python.org/3/library/pickle.html#pickle.dumps
    #    BUT you will need to ask me for more explanation.
    # 3. We assume that the loaded object (stock_tickers_data) is actually a DICTIONARY, with 2 entries:
    #    a. stock_tickers_data["df"] contains the dataframe of the old saved data,
    #       in the format given by yf.download
    #    b. stock_tickers_data["tickers"] contains the list of tickers that were included in that old data
    # 4. We now have 2 cases:
    #    a. If the tickers we want NOW (tickers) match the OLD tickers (stock_tickers_data["tickers"]),
    #       then that is great, that means the old data is valid, so we should return it.
    #    b. If the tickers we want NOW are different than the OLD tickers, then the old data is
    #       invalid, so we should return None so that the rest of the code will download everything fresh.
    #       If this happens, then also print out a message so that we know if that happens.

def download_from_yahoo(tickers, start, end, interval):
    # Try downloading AAPL first, to see if there is any data in the date range
    apple_data = yf.download('AAPL', start=start, end=end, interval=interval, threads=False)
    if apple_data.shape[0] == 0:
        print("No data between {} and {}, will not attempt to download stocks.".format(start, end))
        return None

    print('downloading {} stocks from {} to {}'.format(len(tickers), start, end))
    return yf.download(tickers, start=start, end=end, interval=interval, threads=32)

def extract_overnight_times_30_min(df):
    df = df["Open"]

    tenthirty_index = df.index.map(lambda date_time: date_time.hour == 10 and date_time.minute == 30)
    three_index = df.index.map(lambda date_time: date_time.hour == 15 and date_time.minute == 00)

    prices_morning = df.loc[tenthirty_index, :].copy()
    prices_morning.index = prices_morning.index.map(lambda date_time: date_time.date())

    prices_afternoon = df.loc[three_index, :].copy()
    prices_afternoon.index = prices_afternoon.index.map(lambda date_time: date_time.date())

    morning_tuples_index = [('10:30', tup) for tup in prices_morning.columns.values]
    afternoon_tuples_index = [('15:00', tup) for tup in prices_afternoon.columns.values]

    morning_index = pd.MultiIndex.from_tuples(morning_tuples_index)
    afternoon_index = pd.MultiIndex.from_tuples(afternoon_tuples_index)
    
    prices_morning.columns = morning_index
    prices_afternoon.columns = afternoon_index

    combined = pd.concat([prices_morning, prices_afternoon], axis=1)
    return combined

def extract_overnight_times_60_min(df):
    df = df["Open"]

    tenthirty_index = df.index.map(lambda date_time: date_time.hour == 10 and date_time.minute == 30)
    two_thirty_index = df.index.map(lambda date_time: date_time.hour == 14 and date_time.minute == 30)
    three_thirty_index = df.index.map(lambda date_time: date_time.hour == 15 and date_time.minute == 30)

    prices_morning = df.loc[tenthirty_index, :].copy()
    prices_morning.index = prices_morning.index.map(lambda date_time: date_time.date())

    prices_two_thirty = df.loc[two_thirty_index, :].copy()
    prices_two_thirty.index = prices_two_thirty.index.map(lambda date_time: date_time.date())

    prices_three_thirty = df.loc[three_thirty_index, :].copy()
    prices_three_thirty.index = prices_three_thirty.index.map(lambda date_time: date_time.date())

    prices_afternoon = (prices_two_thirty + prices_three_thirty) / 2

    morning_tuples_index = [('10:30', tup) for tup in prices_morning.columns.values]
    afternoon_tuples_index = [('15:00', tup) for tup in prices_afternoon.columns.values]

    morning_index = pd.MultiIndex.from_tuples(morning_tuples_index)
    afternoon_index = pd.MultiIndex.from_tuples(afternoon_tuples_index)

    prices_morning.columns = morning_index
    prices_afternoon.columns = afternoon_index

    combined = pd.concat([prices_morning, prices_afternoon], axis=1)

    return combined


def download_stock(tickers, start, end):
    one_day = datetime.timedelta(days=1)

    days_ago_60 = datetime.date.today() - datetime.timedelta(days=60)
    
    #  start ------------- end

    range_30_min = None
    range_60_min = None
    if end <= days_ago_60:
        # start ------------- end -------- days_ago_60
        range_60_min = (start, end + one_day)
    elif start <= days_ago_60 and days_ago_60 < end:
        # start ------ days_ago_60 ------- end
        range_30_min = (days_ago_60 + one_day, end + one_day)
        range_60_min = (start, days_ago_60 + one_day)
    else:
        # days_ago_60 -------- start ------------- end
        range_30_min = (start, end + one_day)
    
    df_30_min = None
    df_60_min = None
    
    if range_30_min is not None:
        df_30_min = download_from_yahoo(tickers, range_30_min[0], range_30_min[1], '30m')
        df_30_min = extract_overnight_times_30_min(df_30_min)
    
    if range_60_min is not None:
        df_60_min = download_from_yahoo(tickers, range_60_min[0], range_60_min[1], '60m')
        df_60_min = extract_overnight_times_60_min(df_60_min)


    # print(df_30_min)
    # print(df_60_min)

    df_merged = pd.concat([df_60_min, df_30_min])

    return df_merged



    # # downloader = AlpacaV1Downloader('PKDZ66P4JY43Z5WXPUQG', '7u9Mttz8JowIJZiB7Dq5uX9bhjRCOF7t6MtssJ4R')
    # downloader = AlpacaV1Downloader('PKDV56VEU69G71YONUL0', 'JdsFFESL8szlaoICOGb20CyoiKcUU22oM8kISqiP')
    #
    # df = downloader.get_prices(tickers, start, end)
    # return df

def fetch_stock_data(tickers, start, end):
    import pickle
    # Step 1. Load existing data from file (if any)
    # existing_data = load_stock_file(tickers, 'stockdata.pickle')
    existing_data = None

    # Step 2. Download data that you need that isn't loaded from file
    if existing_data is not None and existing_data.index[-1] >= start:
        # If the existing data overlaps with the wanted data,
        # then we only download the part of the wanted data that we don't have. For example:
        #
        # Want:             -----********
        # Existing:  ------------
        #
        # We only need to download the * parts

        date_time = existing_data.index[-1]
        thirtymin_afterstart = date_time + datetime.timedelta(minutes=30)
        downloaded_data = download_stock(tickers, start=thirtymin_afterstart, end=end)
        # downloaded_data = yf.download(tickers, start=thirtymin_afterstart, end=end, interval='30m', threads=False)
    else:
        # If we either don't have existing data, or if there is no overlap,
        # we just download everything.
        downloaded_data = download_stock(tickers, start=start, end=end)
        # downloaded_data = yf.download(tickers, start=start, end=end, interval='30m', threads=False)

    # Step 3. Merge those
    if downloaded_data is None:
        merged_data = existing_data
    else:
        if existing_data is None:
            merged_data = downloaded_data
        else:
            merged_data = pd.concat([existing_data, downloaded_data], axis=0)

    # Step 4. Save merged data back to file
    dic = {'tickers': tickers, 'df': merged_data}
    with open('stockdata.pickle', 'wb') as handle:
        pickle.dump(dic, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Step 5. Return merged data as dataframe
    return merged_data.loc[start:end, :]

