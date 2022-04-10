import sys
import yaml
import pandas as pd
from datetime import datetime
from autotrader.brokers.virtual.broker import Broker


def read_yaml(file_path: str) -> dict:
    """Function to read and extract contents from .yaml file.
    
    Parameters
    ----------
    file_path : str
        The absolute filepath to the yaml file.

    Returns
    -------
    dict
        The loaded yaml file in dictionary form.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)
    
    
def write_yaml(data: dict, filepath: str) -> None:
    """Writes a dictionary to a yaml file.

    Parameters
    ----------
    data : dict
        The dictionary to write to yaml.
    filepath : str
        The filepath to save the yaml file.

    Returns
    -------
    None
        The data will be written to the filepath provided.
    """
    with open(filepath, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)
        
    
def get_config(environment: str, global_config: dict, feed: str) -> dict:
    """Returns the configuration dictionary based on the requested 
    environment.

    Parameters
    ----------
    environment : str
        The trading evironment ('demo' or 'real').
    global_config : dict
        The global configuration dictionary.
    feed : str
        The data feed.

    Raises
    ------
    Exception
        When an unrecognised data feed is provided.

    Returns
    -------
    dict
        The AutoTrader configuration dictionary.
    """
    
    if environment.lower() == 'real':
        # Live trading
        if feed.upper() == 'OANDA':
            data_source     = 'OANDA'
            api             = global_config['OANDA']['LIVE_API']
            access_token    = global_config['OANDA']['ACCESS_TOKEN']
            account_id      = global_config['OANDA']['DEFAULT_ACCOUNT_ID']
            port            = global_config['OANDA']['PORT']
            
            config_dict = {'data_source': data_source,
                           'API': api, 
                           'ACCESS_TOKEN': access_token, 
                           'ACCOUNT_ID': account_id, 
                           'PORT': port}
            
        elif feed.upper() == 'IB':
            # TODO - check port for live trading
            data_source = 'IB'
            host = global_config['host'] if 'host' in global_config else '127.0.0.1'
            port = global_config['port'] if 'port' in global_config else 7497
            client_id = global_config['clientID'] if 'clientID' in global_config else 1
            read_only = global_config['read_only'] if 'read_only' in global_config else False
            account = global_config['account'] if 'account' in global_config else ''
            
            config_dict = {'data_source': data_source,
                           'host': host,
                           'port': port,
                           'clientID': client_id,
                           'account': account,
                           'read_only': read_only}
            
        elif feed.upper() == 'YAHOO':
            data_source = 'yfinance'
            config_dict = {'data_source': data_source}
            
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
            
            config_dict = {'data_source': data_source,
                           'API': api, 
                           'ACCESS_TOKEN': access_token, 
                           'ACCOUNT_ID': account_id, 
                           'PORT': port}
            
        elif feed.upper() == 'IB':
            # TODO - check port for paper trading
            data_source = 'IB'
            host = global_config['host'] if 'host' in global_config else '127.0.0.1'
            port = global_config['port'] if 'port' in global_config else 7497
            client_id = global_config['clientID'] if 'clientID' in global_config else 1
            read_only = global_config['read_only'] if 'read_only' in global_config else False
            account = global_config['account'] if 'account' in global_config else ''
            
            config_dict = {'data_source': data_source,
                           'host': host,
                           'port': port,
                           'clientID': client_id,
                           'account': account,
                           'read_only': read_only}
            
        elif feed.upper() == 'YAHOO':
            data_source = 'yfinance'
            config_dict = {'data_source': data_source}
            
        else:
            raise Exception(f"Unrecognised data feed: '{feed}'. " + \
                  "Please check global config and retry.")
    
    return config_dict
    

class BacktestResults:
    """AutoTrader backtest results class."""
    def __init__(self, broker: Broker, instrument: str = None):
        
        self.instruments_traded = None
        self.account_history = None
        self.trade_history = None
        self.order_history = None
        self.open_trades = None
        self.cancelled_orders = None
        
        self.analyse_backtest(broker, instrument)
    
    
    def __str__(self):
        return 'AutoTrader Backtest Results'
    
    
    def __repr__(self):
        return 'AutoTrader Backtest Results'
        
    
    def analyse_backtest(self, broker: Broker, instrument: str = None):
        """Analyses backtest and creates summary of key details.
        """
        # Construct trade and order summaries
        trades = BacktestResults.create_trade_summary(trades=broker.trades, instrument=instrument)
        orders = BacktestResults.create_trade_summary(orders=broker.orders, instrument=instrument)
        
        # Construct account history
        account_history = broker.account_history.copy()
        account_history = account_history[~account_history.index.duplicated(keep='last')]
        account_history['drawdown'] = account_history.NAV/account_history.NAV.cummax() - 1
        
        # Assign attributes
        self.instruments_traded = list(orders.instrument.unique())
        self.account_history = account_history
        self.trade_history = trades
        self.order_history = orders
        self.open_trades = trades[trades.status == 'open']
        self.cancelled_orders = orders[orders.status == 'cancelled']
    
    
    @staticmethod
    def create_trade_summary(trades: dict = None, orders: dict = None, 
                      instrument: str = None) -> pd.DataFrame:
        """Creates backtest trade summary dataframe.
        """
        # TODO - index by ID
        
        if trades is not None:
            iter_dict = trades
        else:
            iter_dict = orders
        
        iter_dict = {} if iter_dict is None else iter_dict 
        
        product = []
        status = []
        ids = []
        times_list = []
        order_price = []
        size = []
        direction = []
        stop_price = []
        take_price = []
        
        if trades is not None:
            entry_time = []
            fill_price = []
            profit = []
            portfolio_balance = []
            exit_times = []
            exit_prices = []
            trade_duration = []
            fees = []
        
        for ID, item in iter_dict.items():
            product.append(item.instrument)
            status.append(item.status)
            ids.append(item.id)
            size.append(item.size)
            direction.append(item.direction)
            times_list.append(item.order_time)
            order_price.append(item.order_price)
            stop_price.append(item.stop_loss)
            take_price.append(item.take_profit)
        
        if trades is not None:
            for trade_id, trade in iter_dict.items():
                entry_time.append(trade.time_filled)
                fill_price.append(trade.fill_price)
                profit.append(trade.profit)
                portfolio_balance.append(trade.balance)
                exit_times.append(trade.exit_time)
                exit_prices.append(trade.exit_price)
                fees.append(trade.fees)
                if trade.status == 'closed':
                    if type(trade.exit_time) == str:
                        exit_dt = datetime.strptime(trade.exit_time, "%Y-%m-%d %H:%M:%S%z")
                        entry_dt = datetime.strptime(trade.time_filled, "%Y-%m-%d %H:%M:%S%z")
                        trade_duration.append(exit_dt.timestamp() - entry_dt.timestamp())
                    elif isinstance(trade.exit_time, pd.Timestamp):
                        trade_duration.append((trade.exit_time - trade.time_filled).total_seconds())
                    else:
                        trade_duration.append(trade.exit_time.timestamp() - 
                                              trade.time_filled.timestamp())
                else:
                    trade_duration.append(None)
                
            dataframe = pd.DataFrame({"instrument": product,
                                      "status": status,
                                      "ID": ids, 
                                      "order_price": order_price,
                                      "order_time": times_list,
                                      "fill_time": entry_time,
                                      "fill_price": fill_price, "size": size,
                                      "direction": direction,
                                      "stop_loss": stop_price, "take_profit": take_price,
                                      "profit": profit, "balance": portfolio_balance,
                                      "exit_time": exit_times, "exit_price": exit_prices,
                                      "trade_duration": trade_duration,
                                      "fees": fees},
                                     index = pd.to_datetime(entry_time))
            
            # Fill missing values for balance
            dataframe.balance.fillna(method='ffill', inplace=True)
            
        else:
            dataframe = pd.DataFrame({"instrument": product,
                                      "status": status,
                                      "ID": ids, 
                                      "order_price": order_price,
                                      "order_time": times_list,
                                      "size": size,
                                      "direction": direction,
                                      "stop_loss": stop_price, 
                                      "take_profit": take_price},
                                     index = pd.to_datetime(times_list))
            
        dataframe = dataframe.sort_index()
        
        # Filter by instrument
        if instrument is not None:
            dataframe = dataframe[dataframe['instrument'] == instrument]
        
        return dataframe


def get_watchlist(index, feed):
    """Returns a watchlist of instruments. 
    
    Notes
    ------
    The current implementation only support forex indices, with Oanda 
    formatting.
    
    Examples
    --------
    >>> get_warchlist('forex:major')
        [Out]: list of major forex pairs
    """
    
    if len(index) == 0:
        print("\nArgument for scan missing. Please specify instrument/index to scan.")
        print("Try $ ./AutoTrader.py -h s for more help.\n")
        sys.exit(0)
    
    if index == 'all':
        ''' Returns all currency pairs. '''
        watchlist = ['EUR_USD', 'USD_JPY', 'GBP_USD', 'AUD_USD', 
                     'USD_CAD', 'USD_CHF', 'NZD_USD', 'EUR_GBP',
                     'EUR_AUD', 'EUR_CAD', 'EUR_CHF', 'EUR_JPY',
                     'EUR_NZD', 'GBP_JPY', 'GBP_AUD', 'GBP_CAD',
                     'GBP_CHF', 'GBP_NZD', 'AUD_CAD', 'AUD_CHF',
                     'AUD_JPY', 'AUD_NZD', 'CAD_CHF', 'CAD_JPY',
                     'CHF_JPY', 'NZD_CHF', 'NZD_JPY']
    
    elif index == 'major':
        ''' Returns major currency pairs. '''
        if feed.lower() == 'oanda':
            watchlist = ['EUR_USD', 'USD_JPY', 'GBP_USD', 'AUD_USD', 
                         'USD_CAD', 'USD_CHF', 'NZD_USD']
            
        elif feed.lower() == 'yahoo':
            watchlist = ['EURUSD=X', 'USDJPY=X', 'GBPUSD=X', 'AUDUSD=X', 
                         'USDCAD=X', 'USDCHF=X', 'NZDUSD=X']
        
    elif index == 'minor':
        ''' Returns minor currency pairs. '''
        
        if feed.lower() == 'oanda':
            watchlist = ['EUR_GBP', 'EUR_AUD', 'EUR_CAD', 'EUR_CHF',
                         'EUR_JPY', 'EUR_NZD', 'GBP_JPY', 'GBP_AUD',
                         'GBP_CAD', 'GBP_CHF', 'GBP_NZD', 'AUD_CAD',
                         'AUD_CHF', 'AUD_JPY', 'AUD_NZD', 'CAD_CHF',
                         'CAD_JPY', 'CHF_JPY', 'NZD_CHF', 'NZD_JPY']
            
        elif feed.lower() == 'yahoo':
            watchlist = ['EURGBP=X', 'EURAUD=X', 'EURCAD=X', 'EURCHF=X',
                         'EURJPY=X', 'EURNZD=X', 'GBPJPY=X', 'GBPAUD=X',
                         'GBPCAD=X', 'GBPCHF=X', 'GBPNZD=X', 'AUDCAD=X',
                         'AUDCHF=X', 'AUDJPY=X', 'AUDNZD=X', 'CADCHF=X',
                         'CADJPY=X', 'CHFJPY=X', 'NZDCHF=X', 'NZDJPY=X']
    
    elif index == 'exotic':
        ''' Returns exotic currency pairs. '''
        watchlist = ['EUR_TRY', 'USD_HKD', 'JPY_NOK', 'NZD_SGD',
        	         'GBP_ZAR', 'AUD_MXN'] 
    
    elif index[3] == "_":
        watchlist = [index]
    
    else:
        print("Not supported.")
        sys.exit(0)

    
    return watchlist


class DataStream:
    """Data stream class.
    
    This class is intended to provide a means of custom data pipelines.
    
    Methods
    -------
    _retrieve_data
        Returns data, multi_data, quote_data, auxdata
    
    """
    
    def __init__(self, **kwargs):
        # Attributes
        self.instrument = None
        self.feed = None
        self.data_filepaths = None
        self.quote_data_file = None
        self.auxdata_files = None
        self.strategy_params = None
        self.get_data  = None
        self.data_start = None
        self.data_end = None
        
        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])
        
    
    def refresh(self, timestamp: datetime = None):
        """Returns up-to-date trading data.

        Parameters
        ----------
        timestamp : datetime, optional
            The current timestamp. The default is None.

        Returns
        -------
        data : pd.DataFrame
            The OHLC price data.
        multi_data : dict
            A dictionary of DataFrames.
        quote_data : pd.DataFrame
            The quote data.
        auxdata : dict
            Strategy auxiliary data.

        """
        # Retrieve main data
        if self.data_filepaths is not None:
            # Local data filepaths provided
            if isinstance(self.data_filepaths, str):
                # Single data filepath provided
                data = self.get_data.local(self.data_filepaths, self.data_start, 
                                            self.data_end)
                multi_data = None
                
            elif isinstance(self.data_filepaths, dict):
                # Multiple data filepaths provided
                multi_data = {}
                for granularity, filepath in self.data_filepaths.items():
                    data = self.get_data.local(filepath, self.data_start, self.data_end)
                    multi_data[granularity] = data
                
                # Extract first dataset as base data
                data = multi_data[list(self.data_filepaths.keys())[0]]
        
        else:
            # Download data
            multi_data = {}
            for granularity in self.strategy_params['granularity'].split(','):
                data_func = getattr(self.get_data, self.feed.lower())
                data = data_func(self.instrument, granularity=granularity, 
                                 count=self.strategy_params['period'], 
                                 start_time=self.data_start,
                                 end_time=self.data_end)
                
                multi_data[granularity] = data
            
            data = multi_data[self.strategy_params['granularity'].split(',')[0]]
            
            if len(multi_data) == 1:
                multi_data = None
        
        # Retrieve quote data
        if self.quote_data_file is not None:
            quote_data = self.get_data.local(self.quote_data_file, 
                                              self.data_start, self.data_end)
        else:
            quote_data_func = getattr(self.get_data,f'_{self.feed.lower()}_quote_data')
            quote_data = quote_data_func(data, self.instrument, 
                                         self.strategy_params['granularity'].split(',')[0], 
                                         self.data_start, self.data_end)
        
        # Retrieve auxiliary data
        if self.auxdata_files is not None:
            if isinstance(self.auxdata_files, str):
                # Single data filepath provided
                auxdata = self.get_data.local(self.auxdata_files, self.data_start, 
                                               self.data_end)
                
            elif isinstance(self.auxdata_files, dict):
                # Multiple data filepaths provided
                auxdata = {}
                for key, filepath in self.auxdata_files.items():
                    data = self.get_data.local(filepath, self.data_start, self.data_end)
                    auxdata[key] = data
        else:
            auxdata = None
        
        # Correct any data mismatches
        data, quote_data = self.match_quote_data(data, quote_data)
        
        return data, multi_data, quote_data, auxdata
        
    
    def match_quote_data(self, data: pd.DataFrame, 
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
    
    
    def get_trading_bars(self, data: pd.DataFrame, quote_bars: bool,
                         timestamp: datetime = None, 
                         processed_strategy_data: dict = None) -> dict:
        """Returns a dictionary of the current bars of the products being 
        traded.

        Parameters
        ----------
        data : pd.DataFrame
            The strategy base OHLC data.
        quote_bars : bool
            Boolean flag to signal that quote data bars are being requested.

        Returns
        -------
        dict
            A dictionary of bars, keyed by the product name.
        
        Notes
        -----
        The quote data bars dictionary must have the exact same keys as the
        trading bars dictionary. The quote_bars boolean flag is provided for
        this reason.
        """
        return {self.instrument: data.iloc[-1]}
    
    
