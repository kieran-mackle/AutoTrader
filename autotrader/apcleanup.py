#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoPlot Cleanup
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
from math import pi


class AutoPlot():
    '''
    AutoPlot.
    
    Attributes
    ----------
    data : df
        The base data.
        

    Methods
    -------
    __init__(data):
        Initialise AutoPlot with the lowest timeframe data being used for 
        plotting.
    
    add_tool(tool_name):
        Add bokeh tool to plot.
    
    '''
    def __init__(self, data):
        self.max_indis_over     = 3
        self.max_indis_below    = 2
        self._modified_data     = None
        self.fig_tools          = "pan,wheel_zoom,box_zoom,undo,redo,reset,save,crosshair"
        self.ohlc_height        = 400
        self.ohlc_width         = 800
        self.bottom_fig_height  = 150
        # self.total_height       = 1000
        self.plot_validation_balance = True
        
        # Modify data index
        self.data               = self._reindex_data(data)
        
        
    def add_tool(self, tool_name):
        '''
        Adds a tool to the plot. 
        
            Parameters:
                tool_name (str): name of tool to add (see Bokeh documentation).
        '''
        
        self.fig_tools          = self.fig_tools + "," + tool_name
    
    
    def _reindex_data(self, data):
        '''
        Resets index of data to obtain integer indexing.
        '''
        
        modified_data           = data.copy()
        modified_data['date']   = modified_data.index
        modified_data           = modified_data.reset_index(drop = True)
        
        return modified_data
    
    
    ''' ------------------- FIGURE MANAGEMENT METHODS --------------------- '''
    
    def _plot_indicators(self, indicators, linked_fig):
        ''' 
        Plots indicators based on indicator type. If inidcator type is 
        "over", it will be plotted on top of linked_fig. If indicator type is 
        "below", it will be plotted on a new figure below the OHLC chart.
        '''

        x_range   = self.data.index
        
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
                # The indicator plot type is recognised
                if plot_type[indi_type] == 'over' and indis_over < self.max_indis_over:
                    if indi_type == 'Supertrend':
                        self._plot_supertrend(indicators[indicator]['data'], 
                                              linked_fig)
                        
                        indis_over     += 1 # Count as 2 indicators
                    elif indi_type == 'Swings':
                        self._plot_swings(indicators[indicator]['data'], 
                                          linked_fig)
                    else:
                        # Generic overlay indicator - plot as line
                        linked_fig.line(x_range, 
                                        indicators[indicator]['data'], 
                                        line_width = 1.5, 
                                        legend_label = indicator,
                                        line_color = colours[indis_over])
                    indis_over     += 1
                    
                elif plot_type[indi_type] == 'below' and indis_below < self.max_indis_below:
                    if indi_type == 'MACD':
                        new_fig     = self._plot_macd(x_range,
                                                      indicators[indicator], 
                                                      linked_fig)
                        new_fig.title = indicator
                    
                    elif indi_type == 'Heikin-Ashi':
                        
                        HA_data     = self._reindex_data(indicators[indicator]['data'])
                        source      = ColumnDataSource(HA_data)
                        source.add((HA_data.Close >= HA_data.Open).values.astype(np.uint8).astype(str),
                                   'change')
                        new_fig     = self._plot_candles(source)
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
                # The indicator plot type is not recognised - plotting on new fig
                if indis_below < self.max_indis_below:
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
    
    
    ''' ------------------------ OVERLAY PLOTTING ------------------------- '''
    
    def _plot_candles(self, source):
        ''' Plots OHLC data onto new figure. '''
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
                                  mode          = 'vline',
                                  renderers     = [candles])
        
        candle_plot.add_tools(candle_hovertool)
        
        return candle_plot
    
    def plot_swings(self, swings, linked_fig):
        '''
        Plots swing detection indicator.
        '''
        swings = pd.merge(self.data, swings, left_on='date', right_index=True)
        
        linked_fig.scatter(list(swings.index),
                            list(swings.Last.values),
                            marker = 'dash',
                            size = 15,
                            fill_color = 'black',
                            legend_label = 'Last Swing Price Level')
    
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
    
    
    
    ''' ----------------------- UNDERFIG PLOTTING ------------------------- '''
    
    def _plot_macd(self, x_range, macd_data, linked_fig):
        ''' Plots MACD indicator. '''
        # Initialise figure
        fig = figure(plot_width     = linked_fig.plot_width,
                     plot_height    = self.bottom_fig_height,
                     title          = None,
                     tools          = linked_fig.tools,
                     active_drag    = linked_fig.tools[0],
                     active_scroll  = linked_fig.tools[1],
                     x_range        = linked_fig.x_range)
        
        histcolour = []
        for i in range(len(macd_data['histogram'])):
            if np.isnan(macd_data['histogram'][i]):
                histcolour.append('lightblue')
            else:
                if macd_data['histogram'][i] < 0:
                    histcolour.append('red')
                else:
                    histcolour.append('lightblue')
        
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
    
    # TODO - create generic line plot method
    