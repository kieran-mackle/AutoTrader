import sys
import yaml
import pandas as pd
from datetime import datetime


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
    
    
