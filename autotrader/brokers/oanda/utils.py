#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Utility functions for Oanda.
----------------------------

"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import os

def response_to_df(response):
    ''' Function to convert api response into a pandas dataframe. '''
    
    candles = response.body["candles"]
    times = []
    close_price, high_price, low_price, open_price = [], [], [], []
    
    for candle in candles:
        if candle.complete == True:
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
    pip_value           = get_pip_ratio(pair)
    pip_stop_distance   = abs(price - stop_price) / pip_value
    quote_risk          = amount_risked / HCF
    price_per_pip       = quote_risk / pip_stop_distance    
    units               = round(price_per_pip / pip_value)
    
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

def update_data_with_candle(data, latest_candle):
    ''' Appends the latest candle to the data. '''
    # latest candle will be in the form of a list.
    # [time, Open, High, Low, Close]
    # Need to convert this to a df.
    # latest_candle = ['2021-06-14 02:54:30', 1.20994, 1.20994, 1.20994, 1.20994]
    candle_time = datetime.strptime(latest_candle[0],
                                    '%Y-%m-%d %H:%M:%S')
    
    candle = pd.DataFrame({"Open": latest_candle[1], 
                      "High": latest_candle[2], 
                      "Low": latest_candle[3],
                      "Close": latest_candle[4]},
                      index=[candle_time])
    new_data = pd.concat([data, candle])
    
    return new_data

def last_period(current_time, granularity, current_candle = False):
    ''' 
        Returns a datetime object corresponding to the last candle that closed,
        based on the current time and the granularity of the candle.
        
        Note: if the current time is 10:15:01, the instrument will have just 
        begun forming the 10:15 candle. As such, the latest candle in the 
        instruments price history is the 10:00 candle, as that is the last 
        candle that has closed.
        
    '''    
    
    letter_to_unit = {'S': 'second',
                      'M': 'minute',
                      'H': 'hour',
                      'D': 'day'}
    
    letter = granularity[0]
    if len(granularity) > 1:
        number = int(granularity[1:])
    else:
        number = 1
    
    current_period      = getattr(current_time, letter_to_unit[letter])
    if current_candle:
        last_period         = number * np.floor(current_period/number)
    else:
        last_period         = number * np.floor(current_period/number) - number
    
    if letter == 'S':
        td = timedelta(microseconds = current_time.microsecond,
                       seconds = current_time.second - last_period)
    elif letter == 'M':
        td = timedelta(microseconds = current_time.microsecond,
                       seconds = current_time.second,
                       minutes = current_time.minute - last_period)
    elif letter == 'H':
        td = timedelta(microseconds = current_time.microsecond,
                       seconds = current_time.second,
                       minutes = current_time.minute,
                       hours = current_time.hour - last_period)
    elif letter == 'H':
        td = timedelta(microseconds = current_time.microsecond,
                       seconds = current_time.second,
                       minutes = current_time.minute,
                       hours = current_time.hour,
                       days = current_time.day - last_period)
        
    last_candle_closed = current_time - td
    
    return last_candle_closed

def write_to_order_summary(order_details, filepath):
    ''' Writes order details to summary file. '''
    
    # Check if file exists already, if not, create
    if not os.path.exists(filepath):
        f = open(filepath, "w")
        f.write("order time, strategy, granularity, order_type, instrument, order_size, ")
        f.write("trigger_price, stop_loss, take_profit\n")
        f.close()
    
    order_time          = order_details["order_time"]
    strategy            = order_details["strategy"]
    order_type          = order_details["order_type"]
    instrument          = order_details["instrument"]
    size                = order_details["size"]
    trigger_price       = order_details["price"]
    stop_loss           = order_details["stop_loss"]
    take_profit         = order_details["take_profit"]
    granularity         = order_details["granularity"]
    
    f                   = open(filepath, "a")
    f.write("{}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(order_time, strategy, 
                                                          granularity, order_type, 
                                                          instrument, size, 
                                                          trigger_price, stop_loss, 
                                                          take_profit))
    f.close()
    

def trade_summary(raw_livetrade_summary, ohlc_data, granularity):
    ''' Constructs trade summary dataframe from Oanda trade history. '''
    
    # Need to create a new coloumn with ohlc_data int index
    # and reutrn new trade summary, after using last_period function
    # Will also need to round the trade summary times to the nearest granularity
    
    # Create ohlc_data int index
    modified_data           = ohlc_data
    modified_data['date']   = modified_data.index
    modified_data           = modified_data.reset_index(drop = True)
    modified_data['data_index'] = modified_data.index
    
    # Round trade summary times to nearest candle
    rounded_times           = [last_period(dt, 'M15', current_candle=True) \
                               for dt in pd.to_datetime(raw_livetrade_summary.Date.values, utc=True)]
    
    # Reset trade summary and add rounded times
    raw_livetrade_summary   = raw_livetrade_summary.reset_index()
    raw_livetrade_summary['Date'] = rounded_times
    
    # Merge to preserve data int index
    livetrade_summary       = pd.merge(modified_data, raw_livetrade_summary, left_on='date', right_on='Date')
    
    return livetrade_summary


def format_watchlist(raw_watchlist):
    
    watchlist = []
    for instrument in raw_watchlist:
        if str(instrument) != 'nan':
            formatted_instrument = instrument[:3] + "_" + instrument[-3:]
            watchlist.append(formatted_instrument)
    
    return watchlist