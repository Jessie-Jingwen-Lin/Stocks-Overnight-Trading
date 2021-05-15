import subprocess
import pandas as pd
import numpy as np
import datetime
from pytz import timezone
import stockdata
import pickle


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
    last_idx_3 = prices_afternoon.last_valid_index()
    last_idx_1030 = prices_morning.last_valid_index()

    first_price = None
    last_price = None
    if first_idx is not None:
        first_price = prices_morning[first_idx]

    if (last_idx_3 is not None) and (last_idx_1030 is not None):
        if last_idx_3 > last_idx_1030:
            last_price = prices_afternoon[last_idx_3]
        elif last_idx_3 < last_idx_1030:
            last_price = prices_morning[last_idx_1030]
        else: # (last_idx_3 == last_idx_1030)
            last_price = prices_afternoon[last_idx_3]
    elif (last_idx_3 is not None) and (last_idx_1030 is None):
        last_price = prices_afternoon[last_idx_3]
    elif (last_idx_3 is None) and (last_idx_1030 is not None):
        last_price = prices_morning[last_idx_1030]

    if (first_price is None) or (last_price is None):
        return False
    else:
        return first_price < last_price

# Note: it must be that stock_price contains at least enough days of data for the days parameter
def ranking(stock_price, start_day):
    
    # Create Dictionary
    stock_price = stock_price.loc[start_day:]

    # filter the stocks with increased gain

    morning_df = stock_price['10:30']
    afternoon_df = stock_price['14:30']
    all_downloaded_tickers = morning_df.columns.values

    #filtered_tickers = [c for c in all_downloaded_tickers if check_increased_gain(morning_df[c], afternoon_df[c])]

    # filtered_tickers = [c for c in stock_price['10:30'].columns.values if increasedgain_index[c]]


    stats_index = []
    stats_mean = []
    stats_std = []
    stats_sum = []

    stock_day_profit = {} # dictionary from ticker name to all day profit ratios

    for ticker in all_downloaded_tickers:
        ticker_today_morning_prices = morning_df[ticker].iloc[1:].values
        ticker_yesterday_afternoon_prices = afternoon_df[ticker].iloc[:-1].values

        day_profit = (ticker_today_morning_prices - ticker_yesterday_afternoon_prices) / ticker_yesterday_afternoon_prices
        num_non_nan = day_profit.shape[0] - np.isnan(day_profit).sum()
        if num_non_nan <= 1:
            # If we have only 0 or 1 day(s) of data, then filter it out, since we can't calculate STD
            continue

        mean_profit_ratio = np.nanmean(day_profit)
        std_profit_ratio = np.nanstd(day_profit)
        #sum_profit_ratio = np.nanprod(1 + day_profit) - 1  # np.prod multiply everything in the array
        sum_profit_ratio = np.nansum(day_profit)

        stats_index.append(ticker)
        stats_mean.append(mean_profit_ratio)
        stats_std.append(std_profit_ratio)
        stats_sum.append(sum_profit_ratio)
        stock_day_profit[ticker] = day_profit

    stats = pd.DataFrame({'mean_profit_ratio': stats_mean, 'std_profit_ratio': stats_std, 'sum_profit_ratio': stats_sum}, index=stats_index)
    day_profit_ratio = pd.DataFrame(stock_day_profit)
    # stats_bymean = stats.sort_values(by="mean_profit_ratio", ascending=False)

    return stats, day_profit_ratio


def df_to_list_of_dicts(df):
    stocks_data = []
    for i in range(0, df.shape[0]):
        stocks_data.append({'Stock': df.index[i], 'Mean_Profit_Ratio': df.iloc[i,0], 'Std_Profit_Ratio': df.iloc[i,1], 'Sum_Profit_Ratio': df.iloc[i,2]})
    return stocks_data

def main():
    tickers = stockdata.get_all_tickers()
    # # tickers = tickers[:100] + ['BFT.W']
    # # print(tickers)


    eastern = timezone('US/Eastern')
    loc_dt = datetime.datetime.now(eastern)
    today = loc_dt.date()

    #days_ago_1 = today - datetime.timedelta(days=1)
    days_ago_6 = today - datetime.timedelta(days=6)
    days_ago_30 = today - datetime.timedelta(days=30)
    days_ago_90 = today - datetime.timedelta(days=90)
    days_ago_365 = today - datetime.timedelta(days=365)
    days_ago_729 = today - datetime.timedelta(days=729)

    stock_price = stockdata.fetch_stock_data(tickers, min(days_ago_6, days_ago_30, days_ago_90, days_ago_365, days_ago_729), today)

    #Filter out tickers which have negative daily profit ratio for 1 week.
    bad_tickers = []
    day_profit_ratio_1w_df = ranking(stock_price=stock_price, start_day=days_ago_6)[1]
    for col_name in day_profit_ratio_1w_df:
        ticker_dpr = day_profit_ratio_1w_df[col_name]
        if sum((ticker_dpr >= 0) | (ticker_dpr.isnull() == True)) != len(ticker_dpr):
            bad_tickers.append(col_name)

    to_drop = [('10:30', to_drop) for to_drop in bad_tickers] + [('14:30', to_drop) for to_drop in bad_tickers]

    stock_price = stock_price.drop(columns=to_drop)
    # stock_price['10:30'] = stock_price['10:30'][new_ticker]
    # stock_price['14:30'] = stock_price['14:30'][new_ticker]

    print("Transformed data:")
    print(stock_price)
    print()
    print(stock_price['10:30'].isnull().sum(axis=1))
    print()
    print(len(stock_price['10:30'].columns))
    print()
    print(stock_price['10:30'].isnull().sum(axis=1)/len(stock_price['10:30'].columns))


    #stats_bymean_1 = ranking(stock_price=stock_price, start_day=days_ago_1)[0]
    stats_bymean_5 = ranking(stock_price=stock_price, start_day=days_ago_6)[0]
    stats_bymean_30 = ranking(stock_price=stock_price, start_day=days_ago_30)[0]
    stats_bymean_90 = ranking(stock_price=stock_price, start_day=days_ago_90)[0]
    stats_bymean_365 = ranking(stock_price=stock_price, start_day=days_ago_365)[0]
    stats_bymean_729 = ranking(stock_price=stock_price, start_day=days_ago_729)[0]

    #print(stats_bymean_30)
   
    data_for_webserver = {
        'datetime': loc_dt,
        #'stocks_data_1d': df_to_list_of_dicts(stats_bymean_1),
        'day_profit_1w_df': ranking(stock_price=stock_price, start_day=days_ago_6)[1],
        'day_profit_1m_df': ranking(stock_price=stock_price, start_day=days_ago_30)[1],
        'day_profit_3m_df': ranking(stock_price=stock_price, start_day=days_ago_90)[1],
        'day_profit_1y_df': ranking(stock_price=stock_price, start_day=days_ago_365)[1],
        'day_profit_2y_df': ranking(stock_price=stock_price, start_day=days_ago_729)[1],
        'stocks_data_1w_df': stats_bymean_5,
        'stocks_data_1m_df': stats_bymean_30,
        'stocks_data_3m_df': stats_bymean_90,
        'stocks_data_1y_df': stats_bymean_365,
        'stocks_data_2y_df': stats_bymean_729,
        'stocks_data_1w': df_to_list_of_dicts(stats_bymean_5),
        'stocks_data_1m': df_to_list_of_dicts(stats_bymean_30),
        'stocks_data_3m': df_to_list_of_dicts(stats_bymean_90),
        'stocks_data_1y': df_to_list_of_dicts(stats_bymean_365),
        'stocks_data_2y': df_to_list_of_dicts(stats_bymean_729),
        'stocks_data_mean_df': ((stats_bymean_5+stats_bymean_30+stats_bymean_90+stats_bymean_365+stats_bymean_729)/5).dropna(),
        'stocks_data_mean': df_to_list_of_dicts(((stats_bymean_5+stats_bymean_30+stats_bymean_90+stats_bymean_365+stats_bymean_729)/5).dropna())
    }

    # print(data_for_webserver['stocks_data_mean'])
 
    # Step 2: save that data to stocks_data.pickle
    with open('data_for_webserver.pkl', 'wb') as f:
        pickle.dump(data_for_webserver, f)



if __name__ == "__main__":
    main()
