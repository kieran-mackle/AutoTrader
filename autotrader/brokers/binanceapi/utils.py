#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module: brokers.binanceapi.utils
Purpose: Utility functions for Binance broker wrapper
Author: Kieran Mackle
'''

import pandas as pd
from datetime import datetime
from autotrader.brokers.broker_utils import BrokerUtils


class Utils(BrokerUtils):
    def __init__(self):
        return
    
    def bars_to_df(self, bars):
        ''' Function to convert Binance klines to Pandas dataframe. '''
        for line in bars:
            del line[5:]
            
        data = pd.DataFrame(bars, columns=['date', 'Open', 'High', 'Low', 'Close'])
        dates = [datetime.fromtimestamp(timestamp/1000) for timestamp in data.date.values]
        
        data.index = dates
        
        return data.drop(['date'], axis=1)

