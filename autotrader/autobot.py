#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module: AutoBot
Purpose: trading bot deplyed by AutoTrader
Author: Kieran Mackle
'''

import sys
import os
import importlib
import time
import pytz
import pandas as pd
import numpy as np
import threading
from shutil import copy2
from datetime import datetime
from autotrader.emailing import emailing
from autotrader.lib import autodata, environment_manager
from autotrader.lib.read_yaml import read_yaml
from autotrader.autostream import AutoStream


class AutoTraderBot():
    '''
    AutoTrader Bot
    ---------------
    
    Attributes
    ----------
    broker : class
        The broker class instance.
        
    instrument : str
        The instrument being traded by the bot.
    
    strategy : class
         The strategy being traded by the bot.
    

    Methods
    -------
    update(i):
        Update strategy with latest data and generate latest signal.
    
    '''
    
    def __init__(self, instrument, strategy_config, broker, data_dict, autotrader_instance):
        '''
        AutoTrader Bot initialisation. 
        '''

        # Inherit user options from autotrader
        self.home_dir           = autotrader_instance.home_dir
        self.scan_mode          = autotrader_instance.scan_mode
        self.scan_index         = autotrader_instance.scan_index
        self.scan_results       = {}
        self.broker_utils       = autotrader_instance.broker_utils
        self.email_params       = autotrader_instance.email_params
        self.notify             = autotrader_instance.notify
        self.verbosity          = autotrader_instance.verbosity
        self.order_summary_fp   = autotrader_instance.order_summary_fp
        self.backtest_mode      = autotrader_instance.backtest_mode
        self.data_start         = autotrader_instance.data_start
        self.data_end           = autotrader_instance.data_end
        self.base_currency      = autotrader_instance.backtest_base_currency
        self.environment        = autotrader_instance.environment
        self.feed               = autotrader_instance.feed
        self.data_file          = autotrader_instance.data_file
        self.MTF_data_files     = autotrader_instance.MTF_data_files
        self.optimise_mode      = autotrader_instance.optimise_mode
        self.check_data_alignment = autotrader_instance.check_data_alignment
        self.allow_dancing_bears = autotrader_instance.allow_dancing_bears
        self.use_stream         = autotrader_instance.use_stream
        self.stream_config      = autotrader_instance.stream_config
        self.MTF_initialisation = autotrader_instance.MTF_initialisation
        
        # Assign local attributes
        self.instrument         = instrument
        self.broker             = broker
        
        # Unpack strategy parameters and assign to strategy_params
        interval                = strategy_config["INTERVAL"]
        period                  = strategy_config["PERIOD"]
        risk_pc                 = strategy_config["RISK_PC"] if 'RISK_PC' in strategy_config else 0
        sizing                  = strategy_config["SIZING"] if 'SIZING' in strategy_config else 0
        params                  = strategy_config["PARAMETERS"]
        strategy_params                 = params
        strategy_params['granularity']  = strategy_params['granularity'] if 'granularity' in strategy_params else interval
        strategy_params['risk_pc']      = strategy_params['risk_pc'] if 'risk_pc' in strategy_params else risk_pc
        strategy_params['sizing']       = strategy_params['sizing'] if 'sizing' in strategy_params else sizing
        strategy_params['period']       = strategy_params['period'] if 'period' in strategy_params else period
        self.strategy_params            = strategy_params
        
        # Import Strategy
        strat_module            = strategy_config["MODULE"]
        strat_name              = strategy_config["CLASS"]
        strat_package_path      = os.path.join(self.home_dir, "strategies") 
        strat_module_path       = os.path.join(strat_package_path, strat_module) + '.py'
        strat_spec              = importlib.util.spec_from_file_location(strat_module, strat_module_path)
        strategy_module         = importlib.util.module_from_spec(strat_spec)
        strat_spec.loader.exec_module(strategy_module)
        strategy                = getattr(strategy_module, strat_name)
        
        # Get broker configuration 
        global_config_fp = os.path.join(self.home_dir, 'config', 'GLOBAL.yaml')
        if os.path.isfile(global_config_fp):
            global_config = read_yaml(global_config_fp)
        else:
            global_config = None
        broker_config  = environment_manager.get_config(self.environment,
                                                        global_config,
                                                        self.feed)
   
        # Start price streaming
        if self.use_stream and self.backtest_mode is False:
            
            # Check how many granularities were requested
            if len(interval.split(',')) > 1:
                # MTF strategy
                self.base_interval = interval.split(',')[0]
                self.MTF_intervals = interval.split(',')[1:]
                
                # Initiate time_to_download dict
                self.time_to_download = {}
                for granularity in self.MTF_intervals:
                    self.time_to_download[granularity] = datetime.now(tz=pytz.utc)
                
            else:
                # Single timeframe strategy
                self.base_interval = interval
                self.MTF_intervals = []
            
            # Start stream
            self._initiate_stream()

        # Multiple time-frame initialisation option
        if self.MTF_initialisation:
            # Only retrieve MTF_data once upon initialisation and store
            # instantiation MTF_data
            self.MTF_data = None
        
        # Data retrieval
        if data_dict is not None:
            # Local data files provided
            self.abs_data_filepath = True
            if type(data_dict) == str:
                # Single timeframe data file provided
                self.data_file = data_dict
            else:
                # MTF data provided
                self.MTF_data_files = data_dict
        else:
            self.abs_data_filepath = False
        
        self.get_data = autodata.GetData(broker_config, self.allow_dancing_bears)
        data, quote_data, MTF_data = self._retrieve_data(instrument, self.feed)
        
        # Data assignment
        if MTF_data is None:
            strat_data = data
        else:
            strat_data = MTF_data
        
        # Instantiate Strategy
        include_broker = strategy_config['INCLUDE_BROKER'] if 'INCLUDE_BROKER' in strategy_config else False
        if include_broker:
            my_strat = strategy(params, strat_data, instrument, self.broker, self.broker_utils)
        else:
            my_strat = strategy(params, strat_data, instrument)
            
        # Assign strategy to local attributes
        self.strategy           = my_strat
        self.data               = data
        self.quote_data         = quote_data
        self.latest_orders      = []
        
        # Assign strategy attributes for tick-based strategy development
        if self.backtest_mode:
            self.strategy._backtesting = True
        if interval.split(',')[0] == 'tick':
            self.strategy._tick_data = True
        
        if int(self.verbosity) > 0:
                print("\nAutoTraderBot assigned to trade {}".format(instrument),
                      "on {} timeframe using {}.".format(self.strategy_params['granularity'],
                                                         strategy_config['NAME']))
    
    
    def _initiate_stream(self):
        '''
        Spawns AutoStream into a new thread.
        '''
        
        record_ticks = False
        record_candles = False
        if self.base_interval == 'tick' or self.base_interval == 'ticks':
            record_ticks = True
        else:
            record_candles = True
        
        
        stream_granularity = self.base_interval
        self.no_candles = self.strategy_params['period']
        
        self.AS = AutoStream(self.home_dir, 
                             self.stream_config, 
                             self.instrument, 
                             granularity = stream_granularity,
                             record_ticks = record_ticks, 
                             record_candles = record_candles,
                             no_candles = self.no_candles,
                             bot = self)
        
        stream_thread = threading.Thread(target = self.AS.start, 
                                         args=(), daemon=False)
        print('Spawning new thread to stream data.')
        stream_thread.start()
        
    
    def _recieve_stream_data(self):
        '''
        Method to tell AutoStream to send data to bot. Called from bot manager.
        '''
        
        self.AS.update_bot = True
    
    def _update_strategy_data(self, data=None):
        '''
        Method to update strategy with latest data. Called by the bot manager
        and autostream.
        '''
        
        if data is not None:
            # Update data attribute (for livetrade compatibility)
            self.data = data
        
        # Retrieve new data
        new_data, _, MTF_data = self._retrieve_data(self.instrument, 
                                                    self.feed,
                                                    base_data = data)
        
        # Check for MTF_data
        if MTF_data is None:
            strat_data = new_data
        else:
            strat_data = MTF_data
        
        # Update strategy with new data
        self.strategy.initialise_strategy(strat_data)
        
    
    def _retrieve_data(self, instrument, feed, base_data = None):
        '''
        Retrieves price data from AutoData.
        '''
        
        interval    = self.strategy_params['granularity']
        period      = self.strategy_params['period']
        price_data_path = os.path.join(self.home_dir, 'price_data')
        
        if self.backtest_mode is True:
            ' ~~~~~~~~~~~~~~~~~~~ Running in backtest mode ~~~~~~~~~~~~~~~~~~ '
            self.get_data.base_currency = self.base_currency
            
            from_date       = self.data_start
            to_date         = self.data_end
            
            if self.data_file is not None:
                # Read local data file
                custom_data_file        = self.data_file
                custom_data_filepath    = os.path.join(price_data_path, custom_data_file) if not self.abs_data_filepath else custom_data_file
                if int(self.verbosity) > 1:
                    print("Using data file specified ({}).".format(custom_data_file))
                data            = pd.read_csv(custom_data_filepath, 
                                              index_col = 0)
                data.index = pd.to_datetime(data.index, utc=True)
                quote_data = data
                
                MTF_data = None
            
            elif self.MTF_data_files is not None:
                # Read local MTF data files
                MTF_data_files = self.MTF_data_files
                MTF_granularities = list(MTF_data_files.keys())
                
                MTF_data = {}
                for granularity in MTF_data_files:
                    # Extract data 
                    custom_data_file = MTF_data_files[granularity]
                    custom_data_filepath = os.path.join(price_data_path, custom_data_file) if not self.abs_data_filepath else custom_data_file
                    if int(self.verbosity) > 1:
                        print("Using data file specified ({}).".format(MTF_data_files[granularity]))
                    data = pd.read_csv(custom_data_filepath, index_col = 0)
                    data.index = pd.to_datetime(data.index, utc=True)
                    
                    if granularity == MTF_granularities[0]:
                        quote_data = data
                    
                    # Add to MTF_data dict
                    MTF_data[granularity] = data
                
                # Extract first dataset to use as base
                first_granularity = MTF_granularities[0]
                data = MTF_data[first_granularity]
                quote_data = quote_data
                
            else:
                # No data file(s) provided, proceed to download
                if int(self.verbosity) > 1:
                    print("\nDownloading OHLC price data for {}.".format(instrument))
                
                if self.optimise_mode is True:
                    # Check if historical data already exists
                    historical_data_name = 'hist_{0}{1}.csv'.format(interval, instrument)
                    historical_quote_data_name = 'hist_{0}{1}_quote.csv'.format(interval, instrument)
                    data_dir_path = os.path.join(self.home_dir, 'price_data')
                    historical_data_file_path = os.path.join(self.home_dir, 
                                                             'price_data',
                                                             historical_data_name)
                    historical_quote_data_file_path = os.path.join(self.home_dir, 
                                                             'price_data',
                                                             historical_quote_data_name)
                    
                    if not os.path.exists(historical_data_file_path):
                        # Data file does not yet exist
                        data        = getattr(self.get_data, feed.lower())(instrument,
                                                         granularity = interval,
                                                         start_time = from_date,
                                                         end_time = to_date)
                        quote_data  = getattr(self.get_data, feed.lower() + '_quote_data')(data,
                                                                                      instrument,
                                                                                      interval,
                                                                                      from_date,
                                                                                      to_date)
                        data, quote_data    = self.broker_utils.check_dataframes(data, quote_data)
                        
                        # Check if price_data folder exists
                        if not os.path.exists(data_dir_path):
                            # If price data directory doesn't exist, make it
                            os.makedirs(data_dir_path)
                            
                        # Save data in file/s
                        data.to_csv(historical_data_file_path)
                        quote_data.to_csv(historical_quote_data_file_path)
                        
                    else:
                        # Data file does exist, import it as dataframe
                        data = pd.read_csv(historical_data_file_path, 
                                           index_col = 0)
                        quote_data = pd.read_csv(historical_quote_data_file_path, 
                                                 index_col = 0)
                    
                    # TODO - add support of MTF for optimisation
                    MTF_data = None
                        
                else:
                    # Running in single backtest mode
                    MTF_data = {}
                    for granularity in interval.split(','):
                        data        = getattr(self.get_data, feed.lower())(instrument,
                                                             granularity = granularity,
                                                             start_time = from_date,
                                                             end_time = to_date)
                        
                        # Only get quote data for first granularity
                        if granularity == interval.split(',')[0]:
                            quote_data  = getattr(self.get_data, feed.lower() + '_quote_data')(data,
                                                                            instrument,
                                                                            granularity,
                                                                            from_date,
                                                                            to_date)
                        
                            data, quote_data = self.broker_utils.check_dataframes(data.drop_duplicates(), 
                                                                                  quote_data.drop_duplicates())
                        
                        MTF_data[granularity] = data
                    
                    # Extract first dataset to use as base
                    first_granularity = interval.split(',')[0]
                    data = MTF_data[first_granularity]
                    quote_data = quote_data
                
                if MTF_data is not None and len(MTF_data) == 1:
                    MTF_data = None
                
                if int(self.verbosity) > 1:
                    print("  Done.\n")
            
            return data, quote_data, MTF_data
        
        else:
            ' ~~~~~~~~~~ Running in livetrade mode or scan mode ~~~~~~~~~~~~~ '
            
            if self.use_stream:
                # Streaming data
                
                # First assign data
                if base_data is not None:
                    data = base_data
                else:
                    print("Stream data has not been recieved yet.")
                    print("Passing NoneType as data.")
                    data = None
                
                # Now retrieve MTF data
                if len(interval.split(',')) > 1:
                    # Fetch MTF data
                    MTF_data = {self.base_interval: data}
                    
                    if self.MTF_initialisation:
                        # Download MTF data for strategy initialisation only
                        if self.MTF_data is None:
                            # MTF_data has not been retrieved yet
                            for granularity in self.MTF_intervals:
                                data = getattr(self.get_data, feed.lower())(instrument,
                                                                            granularity = granularity,
                                                                            count=period)
                                
                                if self.check_data_alignment:
                                    data = self._verify_data_alignment(data, instrument, feed, period, 
                                                                       price_data_path)
                                
                                MTF_data[granularity] = data
                            
                            self.MTF_data = MTF_data
                            
                        else:
                            # MTF_data already exists, reuse
                            MTF_data = self.MTF_data
                            
                            # Replace base_interval data with latest data
                            MTF_data[self.base_interval] = data
                            
                    else:
                        # Download MTF data each update
                        for granularity in self.MTF_intervals:
                            if datetime.now(tz=pytz.utc) > self.time_to_download[granularity]:
                                # Update MTF data
                                data = getattr(self.get_data, feed.lower())(instrument,
                                                                            granularity = granularity,
                                                                            count = period)
                            
                                if self.check_data_alignment:
                                    data = self._verify_data_alignment(data, instrument, feed, period, 
                                                                       price_data_path)
                                
                                # Append to MTF_data
                                MTF_data[granularity] = data
                                
                                # Update next time_to_download
                                self.time_to_download[granularity] = self._next_candle_open(granularity)
                            
                            else:
                                # Use previously downloaded MTF data
                                MTF_data[granularity] = self.MTF_data[granularity]
                        
                        # Update self.MTF_data with latest MTF data
                        self.MTF_data = MTF_data
                                
                            
                else:
                    # There is only one timeframe of data
                    MTF_data = None
                
            
            elif self.data_file is not None:
                # Using price stream data file
                
                custom_data_filepath = self.data_file
                
                # Make copy of file to prevent read-write errors
                copy2(custom_data_filepath, self.abs_streamfile_copy)
                
                if int(self.verbosity) > 1:
                    print("Using data file specified ({}).".format(custom_data_filepath))
                
                # Read datafile to get base interval data
                data = pd.read_csv(self.abs_streamfile_copy, 
                                   index_col = 0,
                                   skipinitialspace=True)
                
                if len(data) > 0:
                    data.index = pd.to_datetime(data.index, 
                                                infer_datetime_format=True,
                                                errors='ignore')
                    
                    # Remove copied file
                    os.remove(self.abs_streamfile_copy)
                    
                else:
                    # Stream has not had enough time to write data yet, revert 
                    # to downloading M1 data
                    data = getattr(self.get_data, feed.lower())(instrument,
                                                                granularity = 'M1',
                                                                count = period)
                    
                    if self.check_data_alignment:
                        data = self._verify_data_alignment(data, instrument, feed, period, 
                                                           price_data_path)
                
                # Fetch MTF data
                MTF_data = {self.base_interval: data}
                
                if self.MTF_initialisation:
                    # Download MTF data for strategy initialisation only
                    if self.MTF_data is None:
                        # MTF_data has not been retrieved yet
                        for granularity in self.MTF_intervals:
                            data = getattr(self.get_data, feed.lower())(instrument,
                                                                        granularity = granularity,
                                                                        count=period)
                            
                            if self.check_data_alignment:
                                data = self._verify_data_alignment(data, instrument, feed, period, 
                                                                   price_data_path)
                            
                            MTF_data[granularity] = data
                        
                        self.MTF_data = MTF_data
                        
                    else:
                        # MTF_data already exists, reuse
                        MTF_data = self.MTF_data
                        
                        # Replace base_interval data with latest data
                        MTF_data[self.base_interval] = data
                        
                else:
                    # Download MTF data each update
                    for granularity in self.MTF_intervals:
                        data = getattr(self.get_data, feed.lower())(instrument,
                                                                    granularity = granularity,
                                                                    count=period)
                        
                        if self.check_data_alignment:
                            data = self._verify_data_alignment(data, instrument, feed, period, 
                                                               price_data_path)
                        
                        MTF_data[granularity] = data
                        
                        
                if len(MTF_data) == 1:
                    # There is only one timeframe of data
                    MTF_data = None
                    
            else:            
                # Running in periodic-download mode
                MTF_data = {}
                for granularity in interval.split(','):
                    if granularity == "tick":
                        print("Warning: cannot download historic tick data. " + \
                              "Please change candlestick granularity in " + \
                              "strategy configuration. Exiting.")
                        sys.exit(0)
                        
                    data = getattr(self.get_data, feed.lower())(instrument,
                                                                granularity = granularity,
                                                                count=period)
                    
                    if self.check_data_alignment:
                        data = self._verify_data_alignment(data, instrument, feed, period, 
                                                           price_data_path)
                    
                    MTF_data[granularity] = data
                
                first_granularity = interval.split(',')[0]
                data = MTF_data[first_granularity]
                
                if len(MTF_data) == 1:
                        MTF_data = None
            
            return data, None, MTF_data


    def _verify_data_alignment(self, data, instrument, feed, period, price_data_path):
        '''
        Verifies data time-alignment based on current time and last
        candle in data. 
        
        When using MTF data, this method will only check the base timeframe.
        '''
        
        interval = self.strategy_params['granularity'].split(',')[0]
        
        # Check data time alignment
        current_time        = datetime.now(tz=pytz.utc)
        last_candle_closed  = self.broker_utils.last_period(current_time, interval)
        data_ts             = data.index[-1].to_pydatetime().timestamp()
        
        if data_ts != last_candle_closed.timestamp():
            # Time misalignment detected - attempt to correct
            count = 0
            while data_ts != last_candle_closed.timestamp():
                print("  Time misalginment detected at {}".format(datetime.now().strftime("%H:%M:%S")),
                      "({}/{}).".format(data.index[-1].minute, last_candle_closed.minute),
                      "Trying again...")
                time.sleep(3) # wait 3 seconds...
                data    = getattr(self.get_data, feed.lower())(instrument,
                                    granularity = interval,
                                    count=period)
                data_ts = data.index[-1].to_pydatetime().timestamp()
                count   += 1
                if count == 3:
                    break
            
            if data_ts != last_candle_closed.timestamp():
                # Time misalignment still present - attempt to correct
                # Check price data directory to see if the stream has caught 
                # the latest candle
                price_data_filename = "{0}{1}.txt".format(interval, instrument)
                abs_price_path      = os.path.join(price_data_path, price_data_filename)
                
                if os.path.exists(abs_price_path):
                    # Price data file matching instrument and granularity 
                    # exists, check latest candle in file
                    f                   = open(abs_price_path, "r")
                    price_lines         = f.readlines()
                    
                    if len(price_lines) > 1:
                        latest_candle       = price_lines[-1].split(',')
                        latest_candle_time  = datetime.strptime(latest_candle[0],
                                                                '%Y-%m-%d %H:%M:%S')
                        UTC_last_candle_in_file = latest_candle_time.replace(tzinfo=pytz.UTC)
                        price_data_ts       = UTC_last_candle_in_file.timestamp()
                        
                        if price_data_ts == last_candle_closed.timestamp():
                            data    = self.broker_utils.update_data_with_candle(data, latest_candle)
                            data_ts = data.index[-1].to_pydatetime().timestamp()
                            print("  Data updated using price stream.")
            
            # if data is still misaligned, perform manual adjustment.
            if data_ts != last_candle_closed.timestamp():
                print("  Could not retrieve updated data. Aborting.")
                sys.exit(0)
        
        return data
    
    
    def _update(self, i):
        '''
        Update strategy with latest data and generate latest signal.
        '''
        
        # First clear self.latest_orders
        self.latest_orders = []
        
        if self.scan_mode:
            open_positions      = None
        else:
            open_positions      = self.broker.get_open_positions(self.instrument)
        
        # Run strategy to get signals
        signal_dict = self.strategy.generate_signal(i, open_positions)
        
        if 0 not in signal_dict:
            # Single order signal, nest in dictionary to allow iteration
            signal_dict = {1: signal_dict}
            
        # Begin iteration over signal_dict to extract each order
        for order in signal_dict:
            order_signal_dict = signal_dict[order].copy()
            
            if (len(order_signal_dict) > 0) and ((order_signal_dict["order_type"] == 'modify') or (order_signal_dict["direction"] != 0)):
                self._process_signal(order_signal_dict, i, self.data, 
                                    self.quote_data, self.instrument)
        
        # TODO - implement the following, maybe
        # else:
        #     signal_type = order_signal_dict["signal_type"] if "signal_type" in order_signal_dict else None
            
        #     if signal_type == 'deployment':
        #         # Strategy deployment signal
        #         runfile = os.path.join(self.home_dir, order_signal_dict['runfile'])
        #         os.system("nohup python3 {} &".format(runfile))
        
        if int(self.verbosity) > 1:
            if len(self.latest_orders) > 0:
                for order in self.latest_orders:
                    order_string = "{}: {} {}".format(order['order_time'].strftime("%b %d %Y %H:%M:%S"), 
                                                      order['instrument'], 
                                                      order['order_type']) + \
                        " order of {} units placed at {}.".format(order['size'],
                                                                  order['order_price'])
                    print(order_string)
            else:
                if int(self.verbosity) > 2:
                    print("{}: No signal detected ({}).".format(self.data.index[i].strftime("%b %d %Y %H:%M:%S"),
                                                            self.instrument))
        
        # Check for orders placed and/or scan hits
        if int(self.notify) > 0 and self.backtest_mode is False:
            
            for order_details in self.latest_orders:
                self.broker_utils.write_to_order_summary(order_details, 
                                                         self.order_summary_fp)
            
            if int(self.notify) > 1 and \
                self.email_params['mailing_list'] is not None and \
                self.email_params['host_email'] is not None:
                    if int(self.verbosity) > 0 and len(self.latest_orders) > 0:
                            print("Sending emails ...")
                            
                    for order_details in self.latest_orders:
                        emailing.send_order(order_details,
                                            self.email_params['mailing_list'],
                                            self.email_params['host_email'])
                        
                    if int(self.verbosity) > 0 and len(self.latest_orders) > 0:
                            print("  Done.\n")
            
        # Check scan results
        if self.scan_mode:
            # Construct scan details dict
            scan_details    = {'index'      : self.scan_index,
                               'strategy'   : self.strategy.name,
                               'timeframe'  : self.strategy_params['granularity']
                                }
            
            # Report AutoScan results
            # Scan reporting with no emailing requested.
            if int(self.verbosity) > 0 or \
                int(self.notify) == 0:
                if len(self.scan_results) == 0:
                    print("{}: No signal detected.".format(self.instrument))
                else:
                    # Scan detected hits
                    for instrument in self.scan_results:
                        signal = self.scan_results[instrument]['signal']
                        signal_type = 'Long' if signal == 1 else 'Short'
                        print(f"{instrument}: {signal_type} signal detected.")
            
            if int(self.notify) > 0:
                # Emailing requested
                if len(self.scan_results) > 0 and \
                    self.email_params['mailing_list'] is not None and \
                    self.email_params['host_email'] is not None:
                    # There was a scanner hit and email information is provided
                    emailing.send_scan_results(self.scan_results, 
                                               scan_details, 
                                               self.email_params['mailing_list'],
                                               self.email_params['host_email'])
                elif int(self.notify) > 1 and \
                    self.email_params['mailing_list'] is not None and \
                    self.email_params['host_email'] is not None:
                    # There was no scan hit, but notify set > 1, so send email
                    # regardless.
                    emailing.send_scan_results(self.scan_results, 
                                               scan_details, 
                                               self.email_params['mailing_list'],
                                               self.email_params['host_email'])
                    
    
    def _update_backtest(self, i):
        '''
        Updates virtual broker with latest price data.
        '''
        candle = self.data.iloc[i]
        self.broker.update_positions(candle, self.instrument)
    
    
    def _process_signal(self, order_signal_dict, i, data, quote_data, 
                       instrument):
        '''
            Process order_signal_dict and send orders to broker.
        '''
        signal = order_signal_dict["direction"]
        
        # Entry signal detected, get price data
        price_data      = self.broker.get_price(instrument=instrument, 
                                                data=data, 
                                                conversion_data=quote_data, 
                                                i=i)
        datetime_stamp  = data.index[i]
        
        if signal < 0:
            order_price = price_data['bid']
            HCF         = price_data['negativeHCF']
        else:
            order_price = price_data['ask']
            HCF         = price_data['positiveHCF']
        
        
        # Define 'working_price' to calculate size and TP
        if order_signal_dict["order_type"] == 'limit' or order_signal_dict["order_type"] == 'stop-limit':
            working_price = order_signal_dict["order_limit_price"]
        else:
            working_price = order_price
        
        # Calculate exit levels
        pip_value   = self.broker_utils.get_pip_ratio(instrument)
        stop_distance = order_signal_dict['stop_distance'] if 'stop_distance' in order_signal_dict else None
        
        # Calculate stop loss price
        if 'stop_loss' not in order_signal_dict and \
            'stop_distance' in order_signal_dict and \
            order_signal_dict['stop_distance'] is not None:
            # Stop loss provided as pip distance, convert to price
            stop_price = working_price - np.sign(signal)*stop_distance*pip_value
        else:
            # Stop loss provided as price
            stop_price = order_signal_dict['stop_loss'] if 'stop_loss' in order_signal_dict else None
        
        # Set stop type
        if stop_price is not None:
            stop_type = order_signal_dict['stop_type'] if 'stop_type' in order_signal_dict else 'limit'
        else:
            # No stop loss specified 
            stop_type = None
            
        # Calculate take profit price
        if 'take_profit' not in order_signal_dict and \
            'take_distance' in order_signal_dict and \
            order_signal_dict['take_distance'] is not None:
            # Take profit distance specified
            take_profit = working_price + np.sign(signal)*order_signal_dict['take_distance']*pip_value
        else:
            # Take profit price specified, or no take profit specified at all
            take_profit = order_signal_dict["take_profit"] if 'take_profit' in order_signal_dict else None
        
        # Calculate risked amount
        amount_risked = self.broker.get_balance() * self.strategy_params['risk_pc'] / 100
        
        # Calculate size
        if 'size' in order_signal_dict:
            size = order_signal_dict['size']
        else:
            if self.strategy_params['sizing'] == 'risk':
                size            = self.broker_utils.get_size(instrument,
                                                 amount_risked, 
                                                 working_price, 
                                                 stop_price, 
                                                 HCF,
                                                 stop_distance)
            else:
                size = self.strategy_params['sizing']
        
        # Construct order dict by building on signal_dict
        order_details                   = order_signal_dict
        order_details["order_time"]     = datetime_stamp
        order_details["strategy"]       = self.strategy.name
        order_details["instrument"]     = instrument
        order_details["size"]           = signal*size
        order_details["order_price"]    = order_price
        order_details["HCF"]            = HCF
        order_details["granularity"]    = self.strategy_params['granularity']
        order_details["stop_distance"]  = stop_distance
        order_details["stop_loss"]      = stop_price
        order_details["take_profit"]    = take_profit
        order_details["stop_type"]      = stop_type
        order_details["related_orders"] = order_signal_dict['related_orders'] if 'related_orders' in order_signal_dict else None

        # Place order
        if self.scan_mode:
            # Bot is scanning
            scan_hit = {"size"  : size,
                        "entry" : order_price,
                        "stop"  : stop_price,
                        "take"  : take_profit,
                        "signal": signal
                        }
            self.scan_results[instrument] = scan_hit
            
        else:
            # Bot is trading
            self.broker.place_order(order_details)
            self.latest_orders.append(order_details)
    
    def _next_candle_open(self, granularity):
        '''
        Returns the UTC datetime object corresponding to the open time of the 
        next candle.
        '''
        
        current_ts = datetime.now(tz=pytz.utc).timestamp()
        granularity_in_seconds = self.broker_utils.interval_to_seconds(granularity)
        next_candle_open_ts = granularity_in_seconds * np.ceil(current_ts / granularity_in_seconds)
        
        return datetime.fromtimestamp(next_candle_open_ts, tz=pytz.utc)
            

    def create_backtest_summary(self, balance, NAV, margin):
        '''
        Constructs backtest summary dictionary for further processing.
        '''
        
        trade_summary = self.broker_utils.trade_summary(self.instrument, self.broker.closed_positions)
        open_trade_summary = self.broker_utils.open_order_summary(self.instrument, self.broker.open_positions)
        cancelled_summary = self.broker_utils.cancelled_order_summary(self.instrument, self.broker.cancelled_orders)
            
        backtest_dict = {}
        backtest_dict['data']           = self.data
        backtest_dict['account_history'] = pd.DataFrame(data={'balance': balance, 
                                                              'NAV': NAV, 
                                                              'margin': margin,
                                                              'drawdown': np.array(NAV)/np.maximum.accumulate(NAV) - 1}, 
                                                        index=self.data.index)
        backtest_dict['trade_summary']  = trade_summary
        backtest_dict['indicators']     = self.strategy.indicators if hasattr(self.strategy, 'indicators') else None
        backtest_dict['instrument']     = self.instrument
        backtest_dict['interval']       = self.strategy_params['granularity']
        backtest_dict['open_trades']    = open_trade_summary
        backtest_dict['cancelled_trades'] = cancelled_summary
        
        self.backtest_summary = backtest_dict
    
    def _get_iteration_range(self):
        '''
        Checks mode of operation and returns data iteration range. For backtesting,
        the entire dataset is iterated over. For livetrading, only the latest candle
        is used.
        '''
        
        if self.backtest_mode:
            start_range = 0
        else:
            start_range = len(self.data)-1
        end_range       = len(self.data)

        return start_range, end_range
    
    def _replace_data(self, data):
        ''' Function to replace the data assigned locally and to the strategy. '''
        
        self.data = data
        self.strategy.data = data
    