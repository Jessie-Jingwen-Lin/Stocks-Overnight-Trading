import subprocess
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
from pytz import timezone
import sys
import pickle

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

def download_from_yahoo(tickers, start, end, interval):
    if sys.platform == 'darwin':
        threads = 32
    else:
        threads = 8

    print('downloading {} stocks from {} to {} using {} threads'.format(len(tickers), start, end, threads))
    return yf.download(tickers, start=start, end=end, interval=interval, threads=threads)

def extract_overnight_times_60_min(df):
    df = df["Open"]

    tenthirty_index = df.index.map(lambda date_time: date_time.hour == 10 and date_time.minute == 30 and date_time.second == 0)
    two_thirty_index = df.index.map(lambda date_time: date_time.hour == 14 and date_time.minute == 30 and date_time.second == 0)

    prices_morning = df.loc[tenthirty_index, :].copy()
    prices_morning.index = prices_morning.index.map(lambda date_time: date_time.date())

    prices_two_thirty = df.loc[two_thirty_index, :].copy()
    prices_two_thirty.index = prices_two_thirty.index.map(lambda date_time: date_time.date())

    prices_afternoon = prices_two_thirty

    morning_tuples_index = [('10:30', tup) for tup in prices_morning.columns.values]
    afternoon_tuples_index = [('15:00', tup) for tup in prices_afternoon.columns.values]

    morning_index = pd.MultiIndex.from_tuples(morning_tuples_index)
    afternoon_index = pd.MultiIndex.from_tuples(afternoon_tuples_index)

    prices_morning.columns = morning_index
    prices_afternoon.columns = afternoon_index

    combined = pd.concat([prices_morning, prices_afternoon], axis=1)

    return combined

def fetch_stock_data(tickers, start, end):
    # First we download the stock data from yahoo finance, for all the tickers.
    # Note: We add one day to the end date, since sometimes yahoo finance doesn't include the end date.
    df_every_60_min = download_from_yahoo(tickers, start, end + datetime.timedelta(days=1), '60m')


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
