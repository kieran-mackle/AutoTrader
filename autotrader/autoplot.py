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
    HoverTool,
    CrosshairTool
)
from bokeh.layouts import gridplot, layout
from bokeh.transform import factor_cmap, cumsum
from bokeh.palettes import Category20c, GnBu3, OrRd3, Category20
from math import pi


class AutoPlot():
    
    def __init__(self):
        self.data               = None
        self.max_indis_over     = 3
        self.max_indis_below    = 2
        self._modified_data     = None
        self.fig_tools          = "pan,wheel_zoom,box_zoom,undo,redo,reset,save,crosshair"
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
    
    def plot_backtest(self, backtest_dict, cumulative_PL=None):
        ''' Creates backtest figure. '''
        NAV             = backtest_dict['NAV']
        trade_summary   = backtest_dict['trade_summary']
        indicators      = backtest_dict['indicators']
        pair            = backtest_dict['instrument']
        interval        = backtest_dict['interval']
        open_trades     = backtest_dict['open_trades']
        cancelled_trades = backtest_dict['cancelled_trades']
        
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
        if len(cancelled_trades) > 0:
            self.plot_partial_orders(cancelled_trades, candle_plot)
        if len(open_trades) > 0:
            self.plot_partial_orders(open_trades, candle_plot, cancelled_orders=False)
        
        # Plot indicators
        if indicators is not None:
            bottom_figs             = self.plot_indicators(indicators, candle_plot)
        else:
            bottom_figs             = []
        
        
        # Auto-scale y-axis of candlestick chart
        autoscale_args      = dict(y_range  = candle_plot.y_range, 
                                   source   = source)
        candle_plot.x_range.js_on_change('end', CustomJS(args = autoscale_args, 
                                                         code = autoscale_code))
        
        # Above plots
        top_fig         = self.plot_portfolio_history(NAV, candle_plot)
        if cumulative_PL is not None:
            self.plot_cumulative_pl(cumulative_PL, top_fig, NAV[0])
        
        # Compile plots for final figure
        plots               = [top_fig, candle_plot] + bottom_figs
        
        linked_crosshair    = CrosshairTool(dimensions='both')
        
        titled  = 0
        t       = Title()
        t.text  = "Backtest chart for {} ({} candles)".format(pair, interval)
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
                
                plot.add_tools(linked_crosshair)
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
    
    
    def plot_multibot_backtest(self, multibot_backtest_results, NAV, cpl_dict):
        ''' 
        Creates multi-bot backtest figure. 
        
            Parameters:
                multibot_backtest_results (df): dataframe of bot backtest results.
                
                NAV (list): Net asset value.
                
                cpl_dict (dict): cumulative PL of each bot.
        '''
        
        # Preparation ----------------------------------- #
        output_file("candlestick.html",
                    title = "AutoTrader Multi-Bot Backtest Results")
        
        if self._modified_data is None:
            self._reindex_data()
        # source                  = ColumnDataSource(self._modified_data)
        # source.add((self._modified_data.Close >= self._modified_data.Open).values.astype(np.uint8).astype(str),
        #             'change')
        
        # TODO - Load JavaScript code for auto-scaling - use for NAV
        # with open(os.path.join(os.path.dirname(__file__), 'lib/autoscale.js'),
        #           encoding = 'utf-8') as _f:
        #     autoscale_code      = _f.read()
        
        linked_crosshair    = CrosshairTool(dimensions='both')
        if len(multibot_backtest_results) < 3:
            multibot_backtest_results['color'] = Category20c[3][0:len(multibot_backtest_results)]
        else:
            multibot_backtest_results['color'] = Category20c[len(multibot_backtest_results)]
            
        MBR = ColumnDataSource(multibot_backtest_results)
        
        # ----------------------- Account Balance -------------------------- #
        navfig = figure(plot_width = 800,
                        plot_height = 150,
                        title = None,
                        active_drag = 'pan',
                        active_scroll = 'wheel_zoom')
        
        # Add glyphs
        navfig.line(self._modified_data.index, 
                    NAV, 
                    line_color = 'black',
                    legend_label = 'Backtest Net Asset Value')
        
        navfig.xaxis.major_label_overrides = {
                    i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(self._modified_data["date"]))
                }
        navfig.xaxis.bounds = (0, self._modified_data.index[-1])
        navfig.sizing_mode = 'stretch_width'
        navfig.legend.location = 'top_left'
        navfig.legend.border_line_width   = 1
        navfig.legend.border_line_color   = '#333333'
        navfig.legend.padding             = 5
        navfig.legend.spacing             = 0
        navfig.legend.margin              = 0
        navfig.legend.label_text_font_size = '8pt'
        navfig.add_tools(linked_crosshair)
        
        # ----------------------- Win rate bar chart ----------------------- #
        instruments = multibot_backtest_results.index.values
        
        winrate = figure(x_range = instruments,
                         title = "Bot win rate (%)",
                         toolbar_location = None,
                         tools = 'hover',
                         tooltips = "@index: @win_rate%",
                         plot_height = 250)
        
        winrate.vbar(x = 'index', 
                     top = 'win_rate',
                     width = 0.9,
                     color = 'color',
                     source = MBR)
        
        winrate.sizing_mode = 'stretch_width'
        
        
        # ----------------- Pie chart of trades per bot --------------------- #
        pie_data = pd.Series(multibot_backtest_results.no_trades).reset_index(name='value').rename(columns={'index':'instrument'})
        pie_data['angle'] = pie_data['value']/pie_data['value'].sum() * 2*pi
        if len(multibot_backtest_results) < 3:
            pie_data['color'] = Category20c[3][0:len(multibot_backtest_results)]
        else:
            pie_data['color'] = Category20c[len(multibot_backtest_results)]

        pie = figure(title = "Trade distribution", 
                     toolbar_location = None,
                     tools = "hover", 
                     tooltips="@instrument: @value",
                     x_range=(-1, 1),
                     y_range=(0.0, 2.0),
                     plot_height = 250)
        
        pie.wedge(x=0, y=1, radius=0.3,
                  start_angle=cumsum('angle', include_zero=True), 
                  end_angle=cumsum('angle'),
                  line_color="white", 
                  fill_color='color',
                  legend_field='instrument',
                  source=pie_data)
        
        pie.axis.axis_label=None
        pie.axis.visible=False
        pie.grid.grid_line_color = None
        pie.sizing_mode = 'stretch_width'
        pie.legend.location = "top_left"
        pie.legend.border_line_width   = 1
        pie.legend.border_line_color   = '#333333'
        pie.legend.padding             = 5
        pie.legend.spacing             = 0
        pie.legend.margin              = 0
        pie.legend.label_text_font_size = '8pt'
        
        # --------------- Bar plot for avg/max win/loss -------------------- #
        win_metrics = ['Average Win', 'Max. Win']
        lose_metrics = ['Average Loss', 'Max. Loss']
        
        abs_max_loss = -1.2*max(multibot_backtest_results.max_loss)
        abs_max_win = 1.2*max(multibot_backtest_results.max_win)
        
        pldata = {'instruments': instruments,
                'Average Win': multibot_backtest_results.avg_win.values,
                'Max. Win': multibot_backtest_results.max_win.values - 
                            multibot_backtest_results.avg_win.values,
                'Average Loss': -multibot_backtest_results.avg_loss.values,
                'Max. Loss': multibot_backtest_results.avg_loss.values - 
                             multibot_backtest_results.max_loss.values}
        
        TOOLTIPS = [
                    ("Instrument:", "@instruments"),
                    ("Max win", "@{Max. Win}"),
                    ("Avg. win", "@{Average Win}"),
                    ("Max Loss", "@{Max. Loss}"),
                    ("Avg. loss", "@{Average Loss}"),
                    ]
        
        plbars = figure(x_range=instruments,
                        y_range=(abs_max_loss, abs_max_win),
                        title="Win/Loss breakdown",
                        toolbar_location=None,
                        tools = "hover",
                        tooltips = TOOLTIPS,
                        plot_height = 250)

        plbars.vbar_stack(win_metrics,
                     x='instruments',
                     width = 0.9,
                     color = ('#008000', '#FFFFFF'),
                     line_color='black',
                     source = ColumnDataSource(pldata),
                     legend_label = ["%s" % x for x in win_metrics])

        plbars.vbar_stack(lose_metrics,
                     x = 'instruments',
                     width = 0.9,
                     color = ('#ff0000' , '#FFFFFF'),
                     line_color='black',
                     source = ColumnDataSource(pldata),
                     legend_label = ["%s" % x for x in lose_metrics])
        
        plbars.x_range.range_padding = 0.1
        plbars.ygrid.grid_line_color = None
        plbars.legend.location = "bottom_center"
        plbars.legend.border_line_width   = 1
        plbars.legend.border_line_color   = '#333333'
        plbars.legend.padding             = 5
        plbars.legend.spacing             = 0
        plbars.legend.margin              = 0
        plbars.legend.label_text_font_size = '8pt'
        plbars.axis.minor_tick_line_color = None
        plbars.outline_line_color = None
        plbars.sizing_mode = 'stretch_width'
    
    
        # --------------------- Cumulative PL ------------------------------ #
        cplfig = figure(plot_width = navfig.plot_width,
                        plot_height = 150,
                        title = None,
                        active_drag = 'pan',
                        active_scroll = 'wheel_zoom',
                        x_range = navfig.x_range)
        
        self.data['data_index'] = self.data.reset_index(drop=True).index
        
        if len(multibot_backtest_results) < 3:
            colors = Category20c[3][0:len(multibot_backtest_results)]
        else:
            colors = Category20c[len(multibot_backtest_results)]
        
        
        for ix, instrument in enumerate(cpl_dict):
            cpldata = cpl_dict[instrument].copy().to_frame()
            cpldata['date'] = cpldata.index
            cpldata         = cpldata.reset_index(drop = True)
            
            cpldata = pd.merge(self.data, cpldata, left_on='date', right_on='date')
            
            cplfig.line(cpldata.data_index.values,
                        cpldata.Profit.values,
                        legend_label = "{}".format(instrument),
                        line_color = colors[ix])
        
        cplfig.legend.location = 'top_left'
        cplfig.legend.border_line_width   = 1
        cplfig.legend.border_line_color   = '#333333'
        cplfig.legend.padding             = 5
        cplfig.legend.spacing             = 0
        cplfig.legend.margin              = 0
        cplfig.legend.label_text_font_size = '8pt'
        cplfig.sizing_mode = 'stretch_width'
        cplfig.add_tools(linked_crosshair)
        
        cplfig.xaxis.major_label_overrides = {
                    i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(self._modified_data["date"]))
                }
        cplfig.xaxis.bounds   = (0, self._modified_data.index[-1])
        
        # -------------------- Construct final figure ---------------------- #     
        final_fig = layout([  
                                   [navfig],
                            [winrate, pie, plbars],
                                   [cplfig]
                        ])
        final_fig.sizing_mode = 'scale_width'
        show(final_fig)
        
    
    def view_indicators(self, indicators=None, instrument=None):
        ''' Constructs indicator visualisation figure. '''
        # Preparation ----------------------------------- #
        if instrument is not None:
            title_string = "AutoTrader IndiView - {}".format(instrument)
        else:
            title_string = "AutoTrader IndiView"
        output_file("candlestick.html",
                    title = title_string)
        
        if self._modified_data is None:
            self._reindex_data()
        
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
        candle_plot.title       = title_string
        
        # Plot indicators
        if indicators is not None:
            bottom_figs             = self.plot_indicators(indicators, candle_plot)
        else:
            bottom_figs             = []
        
        # Auto-scale y-axis of candlestick chart
        autoscale_args          = dict(y_range  = candle_plot.y_range, 
                                       source   = source)
        candle_plot.x_range.js_on_change('end', CustomJS(args = autoscale_args, 
                                                         code = autoscale_code))
        
        plots = [candle_plot] + bottom_figs
        
        for plot in plots:
            if plot is not None:
                plot.xaxis.major_label_overrides = {
                    i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(self._modified_data["date"]))
                }
                plot.xaxis.bounds   = (0, self._modified_data.index[-1])
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
                     'Crossover'   : 'below',
                     'over'        : 'over',
                     'below'       : 'below'}
        
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
        # Merge index to base data time
        swings = pd.merge(self.data, swings, left_on='date', right_index=True)
        
        linked_fig.scatter(list(swings.index),
                            list(swings.Last.values),
                            marker = 'dash',
                            size = 15,
                            fill_color = 'black',
                            legend_label = 'Last Swing Price Level')
        
    
    def plot_partial_orders(self, cancelled_order_summary, linked_fig, 
                            cancelled_orders=True):
        ts              = cancelled_order_summary
        ts['date']      = ts.index 
        ts              = ts.reset_index(drop = True)
        
        # Compute x-range in integer index form
        if self._modified_data is None:
            self._reindex_data()
        
        trade_summary   = pd.merge(self.data, ts, left_on='date', right_on='date')

        
        longs           = trade_summary[trade_summary.Size > 0]
        shorts          = trade_summary[trade_summary.Size < 0]
        
        if cancelled_orders:
            long_legend_label = 'Cancelled long trades'
            short_legend_label = 'Cancelled short trades'
            fill_color = 'black'
            price = 'Order_price'
        else:
            long_legend_label = 'Open long trades'
            short_legend_label = 'Open short trades'
            fill_color = 'white'
            price = 'Entry'
        
        # Partial long trades
        if len(longs) > 0:
            linked_fig.scatter(list(longs.data_index.values),
                               list(longs[price].values),
                               marker = 'triangle',
                               size = 15,
                               fill_color = fill_color,
                               legend_label = long_legend_label)
        
        # Partial short trades
        if len(shorts) > 0:
            linked_fig.scatter(list(shorts.data_index.values),
                               list(shorts[price].values),
                               marker = 'inverted_triangle',
                               size = 15,
                               fill_color = fill_color,
                               legend_label = short_legend_label)
            
        if None not in trade_summary.Stop_loss.values:
            linked_fig.scatter(list(trade_summary.data_index.values),
                                list(trade_summary.Stop_loss.values),
                                marker = 'dash',
                                size = 15,
                                fill_color = 'black',
                                legend_label = 'Stop loss')
        
        if None not in trade_summary.Take_profit.values:
            linked_fig.scatter(list(trade_summary.data_index.values),
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
        # ts_xrange   = self._modified_data[self._modified_data.date.isin(trade_summary.index)].index
        # trade_summary = ts.set_index(ts_xrange)
        
        
        # Assign new 'data_index' column to capture index in trade summary merge
        self.data['data_index'] = self._modified_data.index
        trade_summary = pd.merge(self.data, ts, left_on='date', right_on='date')
        exit_summary = pd.merge(self.data, ts, left_on='date', right_on='Exit_time')
        
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
            linked_fig.scatter(list(profitable_longs.data_index.values),
                               list(profitable_longs.Entry.values),
                               marker = 'triangle',
                               size = 15,
                               fill_color = 'lightgreen',
                               legend_label = 'Profitable long trades')
        
        # Profitable short trades
        if len(profitable_shorts) > 0:
            linked_fig.scatter(list(profitable_shorts.data_index.values),
                               list(profitable_shorts.Entry.values),
                               marker = 'inverted_triangle',
                               size = 15,
                               fill_color = 'lightgreen',
                               legend_label = 'Profitable short trades')
        
        # Unprofitable long trades
        if len(unprofitable_longs) > 0:
            linked_fig.scatter(list(unprofitable_longs.data_index.values),
                               list(unprofitable_longs.Entry.values),
                               marker = 'triangle',
                               size = 15,
                               fill_color = 'orangered',
                               legend_label = 'Unprofitable long trades')
        
        # Unprofitable short trades
        if len(unprofitable_shorts) > 0:
            linked_fig.scatter(list(unprofitable_shorts.data_index.values),
                               list(unprofitable_shorts.Entry.values),
                               marker = 'inverted_triangle',
                               size = 15,
                               fill_color = 'orangered',
                               legend_label = 'Unprofitable short trades')
        
        # Stop loss  levels
        if None in trade_summary.Stop_loss.values:
            pass
        else:
            linked_fig.scatter(list(trade_summary.data_index.values),
                                list(trade_summary.Stop_loss.values),
                                marker = 'dash',
                                size = 15,
                                fill_color = 'black',
                                legend_label = 'Stop loss')
        
        # Take profit levels
        if None in trade_summary.Take_profit.values:
            pass
        else:
            linked_fig.scatter(list(trade_summary.data_index.values),
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

    
    def plot_cumulative_pl(self, cumulative_PL, linked_fig, offset=0):
        ''' Plots cumulative PL of bot. '''
        cpldata = cumulative_PL.to_frame()
        cpldata['date'] = cpldata.index
        cpldata = cpldata.reset_index(drop = True)
        cpldata = pd.merge(self.data, cpldata, left_on='date', right_on='date')
        
        # # Initialise figure
        # fig = figure(plot_width     = linked_fig.plot_width,
        #               plot_height    = 150,
        #               title          = None,
        #               tools          = self.fig_tools,
        #               active_drag    = 'pan',
        #               active_scroll  = 'wheel_zoom',
        #               x_range        = linked_fig.x_range)
        
        # Add glyphs
        linked_fig.step(cpldata.data_index.values,
                 cpldata.Profit.values + offset,
                 line_color         = 'blue',
                 legend_label       = 'Cumulative P/L')
    
        # return fig
    
    
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
        source = ColumnDataSource(self.data)
        source.add(NAV, 'NAV')
        fig.line('data_index', 
                 'NAV', 
                 line_color         = 'black',
                 legend_label       = 'Backtest Net Asset Value',
                 source             = source)
    
        
        # tooltips       = "NAV: $@NAV" ,
        fig_hovertool = HoverTool(tooltips = "NAV: $@{NAV}{%0.2f}", 
                                  formatters={'@{NAV}' : 'printf'},
                                  mode = 'vline')
        
        fig.add_tools(fig_hovertool)
        
        return fig
    
    
    def validate_backtest(self, livetrade_summary, backtest_dict):
        """
            Code below takes oanda csv history and plots it.
            
            When a position is opened, it will be shown as a triangle with no fill (open).
            It will point in the direction of the trade.
            
            When a position is closed, it will be shown as a triangle with red or green 
            fill, depending on if it was profitable or not. It will point in the direction 
            of the closing trade.
            
        """
        backtest_trade_summary  = backtest_dict['trade_summary']
        backtest_cancelled_summary = backtest_dict['cancelled_trades']
        backtest_NAV            = backtest_dict['NAV']
        instrument              = backtest_dict['pair']
        granularity             = backtest_dict['interval']
        
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
        self.plot_partial_orders(backtest_cancelled_summary, backtest_candle_plot)
        backtest_candle_plot.title  = "Backtest Trade History for " + \
            "{} ({} candles)".format(instrument, granularity)
        
        ''' Plot portfolio balances '''
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

