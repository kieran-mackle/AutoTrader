#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTrader strategy template.
"""

# Import packages
import talib
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
pio.renderers.default = 'browser'
import pandas as pd

# Path management
import os


class StrategyClass:

    def __init__(self, params, data, pair):
        ''' Define all indicators used in the strategy '''
        self.name   = "Strategy name"
        self.data   = data
        self.params = params
        
        # Path variables
        strat_dir       = os.path.dirname(os.path.abspath(__file__))
        self.home_dir   = os.path.join(strat_dir, '..')
        

    def generate_signal(self, i, current_position):
        ''' Define strategy to determine entry signals '''
        
        # In this example, the strategy will place market orders.
        # Other order types are:
            # limit - to place a limit order
            # close - to close the current_position
        order_type  = 'market'
        signal_dict = {}
        
        # Put entry strategy here
        signal      = 0
        
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
        
        # Put exit strategy here
        stop = 0
        take = 0
        stop_type = 'limit'
        
        exit_dict = {'stop_loss'    : stop, 
                     'stop_type'    : stop_type,
                     'take_profit'  : take}
        
        return exit_dict
    
    
    def create_price_chart(self, pair, interval):
        # Generate chart
        fig = make_subplots(rows = 1, cols = 1,
                            shared_xaxes = True,
                            vertical_spacing = 0.02,
                            row_heights = [1]
                            )

        # Price chart
        fig.add_trace(go.Candlestick(x = self.data.index[-self.params['view_window']:],
                                     open = self.data['Open'],
                                     high = self.data['High'],
                                     low  = self.data['Low'],
                                     close= self.data['Close'], 
                                     name = 'market data'
                                     ),
                      row = 1,
                      col = 1
                      )
        
        # fig.update_layout(hovermode="y unified")
        fig.update_layout(
                          title = "Price chart for {}/{} ({} candles) using {}".format(pair[:3], 
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
            

    def create_backtest_chart(self, pair, interval, trade_summary, pf_df):
        # Generate chart
        fig = make_subplots(rows = 3, cols = 1,
                            shared_xaxes = True,
                            vertical_spacing = 0.02,
                            row_heights = [0.3, 0.45, 0.25]
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
                                 y      = self.slowEMA[-self.params['view_window']:], 
                                 line   = dict(color='orange', 
                                               width=1
                                               ), 
                                 name='Slow EMA'),
                      row = 2,
                      col = 1
                      )
        fig.add_trace(go.Scatter(x      = self.data.index[-self.params['view_window']:], 
                                 y      = self.fastEMA[-self.params['view_window']:], 
                                 line   = dict(color='blue', 
                                               width=1
                                               ), 
                                 name='Fast EMA'),
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
                                 mode="markers",
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
        
        
        # Stochastic signal
        fig.add_trace(go.Scatter(x = self.data.index,
                                 y = self.slowk, 
                                 line = dict(color = 'blue', 
                                             width = 1), 
                                 name = 'Slow K'),
                      row = 3,
                      col = 1
                      )
        fig.add_trace(go.Scatter(x = self.data.index,
                                 y = self.slowd, 
                                 line = dict(color = 'red', 
                                             width = 1), 
                                 name = 'Slow D'),
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