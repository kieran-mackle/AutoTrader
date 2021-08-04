#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoPlot
----------
General plotting script.

I want to be able to specify my indicators, time period and instrument, and 
get a plot for it.

"""

from datetime import timedelta
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
pio.renderers.default = 'browser'
from autotrader.lib import environment_manager
from autotrader.lib.autodata import GetData
import yaml
import numpy as np
from getopt import getopt
import sys
import os


# Bokeh
from bokeh.models.annotations import Title
from bokeh.plotting import figure, output_file, show
from bokeh.models import (
    CustomJS,
    ColumnDataSource,
    HoverTool
)
from bokeh.layouts import gridplot
from bokeh.transform import factor_cmap


def read_yaml(file_path):
    '''Function to read and extract contents from .yaml file.'''
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def current_candle(current_time, granularity):
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
    last_period         = number * np.floor(current_period/number)# - number
    
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


def granularity_to_seconds(granularity):
    '''Converts the interval to time in seconds'''
    letter = granularity[0]
    
    if len(granularity) > 1:
        number = float(granularity[1:])
    else:
        number = 1
    
    conversions = {'S': 1,
                   'M': 60,
                   'H': 60*60,
                   'D': 60*60*24
                   }
    
    my_int = conversions[letter] * number
    
    return my_int


def plot_oanda_trade_history(filepath, global_config, broker_config, 
                             granularity, instruments=None):
    """
        Code below takes oanda csv history and plots it. Pretty cool!
        
        When a position is opened, it will be shown as a triangle with no fill (open).
        It will point in the direction of the trade.
        
        When a position is closed, it will be shown as a triangle with red or green 
        fill, depending on if it was profitable or not. It will point in the direction 
        of the closing trade.
        
    """
    import AutoTrader
    
    trade_history = pd.read_csv(filepath, index_col = 0)
    trade_history = trade_history.fillna(method='ffill')
    
    if instruments is None:
        instruments = trade_history.Instrument.unique()
    
    for instrument in trade_history.Instrument.unique():
        if str(instrument) != 'nan' and str(instrument) in instruments:
            trade_summary       = trade_history[trade_history.Instrument == instrument]
            
            start_time          = pd.to_datetime(trade_summary.Date.values)[0]
            end_time            = pd.to_datetime(trade_summary.Date.values)[-1]
            formatted_instrument = instrument[:3] + '_' + instrument[-3:]
            
            get_data            = GetData(broker_config)
            aug_start           = start_time - 200*timedelta(seconds = granularity_to_seconds(granularity))
            
            data                = get_data.oanda(formatted_instrument, 
                                                 granularity, 
                                                 start_time = aug_start, 
                                                 end_time = end_time)
            
            # Run AutoTrader in backtest mode to get trade_summary
            home_dir                = os.path.dirname(os.path.abspath(__file__))
            historical_data_name    = 'temp_data.csv'
            historical_data_file_path = os.path.join(home_dir, 
                                                     'price_data',
                                                     historical_data_name)
            data.to_csv(historical_data_file_path)
            
            user_options = {'config_file'   : 'hamacd', 
                            'verbosity'     : '0', 
                            'show_help'     : None, 
                            'notify'        : 0, 
                            'backtest'      : True, 
                            'plot'          : False, 
                            'log'           : False, 
                            'analyse'       : False, 
                            'scan'          : None, 
                            'optimise'      : False, 
                            'data_file'     : historical_data_name,
                            'instruments'   : formatted_instrument
                            }
            
            backtest_trades     = AutoTrader.main(user_options)
            os.remove(historical_data_file_path)
            
            cancelled_orders    = trade_summary[trade_summary.Transaction == 'ORDER_CANCEL']
            insufficient_margin = cancelled_orders[cancelled_orders.Details == 'INSUFFICIENT_MARGIN']
            long_insf_m         = insufficient_margin[insufficient_margin['Direction'] == 'Buy']
            short_insf_m        = insufficient_margin[insufficient_margin['Direction'] == 'Sell']
            
            short_insf_times    = [current_candle(dt, granularity) for dt in pd.to_datetime(short_insf_m.Date.values, utc=True)]
            short_insf_data     = data[data.index.isin(short_insf_times)]
            
            long_insf_times     = [current_candle(dt, granularity) for dt in pd.to_datetime(long_insf_m.Date.values, utc=True)]
            long_insf_data      = data[data.index.isin(long_insf_times)]
            
            filled_orders       = trade_summary[trade_summary.Transaction == 'ORDER_FILL']
            
            sl_orders           = trade_summary[trade_summary.Transaction == 'STOP_LOSS_ORDER']
            tp_orders           = trade_summary[trade_summary.Transaction == 'TAKE_PROFIT_ORDER']
            
            entries             = filled_orders[filled_orders.Details == 'MARKET_ORDER']
            exits               = filled_orders[filled_orders.Details != 'MARKET_ORDER']
            
            long_entries        = entries[entries['Direction'] == 'Buy']
            short_entries       = entries[entries['Direction'] == 'Sell']
            
            profitable_short_exits      = exits[(exits['P/L'] > 0) & (exits['Direction'] == 'Buy')]
            unprofitable_short_exits    = exits[(exits['P/L'] < 0) & (exits['Direction'] == 'Buy')]
            profitable_long_exits       = exits[(exits['P/L'] > 0) & (exits['Direction'] == 'Sell')]
            unprofitable_long_exits     = exits[(exits['P/L'] < 0) & (exits['Direction'] == 'Sell')]
            
            
            ''' Live trade history '''
            # Initialise figure
            fig = make_subplots(rows = 2, cols = 1,
                                shared_xaxes = True,
                                vertical_spacing = 0.02,
                                row_heights = [0.5, 0.5]
                                )
            
            # Price chart
            fig.add_trace(go.Candlestick(x = data.index,
                                         open = data['Open'],
                                         high = data['High'],
                                         low  = data['Low'],
                                         close= data['Close'], 
                                         name = 'market data'
                                         ),
                          row = 1,
                          col = 1
                          )
            
            # Long entries
            fig.add_trace(go.Scatter(x = pd.to_datetime(long_entries.Date.values, utc=True), 
                                     y = long_entries.Price.values, 
                                     mode="markers",
                                     marker_symbol = 105,
                                     marker_size = 12,
                                     marker_line_width = 1,
                                     marker_color = 'black',
                                     name = 'Long position entry'),
                          row = 1,
                          col = 1
                         )
            
            # Cancelled long entries
            fig.add_trace(go.Scatter(x = long_insf_data.index, 
                                      y = long_insf_data.Open.values, 
                                      mode="markers",
                                      marker_symbol = 5,
                                      marker_size = 12,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Cancelled long positions (insufficient margin)'),
                          row = 1,
                          col = 1
                          )
            
            # Short entries
            fig.add_trace(go.Scatter(x = pd.to_datetime(short_entries.Date.values, utc=True), 
                                      y = short_entries.Price.values, 
                                      mode="markers",
                                      marker_symbol = 106,
                                      marker_size = 12,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Short position entry'),
                          row = 1,
                          col = 1
                          )
            
            # # Cancelled short entries
            fig.add_trace(go.Scatter(x = short_insf_data.index, 
                                      y = short_insf_data.Open.values, 
                                      mode="markers",
                                      marker_symbol = 6,
                                      marker_size = 12,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Cancelled short positions (insufficient margin)'),
                          row = 1,
                          col = 1
                          )
            
            # Unprofitable long exits
            fig.add_trace(go.Scatter(x = pd.to_datetime(unprofitable_long_exits.Date.values, utc=True), 
                                     y = unprofitable_long_exits.Price.values, 
                                     mode="markers",
                                     marker_symbol = 0,
                                     marker_size = 5,
                                     marker_line_width = 1,
                                     marker_color = 'black',
                                     name = 'Unprofitable long position exit'),
                          row = 1,
                          col = 1
                          )
            
            # Unprofitable short exits
            fig.add_trace(go.Scatter(x = pd.to_datetime(unprofitable_short_exits.Date.values, utc=True), 
                                      y = unprofitable_short_exits.Price.values, 
                                      mode="markers",
                                      marker_symbol = 0,
                                      marker_size = 5,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Unprofitable short position exit'),
                          row = 1,
                          col = 1
                          )
            
            # Profitable long exits
            fig.add_trace(go.Scatter(x = pd.to_datetime(profitable_long_exits.Date.values, utc=True), 
                                      y = profitable_long_exits.Price.values, 
                                      mode="markers",
                                      marker_symbol = 0,
                                      marker_size = 5,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Profitable long position exit'),
                          row = 1,
                          col = 1
                          )
            
            # Profitable short exits
            fig.add_trace(go.Scatter(x = pd.to_datetime(profitable_short_exits.Date.values, utc=True), 
                                     y = profitable_short_exits.Price.values, 
                                     mode="markers",
                                     marker_symbol = 0,
                                     marker_size = 5,
                                     marker_line_width = 1,
                                     marker_color = 'black',
                                     name = 'Profitable short position exit'),
                          row = 1,
                          col = 1
                         )
            
            # Stop loss levels
            fig.add_trace(go.Scatter(x = pd.to_datetime(sl_orders.Date.values, utc=True), 
                                      y = sl_orders.Price.values, 
                                      mode="markers",
                                      marker_symbol = 41,
                                      marker_size = 12,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Stop loss level'),
                          row = 1,
                          col = 1
                          )
            
            # Take profit levels
            fig.add_trace(go.Scatter(x = pd.to_datetime(tp_orders.Date.values, utc=True), 
                                      y = tp_orders.Price.values, 
                                      mode="markers",
                                      marker_symbol = 41,
                                      marker_size = 12,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Take profit level'),
                          row = 1,
                          col = 1
                          )
            
            # Cancelled stop losses 
            fig.add_trace(go.Scatter(x = pd.to_datetime(insufficient_margin.Date.values, utc=True), 
                                     y = insufficient_margin['Stop Loss'].values, 
                                     mode="markers",
                                     marker_symbol = 41,
                                     marker_size = 12,
                                     marker_line_width = 1,
                                     marker_color = 'black',
                                     name = 'Cancelled short stop losses (insufficient margin)'),
                          row = 1,
                          col = 1
                         )
            
            # Cancelled take profits
            fig.add_trace(go.Scatter(x = pd.to_datetime(insufficient_margin.Date.values, utc=True), 
                                      y = insufficient_margin['Take Profit'].values, 
                                      mode="markers",
                                      marker_symbol = 41,
                                      marker_size = 12,
                                      marker_line_width = 1,
                                      marker_color = 'black',
                                      name = 'Cancelled take profits (insufficient margin)'),
                          row = 1,
                          col = 1
                          )
            
            # fig.update_layout(hovermode="y unified")
            fig.update_layout(title = "Trade history chart for {} ({} candles)".format(instrument, 
                                                                                        granularity)
                              )
            
            
            ''' Backtest trade history '''
            # Price chart
            fig.add_trace(go.Candlestick(x      = data.index,
                                         open   = data['Open'],
                                         high   = data['High'],
                                         low    = data['Low'],
                                         close  = data['Close'], 
                                         name   = 'market data'
                                         ),
                          row = 2,
                          col = 1
                          )
            
            # Backtesting signals
            profitable_longs        = backtest_trades[(backtest_trades['Profit'] > 0) 
                                                    & (backtest_trades['Size'] > 0)]
            profitable_shorts       = backtest_trades[(backtest_trades['Profit'] > 0) 
                                                    & (backtest_trades['Size'] < 0)]
            unprofitable_longs      = backtest_trades[(backtest_trades['Profit'] < 0) 
                                                    & (backtest_trades['Size'] > 0)]
            unprofitable_shorts     = backtest_trades[(backtest_trades['Profit'] < 0) 
                                                    & (backtest_trades['Size'] < 0)]
            stop_losses             = backtest_trades.Stop_loss
            take_profits            = backtest_trades.Take_profit
            entry_times             = pd.to_datetime(backtest_trades.Entry_time.values, 
                                                     utc=True)
            exit_times              = list(backtest_trades.Exit_time)
            exit_prices             = backtest_trades.Exit_price
            
            
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
                                      name = 'Take profit level'),
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
                                     text = backtest_trades.Order_ID),
                          row = 2,
                          col = 1
                          )
            
            # Hide weekends
            fig.update_xaxes(rangeslider_visible=False,
                             rangebreaks=[
                                 dict(bounds=["sat", "mon"]),
                                 ]
                             )
            fig.show()



def plot_candles(source, fig_tools, height, width):
    
    bull_colour             = "#D5E1DD"
    bear_colour             = "#F2583E"
    candle_colours          = [bear_colour, bull_colour]
    colour_map              = factor_cmap('change', candle_colours, ['0', '1'])
    
    candle_tooltips         = [("Date", "@date{%b %d %H:%M:%S}"),
                               ("Open", "@Open{0.0000}"), 
                               ("High", "@High{0.0000}"), 
                               ("Low", "@Low{0.0000}"),
                               ("Close", "@Close{0.0000}")]

    candle_plot = figure(plot_width     = width, 
                         plot_height    = height, 
                         tools          = fig_tools,
                         active_drag    = 'pan',
                         active_scroll  = 'wheel_zoom')

    candle_plot.segment('index', 'High',
                        'index', 'Low', 
                        color   = "black",
                        source  = source)
    candles = candle_plot.vbar('index', 0.7, 'Open', 'Close', 
                               source       = source,
                               line_color   = "black", 
                               fill_color   = colour_map)
    
    candle_hovertool = HoverTool(tooltips   = candle_tooltips, 
                              formatters    = {'@date':'datetime'}, 
                              mode          = 'mouse',
                              renderers     = [candles])
    
    candle_plot.add_tools(candle_hovertool)
    
    return candle_plot


def plot_macd(x_range, macd_data, linked_fig):
    # Initialise figure
    fig = figure(plot_width     = linked_fig.plot_width,
                 plot_height    = 150,
                 title          = None,
                 tools          = linked_fig.tools,
                 active_drag    = linked_fig.tools[0],
                 active_scroll  = linked_fig.tools[1],
                 x_range        = linked_fig.x_range)

    histcolour = np.where(macd_data['histogram'] < 0, 'red', 'lightblue')
    
    # Add glyphs
    fig.line(x_range, macd_data['macd'], line_color = 'blue')
    fig.line(x_range, macd_data['signal'], line_color = 'red')
    fig.quad(top = macd_data['histogram'],
             bottom = 0,
             left = x_range - 0.3,
             right = x_range + 0.3,
             fill_color = histcolour)

    return fig


def plot_trade_history(data, trade_summary, linked_fig):
    ts = trade_summary
    ts['date']   = ts.index 
    ts           = ts.reset_index(drop = True)
    
    # Here:
    ts_xrange   = data[data.date.isin(trade_summary.index)].index
    
    trade_summary = ts.set_index(ts_xrange)
    data['data_index'] = data.index
    exit_summary = pd.merge(data, trade_summary, left_on='date', right_on='Exit_time')
    
    # Backtesting signals
    profitable_longs        = trade_summary[(trade_summary['Profit'] > 0) 
                                            & (trade_summary['Size'] > 0)]
    profitable_shorts       = trade_summary[(trade_summary['Profit'] > 0) 
                                            & (trade_summary['Size'] < 0)]
    unprofitable_longs      = trade_summary[(trade_summary['Profit'] < 0) 
                                            & (trade_summary['Size'] > 0)]
    unprofitable_shorts     = trade_summary[(trade_summary['Profit'] < 0) 
                                            & (trade_summary['Size'] < 0)]
    
    
    # Profitable long trades
    if len(profitable_longs) > 0:
        linked_fig.scatter(list(profitable_longs.index),
                           list(profitable_longs.Entry.values),
                           marker = 'triangle',
                           size = 15,
                           fill_color = 'lightgreen',
                           legend_label = 'Profitable long trades')
    
    # Profitable short trades
    if len(profitable_shorts) > 0:
        linked_fig.scatter(list(profitable_shorts.index),
                           list(profitable_shorts.Entry.values),
                           marker = 'inverted_triangle',
                           size = 15,
                           fill_color = 'lightgreen',
                           legend_label = 'Profitable short trades')
    
    # Unprofitable long trades
    if len(unprofitable_longs) > 0:
        linked_fig.scatter(list(unprofitable_longs.index),
                           list(unprofitable_longs.Entry.values),
                           marker = 'triangle',
                           size = 15,
                           fill_color = 'orangered',
                           legend_label = 'Unprofitable long trades')
    
    # Unprofitable short trades
    if len(unprofitable_shorts) > 0:
        linked_fig.scatter(list(unprofitable_shorts.index),
                           list(unprofitable_shorts.Entry.values),
                           marker = 'inverted_triangle',
                           size = 15,
                           fill_color = 'orangered',
                           legend_label = 'Unprofitable short trades')
    
    
    # Stop loss  levels
    stop_losses = list(trade_summary.Stop_loss.values)
    if np.isnan(stop_losses).any():
        pass
    else:
        linked_fig.scatter(list(trade_summary.index),
                            list(trade_summary.Stop_loss.values),
                            marker = 'dash',
                            size = 15,
                            fill_color = 'black',
                            legend_label = 'Stop loss')
    
    # Take profit levels
    take_profits = list(trade_summary.Take_profit.values)
    if np.isnan(take_profits).any():
        pass
    else:
        linked_fig.scatter(list(trade_summary.index),
                            list(trade_summary.Take_profit.values),
                            marker = 'dash',
                            size = 15,
                            fill_color = 'black',
                            legend_label = 'Take profit')
    
    # Position exits
    linked_fig.scatter(list(exit_summary.data_index),
                       list(exit_summary.Exit_price.values),
                       marker = 'circle',
                       size = 8,
                       fill_color = 'black',
                       legend_label = 'Position exit')



def plot_portfolio_history(data, balance, NAV, linked_fig, fig_tools):
    # Initialise figure
    fig = figure(plot_width     = linked_fig.plot_width,
                  plot_height    = 150,
                  title          = None,
                  tools          = fig_tools,
                  active_drag    = 'pan',
                  active_scroll  = 'wheel_zoom',
                  x_range        = linked_fig.x_range)
    
    # Add glyphs
    fig.line(data.index, 
             NAV, 
             line_color         = 'black',
             legend_label       = 'Net Asset Value')

    return fig


def plot_indicators(x_range, indicators, linked_fig):
    
    plot_type = {'MACD'        : 'below',
                 'EMA'         : 'over',
                 'RSI'         : 'below',
                 'STOCHASTIC'  : 'below',
                 'SMA'         : 'over',
                 'Heikin-Ashi' : 'below'}
    
    # Plot indicators
    indis_over              = 0
    indis_below             = 0
    max_indis_over          = 3
    max_indis_below         = 2
    bottom_figs             = []
    
    colours                 = ['red', 'blue', 'orange', 'green']
    
    for indicator in indicators:
        indi_type = indicators[indicator]['type']
        
        if indi_type in plot_type:
            if plot_type[indi_type] == 'over' and indis_over < max_indis_over:
    
                linked_fig.line(x_range, 
                                indicators[indicator]['data'], 
                                line_width = 1.5, 
                                legend_label = indicator,
                                line_color = colours[indis_over])
                indis_over     += 1
                
            elif plot_type[indi_type] == 'below' and indis_below < max_indis_below:
                if indi_type == 'MACD':
                    new_fig     = plot_macd(x_range,
                                            indicators[indicator], 
                                            linked_fig)
                    new_fig.title = indicator
                
                elif indi_type == 'Heikin-Ashi':
                    
                    data        = indicators[indicator]['data']
                    data['date'] = data.index 
                    data        = data.reset_index(drop = True)
                    source      = ColumnDataSource(data)
                    source.add((data.Close >= data.Open).values.astype(np.uint8).astype(str),
                               'change')
                    
                    fig_tools   = "pan,wheel_zoom,box_zoom,undo,redo,reset,save"
                    
                    new_fig     = plot_candles(source, fig_tools, 300, 800)
                    new_fig.x_range = linked_fig.x_range
                    new_fig.title = indicator
                    indis_below   += max_indis_below # To block any other new plots below.
                
                else:
                    new_fig = figure(plot_width     = linked_fig.plot_width,
                                     plot_height    = 130,
                                     title          = None,
                                     tools          = linked_fig.tools,
                                     active_drag    = linked_fig.tools[0],
                                     active_scroll  = linked_fig.tools[1],
                                     x_range        = linked_fig.x_range)
                    
                    # Add glyphs
                    new_fig.line(x_range, 
                                 indicators[indicator]['data'],
                                 line_color         = 'black', 
                                 legend_label       = indicator)
                    
                indis_below    += 1
                bottom_figs.append(new_fig)
        else:
            if indis_below < max_indis_below:
                # Unknown plot type - plot generally on new bottom fig
                print("Indicator not recognised in AutoPlot.")
                new_fig = figure(plot_width     = linked_fig.plot_width,
                                 plot_height    = 130,
                                 title          = None,
                                 tools          = linked_fig.tools,
                                 active_drag    = linked_fig.tools[0],
                                 active_scroll  = linked_fig.tools[1],
                                 x_range        = linked_fig.x_range)
                
                # Add glyphs
                new_fig.line(x_range, 
                             indicators[indicator]['data'],
                             line_color         = 'black', 
                             legend_label       = indicator)
                
                indis_below    += 1
                bottom_figs.append(new_fig)
            
    return bottom_figs


def plot_backtest(backtest_dict):
    data            = backtest_dict['data']
    balance         = backtest_dict['balance']
    NAV             = backtest_dict['NAV']
    trade_summary   = backtest_dict['trade_summary']
    indicators      = backtest_dict['indicators']
    pair            = backtest_dict['pair']
    interval        = backtest_dict['interval']
    
    # Preparation ----------------------------------- #
    output_file("candlestick.html",
                title = "AutoTrader Backtest Results")
    data['date']            = data.index 
    data                    = data.reset_index(drop = True)
    source                  = ColumnDataSource(data)
    source.add((data.Close >= data.Open).values.astype(np.uint8).astype(str),
               'change')
    fig_tools               = "pan,wheel_zoom,box_zoom,undo,redo,reset,save"
    
    # Load JavaScript code for auto-scaling 
    with open(os.path.join(os.path.dirname(__file__), 'lib/autoscale.js'),
              encoding = 'utf-8') as _f:
        autoscale_code      = _f.read()
    
    # Plotting ------------------------------------- #
    # Create main candlestick plot
    candle_plot             = plot_candles(source, fig_tools, 400, 800)
    
    # Overlay trades 
    plot_trade_history(data, trade_summary, candle_plot)
    
    # Plot indicators
    bottom_figs = plot_indicators(data.index, indicators, candle_plot)
    
    # Auto-scale y-axis of candlestick chart
    autoscale_args      = dict(y_range  = candle_plot.y_range, 
                               source   = source)
    candle_plot.x_range.js_on_change('end', CustomJS(args = autoscale_args, 
                                                     code = autoscale_code))
    
    # Above plots
    top_fig             = None
    top_fig             = plot_portfolio_history(data, balance, NAV, candle_plot, fig_tools)
    
    # Compile plots for final figure
    plots               = [top_fig, candle_plot] + bottom_figs
    
    titled  = 0
    t       = Title()
    t.text  = "Backtest chart for {}/{} ({} candles)".format(pair[:3], pair[-3:], interval)
    for plot in plots:
        if plot is not None:
            plot.xaxis.major_label_overrides = {
                i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(data["date"]))
            }
            plot.xaxis.bounds   = (0, data.index[-1])
            plot.sizing_mode    = 'stretch_width'
            
            if titled == 0:
                plot.title = t
                titled = 1
            
            if plot.legend:
                plot.legend.visible             = True
                plot.legend.location            = 'top_left'
                plot.legend.border_line_width   = 1
                plot.legend.border_line_color   = '#333333'
                plot.legend.padding             = 5
                plot.legend.spacing             = 0
                plot.legend.margin              = 0
                plot.legend.label_text_font_size = '8pt'
                plot.legend.click_policy        = "hide"
            
            plot.min_border_left    = 0
            plot.min_border_top     = 3
            plot.min_border_bottom  = 6
            plot.min_border_right   = 10
            plot.outline_line_color = 'black'

    # Construct final figure
    fig                 = gridplot(plots, 
                                   ncols            = 1, 
                                   toolbar_location = 'right',
                                   toolbar_options  = dict(logo = None), 
                                   merge_tools      = True
                                   )
    fig.sizing_mode     = 'stretch_width'
    show(fig)



def main(user_options):
    '''
        Main function for generating plots
    '''
    # I want this to be where all the plots are actually generated. 
    # Also, the user options will determine what is plotted. Other functions in
    # this script will be used to generate other plotting bits.
    
    # for example:
    #     if user_options['plot_oanda_trade_history'] is true:
    #         call plot_oanda_trade_history to get the relevant information, 
    #         then proceed with plotting.
    
    
    # Path variables
    home_dir        = os.path.dirname(os.path.abspath(__file__))
    price_data_dir  = os.path.join(home_dir, 'price_data')
    global_config_path = os.path.join(home_dir, 'config', 'GLOBAL.yaml')
    
    granularity     = user_options['granularity']
    
    if user_options['live_performance'] is not None:
        
        broker      = user_options['live_performance']
        filepath    = os.path.join(price_data_dir, user_options['filename'])
        
        global_config   = read_yaml(global_config_path)
        broker_config   = environment_manager.get_config('demo', 
                                                         global_config, 
                                                         broker.upper())
        
        if broker == 'oanda':
            instruments = user_options['instruments']
            plot_oanda_trade_history(filepath, 
                                     global_config, 
                                     broker_config, 
                                     granularity,
                                     instruments)
    
    if user_options['backtest'] is not None:
        plot_backtest(user_options['backtest'])
    
    
    # instrument = "EUR_USD"
    # granularity = 'M30'
    # from_date = datetime()
    # to_date = datetime.now()
    
    # data = []
    
    # # indicators = []
    
    # # Use this dict to either overlay indicator on price chart, or on its own
    # indicator_type = {'RSI': 'indicator',
    #                   'EMA': 'overlay',
    #                   'SMA': 'overlay'
    #                   }
    
    
    # overlays    = len()
    # lowers      = len()
    
    # # Generate chart
    # fig = make_subplots(rows = 1+lowers, cols = 1,
    #                     shared_xaxes = True,
    #                     vertical_spacing = 0.02,
    #                     row_heights = [1]
    #                     )
    
    # # Price chart
    # fig.add_trace(go.Candlestick(x = data.index,
    #                              open = data['Open'],
    #                              high = data['High'],
    #                              low  = data['Low'],
    #                              close= data['Close'], 
    #                              name = 'market data'
    #                              ),
    #               row = 1,
    #               col = 1
    #               )
    
    # for indicator in overlays:
    #     fig.add_trace(go.Scatter(x = data.index, 
    #                              y = indicator, 
    #                              line = dict(color='blue', 
    #                                          width=1
    #                                          ), 
    #                              name = 'name'),
    #                   row = 1,
    #                   col = 1
    #                   )
    
    # for number, indicator in enumerate(lowers):
    #     fig.add_trace(go.Scatter(x = data.index, 
    #                              y = indicator, 
    #                              line = dict(color='blue', 
    #                                          width=1
    #                                          ), 
    #                              name = 'name'),
    #                   row = number + 1,
    #                   col = 1
    #                   )
    
    # fig.show()
    
    return













def print_usage():
    """ Print usage options. """
    print("AutoPlot.py")
    print("Utility to plot price charts and indicators.")
    print("--------------------------------------------------------------" \
          + "---------------")
    print("Flag                                 Comment [short flag]")
    print("--------------------------------------------------------------" \
          + "---------------")
    print("Required:") 
    print("  --granularity                      candlestick granularity [-g]")
    print("  --filename                         data filename [-f]")
    print("\nOptional:")
    print("  --help                             show help for usage [-h]")
    print("  --verbosity <int>                  set verbosity (0,1,2) [-v]")
    print("Coming soon:")
    print("  --instrument 'XXX_YYY'             instrument to stream [-i]")

def print_help(option):
    ''' Print usage instructions. '''
    
    if option == 'instrument' or option == 'i':
        print("Help for '--instrument' (-c) option:")
        
        print("\nExample usage:")
        print("./AutoStream.py -c my_config_file")
        
    elif option == 'verbosity' or option == 'v':
        print("Help for '--verbosity' (-v) option:")
        print("-----------------------------------")
        print("The verbosity flag is used to set the level of output.")


short_options = "g:v:f:h:p:i:"
long_options = ['granularity=', 'verbosity=', 'filename=', 'help=', 
                'performance=', 'instruments=']


if __name__ == '__main__':
    options, r = getopt(sys.argv[1:], 
                        short_options, 
                        long_options
                        )
    
    # Defaults
    instrument      = None
    verbosity       = 0
    filename        = None
    show_help       = None
    live_performance = None
    instruments     = None
    backtest        = None
    
    for opt, arg in options:
        if opt in ('-g', '--granularity'):
            granularity = arg
        elif opt in ('-v', '--verbose'):
            verbosity = arg
        elif opt in ('-f', '--filename'):
            filename = arg
        elif opt in ('-h', '--help'):
            show_help = arg
        elif opt in ('-p', 'live_performance'):
            live_performance = arg
        elif opt in ('-i', 'instruments'):
            instruments = arg
        
    
    uo_dict = {'granularity':   granularity,
               'verbosity':     verbosity,
               'filename':      filename,
               'show_help':     show_help,
               'live_performance': live_performance,
               'instruments':   instruments}

    if len(options) == 0:
        print_usage()
        
    elif uo_dict['show_help'] is not None:
        print_help(uo_dict['show_help'])
        
    else:
        main(uo_dict)



