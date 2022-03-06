#!/usr/bin/env python3
# -*- coding: utf-8 -*-
''' 
MACD strategy. 
------------------------
Rules for strategy:
    1. Trade in direction of trend, as per 200EMA.
    2. Entry signal on MACD cross below/above zero line.
    3. Set stop loss at recent price swing.
    4. Target 1.5 take profit.
'''

# Import packages
import os
from finta import TA
import autotrader.indicators as indicators

class SimpleMACD:

    def __init__(self, params, data, pair):
        """Define all indicators used in the strategy.
        """
        self.name   = "Simple MACD Trend Strategy"
        self.data   = data
        self.params = params
        
        # 200EMA
        self.ema    = TA.EMA(data, params['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, self.params['MACD_fast'], 
                            self.params['MACD_slow'], self.params['MACD_smoothing'])
        self.MACD_CO        = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
        self.MACD_CO_vals   = indicators.cross_values(self.MACD.MACD, 
                                                      self.MACD.SIGNAL,
                                                      self.MACD_CO)
        
        # Price swings
        self.swings = indicators.find_swings(data)

        # Construct indicators dict for plotting
        self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                              'macd': self.MACD.MACD,
                                              'signal': self.MACD.SIGNAL},
                           'EMA (200)': {'type': 'MA',
                                         'data': self.ema}}
        
        
    def generate_signal(self, i, current_position):
        """Define strategy to determine entry signals.
        """
        
        order_type  = 'market'
        signal_dict = {}
        
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
        
        return signal_dict
    
    
    def generate_exit_levels(self, signal, i):
        """Function to determine stop loss and take profit levels.
        """
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
    
    
if __name__ == "__main__":
    from autotrader.autotrader import AutoTrader
    
    config = {'NAME': 'MACD Strategy',
              'MODULE': 'macd_strategy',
              'CLASS': 'SimpleMACD',
              'INTERVAL': '1h',
              'PERIOD': 300,
              'RISK_PC': 1.5,
              'SIZING': 'risk',
              'PARAMETERS': {'ema_period': 200,
                             'MACD_fast': 5,
                             'MACD_slow': 19,
                             'MACD_smoothing': 9,
                             'RR': 1.5},
              'WATCHLIST': ['EURUSD=X'],}
    home_dir = os.getcwd()
    
    at = AutoTrader()
    at.configure(verbosity=1, show_plot=True)
    at.add_strategy(config_dict=config, strategy=SimpleMACD)
    at.plot_settings(show_cancelled=False)
    # at.add_data({'EUR_USD': 'EU.csv'})
    at.backtest(start = '1/1/2022',
                end = '1/3/2022',
                initial_balance=1000,
                leverage=30,
                spread=0.5,
                commission=0.005)
    at.run()