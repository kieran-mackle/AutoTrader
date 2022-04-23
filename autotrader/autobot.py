import os
import importlib
import pandas as pd
from autotrader.comms import emailing
from datetime import datetime, timezone
from autotrader.autodata import GetData
from autotrader.brokers.trading import Order
from autotrader.utilities import read_yaml, get_config, BacktestResults


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
    backtest_results : BacktestResults
        A class containing results from the bot in backtest. This 
        is available only after a backtest and has attributes: 'data', 
        'account_history', 'trade_summary', 'indicators', 'instrument', 
        'interval', 'open_trades', 'cancelled_trades'.
    
    """
    
    def __init__(self, instrument: str, strategy_dict: dict, 
                 broker, deploy_dt: datetime, data_dict: dict, 
                 quote_data_path: str, auxdata: dict, 
                 autotrader_instance) -> None:
        """Instantiates an AutoTrader Bot.

        Parameters
        ----------
        instrument : str
            The trading instrument assigned to the bot instance.
        strategy_dict : dict
            The strategy configuration dictionary.
        broker : AutoTrader Broker instance
            The AutoTrader Broker module.
        deploy_dt : datetime
            The datetime stamp of the bot deployment time.
        data_dict : dict
            The strategy data.
        quote_data_path : str
            The quote data filepath for the trading instrument 
            (for backtesting only).
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
        risk_pc = strategy_config["RISK_PC"] if 'RISK_PC' \
            in strategy_config else None
        sizing = strategy_config["SIZING"] if 'SIZING' \
            in strategy_config else None
        params = strategy_config["PARAMETERS"] if "PARAMETERS" in strategy_config else {}
        strategy_params = params
        strategy_params['granularity'] = strategy_params['granularity'] \
            if 'granularity' in strategy_params else interval
        strategy_params['risk_pc'] = strategy_params['risk_pc'] \
            if 'risk_pc' in strategy_params else risk_pc
        strategy_params['sizing'] = strategy_params['sizing'] \
            if 'sizing' in strategy_params else sizing
        strategy_params['period'] = strategy_params['period'] \
            if 'period' in strategy_params else period
        strategy_params['INCLUDE_POSITIONS'] = strategy_config['INCLUDE_POSITIONS'] \
            if 'INCLUDE_POSITIONS' in strategy_config else False
        strategy_config['INCLUDE_BROKER'] = strategy_config['INCLUDE_BROKER'] \
            if 'INCLUDE_BROKER' in strategy_config else False
        strategy_config['INCLUDE_STREAM'] = strategy_config['INCLUDE_STREAM'] \
            if 'INCLUDE_STREAM' in strategy_config else False
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
        
        # Strategy shutdown routine
        self._strategy_shutdown_method = strategy_dict['shutdown_method']
        
        # Get broker configuration 
        if self._global_config_dict is not None:
            # Use global config dict provided
            global_config = self._global_config_dict
        else:
            global_config_fp = os.path.join(self._home_dir, 'config', 'GLOBAL.yaml')
            if os.path.isfile(global_config_fp):
                global_config = read_yaml(global_config_fp)
            else:
                global_config = None
        broker_config = get_config(self._environment, global_config, self._feed)
   
        # Data retrieval
        self._quote_data_file = quote_data_path     # Either str or None
        self._data_filepaths = data_dict            # Either str or dict, or None
        self._auxdata_files = auxdata               # Either str or dict, or None
        
        # Check for portfolio strategy
        trade_portfolio = strategy_config['PORTFOLIO'] if 'PORTFOLIO' in \
            strategy_config else False
        
        portfolio = strategy_config['WATCHLIST'] if trade_portfolio else False
        
        # Fetch data
        self._get_data = GetData(broker_config, self._allow_dancing_bears,
                                 self._base_currency)
        
        # Create instance of data stream object
        stream_attributes = {"data_filepaths": self._data_filepaths,
                             "quote_data_file": self._quote_data_file,
                             "auxdata_files": self._auxdata_files,
                             "strategy_params": self._strategy_params,
                             "get_data": self._get_data,
                             "data_start": self._data_start,
                             "data_end": self._data_end,
                             "instrument": self.instrument,
                             "feed": self._feed,
                             "portfolio": portfolio}
        self.Stream = self._data_stream_object(**stream_attributes)
        
        # Initial data call
        self._refresh_data(deploy_dt)
        
        # Instantiate Strategy
        strategy_inputs = {'parameters': params, 'data': self._strat_data,
                           'instrument': instrument}
        
        if strategy_config['INCLUDE_BROKER']:
            strategy_inputs['broker'] = self._broker
            strategy_inputs['broker_utils'] = self._broker_utils
        
        if strategy_config['INCLUDE_STREAM']:
            strategy_inputs['data_stream'] = self.Stream
            
        my_strat = strategy(**strategy_inputs)
            
        # Assign strategy to local attributes
        self._last_bars = None
        self._strategy = my_strat
        self._strategy_name = strategy_config['NAME'] if 'NAME' in \
            strategy_config else '(unnamed strategy)'
        
        # Assign strategy attributes for tick-based strategy development
        if self._backtest_mode:
            self._strategy._backtesting = True
            self.backtest_results = None
        if interval.split(',')[0] == 'tick':
            self._strategy._tick_data = True
        
        if int(self._verbosity) > 0:
                print(f"\nAutoTraderBot assigned to trade {instrument}",
                      f"with {self._broker_name} broker using {strategy_config['NAME']}.")
    
    
    def __repr__(self):
        return f'{self.instrument} AutoTraderBot'
    
    
    def __str__(self):
        return 'AutoTraderBot instance'
    
    
    def _update(self, i: int = None, timestamp: datetime = None) -> None:
        """Update strategy with the latest data and generate a trade signal.
        

        Parameters
        ----------
        i : int, optional
            The indexing parameter used when running in periodic update mode. 
            The default is None.
        timestamp : datetime, optional
            The timestamp parameter used when running in continuous update 
            mode. The default is None.

        Returns
        -------
        None
            Trade signals generated will be submitted to the broker.

        """
        
        if self._run_mode == 'continuous':
            # Running in continuous update mode
            strat_data, current_bars, quote_bars, sufficient_data = self._check_data(timestamp, self._data_indexing)
            strat_object = strat_data
            
        else:
            # Running in periodic update mode
            current_bars = {self.instrument: self.data.iloc[i]}
            quote_bars = {self.instrument: self.quote_data.iloc[i]}
            sufficient_data = True
            strat_object = i
        
        # Check for new data
        new_data = self._check_last_bar(current_bars) 
        
        if sufficient_data and new_data:
            if self._backtest_mode or self._virtual_livetrading:
                # Update virtual broker with latest price bars
                self._update_virtual_broker(current_bars)
            
            # Get strategy orders
            if self._strategy_params['INCLUDE_POSITIONS']:
                current_position = self._broker.get_positions(self.instrument)
                strategy_orders = self._strategy.generate_signal(strat_object, 
                                            current_position=current_position)
            else:
                strategy_orders = self._strategy.generate_signal(strat_object)
            
            # Check and qualify orders
            orders = self._check_orders(strategy_orders)
            self._qualify_orders(orders, current_bars, quote_bars)
            
            # Submit orders
            for order in orders:
                if self._scan_mode:
                    # Bot is scanning
                    scan_hit = {"size"  : order.size,
                                "entry" : current_bars[order.instrument].Close,
                                "stop"  : order.stop_loss,
                                "take"  : order.take_profit,
                                "signal": order.direction}
                    self._scan_results[self.instrument] = scan_hit
                    
                else:
                    # Bot is trading
                    try:
                        order_time = current_bars[order.instrument].name
                    except:
                        order_time = current_bars[order.data_name].name
                        
                    self._broker.place_order(order, order_time=order_time)
            
            if int(self._verbosity) > 1:
                current_time = current_bars[list(current_bars.keys())[0]].name.strftime('%b %d %Y %H:%M:%S')
                if len(orders) > 0:
                    for order in orders:
                        direction = 'long' if order.direction > 1 else 'short'
                        order_string = f"{current_time}: {order.instrument} "+\
                            f"{direction} {order.order_type} order of " + \
                            f"{order.size} units placed at {order.order_price}."
                        print(order_string)
                else:
                    if int(self._verbosity) > 2:
                        print(f"{current_time}: No signal detected ({self.instrument}).")
            
            # Check for orders placed and/or scan hits
            if int(self._notify) > 0 and not self._backtest_mode:
                for order in orders:
                    self._broker_utils.write_to_order_summary(order, 
                                                              self._order_summary_fp)
                
                if int(self._notify) > 1 and \
                    self._email_params['mailing_list'] is not None and \
                    self._email_params['host_email'] is not None:
                        if int(self._verbosity) > 0 and len(self._latest_orders) > 0:
                                print("Sending emails ...")
                                
                        for order in orders:
                            emailing.send_order(order,
                                                self._email_params['mailing_list'],
                                                self._email_params['host_email'])
                            
                        if int(self._verbosity) > 0 and len(orders) > 0:
                            print("  Done.\n")
            
            # Check scan results
            if self._scan_mode:
                # Construct scan details dict
                scan_details = {'index': self._scan_index,
                                'strategy': self._strategy.name,
                                'timeframe': self._strategy_params['granularity']
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
            
        else:
            if int(self._verbosity) > 1:
                print("\nThe strategy has not been updated as there is either "+\
                      "insufficient data, or no new data. If you believe "+\
                      "this is an error, try setting allow_dancing_bears to "+\
                      "True in AutoTrader.configure().")
        
    
    def _refresh_data(self, timestamp: datetime = None, **kwargs):
        """Refreshes the active Bot's data attributes for trading. 
        
        When backtesting without dynamic data updates, the data attributes
        of the bot will be constant. When using dynamic data, or when 
        livetrading in continuous mode, the data attributes will change 
        as time passes, reflecting more up-to-date data. This method refreshes
        the data attributes for a given timestamp by calling the datastream 
        object.

        Parameters
        ----------
        timestamp : datetime, optional
            The current timestamp. If None, datetime.now() will be called.
            The default is None.
        **kwargs : dict
            Any other named arguments.

        Raises
        ------
        Exception
            When there is an error retrieving the data.

        Returns
        -------
        None: 
            The up-to-date data will be assigned to the Bot instance.

        """
        
        timestamp = datetime.now(timezone.utc) if timestamp is None else timestamp
        
        # Fetch new data
        data, multi_data, quote_data, auxdata = self.Stream.refresh(timestamp=timestamp)
        
        # Check data returned is valid
        if len(data) == 0:
            raise Exception("Error retrieving data.")
        
        # Data assignment
        if multi_data is None:
            strat_data = data
        else:
            strat_data = multi_data
        
        # Auxiliary data assignment
        if auxdata is not None:
            strat_data = {'base': strat_data,
                          'aux': auxdata}
        
        # Assign data attributes to bot
        self._strat_data = strat_data
        self.data = data
        self.multi_data = multi_data
        self.auxdata = auxdata
        self.quote_data = quote_data
        
    
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
                raise Exception(f"Invalid order/s submitted: '{orders}' recieved")
            
            return checked_orders
        
        def add_strategy_data(orders):
            # Append strategy parameters to each order
            for order in orders:
                order.instrument = self.instrument if not order.instrument else order.instrument
                order.strategy = self._strategy.name if 'name' in \
                    self._strategy.__dict__ else self._strategy_name
                order.granularity = self._strategy_params['granularity']
                order._sizing = self._strategy_params['sizing']
                order._risk_pc = self._strategy_params['risk_pc']
                
        def check_order_details(orders: list) -> None:
            for ix, order in enumerate(orders):
                order.instrument = order.instrument if order.instrument is not None else self.instrument
                if order.order_type in ['market', 'limit', 'stop-limit', 'reduce']:
                    if not order.direction:
                        del orders[ix]
        
        # Perform checks
        checked_orders = check_type(orders)
        add_strategy_data(checked_orders)
        check_order_details(checked_orders)
        
        return checked_orders
        
    
    def _qualify_orders(self, orders: list, current_bars: dict,
                        quote_bars: dict) -> None:
        """Passes price data to order to populate missing fields.
        """
        for order in orders:
            if self._req_liveprice:
                liveprice_func = getattr(self._get_data, f'{self._feed.lower()}_liveprice')
                last_price = liveprice_func(order)
            else:
                try:
                    last_price = self._get_data._pseduo_liveprice(last=current_bars[order.instrument].Close,
                                                                  quote_price=quote_bars[order.instrument].Close)
                except:
                    last_price = self._get_data._pseduo_liveprice(last=current_bars[order.data_name].Close,
                                                                  quote_price=quote_bars[order.data_name].Close)
            
            if order.order_type not in ['close', 'reduce', 'modify']:
                if order.direction < 0:
                    order_price = last_price['bid']
                    HCF = last_price['negativeHCF']
                else:
                    order_price = last_price['ask']
                    HCF = last_price['positiveHCF']
            else:
                # Close, reduce or modify order type, provide dummy inputs
                order_price = last_price['ask']
                HCF = last_price['positiveHCF']
            
            # Call order with price and time
            order(broker=self._broker, order_price=order_price, HCF=HCF)
    
    
    def _update_virtual_broker(self, current_bars: dict) -> None:
        """Updates virtual broker with latest price data.
        """
        for product, bar in current_bars.items():
            self._broker._update_positions(bar, product)
    
    
    def _create_backtest_results(self) -> dict:
        """Constructs backtest summary dictionary for further processing.
        """
        backtest_results = BacktestResults(self._broker, self.instrument)
        backtest_results.indicators = self._strategy.indicators if \
            hasattr(self._strategy, 'indicators') else None
        backtest_results.data = self.data
        backtest_results.interval = self._strategy_params['granularity']
        self.backtest_results = backtest_results
    
    
    def _get_iteration_range(self) -> int:
        """Checks mode of operation and returns data iteration range. For backtesting,
        the entire dataset is iterated over. For livetrading, only the latest candle
        is used. ONLY USED IN BACKTESTING NOW.
        """
        
        start_range = self._strategy_params['period']
        end_range = len(self.data)
        
        if len(self.data) < start_range:
            raise Exception("There are not enough bars in the data to " + \
                            "run the backtest with the current strategy " + \
                            "configuration settings. Either extend the " + \
                            "backtest period, or reduce the PERIOD key of " + \
                            "your strategy configuration.")
        
        return start_range, end_range
    
    
    @staticmethod
    def _check_ohlc_data(ohlc_data: pd.DataFrame, timestamp: datetime, 
                         indexing: str = 'open', tail_bars: int = None,
                         check_for_future_data: bool = True) -> pd.DataFrame:
        """Checks the index of inputted data to ensure it contains no future 
        data.

        Parameters
        ----------
        ohlc_data : pd.DataFrame
            DESCRIPTION.
        timestamp : datetime
            The current timestamp.
        indexing : str, optional
            How the OHLC data has been indexed (either by bar 'open' time, or
            bar 'close' time). The default is 'open'.
        tail_bars : int, optional
            If provided, the data will be truncated to provide the number
            of bars specified. The default is None.
        check_for_future_data : bool, optional
            A flag to check for future entries in the data. The default is True.
        
        Raises
        ------
        Exception
            When an unrecognised data indexing type is specified.

        Returns
        -------
        past_data : pd.DataFrame
            The checked data.

        """
        if check_for_future_data:
            if indexing.lower() == 'open':
                past_data = ohlc_data[ohlc_data.index < timestamp]
            elif indexing.lower() == 'close':
                past_data = ohlc_data[ohlc_data.index <= timestamp]
            else:
                raise Exception(f"Unrecognised indexing type '{indexing}'.")
        else:
            past_data = ohlc_data
        
        if tail_bars is not None:
            past_data = past_data.tail(tail_bars)
            
        return past_data
    
    
    def _check_auxdata(self, auxdata: dict, timestamp: datetime, 
                       indexing: str = 'open', tail_bars: int = None,
                       check_for_future_data: bool = True) -> dict:
        """Function to check the strategy auxiliary data.

        Parameters
        ----------
        auxdata : dict
            The strategy's auxiliary data.
        timestamp : datetime
            The current timestamp.
        indexing : str, optional
            How the OHLC data has been indexed (either by bar 'open' time, or
            bar 'close' time). The default is 'open'.
        tail_bars : int, optional
            If provided, the data will be truncated to provide the number
            of bars specified. The default is None.
        check_for_future_data : bool, optional
            A flag to check for future entries in the data. The default is True.

        Returns
        -------
        dict
            The checked auxiliary data.

        """
        processed_auxdata = {}
        for key, item in auxdata.items():
            if isinstance(item, pd.DataFrame) or isinstance(item, pd.Series):
                processed_auxdata[key] = self._check_ohlc_data(item, timestamp, 
                                    indexing, tail_bars, check_for_future_data)
            else:
                processed_auxdata[key] = item
        return processed_auxdata
                
    
    def _check_data(self, timestamp: datetime, indexing: str = 'open') -> dict:
        """Function to return trading data based on the current timestamp. If 
        dynamc_data updates are required (eg. when livetrading), the 
        datastream will be refreshed each update to retrieve new data. The 
        data will then be checked to ensure that there is no future data 
        included.

        Parameters
        ----------
        timestamp : datetime
            DESCRIPTION.
        indexing : str, optional
            DESCRIPTION. The default is 'open'.

        Returns
        -------
        strat_data : dict
            The checked strategy data.
        current_bars : dict(pd.core.series.Series)
            The current bars for each product.
        quote_bars : dict(pd.core.series.Series)
            The current quote data bars for each product.
        sufficient_data : bool
            Boolean flag whether sufficient data is available.

        """
        
        def get_current_bars(data: pd.DataFrame, quote_data: bool = False,
                             processed_strategy_data: dict = None) -> dict:
            """Returns the current bars of data. If the inputted data is for
            quote bars, then the quote_data boolean will be True.
            """
            if len(data) > 0:
                current_bars = self.Stream.get_trading_bars(data=data, 
                                quote_bars=quote_data, timestamp=timestamp,
                                processed_strategy_data=processed_strategy_data)
            else:
                current_bars = None
            return current_bars
        
        def process_strat_data(original_strat_data, check_for_future_data):
            sufficient_data = True
            
            if isinstance(original_strat_data, dict):
                if 'aux' in original_strat_data:
                    base_data = original_strat_data['base']
                    processed_auxdata = self._check_auxdata(original_strat_data['aux'],
                                    timestamp, indexing, no_bars, check_for_future_data)
                else:
                    # MTF data
                    base_data = original_strat_data
                
                # Process base OHLC data
                processed_basedata = {}
                for granularity, data in base_data.items():
                    processed_basedata[granularity] = self._check_ohlc_data(data, 
                                timestamp, indexing, no_bars, check_for_future_data)
                
                # Combine the results of the conditionals above
                strat_data = {}
                if 'aux' in original_strat_data:
                    strat_data['aux'] = processed_auxdata
                    strat_data['base'] = processed_basedata
                else:
                    strat_data = processed_basedata
                    
                # Extract current bar
                first_tf_data = processed_basedata[list(processed_basedata.keys())[0]]
                current_bars = get_current_bars(first_tf_data, 
                                                processed_strategy_data=strat_data)
                
                # Check that enough bars have accumulated
                if len(first_tf_data) < no_bars:
                    sufficient_data = False
                
            elif isinstance(original_strat_data, pd.DataFrame):
                strat_data = self._check_ohlc_data(original_strat_data, 
                             timestamp, indexing, no_bars, check_for_future_data)
                current_bars = get_current_bars(strat_data,
                                                processed_strategy_data=strat_data)
                
                # Check that enough bars have accumulated
                if len(strat_data) < no_bars:
                    sufficient_data = False
            
            else:
                raise Exception("Unrecognised data type. Cannot process.")
            
            return strat_data, current_bars, sufficient_data
        
        # Define minimum number of bars for strategy to run
        no_bars = self._strategy_params['period']
        
        if self._backtest_mode:
            check_for_future_data = True
            if self._dynamic_data:
                self._refresh_data(timestamp)
        else:
            # Livetrading
            self._refresh_data(timestamp)
            check_for_future_data = False
            
        strat_data, current_bars, sufficient_data = process_strat_data(self._strat_data, 
                                                                       check_for_future_data)

        # Process quote data
        if isinstance(self.quote_data, dict):
            processed_quote_data = {}
            for instrument in self.quote_data:
                processed_quote_data[instrument] = self._check_ohlc_data(self.quote_data[instrument], 
                                                               timestamp, 
                                                               indexing, 
                                                               no_bars)
            quote_data = processed_quote_data[instrument] # Dummy
            
        elif isinstance(self.quote_data, pd.DataFrame):
            quote_data = self._check_ohlc_data(self.quote_data, timestamp, 
                                               indexing, no_bars)
            processed_quote_data = {self.instrument: quote_data}
        else:
            raise Exception("Unrecognised data type. Cannot process.")
        
        # Get quote bars
        quote_bars = get_current_bars(quote_data, True, processed_quote_data)
        
        return strat_data, current_bars, quote_bars, sufficient_data
    
    
    def _check_last_bar(self, current_bars: dict) -> bool:
        """Checks for new data to prevent duplicate signals.
        """
        try:
            duplicated_bars = []
            for product, bar in current_bars.items():
                if (bar == self._last_bars[product]).all():
                    duplicated_bars.append(True)
                else:
                    duplicated_bars.append(False)
                    
            if len(duplicated_bars) == sum(duplicated_bars):
                new_data = False
            else: 
                new_data = True
            
        except:
            new_data = True
        
        # Reset last bars
        self._last_bars = current_bars
            
        if int(self._verbosity) > 1 and not new_data:
            print("Duplicate bar detected. Skipping.")
        
        return new_data
        
    
    def _check_strategy_for_plot_data(self, use_strat_plot_data: bool = False):
        """Checks the bot's strategy to see if it has the plot_data attribute.

        Returns
        -------
        plot_data : pd.DataFrame
            The data to plot.
            
        Notes
        -----
        This method is a placeholder for a future feature, allowing 
        customisation of what is plotted by setting plot_data and plot_type
        attributes from within a strategy.
        """
        strat_params = self._strategy.__dict__
        if 'plot_data' in strat_params and use_strat_plot_data:
            plot_data = strat_params['plot_data']
        else:
            plot_data = self.data
            
        return plot_data
    
    
    def _strategy_shutdown(self,):
        if self._strategy_shutdown_method is not None:
            try:
                shutdown_method = getattr(self._strategy, self._strategy_shutdown_method)
                shutdown_method()
            except AttributeError:
                print(f"\nShutdown method '{self._strategy_shutdown_method}' not found!")
    
    
    def _replace_data(self, data: pd.DataFrame) -> None:
        """Function to replace the data assigned locally and to the strategy.
        Called when there is a mismatch in data lengths during multi-instrument
        backtests in periodic update mode.
        """
        self.data = data
        self._strategy.data = data