#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module: lib.instrument_list
Purpose: Returns instrument list of indices
Author: Kieran Mackle
'''

import sys

def get_watchlist(index, feed):
    '''
    This code is currently in development.
    
    Returns a watchlist of instruments. 
    
    Objectives: 
        - return specific list of instruments based on input
          For example; 
              - forex:major -> major forex pairs
              - stocks:asx200
              - custom
    
    The current implementation only support forex indices, with Oanda 
    formatting.
    
    '''
    
    if len(index) == 0:
        print("\nArgument for scan missing. Please specify instrument/index to scan.")
        print("Try $ ./AutoTrader.py -h s for more help.\n")
        sys.exit(0)
    
    if index == 'all':
        ''' Returns all currency pairs. '''
        watchlist = ['EUR_USD', 
                     'USD_JPY', 
                     'GBP_USD', 
                     'AUD_USD', 
                     'USD_CAD', 
                     'USD_CHF', 
                     'NZD_USD',
                     'EUR_GBP',
                     'EUR_AUD',
                     'EUR_CAD',
                     'EUR_CHF',
                     'EUR_JPY',
                     'EUR_NZD',
                     'GBP_JPY',
                     'GBP_AUD',
                     'GBP_CAD',
                     'GBP_CHF',
                     'GBP_NZD',
                     'AUD_CAD',
                     'AUD_CHF',
                     'AUD_JPY',
                     'AUD_NZD',
                     'CAD_CHF',
                     'CAD_JPY',
                     'CHF_JPY',
                     'NZD_CHF',
                     'NZD_JPY',
                     ]
    
    elif index == 'major':
        ''' Returns major currency pairs. '''
        if feed.lower() == 'oanda':
            watchlist = ['EUR_USD', 
                         'USD_JPY', 
                         'GBP_USD', 
                         'AUD_USD', 
                         'USD_CAD', 
                         'USD_CHF', 
                         'NZD_USD'
                         ]
            
        elif feed.lower() == 'yahoo':
            watchlist = ['EURUSD=X', 
                         'USDJPY=X', 
                         'GBPUSD=X', 
                         'AUDUSD=X', 
                         'USDCAD=X', 
                         'USDCHF=X', 
                         'NZDUSD=X'
                         ]
        
    elif index == 'minor':
        ''' Returns minor currency pairs. '''
        
        if feed.lower() == 'oanda':
            watchlist = ['EUR_GBP',
                         'EUR_AUD',
                         'EUR_CAD',
                         'EUR_CHF',
                         'EUR_JPY',
                         'EUR_NZD',
                         'GBP_JPY',
                         'GBP_AUD',
                         'GBP_CAD',
                         'GBP_CHF',
                         'GBP_NZD',
                         'AUD_CAD',
                         'AUD_CHF',
                         'AUD_JPY',
                         'AUD_NZD',
                         'CAD_CHF',
                         'CAD_JPY',
                         'CHF_JPY',
                         'NZD_CHF',
                         'NZD_JPY']
            
        elif feed.lower() == 'yahoo':
            watchlist = ['EURGBP=X',
                         'EURAUD=X',
                         'EURCAD=X',
                         'EURCHF=X',
                         'EURJPY=X',
                         'EURNZD=X',
                         'GBPJPY=X',
                         'GBPAUD=X',
                         'GBPCAD=X',
                         'GBPCHF=X',
                         'GBPNZD=X',
                         'AUDCAD=X',
                         'AUDCHF=X',
                         'AUDJPY=X',
                         'AUDNZD=X',
                         'CADCHF=X',
                         'CADJPY=X',
                         'CHFJPY=X',
                         'NZDCHF=X',
                         'NZDJPY=X']
    
    elif index == 'exotic':
        ''' Returns exotic currency pairs. '''
        watchlist = ['EUR_TRY',
        	      'USD_HKD',
        	      'JPY_NOK',
        	      'NZD_SGD',
        	      'GBP_ZAR',
        	      'AUD_MXN']
    
    
    elif index[3] == "_":
        watchlist = [index]
    
    else:
        print("Not supported.")
        sys.exit(0)

    
    return watchlist


