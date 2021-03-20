import subprocess
import pandas as pd
import numpy as np
import datetime
from pytz import timezone
import stockdata


# def choose_std_filter_limit(days, rank):
#     if days <= 10:
#         std_cutoff = 0.05
#
#     elif 10 < days and days <= 40:
#         std_cutoff = ...
#     elif ...:
#     else:
#         ...
#
#
#     for ticker in rank:
#         if rank[ticker]['std_profit_ratio'] <= std_cutoff:
#             append ticker
#         else:
#             if sum <= ...:
#                 append ticker
#             else:
#                 pass
#     return ___

def check_increased_gain(prices_morning, prices_afternoon):
    first_idx = prices_morning.first_valid_index()
    last_idx = prices_afternoon.last_valid_index()
    if (first_idx is None) or (last_idx is None):
        return False
    elif first_idx > last_idx: # This means that we downloaded some messed up data, so filter out this stock
        return False
    else:
        return prices_morning[first_idx] < prices_afternoon[last_idx]

# Note: it must be that stock_price contains at least enough days of data for the days parameter
def ranking(stock_price, start_day):
    # Create Dictionary
    stock_price = stock_price.loc[start_day:]

    # filter the stocks with increased gain
    all_downloaded_tickers = stock_price['10:30'].columns.values
    filtered_tickers = [c for c in all_downloaded_tickers if check_increased_gain(stock_price['10:30'][c], stock_price['15:00'][c])]

    # filtered_tickers = [c for c in stock_price['10:30'].columns.values if increasedgain_index[c]]

    stats = pd.DataFrame(columns=['mean_profit_ratio', 'std_profit_ratio', 'sum_profit_ratio'])
    for ticker in filtered_tickers:
        day_profit = (stock_price['15:00', ticker].iloc[1:].values - stock_price['10:30', ticker].iloc[:-1].values) / stock_price['10:30', ticker].iloc[:-1].values
        num_non_nan = day_profit.shape[0] - np.isnan(day_profit).sum()
        if num_non_nan <= 1:
            # If we have only 0 or 1 day(s) of data, then filter it out, since we can't calculate STD
            continue

        mean_profit_ratio = np.nanmean(day_profit)
        std_profit_ratio = np.nanstd(day_profit)
        sum_profit_ratio = np.nanprod(1 + day_profit) - 1  # np.prod multiply everything in the array

        stats.loc[ticker] = [mean_profit_ratio, std_profit_ratio, sum_profit_ratio]


    stats_bymean = stats.sort_values(by="mean_profit_ratio", ascending=False)

    return stats_bymean


def main():
    tickers = stockdata.get_all_tickers()
    tickers = tickers[:200]
    # print(tickers)

    eastern = timezone('US/Eastern')
    loc_dt = datetime.datetime.now(eastern)
    today = loc_dt.date()

    days_ago_5 = today - datetime.timedelta(days=5)
    days_ago_30 = today - datetime.timedelta(days=30)

    stock_price = stockdata.fetch_stock_data(tickers, min(days_ago_5, days_ago_30), today)

    stats_bymean_5 = ranking(stock_price=stock_price, start_day=days_ago_5)
    stats_bymean_30 = ranking(stock_price=stock_price, start_day=days_ago_30)

    print(stats_bymean_5)
    print(stats_bymean_30)



if __name__ == "__main__":
    main()