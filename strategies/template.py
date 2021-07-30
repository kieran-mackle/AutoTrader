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
        
        # Construct indicators dict for plotting
        self.indicators = {}
        
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
    