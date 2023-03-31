import subprocess
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
from pytz import timezone
import sys
import pickle

def get_all_tickers():
    ok_na = ['-1.#IND', '1.#QNAN', '1.#IND', '-1.#QNAN', '#N/A N/A', '#N/A', 'N/A', 'n/a', '<NA>', '#NA', '-NaN', '-nan', '']
    subprocess.call('curl ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt > nasdaq_stocknames1', shell = True)
    subprocess.call('curl ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt > nasdaq_stocknames2', shell = True)
    stocknames1 = pd.read_csv('nasdaq_stocknames1', delimiter = '|', keep_default_na=False, na_values=ok_na)
    stocknames2 = pd.read_csv('nasdaq_stocknames2', delimiter = '|', keep_default_na=False, na_values=ok_na)
    stocknames1 = stocknames1.loc[stocknames1['Test Issue']=='N',:] #get rid of Test Issue = Y
    stocknames2 = stocknames2.loc[stocknames2['Test Issue']=='N',:]
    stocknames1 = stocknames1['Symbol']
    stocknames2 = stocknames2['ACT Symbol']

    #debug
    #print(sorted(list(set(list(stocknames1) + list(stocknames2))))[:10])
    

    return sorted(list(set(list(stocknames1) + list(stocknames2))))
    
    #sort alphabetically #set finds unique items in the list, and combine them together

def download_from_yahoo(tickers, start, end, interval):
    if sys.platform == 'darwin':
        threads = 32
    else:
        threads = 8

    print('downloading {} stocks from {} to {} using {} threads'.format(len(tickers), start, end, threads))
    return yf.download(tickers, start=start, end=end, interval=interval, threads=threads)

def extract_overnight_times_60_min(df, morning_time):
    morning_index = df.index.map(lambda date_time: date_time.hour == morning_time[0] and date_time.minute == morning_time[1] and date_time.second == morning_time[2])
    afternoon_index = df.index.map(lambda date_time: date_time.hour == 14 and date_time.minute == 30 and date_time.second == 0)

    prices_morning = df.loc[morning_index, :].copy()
    prices_morning.index = prices_morning.index.map(lambda date_time: date_time.date())

    prices_afternoon = df.loc[afternoon_index, :].copy()
    prices_afternoon.index = prices_afternoon.index.map(lambda date_time: date_time.date())

    prices_morning_time = f'{morning_time[0]}:{morning_time[1]}'
    morning_tuples_index = [(prices_morning_time, tup) for tup in prices_morning.columns.values]
    afternoon_tuples_index = [('14:30', tup) for tup in prices_afternoon.columns.values]

    morning_index = pd.MultiIndex.from_tuples(morning_tuples_index)
    afternoon_index = pd.MultiIndex.from_tuples(afternoon_tuples_index)

    prices_morning.columns = morning_index
    prices_afternoon.columns = afternoon_index

    combined = pd.concat([prices_morning, prices_afternoon], axis=1)

    return combined


def fetch_stock_data(tickers, start, end, morning_time):
    # First we download the stock data from yahoo finance, for all the tickers.
    # Note: We add one day to the end date, since sometimes yahoo finance doesn't include the end date.
    df_every_60_min = download_from_yahoo(tickers, start, end + datetime.timedelta(days=1), '60m')
    df_every_60_min = pd.DataFrame(df_every_60_min)
    print("Direct from yfinance:")
    print(df_every_60_min)

    # We then use the extract_overnight_times_60_min function to extract the 
    # morning / afternoon times for each day into a dataframe. This dataframe will look like:
    #             10:30               15:00
    #             AAPL  TSLA ...       AAPL  TSLA ...
    # 01-01-2021  23    18             23.5  
    # 01-02-2021  25    19             23.2
    # 01-03-2021  24    18.5           24
    #    ...

    df_morning_afternoon = extract_overnight_times_60_min(df = df_every_60_min, morning_time = morning_time)
    # We then extract only the dates we want, to make sure there isn't extra stuff in the dataframe
    stock_price = df_morning_afternoon.loc[start:end, :]
    
    return stock_price