import requests
import numpy as np
import pandas as pd
import multiprocessing
from datetime import datetime, timedelta, time

def chunks(xs, chunk_size):
  n = len(xs)
  leftover = n % chunk_size
  if leftover == 0:
    num_chunks = n // chunk_size
  else:
    num_chunks = n // chunk_size + 1
  
  return [xs[(c*chunk_size):(c*chunk_size + chunk_size)] for c in range(num_chunks)]

class AlpacaV1Downloader:
  def __init__(self, api_key, api_secret_key):
    self.headers = {
      'APCA-API-KEY-ID': api_key,
      'APCA-API-SECRET-KEY': api_secret_key
    }

  def download_bars(self, symbols, start, end, interval):
    assert 1 <= len(symbols) and len(symbols) <= 200

    endpoint = "https://data.alpaca.markets/v1/bars/{}".format(interval)
    start_str = start.isoformat() + "-04:00"
    end_str = end.isoformat() + "-04:00"
    
    params = {
      'symbols': ",".join(symbols),
      'limit': 1000,
      'start': start_str,
      'end': end_str
    }
    response = requests.get(endpoint, headers=self.headers, params=params).json()
    dataframes = [
      pd.DataFrame({
          s: [bar['o'] for bar in response[s]]
        }, 
        index=[datetime.fromtimestamp(bar['t']) for bar in response[s]]
      ) 
      for s in symbols
    ]
    df = pd.concat(dataframes, axis=1)

    if df.shape[0] > 1000:
      df = df.iloc[(df.shape[0] - 1000):]

    return df

  def download_full_history(self, symbols, start, end, interval):
    assert 1 <= len(symbols) and len(symbols) <= 200

    if interval == '15Min':
      dt = timedelta(minutes=15)
    else:
      assert "Unknown interval: " + interval
    
    incomplete_here_back = end
    df = None

    while incomplete_here_back >= start:
      print("Downloading {} -> {}".format(start, incomplete_here_back))
      new_df = self.download_bars(symbols, start, incomplete_here_back, interval)
      if new_df.shape[0] == 0:
        break

      earliest_time = new_df.index[0]
      latest_time = new_df.index[-1]
      print("Received    {} -> {}".format(earliest_time, latest_time))

      df = pd.concat([new_df, df]) # merge new_df and df
      incomplete_here_back = earliest_time - dt
    
    return df


  def get_prices(self, symbols, start, end, interval='15Min'):
    symbol_chunks = chunks(symbols, 200)

    download_full_history_lambda = Closure(closure_converted_download_lambda, the_self=self, start=start, end=end, interval=interval)

    # with multiprocessing.Pool() as pool:
    #   dataframes = pool.map(download_full_history_lambda, symbol_chunks)

    dataframes = list(map(download_full_history_lambda, symbol_chunks))

    df = pd.concat(dataframes, axis=1)

    index_times = df.index.map(lambda dt: dt.time())
    start_time = time(hour=9, minute=30)
    end_time = time(hour=15, minute=30)
    df = df[np.logical_and(start_time <= index_times, index_times <= end_time)]
    
    return df

class Closure:
  def __init__(self, func, **kwargs):
    self.func = func
    self.env = kwargs
  
  def __call__(self, x):
    return self.func(self.env, x)

def closure_converted_download_lambda(env, chunk_of_symbols):
  return env['the_self'].download_full_history(chunk_of_symbols, env['start'], env['end'], env['interval'])

