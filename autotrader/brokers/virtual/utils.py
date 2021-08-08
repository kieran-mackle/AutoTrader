#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Utilities for virtual broker.

"""

import pandas as pd
import numpy as np
import talib as ta
from datetime import datetime

def response_to_df(response):
    ''' Function to convert api response into a pandas dataframe. '''
    
    candles = response.body["candles"]
    times = []
    close_price, high_price, low_price, open_price = [], [], [], []
    
    for candle in candles:
        times.append(candle.time)
        close_price.append(float(candle.mid.c))
        high_price.append(float(candle.mid.h))
        low_price.append(float(candle.mid.l))
        open_price.append(float(candle.mid.o))
    
    dataframe = pd.DataFrame({"Open": open_price, "High": high_price, "Low": low_price, "Close": close_price})
    dataframe.index = pd.to_datetime(times)
    
    return dataframe


def truncate(f, n):
    ''' Truncates a float f to n decimal places without rounding. '''
    s = '{}'.format(f)
    
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    
    return '.'.join([i, (d+'0'*n)[:n]])


def get_pip_ratio(pair):
    ''' Function to return pip value ($/pip) of a given pair. '''
    if pair[-3:] == 'JPY':
        pip_value = 1e-2
    else:
        pip_value = 1e-4
    
    return pip_value


def get_size(pair, amount_risked, price, stop_price, HCF):
    ''' Calculate position size based on account balance and risk profile. '''
    if np.isnan(stop_price):
        units               = amount_risked/(HCF*price)
    else:
        pip_value           = get_pip_ratio(pair)
        pip_stop_distance   = abs(price - stop_price) / pip_value
        if pip_stop_distance == 0:
            units           = 0
        else:
            quote_risk      = amount_risked / HCF
            price_per_pip   = quote_risk / pip_stop_distance
            units           = round(price_per_pip / pip_value)
    
    return units


def check_precision(pair, original_stop, original_take):
    ''' Modify stop/take based on pair for required ordering precision. ''' 
    if pair[-3:] == 'JPY':
        N = 3
    else:
        N = 5
    
    take_price      = float(truncate(original_take, N))
    stop_price      = float(truncate(original_stop, N))
    
    return stop_price, take_price


def interval_to_seconds(interval):
    '''Converts the interval to time in seconds'''
    letter = interval[0]
    
    if len(interval) > 1:
        number = float(interval[1:])
    else:
        number = 1
    
    conversions = {'S': 1,
                   'M': 60,
                   'H': 60*60,
                   'D': 60*60*24
                   }
    
    my_int = conversions[letter] * number
    
    return my_int


def create_trade_lists(pair, timestamps, closed_positions_dict):
    
    long_entry_times    = []
    long_entry_prices   = []
    long_stops          = []
    long_takes          = []
    
    short_entry_times   = []
    short_entry_prices  = []
    short_stops         = []
    short_takes         = []
    
    portfolio_balance   = []
    portfolio_times     = []
    
    for order in closed_positions_dict:
        if closed_positions_dict[order]['pair'] == pair:
            portfolio_balance.append(closed_positions_dict[order]['balance'])      
            portfolio_times.append(closed_positions_dict[order]['exit_time'])
            
            if closed_positions_dict[order]['size'] > 0:
                long_entry_times.append(closed_positions_dict[order]['entry_time'])
                long_entry_prices.append(closed_positions_dict[order]['entry_price'])
                long_stops.append(closed_positions_dict[order]['stop_price'])
                long_takes.append(closed_positions_dict[order]['take_price'])
            else:
                short_entry_times.append(closed_positions_dict[order]['entry_time'])
                short_entry_prices.append(closed_positions_dict[order]['entry_price'])
                short_stops.append(closed_positions_dict[order]['stop_price'])
                short_takes.append(closed_positions_dict[order]['take_price'])

    # TODO all of these could just be put into a dataframe...
    return long_entry_times, long_entry_prices, \
           long_stops, long_takes, short_entry_times, \
           short_entry_prices, short_stops, short_takes, \
           portfolio_balance, portfolio_times



def fix_dataframe(df1, df2):
    # Would be good to check which one is shorter, which is longer, then 
    # return both with corrections
    
    i1 = list(df1.index)
    i2 = list(df2.index)
    new_indices = list(set(i1) - set(i2))
    
    new_df = df2
    
    for index in new_indices:
        
        df_row = df1[df1.index == index]
        
        df_row.Open = None
        df_row.High = None
        df_row.Low = None
        df_row.Close = None
        
        new_df = new_df.append(df_row)
    
    new_df = new_df.sort_index()
    new_df = new_df.interpolate()
    
    return new_df
    
    # insert the row with new index
    # Sort df in ascending order to move new idices into position
    # interpolate to get values at new rows



def check_dataframes(df_1, df_2):
    '''Checks dataframe lengths and corrects if necessary'''
    
    if len(df_1) < len(df_2):
        new_df_1 = fix_dataframe(df_2, df_1)
        new_df_2 = df_2
    elif len(df_1) > len(df_2):
        new_df_2 = fix_dataframe(df_1, df_2)
        new_df_1 = df_1
        
    else:
        new_df_1 = df_1
        new_df_2 = df_2
    
    return new_df_1, new_df_2


def trade_summary(pair, closed_positions_dict):
    # Could also include a pairs list, and only input closed_pos dict
    order_ID    = []
    times_list  = []
    order_price = []
    entry_time  = []
    entry_price = []
    size        = []
    stop_price  = []
    take_price  = []
    profit      = []
    portfolio_balance = []
    exit_times  = []
    exit_prices = []
    trade_duration = []
    
    for order in closed_positions_dict:
        if closed_positions_dict[order]['pair'] == pair:
            order_ID.append(closed_positions_dict[order]['order_ID'])
            entry_time.append(closed_positions_dict[order]['entry_time'])
            times_list.append(closed_positions_dict[order]['order_time'])
            order_price.append(closed_positions_dict[order]['order_price'])
            entry_price.append(closed_positions_dict[order]['entry_price'])
            size.append(closed_positions_dict[order]['size'])
            stop_price.append(closed_positions_dict[order]['stop_price'])
            take_price.append(closed_positions_dict[order]['take_price'])
            profit.append(closed_positions_dict[order]['profit'])
            portfolio_balance.append(closed_positions_dict[order]['balance'])
            exit_times.append(closed_positions_dict[order]['exit_time'])
            exit_prices.append(closed_positions_dict[order]['exit_price'])
            if type(closed_positions_dict[order]['exit_time']) == str:
                exit_dt     = datetime.strptime(closed_positions_dict[order]['exit_time'],
                                                "%Y-%m-%d %H:%M:%S%z")
                entry_dt    = datetime.strptime(closed_positions_dict[order]['entry_time'],
                                                "%Y-%m-%d %H:%M:%S%z")
                trade_duration.append(exit_dt.timestamp() - entry_dt.timestamp())
            else:
                trade_duration.append(closed_positions_dict[order]['exit_time'].timestamp() - 
                                      closed_positions_dict[order]['entry_time'].timestamp())
            
    dataframe = pd.DataFrame({"Order_ID": order_ID, "Order_price": order_price,
                              "Entry_time": entry_time,
                              "Entry": entry_price, "Size": size,
                              "Stop_loss": stop_price, "Take_profit": take_price,
                              "Profit": profit, "Balance": portfolio_balance,
                              "Exit_time": exit_times, "Exit_price": exit_prices,
                              "Trade_duration": trade_duration})
    dataframe.index = pd.to_datetime(times_list)
    dataframe = dataframe.sort_index()
    
    return dataframe

def cancelled_order_summary(pair, closed_positions_dict):
    order_ID    = []
    times_list  = []
    order_price = []
    size        = []
    stop_price  = []
    take_price  = []
    
    for order in closed_positions_dict:
        if closed_positions_dict[order]['pair'] == pair:
            order_ID.append(closed_positions_dict[order]['order_ID'])
            times_list.append(closed_positions_dict[order]['order_time'])
            order_price.append(closed_positions_dict[order]['order_price'])
            size.append(closed_positions_dict[order]['size'])
            stop_price.append(closed_positions_dict[order]['stop'])
            take_price.append(closed_positions_dict[order]['take'])
            
    dataframe = pd.DataFrame({"Order_ID": order_ID, 
                              "Order_price": order_price,
                              "Size": size,
                              "Stop_loss": stop_price, 
                              "Take_profit": take_price})
    dataframe.index = pd.to_datetime(times_list)
    dataframe = dataframe.sort_index()
    
    return dataframe
    

def reconstruct_portfolio(initial_balance, trade_summary, time_index):
    a = trade_summary.Exit_time.values
    
    profit_list = trade_summary.Profit.values.tolist()
    new_df = pd.DataFrame({"Profit": profit_list})
    new_df.index = pd.to_datetime(a, utc=True)
    
    balance   = initial_balance
    portfolio = []
    
    for timestamp in time_index:
        if timestamp in new_df.index:
            # Check if timestamp appears in multiple closed positions
            profit_vals = new_df.Profit[new_df.index == timestamp].values
            profit = 0
            for trade_profit in profit_vals:
                profit += trade_profit
            
        else:
            profit = 0
        
        balance += profit
        portfolio.append(balance)
    
    dataframe = pd.DataFrame({"Balance": portfolio})
    dataframe.index = pd.to_datetime(time_index)
    dataframe = dataframe.sort_index()
    
    return dataframe


def trade_correlation(data, trade_summary):
    
    # Calculate indicators
    RSI         = ta.RSI(data.Close, timeperiod=14)
    ADX14       = ta.ADX(data.High, data.Low, data.Close, timeperiod=14)
    ADX200      = ta.ADX(data.High, data.Low, data.Close, timeperiod=200)
    sk, sd      = ta.STOCH(data.High, data.Low, data.Close)
    fk, fd      = ta.STOCHF(data.High, data.Low, data.Close)
    
    # Extract relevant data
    RSI_traded  = []
    ADX14_traded  = []
    ADX200_traded  = []
    sk_traded   = []
    sd_traded   = []
    fk_traded   = []
    fd_traded   = []
    
    for timestamp in data.index:
        if timestamp in trade_summary.index:
            RSI_traded.append(RSI[RSI.index == timestamp].values[0])
            ADX14_traded.append(ADX14[ADX14.index == timestamp].values[0])
            ADX200_traded.append(ADX200[ADX200.index == timestamp].values[0])
            sk_traded.append(sk[sk.index == timestamp].values[0])
            sd_traded.append(sd[fk.index == timestamp].values[0])
            fk_traded.append(fk[RSI.index == timestamp].values[0])
            fd_traded.append(fd[RSI.index == timestamp].values[0])
    
    # Construct correlation dataframe
    indicator_df = pd.DataFrame({"RSI": RSI_traded, "ADX_14": ADX14_traded,
                                 "ADX_200": ADX200_traded})
    indicator_df.index = trade_summary.index
    
    extended_trade_summary = trade_summary.merge(indicator_df,
                                                 left_index=True,
                                                 right_index=True)
    
    return extended_trade_summary

# def get_correlation(extended_trade_summary, indicator, ):
    
def get_streaks(trade_summary):
    
    profit_list             = trade_summary.Profit.values
    longest_winning_streak  = 1
    longest_losing_streak   = 1
    streak                  = 1
    
    for i in range(1, len(profit_list)):
        if np.sign(profit_list[i]) == np.sign(profit_list[i-1]):
            streak += 1
            
            if np.sign(profit_list[i]) > 0:
                # update winning streak
                longest_winning_streak  = max(longest_winning_streak, streak)
            else:
                # Update losing 
                longest_losing_streak   = max(longest_losing_streak, streak)

        else:
            streak = 1
    
    return longest_winning_streak, longest_losing_streak

