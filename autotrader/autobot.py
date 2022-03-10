import sys
import os
import time
import pytz
import threading
import importlib
import numpy as np
import pandas as pd
from shutil import copy2
from datetime import datetime
from autotrader.comms import emailing
from autotrader.autodata import GetData
from autotrader.brokers.trading import Order
from autotrader.autostream import AutoStream
from autotrader.utilities import read_yaml, get_config


class AutoTraderBot:
    """AutoTrader Trading Bot.
    
    Attributes
    ----------
    instrument : str
        The trading instrument assigned to the bot.
    data : pd.DataFrame
        The OHLC price data used by the bot.
    quote_data : pd.DataFrame
        The OHLC quote data used by the bot.
    MTF_data : dict
        The multiple timeframe data used by the bot.
    backtest_summary : dict
        A dictionary containing results from the bot in backtest. This 
        dictionary is available only after a backtest and has keys: 'data', 
        'account_history', 'trade_summary', 'indicators', 'instrument', 
        'interval', 'open_trades', 'cancelled_trades'.
    
    """
    
    def __init__(self, instrument: str, strategy_dict: dict, 
                 broker, data_dict: dict, quote_data_dict: dict, 
                 auxdata: dict, autotrader_instance) -> None:
        """Instantiates an AutoTrader Bot.

        Parameters
        ----------
        instrument : str
            The trading instrument assigned to the bot instance.
        strategy_dict : dict
            The strategy configuration dictionary.
        broker : AutoTrader Broker instance
            The AutoTrader Broker module.
        data_dict : dict
            The strategy data.
        quote_data_dict : dict
            The quote data for the trading instrument (backtesting only).
        auxdata : dict
            Auxiliary strategy data.
        autotrader_instance : AutoTrader
            The parent AutoTrader instance.

        Raises
        ------
        Exception
            When there is an error retrieving the instrument data.

        Returns
        -------
        None
            The trading bot will be instantiated and ready for trading.

        """
        # Inherit user options from autotrader
        for attribute, value in autotrader_instance.__dict__.items():
            setattr(self, attribute, value)
        self._scan_results = {}
        
        # Assign local attributes
        self.instrument = instrument
        self._broker = broker
        
        # Unpack strategy parameters and assign to strategy_params
        strategy_config = strategy_dict['config']
        interval = strategy_config["INTERVAL"]
        period = strategy_config["PERIOD"]
        risk_pc = strategy_config["RISK_PC"] if 'RISK_PC' in strategy_config \
            else None
        sizing = strategy_config["SIZING"] if 'SIZING' in strategy_config \
            else None
        params = strategy_config["PARAMETERS"]
        strategy_params = params
        strategy_params['granularity'] = strategy_params['granularity'] \
            if 'granularity' in strategy_params else interval
        strategy_params['risk_pc'] = strategy_params['risk_pc'] \
            if 'risk_pc' in strategy_params else risk_pc
        strategy_params['sizing'] = strategy_params['sizing'] \
            if 'sizing' in strategy_params else sizing
        strategy_params['period'] = strategy_params['period'] \
            if 'period' in strategy_params else period
        self._strategy_params = strategy_params
        
        # Import Strategy
        if strategy_dict['class'] is not None:
            strategy = strategy_dict['class']
        else:
            strat_module = strategy_config["MODULE"]
            strat_name = strategy_config["CLASS"]
            strat_package_path = os.path.join(self._home_dir, "strategies") 
            strat_module_path = os.path.join(strat_package_path, 
                                             strat_module) + '.py'
            strat_spec = importlib.util.spec_from_file_location(strat_module, 
                                                                strat_module_path)
            strategy_module = importlib.util.module_from_spec(strat_spec)
            strat_spec.loader.exec_module(strategy_module)
            strategy = getattr(strategy_module, strat_name)
        
        # Get broker configuration 
        global_config_fp = os.path.join(self._home_dir, 'config', 
                                        'GLOBAL.yaml')
        if os.path.isfile(global_config_fp):
            global_config = read_yaml(global_config_fp)
        else:
            global_config = None
        broker_config = get_config(self._environment, global_config, self._feed)
   
        # Start price streaming
        if self._use_stream and self._backtest_mode is False:
            
            # Check how many granularities were requested
            if len(interval.split(',')) > 1:
                # MTF strategy
                self._base_interval = interval.split(',')[0]
                self._MTF_intervals = interval.split(',')[1:]
                
                # Initiate time_to_download dict
                self._time_to_download = {}
                for granularity in self._MTF_intervals:
                    self._time_to_download[granularity] = datetime.now(tz=pytz.utc)
                
            else:
                # Single timeframe strategy
                self._base_interval = interval
                self._MTF_intervals = []
            
            # Start stream
            self._initiate_stream()

        # Multiple time-frame initialisation option
        if self._MTF_initialisation:
            # Only retrieve MTF_data once upon initialisation and store
            # instantiation MTF_data
            self.MTF_data = None
        
        # Data retrieval
        self._quote_data_file = quote_data_dict
        if data_dict is not None:
            # Local data files provided
            self._abs_data_filepath = True
            if type(data_dict) == str:
                # Single timeframe data file provided
                self._data_file = data_dict
            else:
                # MTF data provided
                self._MTF_data_files = data_dict
        else:
            self._abs_data_filepath = False
        
        self._get_data = GetData(broker_config, self._allow_dancing_bears)
        data, quote_data, MTF_data = self._retrieve_data(instrument, 
                                                         self._feed)
        
        # Check data
        if len(data) == 0:
            raise Exception("Error retrieving data.")
        
        # Data assignment
        if MTF_data is None:
            strat_data = data
        else:
            strat_data = MTF_data
        
        # Auxiliary data assignment
        if auxdata is not None:
            strat_data = {'base': strat_data,
                          'aux': auxdata}
        
        # Instantiate Strategy
        include_broker = strategy_config['INCLUDE_BROKER'] \
            if 'INCLUDE_BROKER' in strategy_config else False
        if include_broker:
            my_strat = strategy(params, strat_data, instrument, 
                                self._broker, self._broker_utils)
        else:
            my_strat = strategy(params, strat_data, instrument)
            
        # Assign strategy to local attributes
        self._strategy = my_strat
        self.data = data
        self.MTF_data = MTF_data
        self.quote_data = quote_data
        self._latest_orders = []
        
        # Assign strategy attributes for tick-based strategy development
        if self._backtest_mode:
            self._strategy._backtesting = True
            self.backtest_summary = None
        if interval.split(',')[0] == 'tick':
            self._strategy._tick_data = True
        
        if int(self._verbosity) > 0:
                print("\nAutoTraderBot assigned to trade {}".format(instrument),
                      "on {} timeframe using {}.".format(self._strategy_params['granularity'],
                                                         strategy_config['NAME']))
    
    
    def __repr__(self):
        return f'{self.instrument} AutoTraderBot'
    
    
    def __str__(self):
        return 'AutoTraderBot instance'
    
    
    def _initiate_stream(self) -> None:
        """Spawns AutoStream into a new thread.
        """
        record_ticks = False
        record_candles = False
        if self._base_interval == 'tick' or self._base_interval == 'ticks':
            record_ticks = True
        else:
            record_candles = True
        
        stream_granularity = self._base_interval
        self._no_candles = self._strategy_params['period']
        
        self._AS = AutoStream(self._home_dir, 
                             self._stream_config, 
                             self.instrument, 
                             granularity = stream_granularity,
                             record_ticks = record_ticks, 
                             record_candles = record_candles,
                             no_candles = self._no_candles,
                             bot = self)
        
        stream_thread = threading.Thread(target = self._AS.start, 
                                         args=(), daemon=False)
        print('Spawning new thread to stream data.')
        stream_thread.start()
        
    
    def _recieve_stream_data(self) -> None:
        """Method to tell AutoStream to send data to bot. Called from 
        bot manager.
        """
        self._AS.update_bot = True
    
    
    def _update_strategy_data(self, data: pd.DataFrame = None) -> None:
        """Method to update strategy with latest data. Called by the bot
        manager and autostream.
        """
        if data is not None:
            # Update data attribute (for livetrade compatibility)
            self.data = data
        
        # Retrieve new data
        new_data, _, MTF_data = self._retrieve_data(self.instrument, 
                                                    self._feed,
                                                    base_data = data)
        
        # Check for MTF_data
        if MTF_data is None:
            strat_data = new_data
        else:
            strat_data = MTF_data
        
        # Update strategy with new data
        self._strategy.initialise_strategy(strat_data)
        
    
    def _retrieve_data(self, instrument: str, feed: str, 
                       base_data: pd.DataFrame = None) -> pd.DataFrame:
        """Retrieves price data from AutoData.
        """
        interval = self._strategy_params['granularity']
        period = self._strategy_params['period']
        price_data_path = os.path.join(self._home_dir, 'price_data')
        
        if self._backtest_mode is True:
            # Running in backtest mode 
            self._get_data.base_currency = self._base_currency
            from_date = self._data_start
            to_date = self._data_end
            
            if self._data_file is not None:
                # Read local data file
                custom_data_file = self._data_file
                custom_data_filepath = os.path.join(price_data_path, 
                                                    custom_data_file) \
                    if not self._abs_data_filepath else custom_data_file
                if int(self._verbosity) > 1:
                    print("Using data file specified ({}).".format(custom_data_file))
                data = self._get_data.local(custom_data_filepath, self._data_start, 
                                            self._data_end)
                
                # Load quote data
                if self._quote_data_file is not None:
                    quote_data = self._get_data.local(self._quote_data_file, 
                                                      self._data_start, 
                                                      self._data_end)
                else:
                    quote_data = data
                
                # Correct any data mismatches
                data, quote_data = self._match_quote_data(data, quote_data)
                MTF_data = None
            
            elif self._MTF_data_files is not None:
                # Read local MTF data files
                MTF_data_files = self._MTF_data_files
                MTF_granularities = list(MTF_data_files.keys())
                
                MTF_data = {}
                for granularity in MTF_data_files:
                    # Extract data 
                    custom_data_file = MTF_data_files[granularity]
                    custom_data_filepath = os.path.join(price_data_path, 
                                                        custom_data_file) \
                        if not self._abs_data_filepath else custom_data_file
                    if int(self._verbosity) > 1:
                        print("Using data file specified ({}).".format(MTF_data_files[granularity]))
                    data = self._get_data.local(custom_data_filepath, self._data_start, 
                                                self._data_end)
                    
                    if granularity == MTF_granularities[0]:
                        # Assign quote data for backtesting
                        if self._quote_data_file is not None:
                            quote_data = self._get_data.local(self._quote_data_file, 
                                                              self._data_start, 
                                                              self._data_end)
                            data, quote_data = self._match_quote_data(data, 
                                                                      quote_data)
                        else:
                            quote_data = data
                    
                    # Add to MTF_data dict
                    MTF_data[granularity] = data
                
                # Extract first dataset to use as base
                first_granularity = MTF_granularities[0]
                data = MTF_data[first_granularity]
                quote_data = quote_data
                
            else:
                # No data file(s) provided, proceed to download
                if int(self._verbosity) > 1:
                    print(f"\nDownloading OHLC price data for {instrument}.")
                
                if self._optimise_mode is True:
                    # Check if historical data already exists
                    historical_data_name = f'hist_{interval}{instrument}.csv'
                    historical_quote_data_name = f'hist_{interval}{instrument}_quote.csv'
                    data_dir_path = os.path.join(self._home_dir, 'price_data')
                    historical_data_file_path = os.path.join(self._home_dir, 
                                        'price_data', historical_data_name)
                    historical_quote_data_file_path = os.path.join(self._home_dir, 
                                        'price_data', historical_quote_data_name)
                    
                    try:
                        data = self._get_data.local(historical_data_file_path)
                        quote_data = self._get_data.local(historical_quote_data_file_path)
                    except:
                        # Data file does not yet exist, download
                        data = getattr(self._get_data, feed.lower())(instrument,
                                       granularity = interval, start_time = from_date,
                                       end_time = to_date)
                        quote_data = getattr(self._get_data,f'_{feed.lower()}_quote_data')(data,
                                             instrument, interval, from_date, to_date)
                        data, quote_data = self._broker_utils.check_dataframes(data, quote_data)
                        
                        # Check if price_data folder exists
                        if not os.path.exists(data_dir_path):
                            # If price data directory doesn't exist, make it
                            os.makedirs(data_dir_path)
                            
                        # Save data in file/s
                        data.to_csv(historical_data_file_path)
                        quote_data.to_csv(historical_quote_data_file_path)

                    MTF_data = None
                        
                else:
                    # Running in single-instrument MTF backtest mode
                    MTF_data = {}
                    for granularity in interval.split(','):
                        data = getattr(self._get_data, feed.lower())(instrument,
                                                             granularity = granularity,
                                                             start_time = from_date,
                                                             end_time = to_date)
                        
                        # Only get quote data for first granularity
                        if granularity == interval.split(',')[0]:
                            quote_data = getattr(self._get_data, f'_{feed.lower()}_quote_data')(data,
                                                 instrument, granularity, from_date, to_date)
                        
                            data, quote_data = self._broker_utils.check_dataframes(data.drop_duplicates(), 
                                                                                  quote_data.drop_duplicates())
                        
                        MTF_data[granularity] = data
                    
                    # Extract first dataset to use as base
                    first_granularity = interval.split(',')[0]
                    data = MTF_data[first_granularity]
                    quote_data = quote_data
                
                if MTF_data is not None and len(MTF_data) == 1:
                    MTF_data = None
                
                if int(self._verbosity) > 1:
                    print("  Done.\n")
            
            return data, quote_data, MTF_data
        
        else:
            # Running in livetrade mode or scan mode
            if self._use_stream:
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
                    MTF_data = {self._base_interval: data}
                    
                    if self._MTF_initialisation:
                        # Download MTF data for strategy initialisation only
                        if self.MTF_data is None:
                            # MTF_data has not been retrieved yet
                            for granularity in self._MTF_intervals:
                                data = getattr(self._get_data, feed.lower())(instrument,
                                                                            granularity = granularity,
                                                                            count=period)
                                
                                if self._check_data_alignment:
                                    data = self._verify_data_alignment(data, instrument, feed, period, 
                                                                       price_data_path)
                                
                                MTF_data[granularity] = data
                            
                            self.MTF_data = MTF_data
                            
                        else:
                            # MTF_data already exists, reuse
                            MTF_data = self.MTF_data
                            
                            # Replace base_interval data with latest data
                            MTF_data[self._base_interval] = data
                            
                    else:
                        # Download MTF data each update
                        for granularity in self._MTF_intervals:
                            if datetime.now(tz=pytz.utc) > self._time_to_download[granularity]:
                                # Update MTF data
                                data = getattr(self._get_data, feed.lower())(instrument,
                                               granularity = granularity, count = period)
                            
                                if self._check_data_alignment:
                                    data = self._verify_data_alignment(data, instrument, feed, period, 
                                                                       price_data_path)
                                
                                # Append to MTF_data
                                MTF_data[granularity] = data
                                
                                # Update next time_to_download
                                self._time_to_download[granularity] = self._next_candle_open(granularity)
                            
                            else:
                                # Use previously downloaded MTF data
                                MTF_data[granularity] = self.MTF_data[granularity]
                        
                        # Update self.MTF_data with latest MTF data
                        self.MTF_data = MTF_data
                            
                else:
                    # There is only one timeframe of data
                    MTF_data = None
                
            
            elif self._data_file is not None:
                # Using price stream data file
                custom_data_filepath = self._data_file
                
                # Make copy of file to prevent read-write errors
                copy2(custom_data_filepath, self.abs_streamfile_copy)
                
                if int(self._verbosity) > 1:
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
                    data = getattr(self._get_data, feed.lower())(instrument,
                                   granularity = 'M1', count = period)
                    
                    if self._check_data_alignment:
                        data = self._verify_data_alignment(data, instrument, feed, period, 
                                                           price_data_path)
                
                # Fetch MTF data
                MTF_data = {self._base_interval: data}
                
                if self._MTF_initialisation:
                    # Download MTF data for strategy initialisation only
                    if self.MTF_data is None:
                        # MTF_data has not been retrieved yet
                        for granularity in self._MTF_intervals:
                            data = getattr(self._get_data, feed.lower())(instrument,
                                           granularity = granularity, count=period)
                            
                            if self._check_data_alignment:
                                data = self._verify_data_alignment(data, instrument, feed, period, 
                                                                   price_data_path)
                            
                            MTF_data[granularity] = data
                        
                        self.MTF_data = MTF_data
                        
                    else:
                        # MTF_data already exists, reuse
                        MTF_data = self.MTF_data
                        
                        # Replace base_interval data with latest data
                        MTF_data[self._base_interval] = data
                        
                else:
                    # Download MTF data each update
                    for granularity in self._MTF_intervals:
                        data = getattr(self._get_data, feed.lower())(instrument,
                                       granularity = granularity, count=period)
                        
                        if self._check_data_alignment:
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
                        
                    data = getattr(self._get_data, feed.lower())(instrument,
                                   granularity = granularity, count=period)
                    
                    if self._check_data_alignment:
                        data = self._verify_data_alignment(data, instrument, feed, period, 
                                                           price_data_path)
                    
                    MTF_data[granularity] = data
                
                first_granularity = interval.split(',')[0]
                data = MTF_data[first_granularity]
                
                if len(MTF_data) == 1:
                        MTF_data = None
            
            return data, None, MTF_data


    @staticmethod
    def _check_data_period(data: pd.DataFrame, from_date: datetime, 
                           to_date: datetime) -> pd.DataFrame:
        """Checks and returns the dataset matching the backtest start and 
        end dates (as close as possible).
        """
        return data[(data.index >= from_date) & (data.index <= to_date)]
        

    def _verify_data_alignment(self, data: pd.DataFrame, instrument: str, 
                               feed: str, period: str, 
                               price_data_path: str) -> pd.DataFrame:
        """Verifies data time-alignment based on current time and last
        candle in data. 
        
        When using MTF data, this method will only check the base timeframe.
        """
        interval = self._strategy_params['granularity'].split(',')[0]
        
        # Check data time alignment
        current_time = datetime.now(tz=pytz.utc)
        last_candle_closed = self._broker_utils.last_period(current_time, interval)
        data_ts = data.index[-1].to_pydatetime().timestamp()
        
        if data_ts != last_candle_closed.timestamp():
            # Time misalignment detected - attempt to correct
            count = 0
            while data_ts != last_candle_closed.timestamp():
                print("  Time misalginment detected at {}".format(datetime.now().strftime("%H:%M:%S")),
                      "({}/{}).".format(data.index[-1].minute, last_candle_closed.minute),
                      "Trying again...")
                time.sleep(3) # wait 3 seconds...
                data = getattr(self._get_data, feed.lower())(instrument,
                                granularity = interval,
                                count=period)
                data_ts = data.index[-1].to_pydatetime().timestamp()
                count += 1
                if count == 3:
                    break
            
            if data_ts != last_candle_closed.timestamp():
                # Time misalignment still present - attempt to correct
                # Check price data directory to see if the stream has caught 
                # the latest candle
                price_data_filename = "{0}{1}.txt".format(interval, instrument)
                abs_price_path = os.path.join(price_data_path, price_data_filename)
                
                if os.path.exists(abs_price_path):
                    # Price data file matching instrument and granularity 
                    # exists, check latest candle in file
                    f = open(abs_price_path, "r")
                    price_lines = f.readlines()
                    
                    if len(price_lines) > 1:
                        latest_candle = price_lines[-1].split(',')
                        latest_candle_time = datetime.strptime(latest_candle[0],
                                                                '%Y-%m-%d %H:%M:%S')
                        UTC_last_candle_in_file = latest_candle_time.replace(tzinfo=pytz.UTC)
                        price_data_ts = UTC_last_candle_in_file.timestamp()
                        
                        if price_data_ts == last_candle_closed.timestamp():
                            data = self._broker_utils.update_data_with_candle(data, latest_candle)
                            data_ts = data.index[-1].to_pydatetime().timestamp()
                            print("  Data updated using price stream.")
            
            # if data is still misaligned, perform manual adjustment.
            if data_ts != last_candle_closed.timestamp():
                print("  Could not retrieve updated data. Aborting.")
                sys.exit(0)
        
        return data
    
    
    def _update(self, i: int) -> None:
        """Update strategy with latest data and generate latest signal.
        """
        # Reset self._latest_orders
        self._latest_orders = []
        
        if self._scan_mode:
            open_positions = None
        else:
            open_positions = self._broker.get_positions(self.instrument)
        
        # Run strategy to get signals
        # TODO - parameterise signal method name
        strategy_orders = self._strategy.generate_signal(i, open_positions)
        orders = self._check_orders(strategy_orders)
        self._qualify_orders(orders, i)
        
        # Iterate over orders to submit
        for order in orders:
            if self._scan_mode:
                # Bot is scanning
                scan_hit = {"size"  : order.size,
                            "entry" : self.data.Close[i],
                            "stop"  : order.stop_loss,
                            "take"  : order.take_profit,
                            "signal": order.direction}
                self._scan_results[self.instrument] = scan_hit
                pass
                
            else:
                # Bot is trading
                self._broker.place_order(order, order_time=self.data.index[i])
                self._latest_orders.append(order)
        
        if int(self._verbosity) > 1:
            if len(self._latest_orders) > 0:
                for order in self._latest_orders:
                    order_string = "{}: {} {}".format(order.order_time.strftime("%b %d %Y %H:%M:%S"), 
                                                      order.instrument, 
                                                      order.order_type) + \
                        " order of {} units placed at {}.".format(order.size,
                                                                  order.order_price)
                    print(order_string)
            else:
                if int(self._verbosity) > 2:
                    print("{}: No signal detected ({}).".format(self.data.index[i].strftime("%b %d %Y %H:%M:%S"),
                                                                self.instrument))
        
        # Check for orders placed and/or scan hits
        if int(self._notify) > 0 and self._backtest_mode is False:
            
            for order_details in self._latest_orders:
                self._broker_utils.write_to_order_summary(order_details, 
                                                         self._order_summary_fp)
            
            if int(self._notify) > 1 and \
                self._email_params['mailing_list'] is not None and \
                self._email_params['host_email'] is not None:
                    if int(self._verbosity) > 0 and len(self._latest_orders) > 0:
                            print("Sending emails ...")
                            
                    for order_details in self._latest_orders:
                        emailing.send_order(order_details,
                                            self._email_params['mailing_list'],
                                            self._email_params['host_email'])
                        
                    if int(self._verbosity) > 0 and len(self._latest_orders) > 0:
                            print("  Done.\n")
            
        # Check scan results
        if self._scan_mode:
            # Construct scan details dict
            scan_details    = {'index'      : self._scan_index,
                               'strategy'   : self._strategy.name,
                               'timeframe'  : self._strategy_params['granularity']
                               }
            
            # Report AutoScan results
            # Scan reporting with no emailing requested.
            if int(self._verbosity) > 0 or \
                int(self._notify) == 0:
                if len(self._scan_results) == 0:
                    print("{}: No signal detected.".format(self.instrument))
                else:
                    # Scan detected hits
                    for instrument in self._scan_results:
                        signal = self._scan_results[instrument]['signal']
                        signal_type = 'Long' if signal == 1 else 'Short'
                        print(f"{instrument}: {signal_type} signal detected.")
            
            if int(self._notify) > 0:
                # Emailing requested
                if len(self._scan_results) > 0 and \
                    self._email_params['mailing_list'] is not None and \
                    self._email_params['host_email'] is not None:
                    # There was a scanner hit and email information is provided
                    emailing.send_scan_results(self._scan_results, 
                                               scan_details, 
                                               self._email_params['mailing_list'],
                                               self._email_params['host_email'])
                elif int(self._notify) > 1 and \
                    self._email_params['mailing_list'] is not None and \
                    self._email_params['host_email'] is not None:
                    # There was no scan hit, but notify set > 1, so send email
                    # regardless.
                    emailing.send_scan_results(self._scan_results, 
                                               scan_details, 
                                               self._email_params['mailing_list'],
                                               self._email_params['host_email'])
                    
    
    def _check_orders(self, orders) -> list:
        """Checks that orders returned from strategy are in the correct
        format.
        
        Returns
        -------
        List of Orders
        
        Notes
        -----
        An order must have (at the very least) an order type specified. Usually,
        the direction will also be required, except in the case of close order 
        types. If an order with no order type is provided, it will be ignored.
        """
        
        def check_type(orders):
            checked_orders = []
            if isinstance(orders, dict):
                # Order(s) provided in dictionary
                if 'order_type' in orders:
                    # Single order dict provided
                    if 'instrument' not in orders:
                        orders['instrument'] = self.instrument
                    checked_orders.append(Order._from_dict(orders))
                    
                elif len(orders) > 0:
                    # Multiple orders provided
                    for key, item in orders.items():
                        if isinstance(item, dict) and 'order_type' in item:
                            # Convert order dict to Order object
                            if 'instrument' not in item:
                                item['instrument'] = self.instrument
                            checked_orders.append(Order._from_dict(item))
                        elif isinstance(item, Order):
                            # Native Order object, append as is
                            checked_orders.append(item)
                        else:
                            raise Exception(f"Invalid order submitted: {item}")
                
                elif len(orders) == 0:
                    # Empty order dict
                    pass
                
            elif isinstance(orders, Order):
                # Order object directly returned
                checked_orders.append(orders)
                
            elif isinstance(orders, list):
                # Order(s) provided in list
                for item in orders:
                    if isinstance(item, dict) and 'order_type' in item:
                        # Convert order dict to Order object
                        if 'instrument' not in item:
                            item['instrument'] = self.instrument
                        checked_orders.append(Order._from_dict(item))
                    elif isinstance(item, Order):
                        # Native Order object, append as is
                        checked_orders.append(item)
                    else:
                        raise Exception(f"Invalid order submitted: {item}")
            else:
                raise Exception(f"Invalid order submitted: {item}")
            
            return checked_orders
        
        def add_strategy_data(orders):
            # Append strategy parameters to each order
            for order in orders:
                order.instrument = self.instrument if not order.instrument else order.instrument
                order.strategy = self._strategy.name
                order.granularity = self._strategy_params['granularity']
                order._sizing = self._strategy_params['sizing']
                order._risk_pc = self._strategy_params['risk_pc']
                
        def check_order_details(orders: list) -> None:
            for ix, order in enumerate(orders):
                if order.order_type in ['market', 'limit', 'stop-limit', 'reduce']:
                    if not order.direction:
                        del orders[ix]
                        if self._verbosity > 1:
                            print("No trade direction provided for " + \
                                  f"{order.order_type} order. Order will be ignored.")
        
        # Perform checks
        checked_orders = check_type(orders)
        add_strategy_data(checked_orders)
        check_order_details(checked_orders)
        
        return checked_orders
        
    
    def _qualify_orders(self, orders: list, i: int) -> None:
        """Passes price data to order to populate missing fields.
        """
        for order in orders:
            if self._req_liveprice:
                liveprice_func = getattr(self._get_data, f'{self._feed.lower()}_liveprice')
                last_price = liveprice_func(order)
            else:
                last_price = self._get_data._pseduo_liveprice(last=self.data.Close[i],
                                                              quote_price=self.quote_data.Close[i])
            
            if order.direction < 0:
                order_price = last_price['bid']
                HCF = last_price['negativeHCF']
            else:
                order_price = last_price['ask']
                HCF = last_price['positiveHCF']
            
            # Call order with price and time
            order(broker=self._broker, order_price=order_price, HCF=HCF)
    
    
    def _update_backtest(self, i: int) -> None:
        """Updates virtual broker with latest price data for backtesting.
        """
        candle = self.data.iloc[i]
        self._broker._update_positions(candle, self.instrument)
    
    
    def _next_candle_open(self, granularity: str) -> datetime:
        """Returns the UTC datetime object corresponding to the open time of the 
        next candle.
        """
        current_ts = datetime.now(tz=pytz.utc).timestamp()
        granularity_in_seconds = self._broker_utils.interval_to_seconds(granularity)
        next_candle_open_ts = granularity_in_seconds * np.ceil(current_ts / granularity_in_seconds)
        
        return datetime.fromtimestamp(next_candle_open_ts, tz=pytz.utc)
            

    def _create_backtest_summary(self, balance: pd.Series, NAV: pd.Series, 
                                margin: pd.Series) -> dict:
        """Constructs backtest summary dictionary for further processing.
        """
        trade_summary = self._broker_utils.trade_summary(trades=self._broker.trades,
                                                         instrument=self.instrument)
        order_summary = self._broker_utils.trade_summary(orders=self._broker.orders,
                                                         instrument=self.instrument)
        
        # closed_trades = trade_summary[trade_summary.status == 'closed']
        open_trade_summary = trade_summary[trade_summary.status == 'open']
        cancelled_summary = order_summary[order_summary.status == 'cancelled']
        
        backtest_dict = {}
        backtest_dict['data'] = self.data
        backtest_dict['account_history'] = pd.DataFrame(data={'balance': balance, 
                                                              'NAV': NAV, 
                                                              'margin': margin,
                                                              'drawdown': np.array(NAV)/np.maximum.accumulate(NAV) - 1}, 
                                                        index=self.data.index)
        backtest_dict['trade_summary'] = trade_summary
        backtest_dict['indicators'] = self._strategy.indicators if hasattr(self._strategy, 'indicators') else None
        backtest_dict['instrument'] = self.instrument
        backtest_dict['interval'] = self._strategy_params['granularity']
        backtest_dict['open_trades'] = open_trade_summary
        backtest_dict['cancelled_trades'] = cancelled_summary
        
        self.backtest_summary = backtest_dict
    
    
    def _get_iteration_range(self) -> int:
        """Checks mode of operation and returns data iteration range. For backtesting,
        the entire dataset is iterated over. For livetrading, only the latest candle
        is used.
        """
        if self._backtest_mode:
            start_range = 0
        else:
            start_range = len(self.data)-1
        end_range       = len(self.data)

        return start_range, end_range
    
    
    def _replace_data(self, data: pd.DataFrame) -> None:
        """Function to replace the data assigned locally and to the strategy.
        """
        self.data = data
        self._strategy.data = data
    
    
    def _match_quote_data(self, data: pd.DataFrame, 
                          quote_data: pd.DataFrame) -> pd.DataFrame:
        """Function to match index of trading data and quote data.
        """
        datasets = [data, quote_data]
        adjusted_datasets = []
        
        for dataset in datasets:
            # Initialise common index
            common_index = dataset.index
            
            # Update common index by intersection with other data 
            for other_dataset in datasets:
                common_index = common_index.intersection(other_dataset.index)
            
            # Adjust data using common index found
            adj_data = dataset[dataset.index.isin(common_index)]
            
            adjusted_datasets.append(adj_data)
        
        # Unpack adjusted datasets
        adj_data, adj_quote_data = adjusted_datasets
        
        return adj_data, adj_quote_data