import os
import sys
import yaml
import time
import threading
import traceback
import pandas as pd
from datetime import datetime
from autotrader.autodata import GetData


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
    
    Objectives: 
        - return specific list of instruments based on input
          For example; 
              - forex:major -> major forex pairs
              - stocks:asx200
              - custom
    
    The current implementation only support forex indices, with Oanda 
    formatting.
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


class ManageBot:
    """Detaches from AutoTrader run script to allow for a single deployment.
    
    Attributes
    ----------
    bot: class
        The bot being managed.
    
    Methods 
    --------
    update_bot_data()
        Passes the latest price data to the bot.
    kill_bot()
        Terminates the bot from trading.
    write_bot_to_log()
        Adds the bot being managed to the bots_deployed logfile.
    remove_bot_from_log()
        Removes the bot being managed from the bots_deployed logfile.
    
    Notes
    -----
    Strategies being deployed to bot manager must have the following methods:
        - initialise_strategy()
        - exit_strategy(i)
    
    As well as a "terminate" boolean attribute.
    
    Currently, there is only one way to intervene and kill a bot. This is to
    create an empty file named 'killbots' in the home_dir. Note that this
    will kill all bots running. In future updates, killing selected bots will 
    be supported. Options for this include:
        - creating an empty file with name related to specific bot
        - bot manager will create an empty file corresponding to each bot 
          (perhaps in a bots_deployed directory), allowing killing of bots by
          deleting their specific file.
    
    """
    
    def __init__(self, bot, home_dir, bot_name_string, use_stream):
        
        self.bot = bot
        self.home_dir = home_dir
        self.managing = True
        self.use_stream = use_stream
        
        self.active_bots_dir = os.path.join(home_dir, 'active_bots')
        self.active_bot_path = os.path.join(self.active_bots_dir, bot_name_string)
        self.killfile = os.path.join(self.home_dir, 'killbots')
        self.suspendfile = os.path.join(self.home_dir, 'suspendbots')
        
        # Create name string
        self.bot_name_string = bot_name_string
        
        # Check if active_bots directory exists
        if not os.path.isdir(self.active_bots_dir):
            # Directory does not exist, create it
            os.mkdir(self.active_bots_dir)
        
        # Check if bot is already deployed
        bot_already_deployed = self.check_bots_deployed()
        
        if not bot_already_deployed:
            # Spawn new thread for bot manager
            thread = threading.Thread(target=self.manage_bot, args=(), 
                                      daemon=False)
            print("Bot recieved. Now managing bot '{}'.".format(bot_name_string))
            print("To kill bot, delete from bots_deployed directory.")
            print("Alternatively create file named 'killbots' in the home_dir" \
                  + " to kill all bots.\n")
            print("You can also suspend a bot by creating a 'suspendbots' file." \
                  + " Deleting this file will then resume the bots.")
            thread.start()
        else:
            print("Notice: Bot has already been deployed. Exiting.")
        
        
    def manage_bot(self):
        '''
        Manages bot until terminal condition is met.
        '''
        
        # Add bot to log
        self.write_bot_to_log()
        
        # Signal that bot is ready to recieve data from stream
        if self.use_stream:
            self.bot._recieve_stream_data()
        
        # Manage
        while self.managing:
            
            # First check for any termination signals
            if self.bot.strategy.terminate:
                print("\nBot will be terminated.")
                self.remove_bot_from_log()
                
                # End management
                self.managing = False
            
            elif not os.path.exists(self.active_bot_path):
                print("\nBot file deleted. Bot will be terminated.")
                
                if self.use_stream:
                    # Sleep for 5 seconds to allow for any residual stream actions 
                    time.sleep(5)
                    
                self.bot.strategy.exit_strategy(-1)
                
                # End management
                self.managing = False
            
            elif os.path.exists(self.killfile):
                print("\nKillfile detected. Bot will be terminated.")
                
                if self.use_stream:
                    # Sleep for 5 seconds to allow for any residual stream actions 
                    time.sleep(5)
                    
                self.bot.strategy.exit_strategy(-1)
                
                # Remove bot from log
                self.remove_bot_from_log()
                
                # End management
                self.managing = False
            
            elif os.path.exists(self.suspendfile):
                print("\nSuspending {} bot.".format(self.bot_name_string))
                self.suspend()
                print("Resuming {} bot.".format(self.bot_name_string))
                
            else:
                # No termination signal detected, proceed to manage
                
                if not self.use_stream:
                    # Periodic update mode
                    for atempt in range(3):
                        try:
                            # Refresh strategy with latest data
                            self.bot._update_strategy_data()
                            
                            # Call bot update to act on latest data
                            self.bot._update(-1)
                        
                        except BaseException as ex:
                            # Get current system exception
                            ex_type, ex_value, ex_traceback = sys.exc_info()
                        
                            # Extract unformatter stack traces as tuples
                            trace_back = traceback.extract_tb(ex_traceback)
                        
                            # Format stacktrace
                            stack_trace = list()
                        
                            for trace in trace_back:
                                trade_string = "File : %s , Line : %d, " % (trace[0], trace[1]) + \
                                               "Func.Name : %s, Message : %s" % (trace[2], trace[3])
                                stack_trace.append(trade_string)
                            
                            print("WARNING FROM BOT MANAGER: The following exception was caught " +\
                                  "when updating {}.".format(self.bot_name_string))
                            print("Exception type : %s " % ex_type.__name__)
                            print("Exception message : %s" %ex_value)
                            print("Stack trace : %s" %stack_trace)
                            print("  Trying again.")
                        
                        else:
                            break
                        
                    else:
                        print("FATAL: All attempts have failed. Going to sleep.")
                    
                    # Pause an amount, depending on granularity
                    base_granularity = self.bot.strategy_params['granularity'].split(',')[0]
                    if base_granularity == 'tick':
                        time.sleep(3)
                    else:
                        sleep_time = 0.25*self.granularity_to_seconds(base_granularity)
                        time.sleep(sleep_time)


    def suspend(self):
        while os.path.exists(self.suspendfile):
            pass    
            
        
    def write_bot_to_log(self):
        '''
        Adds the bot being managed to the bots_deployed logfile.
        '''
        
        with open(self.active_bot_path, 'w') as f:
            pass
    
    
    def remove_bot_from_log(self):
        '''
        Removes the bot being managed from the bots_deployed logfile.
        '''
        
        os.remove(self.active_bot_path)
        
    
    def check_bots_deployed(self):
        '''
        Checks the bots currently deployed to prevent a re-deployment.
        '''
        
        if os.path.exists(self.active_bot_path):
            return True
        else:
            return False
        

    def granularity_to_seconds(self, granularity):
        '''Converts the interval to time in seconds'''
        letter = granularity[0]
        
        if len(granularity) > 1:
            number = float(granularity[1:])
        else:
            number = 1
        
        conversions = {'S': 1,
                       'M': 60,
                       'H': 60*60,
                       'D': 60*60*24
                       }
        
        seconds = conversions[letter] * number
        
        return seconds
    

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
    
    
