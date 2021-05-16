import subprocess
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
from pytz import timezone
import sys
import pickle
from twelvedata import TDClient
from twelvedata import exceptions

td = TDClient(apikey="cd14e1f582e6432ba0e34c18dd31f96a")

def get_all_tickers_ftp():
    subprocess.call('curl ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt > nasdaq_stocknames1', shell = True)
    subprocess.call('curl ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt > nasdaq_stocknames2', shell = True)
    stocknames1 = pd.read_csv('nasdaq_stocknames1', delimiter = '|')
    stocknames2 = pd.read_csv('nasdaq_stocknames2', delimiter = '|')
    stocknames1 = stocknames1.loc[stocknames1['Test Issue']=='N',:] #get rid of Test Issue = Y
    stocknames2 = stocknames2.loc[stocknames2['Test Issue']=='N',:]
    stocknames1 = stocknames1['Symbol']
    stocknames2 = stocknames2['ACT Symbol']
    return sorted(list(set(list(stocknames1) + list(stocknames2)))) 

def get_all_tickers_twelvedata():
    all_nyse_stocks = td.get_stocks_list(exchange="NYSE").as_json()
    all_nasdaq_stocks = td.get_stocks_list(exchange="NASDAQ").as_json()

    return sorted(list(set(list(map(lambda t: t["symbol"], all_nyse_stocks)) + list(map(lambda t: t["symbol"], all_nasdaq_stocks)))))

    

def get_all_tickers():
    return get_all_tickers_twelvedata()

def download_from_yahoo(tickers, start, end, interval):
    if sys.platform == 'darwin':
        threads = 32
    else:
        threads = 8

    print('downloading {} stocks from {} to {} using {} threads'.format(len(tickers), start, end, threads))
    return yf.download(tickers, start=start, end=end, interval=interval, threads=threads)

    

def download_chunk_from_twelvedata(tickers_idx, start, end, interval, num_chunks):
    idx = tickers_idx[0]
    tickers = tickers_idx[1]
    print("Downloading chunk {} / {}".format(idx, num_chunks))

    try:
        df = td.time_series(
            symbol=tickers,
            interval='30min',
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            outputsize=100, # 5000
            timezone="America/New_York",
        ).as_pandas()["open"]
    except exceptions.BadRequestError as err:
       # TODO: check the cases of err
       print("\tdownload error occurred. Discarding this chunk!")
       print(err)
       return None

    if type(df.index[0]) is not tuple:
        new_index_tuples = [(tickers[0], x) for x in df.index]
        df.index = pd.MultiIndex.from_tuples(new_index_tuples)

    if isinstance(df.index[0][1], str):
        df.index = df.index.map(lambda ticker_dtstr: (ticker_dtstr[0], datetime.datetime.fromisoformat(ticker_dtstr[1])))
    elif isinstance(df.index[0][1], pd.Timestamp):
        df.index = df.index.map(lambda ticker_dtstr: (ticker_dtstr[0], ticker_dtstr[1].to_pydatetime()))
    else:
        raise 'Unknown datatype for index: ' + str(type(df.index[0][1]))
    
    return df.astype(float)


# https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n): 
        yield l[i:i + n]

def download_from_twelvedata(tickers, start, end, interval):
    if interval == "60m":
        interval = "1h"
    
    ticker_chunks = list(divide_chunks(tickers, 1))
    num_chunks = len(ticker_chunks)

    dfs = list(map(lambda chunk: download_chunk_from_twelvedata(chunk, start, end, interval, num_chunks), enumerate(ticker_chunks)))
    dfs = list(filter(lambda df: df is not None, dfs))
    df = pd.concat(dfs)
    return df
    


def is_morning_time(dt):
    return dt.hour == 10 and dt.minute == 30 and dt.second == 0

def is_afternoon_time(dt):
    return dt.hour == 14 and dt.minute == 30 and dt.second == 0

def extract_overnight_times_60_min(df):
    tenthirty_index = df.index.map(lambda ticker_dtstr: is_morning_time(ticker_dtstr[1]))
    two_thirty_index = df.index.map(lambda ticker_dtstr: is_afternoon_time(ticker_dtstr[1]))

    prices_morning = df.loc[tenthirty_index, :].copy()
    prices_morning.index = prices_morning.index.map(lambda ticker_dt: (ticker_dt[0], ticker_dt[1].date()))

    prices_afternoon = df.loc[two_thirty_index, :].copy()
    prices_afternoon.index = prices_afternoon.index.map(lambda ticker_dt: (ticker_dt[0], ticker_dt[1].date()))

    prices_morning = prices_morning.unstack(level=0)
    prices_afternoon = prices_afternoon.unstack(level=0)
    
    morning_tuples_index = [('10:30', tup) for tup in prices_morning.columns.values]
    afternoon_tuples_index = [('14:30', tup) for tup in prices_afternoon.columns.values]

    morning_index = pd.MultiIndex.from_tuples(morning_tuples_index)
    afternoon_index = pd.MultiIndex.from_tuples(afternoon_tuples_index)

    prices_morning.columns = morning_index
    prices_afternoon.columns = afternoon_index

    combined = pd.concat([prices_morning, prices_afternoon], axis=1)

    return combined

def fetch_stock_data(tickers, start, end):
    # First we download the stock data from yahoo finance, for all the tickers.
    # Note: We add one day to the end date, since sometimes yahoo finance doesn't include the end date.
    df_every_60_min = download_from_twelvedata(tickers, start, end + datetime.timedelta(days=1), '60m')

    print("Direct from twelvedata:")
    # print(df_every_60_min)

    # We then use the extract_overnight_times_60_min function to extract the 
    # morning / afternoon times for each day into a dataframe. This dataframe will look like:
    #             10:30               15:00
    #             AAPL  TSLA ...       AAPL  TSLA ...
    # 01-01-2021  23    18             23.5  
    # 01-02-2021  25    19             23.2
    # 01-03-2021  24    18.5           24
    #    ...

    df_morning_afternoon = extract_overnight_times_60_min(df_every_60_min)
    
    # We then extract only the dates we want, to make sure there isn't extra stuff in the dataframe
    return df_morning_afternoon.loc[start:end, :]
