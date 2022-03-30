import os
import sys
import time
import timeit
import pyfiglet
import importlib
import numpy as np
import pandas as pd
from ast import literal_eval
from scipy.optimize import brute
from autotrader.autoplot import AutoPlot
from autotrader.autobot import AutoTraderBot
from datetime import datetime, timedelta, timezone
from autotrader.utilities import read_yaml, get_config, get_watchlist, DataStream


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
    analyse_backtest(bot=None)
        Analyse backtest results of a single trading bot.
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
        
        # Local Data Parameters
        self._data_indexing = 'open'
        self._data_stream_object = DataStream
        self._data_file = None
        self._MTF_data_files = None
        self._local_data = None
        self._local_quote_data = None
        self._auxdata = None
        
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
                config_file_path = os.path.join(self._home_dir, 'config', config_filename)
                new_strategy = read_yaml(config_file_path + '.yaml')
            else:
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
                 auxdata: dict = None, stream_object = None) -> None:
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
                      use_strat_plot_data: bool = False) -> None:
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
        
        if len(bots) == 1:
            # Single bot backtest, return directly
            bots = bots[list(bots.keys())[0]]
        
        return bots
        
    
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
        
        if bot is None:
            if len(self._bots_deployed) == 1:
                bot = self._bots_deployed[0]
            else:
                # Multi-bot backtest
                self.plot_multibot_backtest()
                return
        
        data = bot._check_strategy_for_plot_data(self._use_strat_plot_data)
        ap = self._instantiate_autoplot(data)
        profit_df = pd.merge(bot.data, 
                             bot.backtest_summary['trade_summary']['profit'], 
                             left_index=True, right_index=True).profit.cumsum()
        
        ap.plot(backtest_dict=bot.backtest_summary, cumulative_PL=profit_df)
    
    
    def plot_multibot_backtest(self) -> None:
        """Plots the backtest results for multiple trading bots.
        
        Returns
        -------
        None
            A chart will be generated and shown.
        """
        cpl_dict = {}
        for bot in self._bots_deployed:
            profit_df = pd.merge(bot.data, 
                     bot.backtest_summary['trade_summary']['profit'], 
                     left_index=True, right_index=True).profit.cumsum()
            cpl_dict[bot.instrument] = profit_df
        
        ap = self._instantiate_autoplot(bot.data)
        ap._plot_multibot_backtest(self.multibot_backtest_results, 
                                   bot.backtest_summary['account_history']['NAV'], 
                                   cpl_dict, 
                                   bot.backtest_summary['account_history']['margin'])
        
    
    def analyse_backtest(self, bot = None) -> dict:
        """Analyses bot backtest results to extract key statistics.
        
        Parameters
        ----------
        bot : AutoTraderBot, optional
            An AutoTraderBot class instance. The default is None.
            
        Returns
        -------
        backtest_results : dict
            A dictionary of backtest results.
        
        Notes
        -----
        If no bot is supplied, the backtest will be analysed for all bots 
        assiged during the backtest.
        
        See Also
        --------
        get_bots_deployed
        """
        
        if bot is None:
            if len(self._bots_deployed) == 1:
                bot = self._bots_deployed[0]
            else:
                print("Reverting to multi-bot backtest.")
                return self.multibot_backtest_analysis()
                    
        backtest_summary = bot.backtest_summary
        
        trade_summary   = backtest_summary['trade_summary']
        instrument      = backtest_summary['instrument']
        account_history = backtest_summary['account_history']
        
        cpl = trade_summary.profit.cumsum()
        
        backtest_results = {}
        
        # All trades
        no_trades = len(trade_summary[trade_summary['status'] == 'closed'])
        backtest_results['no_trades'] = no_trades
        backtest_results['start'] = account_history.index[0]
        backtest_results['end'] = account_history.index[-1]
        
        if no_trades > 0:
            backtest_results['all_trades'] = {}
            wins        = trade_summary[trade_summary.profit > 0]
            avg_win     = np.mean(wins.profit)
            max_win     = np.max(wins.profit)
            loss        = trade_summary[trade_summary.profit < 0]
            avg_loss    = abs(np.mean(loss.profit))
            max_loss    = abs(np.min(loss.profit))
            win_rate    = 100*len(wins)/no_trades
            longest_win_streak, longest_lose_streak  = self._broker_utils.get_streaks(trade_summary)
            avg_trade_duration = np.nanmean(trade_summary.trade_duration.values)
            min_trade_duration = min(trade_summary.trade_duration.values)
            max_trade_duration = max(trade_summary.trade_duration.values)
            max_drawdown = min(account_history.drawdown)
            total_fees = trade_summary.fees.sum()
            
            starting_balance = account_history.balance[0]
            ending_balance = account_history.balance[-1]
            ending_NAV = account_history.NAV[-1]
            abs_return = ending_balance - starting_balance
            pc_return = 100 * abs_return / starting_balance
            
            backtest_results['all_trades']['starting_balance'] = starting_balance
            backtest_results['all_trades']['ending_balance'] = ending_balance
            backtest_results['all_trades']['ending_NAV']    = ending_NAV
            backtest_results['all_trades']['abs_return']    = abs_return
            backtest_results['all_trades']['pc_return']     = pc_return
            backtest_results['all_trades']['avg_win']       = avg_win
            backtest_results['all_trades']['max_win']       = max_win
            backtest_results['all_trades']['avg_loss']      = avg_loss
            backtest_results['all_trades']['max_loss']      = max_loss
            backtest_results['all_trades']['win_rate']      = win_rate
            backtest_results['all_trades']['win_streak']    = longest_win_streak
            backtest_results['all_trades']['lose_streak']   = longest_lose_streak
            backtest_results['all_trades']['longest_trade'] = str(timedelta(seconds = int(max_trade_duration)))
            backtest_results['all_trades']['shortest_trade'] = str(timedelta(seconds = int(min_trade_duration)))
            backtest_results['all_trades']['avg_trade_duration'] = str(timedelta(seconds = int(avg_trade_duration)))
            backtest_results['all_trades']['net_pl']        = cpl.values[-1]
            backtest_results['all_trades']['max_drawdown']  = max_drawdown
            backtest_results['all_trades']['total_fees']    = total_fees
            
        # Cancelled and open orders
        cancelled_orders = self._broker.get_orders(instrument, 'cancelled')
        open_trades = self._broker.get_positions(instrument)
        backtest_results['no_open'] = len(open_trades)
        backtest_results['no_cancelled'] = len(cancelled_orders)
        
        # Long trades
        long_trades = trade_summary[trade_summary['direction'] > 0]
        no_long = len(long_trades)
        backtest_results['long_trades'] = {}
        backtest_results['long_trades']['no_trades'] = no_long
        if no_long > 0:
            long_wins       = long_trades[long_trades.profit > 0]
            avg_long_win    = np.mean(long_wins.profit)
            max_long_win    = np.max(long_wins.profit)
            long_loss       = long_trades[long_trades.profit < 0]
            avg_long_loss   = abs(np.mean(long_loss.profit))
            max_long_loss   = abs(np.min(long_loss.profit))
            long_wr         = 100*len(long_trades[long_trades.profit > 0])/no_long
            
            backtest_results['long_trades']['avg_long_win']     = avg_long_win
            backtest_results['long_trades']['max_long_win']     = max_long_win 
            backtest_results['long_trades']['avg_long_loss']    = avg_long_loss
            backtest_results['long_trades']['max_long_loss']    = max_long_loss
            backtest_results['long_trades']['long_wr']          = long_wr
            
        # Short trades
        short_trades    = trade_summary[trade_summary['direction'] < 0]
        no_short        = len(short_trades)
        backtest_results['short_trades'] = {}
        backtest_results['short_trades']['no_trades'] = no_short
        if no_short > 0:
            short_wins      = short_trades[short_trades.profit > 0]
            avg_short_win   = np.mean(short_wins.profit)
            max_short_win   = np.max(short_wins.profit)
            short_loss      = short_trades[short_trades.profit < 0]
            avg_short_loss  = abs(np.mean(short_loss.profit))
            max_short_loss  = abs(np.min(short_loss.profit))
            short_wr        = 100*len(short_trades[short_trades.profit > 0])/no_short
            
            backtest_results['short_trades']['avg_short_win']   = avg_short_win
            backtest_results['short_trades']['max_short_win']   = max_short_win
            backtest_results['short_trades']['avg_short_loss']  = avg_short_loss
            backtest_results['short_trades']['max_short_loss']  = max_short_loss
            backtest_results['short_trades']['short_wr']        = short_wr
        
        return backtest_results
    
    
    def multibot_backtest_analysis(self, bots: list = None) -> dict:
        """Analyses backtest results of multiple bots to create an overall 
        performance summary.
        
        Parameters
        -----------
        bots : list[AutoTraderBot]
            A list of AutoTrader bots to analyse.
        
        Returns
        -------
        backtest_results : dict
            A dictionary of backtest results.
        
        Notes
        -----
        If no bots are supplied, the backtest will be analysed for all bots 
        assiged during the backtest.
        
        See Also
        --------
        get_bots_deployed
        """
        
        instruments = []
        win_rate    = []
        no_trades   = []
        avg_win     = []
        max_win     = []
        avg_loss    = []
        max_loss    = []
        no_long     = []
        no_short    = []
        
        if bots is None:
            bots = self._bots_deployed
        
        for bot in bots:
            backtest_results = self.analyse_backtest(bot)
            
            instruments.append(bot.instrument)
            no_trades.append(backtest_results['no_trades'])
            if backtest_results['no_trades'] > 0:
                win_rate.append(backtest_results['all_trades']['win_rate'])
                avg_win.append(backtest_results['all_trades']['avg_win'])
                max_win.append(backtest_results['all_trades']['max_win'])
                avg_loss.append(backtest_results['all_trades']['avg_loss'])
                max_loss.append(backtest_results['all_trades']['max_loss'])
                no_long.append(backtest_results['long_trades']['no_trades'])
                no_short.append(backtest_results['short_trades']['no_trades'])
            else:
                win_rate.append(np.nan)
                avg_win.append(np.nan)
                max_win.append(np.nan)
                avg_loss.append(np.nan)
                max_loss.append(np.nan)
                no_long.append(np.nan)
                no_short.append(np.nan)
        
        multibot_backtest_results = pd.DataFrame(data={'win_rate': win_rate,
                                                       'no_trades': no_trades,
                                                       'avg_win': avg_win,
                                                       'max_win': max_win,
                                                       'avg_loss': avg_loss,
                                                       'max_loss': max_loss,
                                                       'no_long': no_long,
                                                       'no_short': no_short},
                                                 index=instruments)
        
        return multibot_backtest_results
        
    
    def print_multibot_backtest_results(self, backtest_results: dict = None) -> None:
        """Prints to console the backtest results of a multi-bot backtest.
        
        Parameters
        -----------
        backtest_results : dict
            A dictionary containing backtest results.
            
        See Also
        --------
        Analyse backtest method to generate backtest_results.
        """
        
        bot = self._bots_deployed[0]
        account_history = bot.backtest_summary['account_history']
        
        start_date = account_history.index[0]
        end_date = account_history.index[-1]
        
        starting_balance = account_history.balance[0]
        ending_balance = account_history.balance[-1]
        ending_NAV = account_history.NAV[-1]
        abs_return = ending_balance - starting_balance
        pc_return = 100 * abs_return / starting_balance
        
        print("\n---------------------------------------------------")
        print("            MultiBot Backtest Results")
        print("---------------------------------------------------")
        print("Start date:              {}".format(start_date))
        print("End date:                {}".format(end_date))
        print("Starting balance:        ${}".format(round(starting_balance, 2)))
        print("Ending balance:          ${}".format(round(ending_balance, 2)))
        print("Ending NAV:              ${}".format(round(ending_NAV, 2)))
        print("Total return:            ${} ({}%)".format(round(abs_return, 2), 
                                          round(pc_return, 1)))
        
        print("Instruments traded: ", backtest_results.index.values)
        print("Total no. trades:   ", backtest_results.no_trades.sum())
        print("Short trades:       ", backtest_results.no_short.sum(),
              "({}%)".format(round(100*backtest_results.no_short.sum()/backtest_results.no_trades.sum(),2)))
        print("Long trades:        ", backtest_results.no_long.sum(),
              "({}%)".format(round(100*backtest_results.no_long.sum()/backtest_results.no_trades.sum(),2)))
        
        print("\nInstrument win rates (%):")
        print(backtest_results[['win_rate', 'no_trades']])
        print("\nMaximum/Average Win/Loss breakdown ($):")
        print(backtest_results[["max_win", "max_loss", "avg_win", "avg_loss"]])
        print("\nAverage Reward to Risk Ratio:")
        print(round(backtest_results.avg_win / backtest_results.avg_loss,1))
        print("")
        
    
    @staticmethod
    def print_backtest_results(backtest_results: dict) -> None:
        """Prints backtest results.

        Parameters
        ----------
        backtest_results : dict
            The backtest results dictionary.

        Returns
        -------
        None
            Backtest results will be printed.

        See Also
        ----------
        analyse_backtest
        """
        start_date = backtest_results['start'].strftime("%b %d %Y %H:%M:%S")
        end_date = backtest_results['end'].strftime("%b %d %Y %H:%M:%S")
        
        no_trades   = backtest_results['no_trades']
        if no_trades > 0:
            win_rate    = backtest_results['all_trades']['win_rate']
            abs_return  = backtest_results['all_trades']['abs_return']
            pc_return   = backtest_results['all_trades']['pc_return']
            max_drawdown = backtest_results['all_trades']['max_drawdown']
            max_win     = backtest_results['all_trades']['max_win']
            avg_win     = backtest_results['all_trades']['avg_win']
            max_loss    = backtest_results['all_trades']['max_loss']
            avg_loss    = backtest_results['all_trades']['avg_loss']
            longest_win_streak = backtest_results['all_trades']['win_streak']
            longest_lose_streak = backtest_results['all_trades']['lose_streak']
            total_fees = backtest_results['all_trades']['total_fees']
            starting_balance = backtest_results['all_trades']['starting_balance']
            ending_balance = backtest_results['all_trades']['ending_balance']
            ending_NAV = backtest_results['all_trades']['ending_NAV']
        
        print("\n----------------------------------------------")
        print("               Backtest Results")
        print("----------------------------------------------")
        if no_trades > 0:
            print("Start date:              {}".format(start_date))
            print("End date:                {}".format(end_date))
            print("Starting balance:        ${}".format(round(starting_balance, 2)))
            print("Ending balance:          ${}".format(round(ending_balance, 2)))
            print("Ending NAV:              ${}".format(round(ending_NAV, 2)))
            print("Total return:            ${} ({}%)".format(round(abs_return, 2), 
                                              round(pc_return, 1)))
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
            print("Average trade duration:  {}".format(backtest_results['all_trades']['avg_trade_duration']))
            
        else:
            print("No trades taken.")
        
        no_open = backtest_results['no_open']
        no_cancelled = backtest_results['no_cancelled']
        
        if no_open > 0:
            print("Orders still open:       {}".format(no_open))
        if no_cancelled > 0:
            print("Cancelled orders:        {}".format(no_cancelled))
        
        # Long trades
        no_long = backtest_results['long_trades']['no_trades']
        print("\n            Summary of long trades")
        print("----------------------------------------------")
        if no_long > 0:
            avg_long_win = backtest_results['long_trades']['avg_long_win']
            max_long_win = backtest_results['long_trades']['max_long_win']
            avg_long_loss = backtest_results['long_trades']['avg_long_loss']
            max_long_loss = backtest_results['long_trades']['max_long_loss']
            long_wr = backtest_results['long_trades']['long_wr']
            
            print("Number of long trades:   {}".format(no_long))
            print("Long win rate:           {}%".format(round(long_wr, 1)))
            print("Max win:                 ${}".format(round(max_long_win, 2)))
            print("Average win:             ${}".format(round(avg_long_win, 2)))
            print("Max loss:                -${}".format(round(max_long_loss, 2)))
            print("Average loss:            -${}".format(round(avg_long_loss, 2)))
        else:
            print("There were no long trades.")
          
        # Short trades
        no_short = backtest_results['short_trades']['no_trades']
        print("\n             Summary of short trades")
        print("----------------------------------------------")
        if no_short > 0:
            avg_short_win = backtest_results['short_trades']['avg_short_win']
            max_short_win = backtest_results['short_trades']['max_short_win']
            avg_short_loss = backtest_results['short_trades']['avg_short_loss']
            max_short_loss = backtest_results['short_trades']['max_short_loss']
            short_wr = backtest_results['short_trades']['short_wr']
            
            print("Number of short trades:  {}".format(no_short))
            print("short win rate:          {}%".format(round(short_wr, 1)))
            print("Max win:                 ${}".format(round(max_short_win, 2)))
            print("Average win:             ${}".format(round(avg_short_win, 2)))
            print("Max loss:                -${}".format(round(max_short_loss, 2)))
            print("Average loss:            -${}".format(round(avg_short_loss, 2)))
            
        else:
            print("There were no short trades.")

    
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
        
        if self._backtest_mode:
            NAV     = []
            balance = []
            margin  = []
            tradetimes = []
        
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
        
        # Assign strategy to bot for each instrument in watchlist 
        for strategy in self._strategy_configs:
            for instrument in self._strategy_configs[strategy]['WATCHLIST']:
                data_dict = self._local_data[instrument] \
                    if self._local_data is not None else None
                quote_data_path = self._local_quote_data[instrument] \
                    if self._local_quote_data is not None else None
                auxdata = self._auxdata[instrument] \
                    if self._auxdata is not None else None
                
                strategy_class = self._strategy_configs[strategy]['CLASS']
                strategy_dict = {'config': self._strategy_configs[strategy],
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
                while timestamp <= end_time:
                    # Update each bot with latest data to generate signal
                    for bot in self._bots_deployed:
                        bot._update(timestamp=timestamp)
                        
                    # Update backtest tracking stats
                    NAV.append(self._broker.NAV)
                    balance.append(self._broker.portfolio_balance)
                    margin.append(self._broker.margin_available)
                    tradetimes.append(timestamp)
                    
                    # Iterate through time
                    timestamp += self._timestep
        
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
                        
                    # Update backtest tracking
                    NAV.append(self._broker.NAV)
                    balance.append(self._broker.portfolio_balance)
                    margin.append(self._broker.margin_available)
                    tradetimes.append(self._bots_deployed[0].data.index[i])
        
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
            # Create backtest summary for each bot 
            for bot in self._bots_deployed:
                bot._create_backtest_summary(balance, NAV, margin, tradetimes)            
            
            if int(self._verbosity) > 0:
                print(f"Backtest complete (runtime {round((backtest_end_time - backtest_start_time), 3)} s).")
                if len(self._bots_deployed) == 1:
                    bot = self._bots_deployed[0]
                    backtest_results = self.analyse_backtest(bot)
                    self.print_backtest_results(backtest_results)
                    
                else:
                    self.multibot_backtest_results = self.multibot_backtest_analysis()
                    self.print_multibot_backtest_results(self.multibot_backtest_results)
                    
                    print("Results for multiple-instrument backtests have been")
                    print("written to AutoTrader.multibot_backtest_results.")
                    print("Individual bot results can be found in the")
                    print("'bots_deployed' attribute of the AutoTrader instance.")
            
            if self._show_plot:
                if len(self._bots_deployed) == 1:
                    if len(self._broker.trades) > 0:
                        self.plot_backtest(bot=self._bots_deployed[0])
                
                else:
                    # Backtest run with multiple bots
                    self.plot_multibot_backtest()
        
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
                # look to AutoTraderBot._create_backtest_summary for process
                pass
        

    def _clear_strategies(self) -> None:
        """Removes all strategies saved in autotrader instance.
        """
        self._strategy_configs = {}
    
    
    def _clear_bots(self) -> None:
        """Removes all deployed bots in autotrader instance.
        """
        self._bots_deployed = []
    
    
    def _instantiate_autoplot(self, data: pd.DataFrame) -> AutoPlot:
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
        
        self.objective      = 'profit + MDD'
        
        ''' --------------------------------------------------------------- '''
        '''                          Unpack user options                    '''
        ''' --------------------------------------------------------------- '''
        
        # Look in self._strategy_configs for config
        if len(self._strategy_configs) > 1:
            print("Error: please optimise one strategy at a time.")
            print("Exiting.")
            sys.exit(0)
        else:
            config_dict = self._strategy_configs[list(self._strategy_configs.keys())[0]]
                
        ''' --------------------------------------------------------------- '''
        '''                      Define optimisation inputs                 '''
        ''' --------------------------------------------------------------- '''
        my_args = (config_dict, self._opt_params, self._verbosity)
        
        ''' --------------------------------------------------------------- '''
        '''                             Run Optimiser                       '''
        ''' --------------------------------------------------------------- '''
        start = timeit.default_timer()
        result = brute(func         = self._optimisation_helper_function, 
                       ranges       = self._bounds, 
                       args         = my_args, 
                       Ns           = self._Ns,
                       full_output  = True)
        stop = timeit.default_timer()
        
        ''' --------------------------------------------------------------- '''
        '''      Delete historical data file after running optimisation     '''
        ''' --------------------------------------------------------------- '''
        granularity             = config_dict["INTERVAL"]
        pair                    = config_dict["WATCHLIST"][0]
        historical_data_name    = 'hist_{0}{1}.csv'.format(granularity, pair)
        historical_quote_data_name = 'hist_{0}{1}_quote.csv'.format(granularity, pair)
        historical_data_file_path = os.path.join(self._home_dir, 
                                                 'price_data',
                                                 historical_data_name)
        historical_quote_data_file_path = os.path.join(self._home_dir, 
                                                       'price_data',
                                                       historical_quote_data_name)
        os.remove(historical_data_file_path)
        os.remove(historical_quote_data_file_path)
        
        opt_params = result[0]
        opt_value = result[1]
        
        ''' --------------------------------------------------------------- '''
        '''                           Print output                          '''
        ''' --------------------------------------------------------------- '''
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
        
        ''' ------------------------------------------------------------------ '''
        '''   Edit strategy parameters in config_dict using supplied params    '''
        ''' ------------------------------------------------------------------ '''
        for parameter in config_dict['PARAMETERS']:
            if parameter in opt_params:
                config_dict['PARAMETERS'][parameter] = params[opt_params.index(parameter)]
            else:
                continue
        
        ''' ------------------------------------------------------------------ '''
        '''           Run AutoTrader and evaluate objective function           '''
        ''' ------------------------------------------------------------------ '''
        self._clear_strategies()
        self._clear_bots()
        self.add_strategy(config_dict = config_dict)
        self._main()
        
        bot = self._bots_deployed[0]
            
        try:
            backtest_results = self.analyse_backtest(bot)
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
            print("\nWarning: mismatched data lengths detected. Correcting via row reduction.")
            self._normalise_bot_data()
    
    
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
        
