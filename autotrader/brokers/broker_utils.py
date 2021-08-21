# -*- coding: utf-8 -*-
"""
Broker Utilities SuperClass

"""

import pandas as pd
import numpy as np
from datetime import datetime
import os


class BrokerUtils:
    
    def __init__(self):
        return
    
    def response_to_df(self, response):
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
    
    
    def truncate(self, f, n):
        ''' Truncates a float f to n decimal places without rounding. '''
        s = '{}'.format(f)
        
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        
        return '.'.join([i, (d+'0'*n)[:n]])
    
    
    def get_pip_ratio(self, pair):
        ''' Function to return pip value ($/pip) of a given pair. '''
        if pair[-3:] == 'JPY':
            pip_value = 1e-2
        else:
            pip_value = 1e-4
        
        return pip_value
    
    
    def get_size(self, pair, amount_risked, price, stop_price, HCF, stop_distance = None):
        ''' Calculate position size based on account balance and risk profile. '''
        if stop_price is None and stop_distance is None:
            # No stop loss being used, instead risk portion of account
            units               = amount_risked/(HCF*price)
        else:
            pip_value           = self.get_pip_ratio(pair)
            
            if stop_price is None:
                pip_stop_distance = stop_distance
            else:
                pip_stop_distance = abs(price - stop_price) / pip_value
            
            
            if pip_stop_distance == 0:
                units           = 0
            else:
                quote_risk      = amount_risked / HCF
                price_per_pip   = quote_risk / pip_stop_distance
                units           = round(price_per_pip / pip_value)
        
        return units
    
    
    def check_precision(self, pair, original_stop, original_take):
        ''' Modify stop/take based on pair for required ordering precision. ''' 
        if pair[-3:] == 'JPY':
            N = 3
        else:
            N = 5
        
        take_price      = float(self.truncate(original_take, N))
        stop_price      = float(self.truncate(original_stop, N))
        
        return stop_price, take_price
    
    
    def interval_to_seconds(self, interval):
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
    
    def write_to_order_summary(self, order_details, filepath):
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
        trigger_price       = order_details["order_price"]
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
        
    
    def check_dataframes(self, df_1, df_2):
        '''Checks dataframe lengths and corrects if necessary'''
        
        if len(df_1) < len(df_2):
            new_df_1 = self.fix_dataframe(df_2, df_1)
            new_df_2 = df_2
        elif len(df_1) > len(df_2):
            new_df_2 = self.fix_dataframe(df_1, df_2)
            new_df_1 = df_1
            
        else:
            new_df_1 = df_1
            new_df_2 = df_2
        
        return new_df_1, new_df_2
    
    def fix_dataframe(self, df1, df2):
        ''' 
        Makes sure that the quote data and data dataframes are the same
        lenght.
        '''
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
    
    def trade_summary(self, pair, closed_positions_dict):
        ''' Creates backtest trade summary dataframe. '''
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
            if closed_positions_dict[order]['instrument'] == pair:
                order_ID.append(closed_positions_dict[order]['order_ID'])
                entry_time.append(closed_positions_dict[order]['time_filled'])
                times_list.append(closed_positions_dict[order]['order_time'])
                order_price.append(closed_positions_dict[order]['order_price'])
                entry_price.append(closed_positions_dict[order]['entry_price'])
                size.append(closed_positions_dict[order]['size'])
                stop_price.append(closed_positions_dict[order]['stop_loss'])
                take_price.append(closed_positions_dict[order]['take_profit'])
                profit.append(closed_positions_dict[order]['profit'])
                portfolio_balance.append(closed_positions_dict[order]['balance'])
                exit_times.append(closed_positions_dict[order]['exit_time'])
                exit_prices.append(closed_positions_dict[order]['exit_price'])
                if type(closed_positions_dict[order]['exit_time']) == str:
                    exit_dt     = datetime.strptime(closed_positions_dict[order]['exit_time'],
                                                    "%Y-%m-%d %H:%M:%S%z")
                    entry_dt    = datetime.strptime(closed_positions_dict[order]['time_filled'],
                                                    "%Y-%m-%d %H:%M:%S%z")
                    trade_duration.append(exit_dt.timestamp() - entry_dt.timestamp())
                else:
                    trade_duration.append(closed_positions_dict[order]['exit_time'].timestamp() - 
                                          closed_positions_dict[order]['time_filled'].timestamp())
                
        dataframe = pd.DataFrame({"Order_ID": order_ID, 
                                  "Order_price": order_price,
                                  "Order_time": times_list,
                                  "Entry_time": entry_time,
                                  "Entry": entry_price, "Size": size,
                                  "Stop_loss": stop_price, "Take_profit": take_price,
                                  "Profit": profit, "Balance": portfolio_balance,
                                  "Exit_time": exit_times, "Exit_price": exit_prices,
                                  "Trade_duration": trade_duration})
        dataframe.index = pd.to_datetime(entry_time)
        dataframe = dataframe.sort_index()
        
        return dataframe
    
    def cancelled_order_summary(self, pair, positions_dict):
        ''' Creates cancelled order summary dataframe. '''
        order_ID    = []
        times_list  = []
        order_price = []
        size        = []
        stop_price  = []
        take_price  = []
        
        for order in positions_dict:
            if positions_dict[order]['instrument'] == pair:
                order_ID.append(positions_dict[order]['order_ID'])
                times_list.append(positions_dict[order]['order_time'])
                order_price.append(positions_dict[order]['order_price'])
                size.append(positions_dict[order]['size'])
                stop_price.append(positions_dict[order]['stop_loss'])
                take_price.append(positions_dict[order]['take_profit'])
                
        dataframe = pd.DataFrame({"Order_ID": order_ID, 
                                  "Order_price": order_price,
                                  "Size": size,
                                  "Stop_loss": stop_price, 
                                  "Take_profit": take_price})
        dataframe.index = pd.to_datetime(times_list)
        dataframe = dataframe.sort_index()
        
        return dataframe
        
    def open_order_summary(self, pair, positions_dict):
        ''' Creates open order summary dataframe. '''
        order_ID    = []
        times_list  = []
        order_price = []
        size        = []
        stop_price  = []
        take_price  = []
        entry_time  = []
        entry_price = []
        
        for order in positions_dict:
            if positions_dict[order]['instrument'] == pair:
                order_ID.append(positions_dict[order]['order_ID'])
                times_list.append(positions_dict[order]['order_time'])
                order_price.append(positions_dict[order]['order_price'])
                size.append(positions_dict[order]['size'])
                stop_price.append(positions_dict[order]['stop_loss'])
                take_price.append(positions_dict[order]['take_profit'])
                entry_time.append(positions_dict[order]['time_filled'])
                entry_price.append(positions_dict[order]['entry_price'])
                
                
        dataframe = pd.DataFrame({"Order_ID": order_ID, 
                                  "Order_price": order_price,
                                  "Order_time": times_list,
                                  "Size": size,
                                  "Stop_loss": stop_price, 
                                  "Take_profit": take_price,
                                  "Entry_time": entry_time,
                                  "Entry": entry_price})
        dataframe.index = pd.to_datetime(entry_time)
        dataframe = dataframe.sort_index()
        
        return dataframe
    
    def get_streaks(self, trade_summary):
        ''' Calculates longest winning and losing streaks from trade summary. '''
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


    def reconstruct_portfolio(self, initial_balance, trade_summary, time_index):
        ''' REDUNDANT '''
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