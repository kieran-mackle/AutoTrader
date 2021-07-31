#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function to parse scan request and return watchlist.

"""
import sys

def get_watchlist(index):
    
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
                     'NZD_USD'
                     ]
    
    elif index == 'major':
        ''' Returns major currency pairs. '''
        watchlist = ['EUR_USD', 
                     'USD_JPY', 
                     'GBP_USD', 
                     'AUD_USD', 
                     'USD_CAD', 
                     'USD_CHF', 
                     'NZD_USD'
                     ]
        
    elif index == 'minor':
        ''' Returns minor currency pairs. '''
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


