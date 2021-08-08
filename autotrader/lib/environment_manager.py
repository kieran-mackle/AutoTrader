#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 12:39:11 2021

@author: kieran
"""

def get_config(environment, global_config, feed):
    '''
        Returns the configuration dictionary based on the requested 
        environment.
        
    '''
    
    if environment == 'real':
        if feed == 'OANDA':
            data_source     = 'OANDA'
            api             = global_config['OANDA']['LIVE_API']
            access_token    = global_config['OANDA']['ACCESS_TOKEN']
            account_id      = global_config['OANDA']['DEFAULT_ACCOUNT_ID']
            port            = global_config['OANDA']['PORT']
            
            config_dict = {'data_source'    : data_source,
                           'API'            : api, 
                           'ACCESS_TOKEN'   : access_token, 
                           'ACCOUNT_ID'     : account_id, 
                           'PORT'           : port}
            
        elif feed == 'IB':
            data_source     = 'IB'
            print("Interactive brokers not supported yet.")
            
        elif feed == 'yahoo':
            data_source     = 'yfinance'
            config_dict = {'data_source'    : data_source}
            
        else:
            print("Unrecognised data feed. Please check config and retry.")
            
    
    else:
        if feed.upper() == 'OANDA':
            data_source     = 'OANDA'
            api             = global_config['OANDA']['PRACTICE_API']
            access_token    = global_config['OANDA']['ACCESS_TOKEN']
            account_id      = global_config['OANDA']['DEFAULT_ACCOUNT_ID']
            port            = global_config['OANDA']['PORT']
            
            config_dict = {'data_source'    : data_source,
                           'API'            : api, 
                           'ACCESS_TOKEN'   : access_token, 
                           'ACCOUNT_ID'     : account_id, 
                           'PORT'           : port}
            
        elif feed.upper() == 'IB':
            data_source     = 'IB'
            print("Interactive brokers not supported yet.")
            return
            
        elif feed.upper() == 'YAHOO':
            data_source = 'yfinance'
            config_dict = {'data_source'    : data_source}
            
        else:
            print("Unrecognised data feed {}.".format(feed) + \
                  "Please check global config and retry.")
    
    
    return config_dict