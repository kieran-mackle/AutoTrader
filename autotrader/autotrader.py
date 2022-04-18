import os
import sys
import time
import timeit
import pyfiglet
import importlib
import numpy as np
import pandas as pd
from tqdm import tqdm
from ast import literal_eval
from scipy.optimize import brute
from autotrader.autoplot import AutoPlot
from autotrader.autobot import AutoTraderBot
from datetime import datetime, timezone
from autotrader.utilities import (read_yaml, get_config, 
                                  get_watchlist, DataStream, BacktestResults)


class AutoTrader:
    """A Python-Based Development Platform For Automated Trading Systems.
    
    Methods
    -------
    configure(...)
        Configures run settings for AutoTrader.
    add_strategy(...)
        Adds a strategy to the active AutoTrader instance. 
    backtest(...)
        Configures backtest settings.
    optimise(...)
        Configures optimisation settings.
    scan(...)
        Configures scan settings.
    run()
        Runs AutoTrader with configured settings.
    add_data(...)
        Specify local data files to use for backtests.
    plot_settings(...)
        Configures the plot settings for AutoPlot.
    get_bots_deployed(instrument=None)
        Returns the AutoTrader trading bots deployed in the active instance.
    plot_backtest(bot=None)
        Plots backtest results of a trading Bot.
    plot_multibot_backtest(backtest_results=None)
        Plots backtest results for multiple trading bots.
    multibot_backtest_analysis(bots=None)
        Analyses backtest results of multiple trading bots.
    print_backtest_results(backtest_results)
        Prints backtest results.
    print_multibot_backtest_results(backtest_results=None)
        Prints a multi-bot backtest results.
    
    References
    ----------
    Author: Kieran Mackle
    
    Version: 0.6.0
    
    Homepage: https://kieran-mackle.github.io/AutoTrader/
    
    GitHub: https://github.com/kieran-mackle/AutoTrader
    """
    
    def __init__(self) -> None:
        """AutoTrader initialisation. Called when creating new AutoTrader 
        instance.
        """
        
        self._home_dir = None
        self._verbosity = 1
        
        self._global_config_dict = None
        self._instance_str = None
        self._run_mode = 'periodic'
        self._timestep = pd.Timedelta('10s').to_pytimedelta()
        self._feed = 'yahoo'
        self._req_liveprice = False
        
        self._notify = 0
        self._email_params = None
        self._order_summary_fp = None
        self._show_plot = False
        
        # Livetrade Parameters
        self._check_data_alignment = True
        self._allow_dancing_bears = False
        
        self._broker = None
        self._broker_utils = None
        self._broker_verbosity = 0
        self._environment = 'demo'
        self._account_id = None
        
        self._strategy_configs = {}
        self._strategy_classes = {}
        self._shutdown_methods = {}
        self._uninitiated_strat_files = []
        self._uninitiated_strat_dicts = []
        self._bots_deployed = []
        
        # Backtesting Parameters
        self._backtest_mode = False
        self._data_start = None
        self._data_end = None
        self.backtest_results = None
        
        # Local Data Parameters
        self._data_indexing = 'open'
        self._data_stream_object = DataStream
        self._data_file = None
        self._MTF_data_files = None
        self._local_data = None
        self._local_quote_data = None
        self._auxdata = None
        self._dynamic_data = False
        
        # Virtual Broker Parameters
        self._virtual_livetrading = False
        self._virtual_initial_balance = None
        self._virtual_spread = None
        self._virtual_commission = None
        self._virtual_leverage = None
        self._virtual_broker_hedging = False
        self._virtual_margin_call = 0
        self._base_currency = None
        
        # Optimisation Parameters
        self._optimise_mode = False
        self._opt_params = None
        self._bounds = None
        self._Ns = None
        
        # Scan Parameters
        self._scan_mode = False
        self._scan_index = None
        self._scan_watchlist = None
        
        # Plotting
        self._max_indis_over = 3
        self._max_indis_below = 2
        self._fig_tools = "pan,wheel_zoom,box_zoom,undo,redo,reset,save,crosshair"
        self._ohlc_height = 400
        self._ohlc_width = 800
        self._top_fig_height = 150
        self._bottom_fig_height = 150
        self._jupyter_notebook = False
        self._show_cancelled = True
        self._chart_timeframe = 'default'
        self._chart_theme = 'caliber'
        self._use_strat_plot_data = False
        self._plot_portolio_chart = False
        
    
    def __repr__(self):
        return f'AutoTrader instance in {self._feed} {self._environment} environment'
    
    
    def __str__(self):
        return 'AutoTrader instance'
    
    
    def configure(self, verbosity: int = 1, broker: str = 'virtual', 
                  feed: str = 'yahoo', req_liveprice: bool = False, 
                  notify: int = 0, home_dir: str = None, 
                  allow_dancing_bears: bool = False, account_id: str = None, 
                  environment: str = 'demo', show_plot: bool = False,
                  jupyter_notebook: bool = False, mode: str = 'periodic',
                  update_interval: str = '10s', data_index_time: str = 'open',
                  global_config: dict = None, instance_str: str = None,
                  broker_verbosity: int = 0) -> None:
        """Configures run settings for AutoTrader.

        Parameters
        ----------
        verbosity : int, optional
            The verbosity of AutoTrader (0, 1, 2). The default is 1.
        broker : str, optional
            The broker to connect to. The default is 'virtual'.
        feed : str, optional
            The data feed to be used ('yahoo', 'oanda', 'ib'). The default is 'yahoo'.
        req_liveprice : bool, optional
            Request live market price from broker before placing trade, rather 
            than using the data already provided. The default is False. 
        notify : int, optional
            The level of email notifications (0, 1, 2). The default is 0.
        home_dir : str, optional
            The project home directory. The default is the current working directory.
        allow_dancing_bears : bool, optional
            Allow incomplete candles to be passed to the strategy. The default is False.
        account_id : str, optional
            The brokerage account ID to be used. The default is None.
        environment : str, optional
            The trading environment of this instance ('demo', 'real'). The 
            default is 'demo'.
        show_plot : bool, optional
            Automatically generate backtest chart. The default is False.
        jupyter_notebook : bool, optional
            Set to True when running in Jupyter notebook environment. The 
            default is False.
        mode : str, optional
            The run mode (either 'periodic' or 'continuous'). The default is
            'periodic'.
        update_interval : str, optional
            The update interval to use when running in 'continuous' mode. This
            should align with the highest resolution bar granularity in your
            strategy to allow adequate updates. The string inputted will be
            converted to a timedelta object. The default is '10s'.
        data_index_time : str, optional
            The time by which the data is indexed. Either 'open', if the data
            is indexed by the bar open time, or 'close', if the data is indexed
            by the bar close time. The default is 'open'.
        global_config : dict, optional
            Optionally provide your global configuration directly as a 
            dictionary, rather than it being read in from a yaml file. The
            default is None. 
        instance_str : str, optional
            The name of the active AutoTrader instance, used to control bots
            deployed when livetrading in continuous mode. When not specified,
            the instance string will be of the form 'autotrader_instance_n'.
            The default is None.
        broker_verbosity : int, optional
            The verbosity of the broker. The default is 0.
        
        Returns
        -------
        None
            Calling this method configures the internal settings of 
            the active AutoTrader instance.
        """
        self._verbosity = verbosity
        self._feed = feed
        self._req_liveprice = req_liveprice
        self._broker_name = broker
        self._notify = notify
        self._home_dir = home_dir if home_dir is not None else os.getcwd()
        self._allow_dancing_bears = allow_dancing_bears
        self._account_id = account_id
        self._environment = environment
        self._show_plot = show_plot
        self._jupyter_notebook = jupyter_notebook
        self._run_mode = mode
        self._timestep = pd.Timedelta(update_interval).to_pytimedelta()
        self._data_indexing = data_index_time
        self._global_config_dict = global_config
        self._instance_str = instance_str
        self._broker_verbosity = broker_verbosity
        
        
    def virtual_livetrade_config(self, initial_balance: float = 1000, 
                                  spread: float = 0, commission: float = 0, 
                                  leverage: int = 1, base_currency: str = 'AUD', 
                                  hedging: bool = False, 
                                  margin_call_fraction: float = 0) -> None:
        """Configures the virtual broker's initial state to allow livetrading
        on the virtual broker.
        
        Parameters
        ----------
        initial_balance : float, optional
            The initial balance of the account. The default is 1000.
        spread : float, optional
            The bid/ask spread to use. The default is 0.
        commission : float, optional
            Trading commission as percentage per trade. The default is 0.
        leverage : int, optional
            Account leverage. The default is 1.
        base_currency : str, optional
            The base currency of the account. The default is 'AUD'.
        hedging : bool, optional
            Allow hedging in the virtual broker (opening simultaneous 
            trades in oposing directions). The default is False.
        margin_call_fraction : float, optional
            The fraction of margin usage at which a margin call will occur.
            The default is 0.
            
        """
        # Assign attributes
        self._virtual_livetrading = True
        self._virtual_initial_balance = initial_balance
        self._virtual_spread = spread
        self._virtual_commission = commission
        self._virtual_leverage = leverage
        self._virtual_broker_hedging = hedging
        self._virtual_margin_call = margin_call_fraction
        self._base_currency = base_currency
        
        # Enforce virtual broker
        self._broker_name = 'virtual'
        

    def add_strategy(self, config_filename: str = None, 
                     config_dict: dict = None, strategy = None,
                     shutdown_method: str = None) -> None:
        """Adds a strategy to AutoTrader.

        Parameters
        ----------
        config_filename : str, optional
            The prefix of the yaml strategy configuration file, located in 
            home_dir/config. The default is None.
        config_dict : dict, optional
            Alternative to config_filename, a strategy configuration 
            dictionary can be passed directly. The default is None.
        strategy : AutoTrader Strategy, optional
            The strategy class object. The default is None.
        shutdown_method : str, optional
            The name of the shutdown method in the strategy (if any). This
            method will be called when AutoTrader is livetrading in continuous
            mode, and the instance has recieved the shutdown signal. The 
            default is None.

        Returns
        -------
        None
            The strategy will be added to the active AutoTrader instance.
        """
        # TODO - assign unique ID to different strategies to prevent instrument
        # traded names conflict
        
        if self._home_dir is None:
            # Home directory has not yet been set, postpone strategy addition
            if config_filename is None:
                self._uninitiated_strat_dicts.append(config_dict)
            else:
                self._uninitiated_strat_files.append(config_filename)
            
            if shutdown_method is not None:
                raise Exception("Providing the shutdown method requires "+\
                                "the home directory to have been configured. "+\
                                "please either specify it, or simply call "+\
                                "the configure method before adding a strategy.")
            
        else:
            # Home directory has been set
            if config_dict is None:
                # Config YAML filepath provided
                config_file_path = os.path.join(self._home_dir, 'config', config_filename)
                new_strategy = read_yaml(config_file_path + '.yaml')
            else:
                # Config dictionary provided directly
                new_strategy = config_dict
            
            name = new_strategy['NAME']
            
            if name in self._strategy_configs:
                print("Warning: duplicate strategy name deteced. Please check " + \
                      "the NAME field of your strategy configuration file and " + \
                      "make sure it is not the same as other strategies being " + \
                      "run from this instance.")
                print("Conflicting name:", name)
            
            self._strategy_configs[name] = new_strategy
            
            self._shutdown_methods[name] = shutdown_method
            
        if strategy is not None:
            self._strategy_classes[strategy.__name__] = strategy
            
    
    def backtest(self, start: str = None, end: str = None, 
                 initial_balance: float = 1000, spread: float = 0, 
                 commission: float = 0, leverage: int = 1,
                 base_currency: str = 'AUD', start_dt: datetime = None, 
                 end_dt: datetime = None, hedging: bool = False,
                 margin_call_fraction: float = 0) -> None:
        """Configures settings for backtesting.

        Parameters
        ----------
        start : str, optional
            Start date for backtesting, in format dd/mm/yyyy. The default is None.
        end : str, optional
            End date for backtesting, in format dd/mm/yyyy. The default is None.
        start_dt : datetime, optional
            Datetime object corresponding to start time. The default is None.
        end_dt : datetime, optional
            Datetime object corresponding to end time. The default is None.
        initial_balance : float, optional
            The initial balance of the account. The default is 1000.
        spread : float, optional
            The bid/ask spread to use in backtest. The default is 0.
        commission : float, optional
            Trading commission as percentage per trade. The default is 0.
        leverage : int, optional
            Account leverage. The default is 1.
        base_currency : str, optional
            The base currency of the account. The default is 'AUD'.
        hedging : bool, optional
            Allow hedging in the virtual broker (opening simultaneous 
            trades in oposing directions). The default is False.
        margin_call_fraction : float, optional
            The fraction of margin usage at which a margin call will occur.
            The default is 0.
            
        Notes
        ------
            Start and end times must be specified as the same type. For
            example, both start and end arguments must be provided together, 
            or alternatively, start_dt and end_dt must both be provided.
        """
        
        # Convert start and end strings to datetime objects
        if start_dt is None and end_dt is None:
            start_dt = datetime.strptime(start + '+0000', '%d/%m/%Y%z')
            end_dt = datetime.strptime(end + '+0000', '%d/%m/%Y%z')
        
        # Assign attributes
        self._backtest_mode = True
        self._data_start = start_dt
        self._data_end = end_dt
        self._virtual_initial_balance = initial_balance
        self._virtual_spread = spread
        self._virtual_commission = commission
        self._virtual_leverage = leverage
        self._virtual_broker_hedging = hedging
        self._virtual_margin_call = margin_call_fraction
        self._base_currency = base_currency
        
        # Enforce virtual broker
        self._broker_name = 'virtual'
        
    
    def optimise(self, opt_params: list, bounds: list, Ns: int = 4,
                 force_download: bool = False) -> None:
        """Optimisation configuration.
        
        Parameters
        ----------
        opt_params : list
            The parameters to be optimised, as they  are named in the 
            strategy configuration file.
        bounds : list(tuples)
            The bounds on each of the parameters to be optimised, specified
            as a tuple of the form (lower, upper) for each parameter. The
            default is 4.
        force_download : bool, optional
            Force AutoTrader to download data each iteration. This is not
            recommended. Instead, you should provide local download to optimise
            on, using the add_data method. The default is False.
        Ns : int, optional
            The number of points along each dimension of the optimisation grid.
        
        Raises
        ------
        Exception:
            When force_download is False, and local data has not been added 
            through the add_data method. Note that add_data should be called
            prior to calling the optimise method.
        
        Returns
        -------
        None:
            The optimisation settings will be saved to the active AutoTrader
            instance.
        
        See Also
        --------
        AutoTrader.add_data()
        """
        
        if type(bounds) == str:
            full_tuple = literal_eval(bounds)
            bounds = [(x[0], x[-1]) for x in full_tuple]

        if type(opt_params) == str:
            opt_params = opt_params.split(',')
        
        self._optimise_mode = True
        self._opt_params = opt_params
        self._bounds = bounds
        self._Ns = Ns
        
        if self._local_data is None:
            raise Exception("Local data files have not been provided. " +\
                            "Please do so using AutoTrader.add_data(), " +\
                            "or set force_download to True to proceed.")
        
        
    def add_data(self, data_dict: dict = None, quote_data: dict = None, 
                 data_directory: str = 'price_data', abs_dir_path: str = None, 
                 auxdata: dict = None, stream_object = None,
                 dynamic_data: bool = False) -> None:
        """Specify local data to run AutoTrader on.

        Parameters
        ----------
        data_dict : dict, optional
            A dictionary containing the filenames of the datasets
            to be used. The default is None.
        quote_data : dict, optional
            A dictionary containing the quote data filenames 
            of the datasets provided in data_dict. The default is None.
        data_directory : str, optional
            The name of the sub-directory containing price
            data files. This directory should be located in the project
            home directory (at.home_dir). The default is 'price_data'.
        abs_dir_path : str, optional
            The absolute path to the data_directory. This parameter
            may be used when the datafiles are stored outside of the project
            directory. The default is None.
        auxdata : dict, optional
            A dictionary containing the data paths to supplement the 
            data passed to the strategy module. For strategies involving 
            multiple products, the keys of this dictionary must correspond
            to the products, with the auxdata in nested dictionaries or 
            otherwise. The default is None.
        stream_object : DataStream, optional
            A custom data stream object, allowing custom data pipelines. The 
            default is DataStream (from autotrader.utilities).
        dynamic_data : bool, optional
            A boolean flag to signal that the stream object provided should 
            be refreshed each timestep of a backtest.
        
        Raises
        ------
        Exception
            When multiple quote-data files are provided per instrument traded.

        Returns
        -------
        None
            Data will be assigned to the active AutoTrader instance for
            later use.
        
        Notes
        ------
            To ensure proper directory configuration, this method should only 
            be called after calling autotrader.configure().
            
            The data provided to the strategy will either contain a single 
            timeframe OHLC dataframe, a dictionary of MTF dataframes, or 
            a dict with 'base' and 'aux' keys, for aux and base strategy 
            data (which could be single of MTF).
            
        Examples
        --------
            An example data_dict is shown below.
            
            >>> data_dict = {'product1': 'filename1.csv',
                             'product2': 'filename2.csv'}
            
            For MTF data, data_dict should take the form shown below. In 
            the case of MTF data, quote data should only be provided for
            the base timeframe (ie. the data which will be iterated on
            when backtesting). Therefore, the quote_data dict will look
            the same for single timeframe and MTF backtests.
            
            >>> data_dict = {'product1': {'H1': 'product1_H1.csv',
                                          'D': 'product1_D.csv'},
                             'product2': {'H1': 'product2_H1.csv',
                                          'D': 'product2_D.csv'}
                             }
        
            An example for the quate_data dictionary is shown below.
        
            >>> quote_data = {'product1': 'product1_quote.csv',
                              'product2': 'product2_quote.csv'}
        
            The auxdata dictionary can take the form shown below. This data 
            will be passed on to your strategy.
        
            >>> auxdata = {'product1': 'aux_price_data.csv', 
                           'product2': {'extra_data1': 'dataset1.csv',
                                        'extra_data2': 'dataset2.csv'}
                           }
            
        """
        dir_path = abs_dir_path if abs_dir_path is not None \
            else os.path.join(self._home_dir, data_directory)
        
        # Trading data
        if data_dict is not None:
            # Assign local data attribute
            local_data = {}
            
            # Populate local_data
            for product in data_dict:
                if type(data_dict[product]) == dict:
                    # MTF data
                    MTF_data = {}
                    for timeframe in data_dict[product]:
                        MTF_data[timeframe] = os.path.join(dir_path, data_dict[product][timeframe])
                    
                    local_data[product] = MTF_data
                else:
                    # Single timeframe data
                    local_data[product] = os.path.join(dir_path, data_dict[product])
                    
            self._local_data = local_data
        
        # Quote data
        if quote_data is not None:
            # Assign local data attribute
            local_quote_data = {}
            
            # Populate local_quote_data
            for product in quote_data:
                if type(quote_data[product]) == dict:
                    raise Exception("Only a single quote-data file should be " +\
                                    "provided per instrument traded.")
                    
                else:
                    local_quote_data[product] = os.path.join(dir_path, quote_data[product])
            
            self._local_quote_data = local_quote_data
        
        if auxdata is not None:
            modified_auxdata = {}
            for product, item in auxdata.items():
                if isinstance(item, dict):
                    # Multiple datasets for product
                    modified_auxdata[product] = {}
                    for key, dataset in item:
                        modified_auxdata[product][key] = os.path.join(dir_path, dataset)
                else:
                    # Item is not dict
                    modified_auxdata[product] = os.path.join(dir_path, item)
                    
            self._auxdata = modified_auxdata
        
        # Assign data stream object
        if stream_object is not None:
            self._data_stream_object = stream_object
        
        self._dynamic_data = dynamic_data
    
    
    def scan(self, strategy_filename: str = None, 
             strategy_dict: dict = None, scan_index: str = None) -> None:
        """Configure AutoTrader scan settings. 
        
        Parameters
        ----------
        strategy_filename : str, optional
             The prefix of yaml strategy configuration file, located in 
             home_dir/config. The default is None.
        strategy_dict : dict, optional
            A strategy configuration dictionary. The default is None.
        scan_index : str, optional
            Forex scan index. The default is None.

        Returns
        -------
        None
            The scan settings of the active AutoTrader instance will be
            configured.
        """
        
        # If a strategy is provided here, add it
        if strategy_filename is not None:
            self.add_strategy(strategy_filename)
        elif strategy_dict is not None:
            self.add_strategy(strategy_dict=strategy_dict)
        
        # If scan index provided, use that. Else, use strategy watchlist
        if scan_index is not None:
            self._scan_watchlist = get_watchlist(scan_index, self._feed)

        else:
            scan_index = 'Strategy watchlist'
            
        self._scan_mode = True
        self._scan_index = scan_index
        self._check_data_alignment = False
    
    
    def run(self) -> None:
        """Performs essential checks and runs AutoTrader.
        """
        # Define home_dir if undefined
        if self._home_dir is None:
            self._home_dir = os.getcwd()
        
        # Load uninitiated strategies
        for strat_dict in self._uninitiated_strat_dicts:
            self.add_strategy(strategy_dict=strat_dict)
        for strat_config_file in self._uninitiated_strat_files:
            self.add_strategy(strategy_filename=strat_config_file)
        
        if self._scan_watchlist is not None:
            # Scan watchlist has not overwritten strategy watchlist
            self._update_strategy_watchlist()
        
        if len(self._strategy_configs) == 0:
            print("Error: no strategy has been provided. Do so by using the" +\
                  " 'add_strategy' method of AutoTrader.")
            sys.exit(0)
            
        if sum([self._backtest_mode, self._scan_mode]) > 1:
            print("Error: backtest mode and scan mode are both set to True," +\
                  " but only one of these can run at a time.")
            print("Please check your inputs and try again.")
            sys.exit(0)
        
        if self._backtest_mode:
            if self._notify > 0:
                print("Warning: notify set to {} ".format(self._notify) + \
                      "during backtest. Setting to zero to prevent emails.")
                self._notify = 0
            
            # Check that the backtest does not request future data
            if self._data_end > datetime.now(tz=timezone.utc):
                print("Warning: you have requested backtest data into the "+\
                      "future. The backtest end date will be adjsuted to "+ \
                      "the current time.")
                self._data_end = datetime.now(tz=timezone.utc)
            
        if self._optimise_mode:
            if self._backtest_mode:
                self._run_optimise()
            else:
                print("Please set backtest parameters to run optimisation.")
        else:
            if not self._backtest_mode and self._broker_name == 'virtual':
                if not self._virtual_livetrading:
                    raise Exception("Live-trade mode requires setting the "+\
                                    "broker. Please do so using the "+\
                                    "AutoTrader configure method. If you "+\
                                    "would like to use the virtual broker "+\
                                    "for sandbox livetrading, please "+\
                                    "configure the virtual broker account "+\
                                    "with the virtual_livetrade_config method.")
                
            self._main()
    
    
    def plot_settings(self, max_indis_over: int = 3, max_indis_below: int = 2,
                      fig_tools: str = "pan,wheel_zoom,box_zoom,undo,redo,reset,save,crosshair",
                      ohlc_height: int = 400, ohlc_width: int = 800, 
                      top_fig_height: int = 150, bottom_fig_height: int = 150, 
                      jupyter_notebook: bool = False, show_cancelled: bool = True,
                      chart_timeframe: str = 'default', chart_theme: str = 'caliber',
                      use_strat_plot_data: bool = False, 
                      portfolio_chart: bool = False) -> None:
        """Configure the plot settings.

        Parameters
        ----------
        max_indis_over : int, optional
            Maximum number of indicators overlaid on the main chart. The 
            default is 3.
        max_indis_below : int, optional
            Maximum number of indicators below the main chart. The default is 2.
        fig_tools : str, optional
            The figure tools. The default is "pan,wheel_zoom,box_zoom,undo,
            redo,reset,save,crosshair".
        ohlc_height : int, optional
            The height (px) of the main chart. The default is 400.
        ohlc_width : int, optional
            The width (px) of the main chart. The default is 800.
        top_fig_height : int, optional
            The height (px) of the figure above the main chart. The default is 150.
        bottom_fig_height : int, optional
            The height (px) of the figure(s) below the main chart. The default is 150.
        jupyter_notebook : bool, optional
            Boolean flag when running in Jupyter Notebooks, to allow inline
            plotting. The default is False.
        show_cancelled : bool, optional
            Show/hide cancelled trades. The default is True.
        chart_timeframe : str, optional
            The bar timeframe to use when gerating the chart. The timeframe
            provided must be a part of the strategy dataset. The default is 'default'.
        chart_theme : bool, optional
            The theme of the Bokeh chart generated. The default is "caliber".
        use_strat_plot_data : bool, optional
            Boolean flag to use data from the strategy instead of candlestick
            data for the chart. If True, ensure your strategy has a timeseries
            data attribute named 'plot_data'. The default is False.
        portfolio_chart : bool, optional
            Override the default plot settings to plot the portfolio chart
            even when running a single instrument backtest.
        
        Returns
        -------
        None
            The plot settings will be saved to the active AutoTrader instance.
        """
        # Assign attributes
        self._max_indis_over    = max_indis_over
        self._max_indis_below   = max_indis_below
        self._fig_tools         = fig_tools
        self._ohlc_height       = ohlc_height
        self._ohlc_width        = ohlc_width
        self._top_fig_heigh     = top_fig_height
        self._bottom_fig_height = bottom_fig_height
        self._jupyter_notebook  = jupyter_notebook
        self._show_cancelled    = show_cancelled
        self._chart_timefram    = chart_timeframe
        self._chart_theme       = chart_theme
        self._use_strat_plot_data = use_strat_plot_data
        self._plot_portolio_chart = portfolio_chart
    
    
    def get_bots_deployed(self, instrument: str = None) -> dict:
        """Returns a dictionary of AutoTrader trading bots, organised by 
        instrument traded.

        Parameters
        ----------
        instrument : str, optional
            The instrument of the bot to retrieve. The default is None.
            
        Returns
        -------
        dict
            A dictionary of deployed AutoTrader bot instances.
        
        Notes
        -----
        If there is only one trading bot deployed, this will be returned 
        directly, rather than in a dict.
        """
        bots = {}
        for bot in self._bots_deployed:
            bots[bot.instrument] = bot
        
        if instrument is not None:
            # Retrieve bot requested
            try:
                bots = bots[instrument]
            except:
                raise Exception(f"There were no bots found to be trading '{instrument}'.")
        else:
            if len(bots) == 1:
                # Single bot backtest, return directly
                bots = bots[list(bots.keys())[0]]
        
        return bots
        
    
    def print_backtest_results(self, backtest_results: BacktestResults = None) -> None:
        """Prints backtest results.

        Parameters
        ----------
        backtest_results : BacktestResults
            The backtest results class object.

        Returns
        -------
        None
            Backtest results will be printed.
        """
        
        if backtest_results is None:
            backtest_results = self.backtest_results
            
        backtest_summary = backtest_results.summary()
        start_date = backtest_summary['start'].strftime("%b %d %Y %H:%M:%S")
        end_date = backtest_summary['end'].strftime("%b %d %Y %H:%M:%S")
        
        starting_balance = backtest_summary['starting_balance']
        ending_balance = backtest_summary['ending_balance']
        ending_NAV = backtest_summary['ending_NAV']
        abs_return = backtest_summary['abs_return']
        pc_return = backtest_summary['pc_return']
        
        no_trades = backtest_summary['no_trades']
        if no_trades > 0:
            win_rate = backtest_summary['all_trades']['win_rate']
            max_drawdown = backtest_summary['all_trades']['max_drawdown']
            max_win = backtest_summary['all_trades']['max_win']
            avg_win = backtest_summary['all_trades']['avg_win']
            max_loss = backtest_summary['all_trades']['max_loss']
            avg_loss = backtest_summary['all_trades']['avg_loss']
            longest_win_streak = backtest_summary['all_trades']['win_streak']
            longest_lose_streak = backtest_summary['all_trades']['lose_streak']
            total_fees = backtest_summary['all_trades']['total_fees']
            
        
        print("\n----------------------------------------------")
        print("               Backtest Results")
        print("----------------------------------------------")
        print("Start date:              {}".format(start_date))
        print("End date:                {}".format(end_date))
        print("Starting balance:        ${}".format(round(starting_balance, 2)))
        print("Ending balance:          ${}".format(round(ending_balance, 2)))
        print("Ending NAV:              ${}".format(round(ending_NAV, 2)))
        print("Total return:            ${} ({}%)".format(round(abs_return, 2), 
                                          round(pc_return, 1)))
        if no_trades > 0:
            print("Total no. trades:        {}".format(no_trades))
            print("Total fees:              ${}".format(round(total_fees, 3)))
            print("Backtest win rate:       {}%".format(round(win_rate, 1)))
            print("Maximum drawdown:        {}%".format(round(max_drawdown*100, 2)))
            print("Max win:                 ${}".format(round(max_win, 2)))
            print("Average win:             ${}".format(round(avg_win, 2)))
            print("Max loss:                -${}".format(round(max_loss, 2)))
            print("Average loss:            -${}".format(round(avg_loss, 2)))
            print("Longest win streak:      {} trades".format(longest_win_streak))
            print("Longest losing streak:   {} trades".format(longest_lose_streak))
            print("Average trade duration:  {}".format(backtest_summary['all_trades']['avg_trade_duration']))
            
        else:
            print("\n No trades closed.")
        
        no_open = backtest_summary['no_open']
        no_cancelled = backtest_summary['no_cancelled']
        
        if no_open > 0:
            print("Trades still open:       {}".format(no_open))
        if no_cancelled > 0:
            print("Cancelled orders:        {}".format(no_cancelled))
        
        # Long trades
        no_long = backtest_summary['long_trades']['no_trades']
        print("\n            Summary of long trades")
        print("----------------------------------------------")
        if no_long > 0:
            avg_long_win = backtest_summary['long_trades']['avg_long_win']
            max_long_win = backtest_summary['long_trades']['max_long_win']
            avg_long_loss = backtest_summary['long_trades']['avg_long_loss']
            max_long_loss = backtest_summary['long_trades']['max_long_loss']
            long_wr = backtest_summary['long_trades']['long_wr']
            
            print("Number of long trades:   {}".format(no_long))
            print("Long win rate:           {}%".format(round(long_wr, 1)))
            print("Max win:                 ${}".format(round(max_long_win, 2)))
            print("Average win:             ${}".format(round(avg_long_win, 2)))
            print("Max loss:                -${}".format(round(max_long_loss, 2)))
            print("Average loss:            -${}".format(round(avg_long_loss, 2)))
        else:
            print("There were no long trades.")
          
        # Short trades
        no_short = backtest_summary['short_trades']['no_trades']
        print("\n             Summary of short trades")
        print("----------------------------------------------")
        if no_short > 0:
            avg_short_win = backtest_summary['short_trades']['avg_short_win']
            max_short_win = backtest_summary['short_trades']['max_short_win']
            avg_short_loss = backtest_summary['short_trades']['avg_short_loss']
            max_short_loss = backtest_summary['short_trades']['max_short_loss']
            short_wr = backtest_summary['short_trades']['short_wr']
            
            print("Number of short trades:  {}".format(no_short))
            print("short win rate:          {}%".format(round(short_wr, 1)))
            print("Max win:                 ${}".format(round(max_short_win, 2)))
            print("Average win:             ${}".format(round(avg_short_win, 2)))
            print("Max loss:                -${}".format(round(max_short_loss, 2)))
            print("Average loss:            -${}".format(round(avg_short_loss, 2)))
            
        else:
            print("There were no short trades.")
        
        # Check for multiple instruments
        if len(backtest_results.instruments_traded) > 1:
            # Mutliple instruments traded
            instruments = backtest_results.instruments_traded
            trade_history = backtest_results.trade_history
            instrument_trades = [trade_history[trade_history.instrument == i] for i in instruments]
            # returns_per_instrument = [trade_history.profit[trade_history.instrument == i].cumsum() for i in instruments]
            max_wins = [instrument_trades[i].profit.max() for i in range(len(instruments))]
            max_losses = [instrument_trades[i].profit.min() for i in range(len(instruments))]
            avg_wins = [instrument_trades[i].profit[instrument_trades[i].profit>0].mean() for i in range(len(instruments))]
            avg_losses = [instrument_trades[i].profit[instrument_trades[i].profit<0].mean() for i in range(len(instruments))]
            win_rates = [100*sum(instrument_trades[i].profit>0)/len(instrument_trades[i]) for i in range(len(instruments))]
            
            results = pd.DataFrame(data={'Instrument': instruments, 
                                         'Max. Win': max_wins, 
                                         'Max. Loss': max_losses, 
                                         'Avg. Win': avg_wins, 
                                         'Avg. Loss': avg_losses, 
                                         'Win rate': win_rates})
            
            print("\n Instrument Breakdown:")
            print(results.to_string(index=False))

    
    def plot_backtest(self, bot=None) -> None:
        """Plots backtest results of an AutoTrader Bot.
        
        Parameters
        ----------
        bot : AutoTrader bot instance, optional
            AutoTrader bot class containing backtest results. The default 
            is None.

        Returns
        -------
        None
            A chart will be generated and shown.
        """
        
        def portfolio_plot():
            ap = self._instantiate_autoplot()
            ap._plot_multibot_backtest(self.backtest_results)
        
        def single_instrument_plot(bot):
            data = bot._check_strategy_for_plot_data(self._use_strat_plot_data)
            ap = self._instantiate_autoplot(data)
            ap.plot(backtest_dict=bot.backtest_results)
        
        if bot is None:
            # No bot has been provided, select automatically
            if len(self.backtest_results.instruments_traded) > 1 or \
                len(self._bots_deployed) > 1 or self._plot_portolio_chart:
                # Multi-product backtest
                portfolio_plot()
            else:
                # Single product backtest
                bot = self._bots_deployed[0]
                single_instrument_plot(bot)
        else:
            # A bot has been provided
            single_instrument_plot(bot)
        
    
    def _main(self) -> None:
        """Run AutoTrader with configured settings.
        """
        # Load configuration
        if self._global_config_dict is not None:
            # Use global config dict provided
            global_config = self._global_config_dict
        else:
            # Try load from file
            global_config_fp = os.path.join(self._home_dir, 'config', 'GLOBAL.yaml')
            if os.path.isfile(global_config_fp):
                global_config = read_yaml(global_config_fp)
            else:
                global_config = None
        
        # Check feed
        if global_config is None and self._feed.lower() in ['oanda']:
            raise Exception(f'Data feed "{self._feed}" requires global '+ \
                            'configuration. If a config file already '+ \
                            'exists, make sure to specify the home_dir.')
            
        broker_config = get_config(self._environment, global_config, self._feed)
        
        if self._account_id is not None:
            # Overwrite default account in global config
            broker_config['ACCOUNT_ID'] = self._account_id
        
        # Append broker verbosity to broker_config
        broker_config['verbosity'] = self._broker_verbosity
        
        self._assign_broker(broker_config)
        self._configure_emailing(global_config)
        
        if int(self._verbosity) > 0:
            if self._backtest_mode:
                print("Beginning new backtest.")

            elif self._scan_mode:
                print("AutoTrader - AutoScan")
                print("Time: {}\n".format(datetime.now().strftime("%A, %B %d %Y, "+
                                                                  "%H:%M:%S")))
            else:
                print("AutoTrader Livetrade")
                print("--------------------")
                print("Current time: {}".format(datetime.now().strftime("%A, %B %d %Y, "+
                                                                  "%H:%M:%S")))
        
        # Assign trading bots to each strategy
        for strategy, config in self._strategy_configs.items():
            # Check for portfolio strategy
            portfolio = config['PORTFOLIO'] if 'PORTFOLIO' in config else False
            watchlist = ["Portfolio"] if portfolio else config['WATCHLIST']
            for instrument in watchlist:
                # TODO - local data dict for portfolio
                data_dict = self._local_data[instrument] \
                    if self._local_data is not None else None
                quote_data_path = self._local_quote_data[instrument] \
                    if self._local_quote_data is not None else None
                auxdata = self._auxdata[instrument] \
                    if self._auxdata is not None else None
                
                strategy_class = config['CLASS']
                strategy_dict = {'config': config,
                                 'class': self._strategy_classes[strategy_class] \
                                     if strategy_class in self._strategy_classes else None,
                                 'shutdown_method': self._shutdown_methods[strategy]}
                bot = AutoTraderBot(instrument, strategy_dict,
                                    self._broker, self._data_start, data_dict, 
                                    quote_data_path, auxdata, self)
                self._bots_deployed.append(bot)
                
        if int(self._verbosity) > 0 and self._backtest_mode:
            print("\nTrading...\n")
            backtest_start_time = timeit.default_timer()
            
        # Begin trading
        if self._run_mode.lower() == 'continuous':
            # Running in continuous update mode
            if self._backtest_mode:
                # Backtesting
                end_time = self._data_end # datetime
                timestamp = self._data_start # datetime
                pbar = tqdm(total=int((self._data_end - self._data_start).total_seconds()),
                            position=0, leave=True)
                while timestamp <= end_time:
                    # Update each bot with latest data to generate signal
                    for bot in self._bots_deployed:
                        bot._update(timestamp=timestamp)
                        
                    # Iterate through time
                    timestamp += self._timestep
                    pbar.update(self._timestep.total_seconds())
                pbar.close()
                
            else:
                # Live trading
                instance_id = self._get_instance_id()
                instance_str = f"autotrader_instance_{instance_id}" if \
                    self._instance_str is None else self._instance_str
                instance_file_exists = self._check_instance_file(instance_str, True)
                deploy_time = time.time()
                while instance_file_exists:
                    for bot in self._bots_deployed:
                        bot._update(timestamp=datetime.now(timezone.utc))
                    time.sleep(self._timestep.seconds - ((time.time() - \
                                deploy_time) % self._timestep.seconds))
                    instance_file_exists = self._check_instance_file(instance_str)
                    
        elif self._run_mode.lower() == 'periodic':
            # Trading in periodic update mode
            if self._backtest_mode:
                # Backtesting
                self._check_bot_data()
                start_range, end_range = self._bots_deployed[0]._get_iteration_range()
                for i in range(start_range, end_range):
                    # Update each bot with latest data to generate signal
                    for bot in self._bots_deployed:
                        bot._update(i=i)
                        
            else:
                # Live trading
                bot._update(i=-1) # Process most recent signal
        
        if int(self._verbosity) > 0 and self._backtest_mode:
            backtest_end_time = timeit.default_timer()
        
        # Run strategy-specific shutdown routines
        for bot in self._bots_deployed:
            bot._strategy_shutdown()
            
        # Run instance shut-down routine
        if self._backtest_mode:
            # Create total backtest results
            self.backtest_results = BacktestResults(self._broker)
            
            # Create backtest results for each bot
            for bot in self._bots_deployed:
                bot._create_backtest_results()            
            
            if int(self._verbosity) > 0:
                print("Backtest complete (runtime " + \
                      f"{round((backtest_end_time - backtest_start_time), 3)} s).")
                self.print_backtest_results()
                
            if self._show_plot:
                self.plot_backtest()
        
        elif self._scan_mode and self._show_plot:
            # Show plots for scanned instruments
            for bot in self._bots_deployed:
                ap = self._instantiate_autoplot(bot.data)
                ap.plot(indicators = bot.strategy.indicators, 
                        instrument = bot.instrument)
                time.sleep(0.3)
        
        else:
            # Live trade complete, run livetrade specific shutdown routines
            if self._broker_name.lower() == 'ib':
                self._broker._disconnect()
            
            elif self._virtual_livetrading:
                # TODO - write broker stats to file (trade summary and so on)
                # look to AutoTraderBot._create_backtest_results for process
                pass
        

    def _clear_strategies(self) -> None:
        """Removes all strategies saved in autotrader instance.
        """
        self._strategy_configs = {}
    
    
    def _clear_bots(self) -> None:
        """Removes all deployed bots in autotrader instance.
        """
        self._bots_deployed = []
    
    
    def _instantiate_autoplot(self, data: pd.DataFrame = None) -> AutoPlot:
        """Creates instance of AutoPlot.

        Parameters
        ----------
        data : pd.DataFrame
            The data to instantiate AutoPlot with.

        Raises
        ------
        Exception
            When attempting to plot on missing data timeframe.

        Returns
        -------
        AutoPlot
            An instance of AutoPlot.
        """
        if self._chart_timeframe == 'default':
            ap = AutoPlot(data)
        else:
            # Instantiate AutoPlot with requested chart timeframe
            if self._chart_timeframe in self._bots_deployed[0].MTF_data.keys():
                # Valid timeframe requested
                ap = AutoPlot(self._bots_deployed[0].MTF_data[self._chart_timeframe])
                ap._add_backtest_price_data(data) # provide nominal timeframe data for merge operations
            else:
                warning_str = f'The chart timeframe requested ({self._chart_timeframe}) was not found ' + \
                    'in the MTF data. Please ensure that the timeframe provided matches ' + \
                    'the format provided in the strategy configuration file, or the local ' + \
                    'data provided.'
                raise Exception(warning_str)
                
        # Assign attributes
        ap.configure(max_indis_over=self._max_indis_over, 
                     max_indis_below = self._max_indis_below,
                     fig_tools = self._fig_tools, 
                     ohlc_height = self._ohlc_height, 
                     ohlc_width = self._ohlc_width, 
                     top_fig_height = self._top_fig_height,
                     bottom_fig_height = self._bottom_fig_height,
                     jupyter_notebook = self._jupyter_notebook,
                     show_cancelled = self._show_cancelled,
                     chart_theme = self._chart_theme,
                     use_strat_plot_data = self._use_strat_plot_data,)
        
        return ap
    
    
    def _update_strategy_watchlist(self) -> None:
        """Updates the watchlist of each strategy with the scan watchlist.
        """
        for strategy in self._strategy_configs:
            self._strategy_configs[strategy]['WATCHLIST'] = self._scan_watchlist
    
    
    def _assign_broker(self, broker_config: dict) -> None:
        """Configures and assigns appropriate broker for trading.
        """
        # Import relevant broker and utilities modules
        broker_module = importlib.import_module(f'autotrader.brokers.{self._broker_name}.broker')
        utils_module = importlib.import_module(f'autotrader.brokers.{self._broker_name}.utils')
        
        # Create broker and utils instances
        utils = utils_module.Utils()
        broker = broker_module.Broker(broker_config, utils)
        
        if self._backtest_mode or self._virtual_livetrading:
            # Using virtual broker, initialise account
            if int(self._verbosity) > 0 and self._backtest_mode:
                banner = pyfiglet.figlet_format("AutoBacktest")
                print(banner)
            broker._make_deposit(self._virtual_initial_balance)
            broker.fee = self._virtual_spread
            broker.leverage = self._virtual_leverage
            broker.commission = self._virtual_commission
            broker.spread = self._virtual_spread
            broker.base_currency = self._base_currency
            broker.hedging = self._virtual_broker_hedging
            broker.margin_closeout = self._virtual_margin_call
        
        self._broker = broker
        self._broker_utils = utils
    
    
    def _configure_emailing(self, global_config: dict) -> None:
        """Configure email settings.
        """
        if int(self._notify) > 0:
            host_email = None
            mailing_list = None
            
            if "EMAILING" in global_config:
                # Look for host email and mailing list in strategy config, if it
                # was not picked up in strategy config
                if "MAILING_LIST" in global_config["EMAILING"] and mailing_list is None:
                    mailing_list    = global_config["EMAILING"]["MAILING_LIST"]
                if "HOST_ACCOUNT" in global_config["EMAILING"] and host_email is None:
                    host_email      = global_config["EMAILING"]["HOST_ACCOUNT"]
            
            if host_email is None:
                print("Warning: email host account not provided.")
            if mailing_list is None:
                print("Warning: no mailing list provided.")
                
            email_params = {'mailing_list': mailing_list,
                            'host_email': host_email}
            self._email_params = email_params
            
            logfiles_path = os.path.join(self._home_dir, 'logfiles')
            order_summary_fp = os.path.join(logfiles_path, 'order_history.txt')
            
            if not os.path.isdir(logfiles_path):
                os.mkdir(logfiles_path)
            
            self._order_summary_fp = order_summary_fp


    def _run_optimise(self) -> None:
        """Runs optimisation of strategy parameters.
        """
        
        # Modify verbosity for optimisation
        verbosity = self._verbosity
        self._verbosity = 0
        self._show_plot = False
        self.objective = 'profit + MDD'
        
        # Look in self._strategy_configs for config
        if len(self._strategy_configs) > 1:
            print("Error: please optimise one strategy at a time.")
            print("Exiting.")
            sys.exit(0)
        else:
            config_dict = self._strategy_configs[list(self._strategy_configs.keys())[0]]
                
        my_args = (config_dict, self._opt_params, self._verbosity)
        
        start = timeit.default_timer()
        result = brute(func         = self._optimisation_helper_function, 
                       ranges       = self._bounds, 
                       args         = my_args, 
                       Ns           = self._Ns,
                       full_output  = True)
        stop = timeit.default_timer()
        
        opt_params = result[0]
        opt_value = result[1]
        
        print("\nOptimisation complete.")
        print('Time to run: {}s'.format(round((stop - start), 3)))
        print("Optimal parameters:")
        print(opt_params)
        print("Objective:")
        print(opt_value)
        
        # Reset verbosity
        self._verbosity = verbosity
    
    
    def _optimisation_helper_function(self, params: list, config_dict: dict, 
                                      opt_params: list, verbosity: int) -> float:
        """Helper function for optimising strategy parameters in AutoTrader.
        This function will parse the ordered params into the config dict.
        """
        for parameter in config_dict['PARAMETERS']:
            if parameter in opt_params:
                config_dict['PARAMETERS'][parameter] = params[opt_params.index(parameter)]
            else:
                continue

        self._clear_strategies()
        self._clear_bots()
        self.add_strategy(config_dict = config_dict)
        self._main()
        
        try:
            backtest_results = self.backtest_results.summary()
            objective = -backtest_results['all_trades']['ending_NAV']
        except:
            objective = 1000
                              
        print("Parameters/objective:", params, "/", round(objective,3))
        
        return objective
    
    
    def _check_bot_data(self) -> None:
        """Function to compare lengths of bot data. 
        """
        data_lengths = [len(bot.data) for bot in self._bots_deployed]
        if min(data_lengths) != np.mean(data_lengths):
            print("Warning: mismatched data lengths detected. "+\
                  "Correcting via row reduction.")
            self._normalise_bot_data()
            print("  Done.\n")
    
    
    def _normalise_bot_data(self) -> None:
        """Function to normalise the data of mutliple bots so that their
        indexes are equal, allowing backtesting.
        """
        
        # Construct list of bot data
        data = [bot.data for bot in self._bots_deployed]
        
        for i, dat in enumerate(data):
            # Initialise common index
            comm_index = dat.index
            
            # Update common index by intersection with other data 
            for j, dat_2 in enumerate(data):
                comm_index = comm_index.intersection(dat_2.index)
            
            # Adjust bot data using common indexes
            adj_data = dat[dat.index.isin(comm_index)]
            
            # Re-assign bot data
            self._bots_deployed[i]._replace_data(adj_data)
    
    
    def _get_instance_id(self):
        """Returns an ID for the active AutoTrader instance.
        """
        dirpath = os.path.join(self._home_dir, 'active_bots')
        
        # Check if active_bots directory exists
        if not os.path.isdir(dirpath):
            # Directory does not exist, create it
            os.mkdir(dirpath)
            instance_id = 1
            
        else:
            # Directory exists, find highest instance
            instances = [f for f in os.listdir(dirpath) if \
                         os.path.isfile(os.path.join(dirpath, f))]
            
            last_id = 0
            for instance in instances:
                if 'autotrader_instance_' in instance:
                    # Ignore custom instance strings
                    last_id = int(instance.split('_')[-1])
            
            instance_id = last_id + 1
        
        return instance_id
    
    
    def _check_instance_file(self, instance_str, initialisation=False):
        """Checks if the AutoTrader instance exists.
        """
        if initialisation:
            # Create the file
            filepath = os.path.join(self._home_dir, 'active_bots', instance_str)
            with open(filepath, mode='w') as f:
                f.write("This instance of AutoTrader contains the following bots:\n")
                for bot in self._bots_deployed:
                    f.write(bot._strategy_name + f" ({bot.instrument})\n")
            instance_file_exists = True
            
            if int(self._verbosity) > 0:
                print(f"Active AutoTrader instance file: active_bots/{instance_str}")
        
        else:
            dirpath = os.path.join(self._home_dir, 'active_bots')
            instances = [f for f in os.listdir(dirpath) if \
                         os.path.isfile(os.path.join('active_bots', f))]
            instance_file_exists = instance_str in instances
        
        if int(self._verbosity) > 0 and not instance_file_exists:
            print(f"Instance file '{instance_str}' deleted. AutoTrader",
                  "will now shut down.")
        
        return instance_file_exists
        
