#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module: lib.environment_manager
Purpose: Construct configuration dictionary based on trading environment
Author: Kieran Mackle
'''

def get_config(environment, global_config, feed):
    '''
        Returns the configuration dictionary based on the requested 
        environment.
        
    '''
    
    if environment.lower() == 'real':
        # Live trading
        if feed.upper() == 'OANDA':
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
            
        elif feed.upper() == 'IB':
            print("WARNING: Interactive brokers not fully supported yet.")
            
            data_source = 'IB'
            config_dict = {'data_source'    : data_source}
            # Any extra information will be added to the config_dict above
            
        elif feed.lower() == 'yahoo':
            data_source = 'yfinance'
            config_dict = {'data_source'    : data_source}
            
        else:
            print("Unrecognised data feed. Please check config and retry.")
            
    
    else:
        # Paper trading
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
            print("WARNING: Interactive brokers not fully supported yet.")
            
            data_source = 'IB'
            config_dict = {'data_source'    : data_source}
            # Any extra information will be added to the config_dict above
            
            
        elif feed.upper() == 'YAHOO':
            data_source = 'yfinance'
            config_dict = {'data_source'    : data_source}
            
        else:
            print("Unrecognised data feed {}.".format(feed) + \
                  "Please check global config and retry.")
    
    
    return config_dict