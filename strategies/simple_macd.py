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
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
pio.renderers.default = 'browser'
import pandas as pd
from lib import indicators

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
        
        # Price swings
        self.swings         = indicators.find_swings(data)
        
        # Path variables
        strat_dir       = os.path.dirname(os.path.abspath(__file__))
        self.home_dir   = os.path.join(strat_dir, '..')
        

    def generate_signal(self, i, current_position):
        ''' Define strategy to determine entry signals '''
        
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
    
    
    def create_backtest_chart(self, pair, interval, trade_summary, pf_df):
        # Generate chart
        fig = make_subplots(rows = 3, cols = 1,
                            shared_xaxes = True,
                            vertical_spacing = 0.02,
                            row_heights = [0.3, 0.5, 0.2]
                            )
        
        # Portfolio balance
        fig.add_trace(go.Scatter(x = pf_df.index, 
                                 y = pf_df.Balance.values, 
                                 line = dict(color = 'blue', 
                                             width = 1), 
                                 name = 'Portfolio Balance'),
                      row = 1,
                      col = 1
                      )
        
        # Price chart
        fig.add_trace(go.Candlestick(x = self.data.index[-self.params['view_window']:],
                                     open = self.data['Open'],
                                     high = self.data['High'],
                                     low  = self.data['Low'],
                                     close= self.data['Close'], 
                                     name = 'market data'
                                     ),
                      row = 2,
                      col = 1
                      )
        
        # Moving averages
        fig.add_trace(go.Scatter(x      = self.data.index[-self.params['view_window']:], 
                                 y      = self.ema[-self.params['view_window']:], 
                                 line   = dict(color='orange', 
                                               width=1
                                               ), 
                                 name='200EMA'),
                      row = 2,
                      col = 1
                      )
        
        # Backtesting signals
        profitable_longs        = trade_summary[(trade_summary['Profit'] > 0) 
                                                & (trade_summary['Size'] > 0)]
        profitable_shorts       = trade_summary[(trade_summary['Profit'] > 0) 
                                                & (trade_summary['Size'] < 0)]
        unprofitable_longs      = trade_summary[(trade_summary['Profit'] < 0) 
                                                & (trade_summary['Size'] > 0)]
        unprofitable_shorts     = trade_summary[(trade_summary['Profit'] < 0) 
                                                & (trade_summary['Size'] < 0)]
        stop_losses             = trade_summary.Stop_loss
        take_profits            = trade_summary.Take_profit
        entry_times             = pd.to_datetime(trade_summary.Entry_time.values, 
                                                 utc=True)
        exit_times              = list(trade_summary.Exit_time)
        exit_prices             = trade_summary.Exit_price
        
        
        # Profitable long trades
        fig.add_trace(go.Scatter(x = pd.to_datetime(profitable_longs.Entry_time.values, utc=True), 
                                 y = profitable_longs.Entry.values, 
                                 mode = "markers",
                                 marker_symbol = 5,
                                 marker_size = 12,
                                 marker_line_width = 1,
                                 marker_color = 'lightgreen',
                                 name = 'Profitable long position entry',
                                 text = profitable_longs.Order_ID.values),
                      row = 2,
                      col = 1
                      )
        
        # Profitable short trades
        fig.add_trace(go.Scatter(x = pd.to_datetime(profitable_shorts.Entry_time.values, utc=True), 
                                 y = profitable_shorts.Entry.values, 
                                 mode="markers",
                                 marker_symbol = 6,
                                 marker_size = 12,
                                 marker_line_width = 1,
                                 marker_color = 'lightgreen',
                                 name = 'Profitable short position entry',
                                 text = profitable_shorts.Order_ID.values),
                      row = 2,
                      col = 1
                      )
        
        # Unprofitable long trades
        fig.add_trace(go.Scatter(x = pd.to_datetime(unprofitable_longs.Entry_time.values, utc=True), 
                                 y = unprofitable_longs.Entry.values, 
                                 mode="markers",
                                 marker_symbol = 5,
                                 marker_size = 12,
                                 marker_line_width = 1,
                                 marker_color = 'orangered',
                                 name = 'Unprofitable long position entry',
                                 text = unprofitable_longs.Order_ID.values),
                      row = 2,
                      col = 1
                      )
        
        # Unprofitable short trades
        fig.add_trace(go.Scatter(x = pd.to_datetime(unprofitable_shorts.Entry_time.values, utc=True), 
                                 y = unprofitable_shorts.Entry.values, 
                                 mode="markers",
                                 marker_symbol = 6,
                                 marker_size = 12,
                                 marker_line_width = 1,
                                 marker_color = 'orangered',
                                 name = 'Unprofitable short position entry',
                                 text = unprofitable_shorts.Order_ID.values),
                      row = 2,
                      col = 1
                      )
        
        # Stop loss levels
        fig.add_trace(go.Scatter(x = entry_times, 
                                  y = stop_losses.values, 
                                  mode="markers",
                                  marker_symbol = 41,
                                  marker_size = 12,
                                  marker_line_width = 1,
                                  marker_color = 'black',
                                  name = 'Stop loss level'),
                      row = 2,
                      col = 1
                      )
        
        # Take profit levels
        fig.add_trace(go.Scatter(x = entry_times, 
                                  y = take_profits.values, 
                                  mode="markers",
                                  marker_symbol = 41,
                                  marker_size = 12,
                                  marker_line_width = 1,
                                  marker_color = 'black',
                                  name = 'Stop loss level'),
                      row = 2,
                      col = 1
                      )
        
        # Position exits
        fig.add_trace(go.Scatter(x = exit_times,
                                 y = exit_prices.values, 
                                 mode="markers",
                                 marker_symbol = 0,
                                 marker_size = 5,
                                 marker_line_width = 1,
                                 marker_color = 'black',
                                 name = 'Position exit',
                                 text = trade_summary.Order_ID),
                      row = 2,
                      col = 1
                      )
        
        
        # RSI
        fig.add_trace(go.Scatter(x = self.data.index,
                                 y = self.MACD, 
                                 line = dict(color = 'blue',
                                             width = 1), 
                                 name = 'MACD'),
                      row = 3,
                      col = 1
                      )
        fig.add_trace(go.Scatter(x = self.data.index,
                                 y = self.MACDsignal, 
                                 line = dict(color = 'red',
                                             width = 1), 
                                 name = 'MACD signal'),
                      row = 3,
                      col = 1
                      )
        
        # fig.update_layout(hovermode="y unified")
        fig.update_layout(
                          title = "Backtest chart for {}/{} ({} candles) using {}".format(pair[:3], 
                                                                                        pair[-3:], 
                                                                                        interval,
                                                                                        self.name)
                          )
        
        # Hide weekends
        fig.update_xaxes(
                rangeslider_visible=False,
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                            ]
                        )
        
        if self.params['show_fig']:
            fig.show()