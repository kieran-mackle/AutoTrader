#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoPlot
----------
Automated plotting script.

"""

import pandas as pd
import numpy as np
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


class AutoPlot():
    
    def __init__(self):
        self.data               = None
        self.max_indis_over     = 3
        self.max_indis_below    = 2
        self._modified_data     = None
        self.fig_tools          = "pan,wheel_zoom,box_zoom,undo,redo,reset,save"
        self.ohlc_height        = 400
        self.ohlc_width         = 800
        self.total_height       = 1000
        self.plot_validation_balance = True
    
    def add_tool(self, tool_name):
        self.fig_tools          = self.fig_tools + "," + tool_name
    
    def _reindex_data(self):
        modified_data           = self.data
        modified_data['date']   = modified_data.index
        modified_data           = modified_data.reset_index(drop = True)
        self._modified_data     = modified_data
    
    def plot_backtest(self, backtest_dict):
        ''' Creates backtest figure. '''
        NAV             = backtest_dict['NAV']
        trade_summary   = backtest_dict['trade_summary']
        indicators      = backtest_dict['indicators']
        pair            = backtest_dict['pair']
        interval        = backtest_dict['interval']
        
        # Preparation ----------------------------------- #
        output_file("candlestick.html",
                    title = "AutoTrader Backtest Results")
        
        if self._modified_data is None:
            self._reindex_data()
        source                  = ColumnDataSource(self._modified_data)
        source.add((self._modified_data.Close >= self._modified_data.Open).values.astype(np.uint8).astype(str),
                   'change')
        
        # Load JavaScript code for auto-scaling 
        with open(os.path.join(os.path.dirname(__file__), 'lib/autoscale.js'),
                  encoding = 'utf-8') as _f:
            autoscale_code      = _f.read()
        
        # Plotting ------------------------------------- #
        # Create main candlestick plot
        candle_plot             = self.plot_candles(source)
        
        # Overlay trades 
        self.plot_trade_history(trade_summary, candle_plot)
        
        # Plot indicators
        bottom_figs = self.plot_indicators(indicators, candle_plot)
        
        # Auto-scale y-axis of candlestick chart
        autoscale_args      = dict(y_range  = candle_plot.y_range, 
                                   source   = source)
        candle_plot.x_range.js_on_change('end', CustomJS(args = autoscale_args, 
                                                         code = autoscale_code))
        
        # Above plots
        top_fig             = self.plot_portfolio_history(NAV, candle_plot)
        
        # Compile plots for final figure
        plots               = [top_fig, candle_plot] + bottom_figs
        
        titled  = 0
        t       = Title()
        t.text  = "Backtest chart for {}/{} ({} candles)".format(pair[:3], pair[-3:], interval)
        for plot in plots:
            if plot is not None:
                plot.xaxis.major_label_overrides = {
                    i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(self._modified_data["date"]))
                }
                plot.xaxis.bounds   = (0, self._modified_data.index[-1])
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
    
    
    def view_indicators(self, indicators):
        ''' Constructs indicator visualisation figure. '''
        # Preparation ----------------------------------- #
        output_file("candlestick.html",
                    title = "AutoTrader IndiView")
        self.data['date']       = self.data.index 
        self.data               = self.data.reset_index(drop = True)
        source                  = ColumnDataSource(self.data)
        source.add((self.data.Close >= self.data.Open).values.astype(np.uint8).astype(str),
                   'change')
        
        # Load JavaScript code for auto-scaling 
        with open(os.path.join(os.path.dirname(__file__), 'lib/autoscale.js'),
                  encoding = 'utf-8') as _f:
            autoscale_code      = _f.read()
            
        # Plotting ------------------------------------- #
        # Create main candlestick plot
        candle_plot             = self.plot_candles(source)
        candle_plot.title       = 'AutoTrader IndiView'
        
        # Plot indicators
        bottom_figs             = self.plot_indicators(indicators, candle_plot)
        
        # Auto-scale y-axis of candlestick chart
        autoscale_args          = dict(y_range  = candle_plot.y_range, 
                                       source   = source)
        candle_plot.x_range.js_on_change('end', CustomJS(args = autoscale_args, 
                                                         code = autoscale_code))
        
        plots = [candle_plot] + bottom_figs
        
        for plot in plots:
            if plot is not None:
                plot.xaxis.major_label_overrides = {
                    i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(self.data["date"]))
                }
                plot.xaxis.bounds   = (0, self.data.index[-1])
                plot.sizing_mode    = 'stretch_width'
    
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
    
    def plot_indicators(self, indicators, linked_fig):
        ''' Plots indicators. '''
        # Get integer index
        if self._modified_data is None:
            self._reindex_data()
        x_range   = self._modified_data.index
        
        plot_type = {'MACD'        : 'below',
                     'MA'          : 'over',
                     'RSI'         : 'below',
                     'STOCHASTIC'  : 'below',
                     'Heikin-Ashi' : 'below',
                     'Supertrend'  : 'over',
                     'Swings'      : 'over',
                     'Engulfing'   : 'below',
                     'Crossover'   : 'below'}
        
        # Plot indicators
        indis_over              = 0
        indis_below             = 0
        bottom_figs             = []
        
        colours                 = ['red', 'blue', 'orange', 'green']
        
        for indicator in indicators:
            indi_type = indicators[indicator]['type']
            
            if indi_type in plot_type:
                if plot_type[indi_type] == 'over' and indis_over < self.max_indis_over:
                    if indi_type == 'Supertrend':
                        self.plot_supertrend(indicators[indicator]['data'], 
                                                      linked_fig)
                        
                        indis_over     += 1 # Count as 2 indicators
                    elif indi_type == 'Swings':
                        self.plot_swings(indicators[indicator]['data'], 
                                                      linked_fig)
                    else:
                        linked_fig.line(x_range, 
                                        indicators[indicator]['data'], 
                                        line_width = 1.5, 
                                        legend_label = indicator,
                                        line_color = colours[indis_over])
                    indis_over     += 1
                    
                elif plot_type[indi_type] == 'below' and indis_below < self.max_indis_below:
                    if indi_type == 'MACD':
                        new_fig     = self.plot_macd(x_range,
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
                                                
                        new_fig     = self.plot_candles(source)
                        new_fig.x_range = linked_fig.x_range
                        new_fig.y_range = linked_fig.y_range
                        new_fig.title = indicator
                        indis_below   += self.max_indis_below # To block any other new plots below.
                    
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
                if indis_below < self.max_indis_below:
                    # Unknown plot type - plot generally on new bottom fig
                    print("Indicator type '{}' not recognised in AutoPlot.".format(indi_type))
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
    
    
    def plot_candles(self, source):
        ''' Plots OHLC data. '''
        bull_colour             = "#D5E1DD"
        bear_colour             = "#F2583E"
        candle_colours          = [bear_colour, bull_colour]
        colour_map              = factor_cmap('change', candle_colours, ['0', '1'])
        
        candle_tooltips         = [("Date", "@date{%b %d %H:%M:%S}"),
                                   ("Open", "@Open{0.0000}"), 
                                   ("High", "@High{0.0000}"), 
                                   ("Low", "@Low{0.0000}"),
                                   ("Close", "@Close{0.0000}")]
    
        candle_plot = figure(plot_width     = self.ohlc_width, 
                             plot_height    = self.ohlc_height, 
                             tools          = self.fig_tools,
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
    
    
    def plot_macd(self, x_range, macd_data, linked_fig):
        ''' Plots MACD indicator. '''
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
        if 'crossvals' in macd_data:
            fig.scatter(x_range,
                        macd_data['crossvals'],
                        marker = 'dash',
                        size = 15,
                        fill_color = 'black',
                        legend_label = 'Last Crossover Value')
    
        return fig
    
    
    def plot_supertrend(self, st_data, linked_fig):
        ''' Plots supertrend indicator. '''
        # Extract supertrend data
        # uptrend     = st_data['uptrend']
        # dntrend     = st_data['downtrend']
        
        # reset index 
        st_data['date']         = st_data.index 
        st_data                 = st_data.reset_index(drop = True)
        
        # Add glyphs
        linked_fig.scatter(st_data.index,
                    st_data['uptrend'],
                    size = 5,
                    fill_color = 'blue',
                    legend_label = 'Up trend support')
        linked_fig.scatter(st_data.index,
                    st_data['downtrend'],
                    size = 5,
                    fill_color = 'red',
                    legend_label = 'Down trend support')
        
    def plot_swings(self, swings, linked_fig):
        # reset index 
        swings                  = swings.reset_index(drop = True)
        
        linked_fig.scatter(list(swings.index),
                            list(swings.Last.values),
                            marker = 'dash',
                            size = 15,
                            fill_color = 'black',
                            legend_label = 'Last Swing Price Level')
        
        return
    
    def plot_cancelled_orders(self, cancelled_order_summary, linked_fig):
        ts              = cancelled_order_summary
        ts['date']      = ts.index 
        ts              = ts.reset_index(drop = True)
        
        # Compute x-range in integer index form
        if self._modified_data is None:
            self._reindex_data()
        ts_xrange       = self._modified_data[self._modified_data.date.isin(cancelled_order_summary.index)].index
        trade_summary   = ts.set_index(ts_xrange)
        
        longs           = trade_summary[trade_summary.Size > 0]
        shorts          = trade_summary[trade_summary.Size < 0]
        
        # Cancelled long trades
        if len(longs) > 0:
            linked_fig.scatter(list(longs.index),
                               list(longs.Order_price.values),
                               marker = 'triangle',
                               size = 15,
                               fill_color = 'black',
                               legend_label = 'Cancelled long trades')
        
        # Cancelled short trades
        if len(shorts) > 0:
            linked_fig.scatter(list(shorts.index),
                               list(shorts.Order_price.values),
                               marker = 'inverted_triangle',
                               size = 15,
                               fill_color = 'black',
                               legend_label = 'Cancelled short trades')
            
        linked_fig.scatter(list(trade_summary.index),
                                list(trade_summary.Stop_loss.values),
                                marker = 'dash',
                                size = 15,
                                fill_color = 'black',
                                legend_label = 'Stop loss')
    
        linked_fig.scatter(list(trade_summary.index),
                                list(trade_summary.Take_profit.values),
                                marker = 'dash',
                                size = 15,
                                fill_color = 'black',
                                legend_label = 'Take profit')
            

    def plot_trade_history(self, trade_summary, linked_fig):
        ''' Plots trades taken over ohlc chart. '''
        ts = trade_summary
        ts['date']   = ts.index 
        ts           = ts.reset_index(drop = True)
        
        # Compute x-range in integer index form
        if self._modified_data is None:
            self._reindex_data()
        ts_xrange   = self._modified_data[self._modified_data.date.isin(trade_summary.index)].index
        trade_summary = ts.set_index(ts_xrange)
        
        # Assign new 'data_index' column to capture index in trade summary merge
        self.data['data_index'] = self._modified_data.index
        exit_summary = pd.merge(self.data, trade_summary, left_on='date', right_on='Exit_time')
        
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
    
    
    def plot_portfolio_history(self, NAV, linked_fig):
        ''' Plots NAV over trade period. '''
        # Initialise figure
        fig = figure(plot_width     = linked_fig.plot_width,
                      plot_height    = 150,
                      title          = None,
                      tools          = self.fig_tools,
                      active_drag    = 'pan',
                      active_scroll  = 'wheel_zoom',
                      x_range        = linked_fig.x_range)
        
        # Add glyphs
        fig.line(self._modified_data.index, 
                 NAV, 
                 line_color         = 'black',
                 legend_label       = 'Backtest Net Asset Value')
    
        return fig
    
    
    def validate_backtest(self, livetrade_summary, backtest_dict,
                          backtest_cancelled_summary, instrument, granularity):
        """
            Code below takes oanda csv history and plots it.
            
            When a position is opened, it will be shown as a triangle with no fill (open).
            It will point in the direction of the trade.
            
            When a position is closed, it will be shown as a triangle with red or green 
            fill, depending on if it was profitable or not. It will point in the direction 
            of the closing trade.
            
        """
        backtest_trade_summary  = backtest_dict['trade_summary']
        backtest_NAV            = backtest_dict['NAV']
        
        # Preparation ----------------------------------- #
        output_file("candlestick.html",
                    title = "AutoTrader Backtest Validation")
        if self._modified_data is None:
            self._reindex_data()
        source                  = ColumnDataSource(self._modified_data)
        source.add((self._modified_data.Close >= self._modified_data.Open).values.astype(np.uint8).astype(str),
                   'change')
        
        
        ''' Plot livetrade history '''
        # Currently no nice way to do this due to .csv formatting
        # Initialise figure with OHLC data
        livetrade_candle_plot       = self.plot_candles(source)
        
        # Load JavaScript code for auto-scaling 
        with open(os.path.join(os.path.dirname(__file__), 'lib/autoscale.js'),
                  encoding = 'utf-8') as _f:
            autoscale_code      = _f.read()
        
        # Auto-scale y-axis of candlestick chart
        autoscale_args      = dict(y_range  = livetrade_candle_plot.y_range, 
                                   source   = source)
        livetrade_candle_plot.x_range.js_on_change('end', CustomJS(args = autoscale_args, 
                                                         code = autoscale_code))
        
        # Add trade history to OHLC chart
        cancelled_orders    = livetrade_summary[livetrade_summary.Transaction == 'ORDER_CANCEL']
        insufficient_margin = cancelled_orders[cancelled_orders.Details == 'INSUFFICIENT_MARGIN']
        short_insf_m        = insufficient_margin[insufficient_margin['Direction'] == 'Sell']
        short_insf_data     = self._modified_data[self._modified_data.index.isin(short_insf_m.data_index)].Open
        
        long_insf_m         = insufficient_margin[insufficient_margin['Direction'] == 'Buy']
        long_insf_data      = self._modified_data[self._modified_data.index.isin(long_insf_m.data_index)].Open
        
        filled_orders               = livetrade_summary[livetrade_summary.Transaction == 'ORDER_FILL']
        sl_orders                   = livetrade_summary[livetrade_summary.Transaction == 'STOP_LOSS_ORDER']
        tp_orders                   = livetrade_summary[livetrade_summary.Transaction == 'TAKE_PROFIT_ORDER']
        
        entries                     = filled_orders[filled_orders.Details == 'MARKET_ORDER']
        exits                       = filled_orders[filled_orders.Details != 'MARKET_ORDER']
        long_entries                = entries[entries['Direction'] == 'Buy']
        short_entries               = entries[entries['Direction'] == 'Sell']
        # profitable_short_exits      = exits[(exits['P/L'] > 0) & (exits['Direction'] == 'Buy')]
        # unprofitable_short_exits    = exits[(exits['P/L'] < 0) & (exits['Direction'] == 'Buy')]
        # profitable_long_exits       = exits[(exits['P/L'] > 0) & (exits['Direction'] == 'Sell')]
        # unprofitable_long_exits     = exits[(exits['P/L'] < 0) & (exits['Direction'] == 'Sell')]
        
        # Long trades
        livetrade_candle_plot.scatter(list(long_entries.data_index.values),
                                      list(long_entries.Price.values),
                                      marker = 'triangle',
                                      size = 15,
                                      fill_color = 'white',
                                      line_color = 'black',
                                      legend_label = 'Long Position Entry')
        
        # Short trades
        livetrade_candle_plot.scatter(list(short_entries.data_index.values),
                                      list(short_entries.Price.values),
                                      marker = 'inverted_triangle',
                                      size = 15,
                                      fill_color = 'white',
                                      line_color = 'black',
                                      legend_label = 'Short Position Entry')
        
        # Position exits
        livetrade_candle_plot.scatter(list(exits.data_index.values),
                                      list(exits.Price.values),
                                      marker = 'circle',
                                      size = 8,
                                      fill_color = 'black',
                                      line_color = 'black',
                                      legend_label = 'Short Position Entry')
        
        # Stop loss  levels
        livetrade_candle_plot.scatter(list(sl_orders.data_index.values),
                            list(sl_orders.Price.values),
                            marker = 'dash',
                            size = 15,
                            fill_color = 'black',
                            legend_label = 'Stop loss')
        
        # Take profit levels
        livetrade_candle_plot.scatter(list(tp_orders.data_index.values),
                            list(tp_orders.Price.values),
                            marker = 'dash',
                            size = 15,
                            fill_color = 'black',
                            legend_label = 'Take profit')
        
        # Cancelled orders
        livetrade_candle_plot.scatter(list(long_insf_m.data_index.values),
                                      list(long_insf_data.values),
                                      marker = 'triangle',
                                      size = 15,
                                      fill_color = 'black',
                                      line_color = 'black',
                                      legend_label = 'Cancelled Long Order')
        
        livetrade_candle_plot.scatter(list(short_insf_m.data_index.values),
                                      list(short_insf_data.values),
                                      marker = 'inverted_triangle',
                                      size = 15,
                                      fill_color = 'black',
                                      line_color = 'black',
                                      legend_label = 'Cancelled Short Order')
        
        
        livetrade_candle_plot.title = "Trade history chart for " + \
            "{} ({} candles)".format(instrument, granularity)
        
        
        ''' Plot backtest trade history '''
        # Create new chart for backtest results 
        backtest_candle_plot        = self.plot_candles(source)
        backtest_candle_plot.x_range = livetrade_candle_plot.x_range
        backtest_candle_plot.y_range = livetrade_candle_plot.y_range
        self.plot_trade_history(backtest_trade_summary, backtest_candle_plot)
        self.plot_cancelled_orders(backtest_cancelled_summary, backtest_candle_plot)
        backtest_candle_plot.title  = "Backtest Trade History for " + \
            "{} ({} candles)".format(instrument, granularity)
        
        ''' Plot portfolio balances '''
        # TODO - reconstruct livetrade balance from trades taken?
        if self.plot_validation_balance:
            top_fig = self.plot_portfolio_history(backtest_NAV, backtest_candle_plot)
            top_fig.line(list(livetrade_summary.data_index.values), 
                          list(livetrade_summary.Balance.fillna(method='bfill').values), 
                          line_color         = 'blue',
                          legend_label       = 'Livetrade Portfolio Balance')
            top_fig.title = "Comparison of Portfolio Balances"
        else:
            top_fig = None
        
        ''' Compile final figure '''
        plots = [top_fig, livetrade_candle_plot, backtest_candle_plot]
        
        for plot in plots:
            if plot is not None:
                plot.xaxis.major_label_overrides = {
                    i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(self.data["date"]))
                }
                plot.xaxis.bounds   = (0, self.data.index[-1])
                plot.sizing_mode    = 'stretch_width'
    
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
        
        fig                 = gridplot(plots, 
                                       ncols            = 1, 
                                       toolbar_location = 'right',
                                       toolbar_options  = dict(logo = None), 
                                       merge_tools      = True
                                       )
        fig.sizing_mode     = 'stretch_width'
        show(fig)

