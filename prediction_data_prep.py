import pandas as pd
import numpy as np
import datetime
from pytz import timezone
import stockdata

def main():
  tickers = stockdata.get_all_tickers()
  # tickers = ["TSLA", "AAPL", "ABNB"]


  eastern = timezone('US/Eastern')
  loc_dt = datetime.datetime.now(eastern)
  today = loc_dt.date()

  #days_ago_1 = today - datetime.timedelta(days=1)
  # days_ago_6 = today - datetime.timedelta(days=6)
  days_ago_729 = today - datetime.timedelta(days=729)

  stock_price = stockdata.fetch_stock_data(tickers, days_ago_729, today)

  morning_df = stock_price['10:30']
  afternoon_df = stock_price['14:30']
  ticker_today_morning_prices = morning_df.iloc[1:].values
  ticker_yesterday_afternoon_prices = afternoon_df.iloc[:-1].values
  day_profit = (ticker_today_morning_prices - ticker_yesterday_afternoon_prices) / ticker_yesterday_afternoon_prices

  # overnight_gains = 

  print(stock_price)

  print(day_profit)

  with open('prediction_prep_data.npy', 'wb') as f:
    np.save(f, day_profit)




if __name__ == "__main__":
  main()