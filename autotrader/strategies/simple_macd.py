#!/usr/bin/env python3
# -*- coding: utf-8 -*-
''' 

Simple MACD strategy. 
------------------------
Rules for strategy:
    1. Trade in direction of trend, as per 200EMA.
    2. Entry signal on MACD cross below/above zero line.
    3. Set stop loss at recent price swing.
    4. Target 1.5 take profit.

'''

# Import packages
import talib
from autotrader.lib import indicators

# Path management
import os


class SimpleMACD:

    def __init__(self, params, data, pair):
        ''' Define all indicators used in the strategy '''
        self.name   = "Simple MACD Trend Strategy"
        self.data   = data
        self.params = params
        
        # 200EMA
        self.ema    = talib.EMA(data.Close.values, params['ema_period'])
        
        # MACD
        self.MACD, self.MACDsignal, self.MACDhist = talib.MACD(data['Close'].values, 
                                                  self.params['MACD_fast'], 
                                                  self.params['MACD_slow'], 
                                                  self.params['MACD_smoothing']
                                                  )
        self.MACD_CO        = indicators.crossover(self.MACD, self.MACDsignal)
        self.MACD_CO_vals   = indicators.cross_values(self.MACD, 
                                                      self.MACDsignal,
                                                      self.MACD_CO)
        # Construct indicators dict for plotting
        self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                              'macd': self.MACD,
                                              'signal': self.MACDsignal,
                                              'histogram': self.MACDhist},
                           'EMA (200)': {'type': 'EMA',
                                         'data': self.ema}}
        
        # Price swings
        self.swings         = indicators.find_swings(data)
        
        # Path variables
        strat_dir       = os.path.dirname(os.path.abspath(__file__))
        self.home_dir   = os.path.join(strat_dir, '..')
        

    def generate_signal(self, i, current_position):
        ''' Define strategy to determine entry signals '''
        
        order_type  = 'market'
        signal_dict = {}
        related_orders  = None
        
        if self.data.Close.values[i] > self.ema[i] and \
            self.MACD_CO[i] == 1 and \
            self.MACD_CO_vals[i] < 0:
                signal = 1
                
        elif self.data.Close.values[i] < self.ema[i] and \
            self.MACD_CO[i] == -1 and \
            self.MACD_CO_vals[i] > 0:
                signal = -1

        else:
            signal = 0
        
        # Calculate exit targets
        exit_dict = self.generate_exit_levels(signal, i)
        
        # Construct signal dictionary
        signal_dict["order_type"]   = order_type
        signal_dict["direction"]    = signal
        signal_dict["stop_loss"]    = exit_dict["stop_loss"]
        signal_dict["stop_type"]    = exit_dict["stop_type"]
        signal_dict["take_profit"]  = exit_dict["take_profit"]
        signal_dict["related_orders"] = related_orders
        
        return signal_dict
    
    
    def generate_exit_levels(self, signal, i):
        ''' Function to determine stop loss and take profit levels '''
        
        stop_type   = 'limit'
        RR          = self.params['RR']
        
        if signal == 0:
            stop    = None
            take    = None
        else:
            if signal == 1:
                stop    = self.swings.Lows[i]
                take    = self.data.Close[i] + RR*(self.data.Close[i] - stop)
            else:
                stop    = self.swings.Highs[i]
                take    = self.data.Close[i] - RR*(stop - self.data.Close[i])
                
        
        exit_dict   = {'stop_loss'    : stop, 
                       'stop_type'    : stop_type,
                       'take_profit'  : take}
        
        return exit_dict
    