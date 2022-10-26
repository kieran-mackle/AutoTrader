import os
import sys
import time
import pickle
import timeit
import importlib
import traceback
import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import Callable
from threading import Thread
from ast import literal_eval
from scipy.optimize import brute
from autotrader.autoplot import AutoPlot
from autotrader.autobot import AutoTraderBot
from datetime import datetime, timedelta, timezone
from autotrader.brokers.broker import AbstractBroker
from autotrader.utilities import (
    read_yaml,
    get_broker_config,
    DataStream,
    TradeAnalysis,
    unpickle_broker,
    print_banner,
)


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
    plot_multibot_backtest(trade_results=None)
        Plots backtest results for multiple trading bots.
    multibot_backtest_analysis(bots=None)
        Analyses backtest results of multiple trading bots.
    print_trade_results(trade_results)
        Prints trade results.
    print_multibot_trade_results(trade_results=None)
        Prints a multi-bot backtest results.

    References
    ----------
    Author: Kieran Mackle

    Homepage: https://kieran-mackle.github.io/AutoTrader/

    GitHub: https://github.com/kieran-mackle/AutoTrader
    """

    def __init__(self) -> None:
        """AutoTrader initialisation. Called when creating new AutoTrader
        instance.
        """
        # Public attributes
        self.trade_results = None

        self._home_dir = None
        self._verbosity = 1

        self._global_config_dict = None
        self._instance_str = None
        self._run_mode = "continuous"
        self._papertrading = False
        self._timestep = None
        self._strategy_timestep = None
        self._warmup_period = pd.Timedelta("0s").to_pytimedelta()
        self._feed = None
        self._req_liveprice = False
        self._max_workers = None

        # Communications
        self._notify = 0
        self._notification_provider = ""
        self._notifier = None
        self._order_summary_fp = None

        # Livetrade Parameters
        self._deploy_time = None
        self._check_data_alignment = True
        self._allow_dancing_bears = False
        self._maintain_broker_thread = False

        # Broker parameters
        self._execution_method = None  # Execution method
        self._broker = None  # Broker instance(s)
        self._brokers_dict = None  # Dictionary of brokers
        self._broker_name = ""  # Broker name(s)
        self._broker_utils = None  # Broker utilities
        self._broker_verbosity = 0  # Broker verbosity
        self._environment = "paper"  # Trading environment
        self._account_id = None  # Trading account
        self._base_currency = None
        self._no_brokers = 0
        self._multiple_brokers = False

        # Strategy parameters
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
        self._broker_histories = None

        # Local Data Parameters
        self._data_directory = None
        self._data_indexing = "open"
        self._data_stream_object = DataStream
        self._data_file = None
        self._MTF_data_files = None
        self._data_path_mapper = None
        self._local_data = None
        self._local_quote_data = None
        self._auxdata = None
        self._dynamic_data = False
        self._allow_duplicate_bars = False

        # Virtual Broker Parameters
        self._virtual_broker_config = {}
        self._virtual_tradeable_instruments = {}  # Instruments tradeable mapper
        self._broker_refresh_freq = "1s"

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
        self._show_plot = False
        self._max_indis_over = 3
        self._max_indis_below = 2
        self._fig_tools = "pan,wheel_zoom,box_zoom,undo,redo,reset,save,crosshair"
        self._ohlc_height = 400
        self._ohlc_width = 800
        self._top_fig_height = 150
        self._bottom_fig_height = 150
        self._jupyter_notebook = False
        self._show_cancelled = True
        self._chart_timeframe = "default"
        self._chart_theme = "caliber"
        self._use_strat_plot_data = False
        self._plot_portolio_chart = False

    def __repr__(self):
        return f"AutoTrader instance"

    def __str__(self):
        return "AutoTrader instance"

    def configure(
        self,
        verbosity: int = 1,
        broker: str = None,
        execution_method: Callable = None,
        feed: str = None,
        req_liveprice: bool = False,
        notify: int = 0,
        notification_provider: str = None,
        home_dir: str = None,
        allow_dancing_bears: bool = False,
        account_id: str = None,
        environment: str = "paper",
        show_plot: bool = False,
        jupyter_notebook: bool = False,
        mode: str = "continuous",
        update_interval: str = None,
        data_index_time: str = "open",
        global_config: dict = None,
        instance_str: str = None,
        broker_verbosity: int = 0,
        home_currency: str = None,
        allow_duplicate_bars: bool = False,
        deploy_time: datetime = None,
        max_workers: int = None,
    ) -> None:
        """Configures run settings for AutoTrader.

        Parameters
        ----------
        verbosity : int, optional
            The verbosity of AutoTrader (0, 1, 2). The default is 1.
        broker : str, optional
            The broker(s) to connect to for trade execution. Multiple exchanges
            can be provided using comma separattion. The default is 'virtual'.
        execution_method : Callable, optional
            The execution model to call when submitting orders to the broker.
            This method must accept the broker instance, the order object,
            order_time and any *args, **kwargs.
        feed : str, optional
            The data feed to be used. This can be the same as the broker
            being used, or another data source. Options include 'yahoo',
            'oanda', 'ib', 'dydx', 'ccxt', 'local' or 'none'. When data is provided
            via the add_data method, the feed is automatically set to 'local'.
            The default is None.
        req_liveprice : bool, optional
            Request live market price from broker before placing trade, rather
            than using the data already provided. The default is False.
        notify : int, optional
            The level of notifications (0, 1, 2). The default is 0.
        notification_provider : str, optional
            The notifications provider to use (currently only Telegram supported).
            The default is None.
        home_dir : str, optional
            The project home directory. The default is the current working directory.
        allow_dancing_bears : bool, optional
            Allow incomplete candles to be passed to the strategy. The default is False.
        account_id : str, optional
            The brokerage account ID to be used. The default is None.
        environment : str, optional
            The trading environment of this instance ('paper', 'live'). The
            default is 'paper'.
        show_plot : bool, optional
            Automatically generate trade chart. The default is False.
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
            converted to a timedelta object. If None is passed, the update
            interval will be inferred from the strategy INTERVAL. The
            default is None.
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
        home_currency : str, optional
            The home currency of trading accounts used (intended for FX
            conversions). The default is None.
        allow_duplicate_bars : bool, optional
            Allow duplicate bars to be passed on to the strategy. The default
            is False.
        deploy_time : datetime, optional
            The time to deploy the bots. If this is a future time, AutoTrader
            will wait until it is reached before deploying. It will also be used
            as an anchor to synchronise future bot updates. If not specified,
            bots will be deployed as soon as possible, with successive updates
            synchronised to the deployment time.
        max_workers : int, optional
            The maximum number of workers to use when spawning threads. The
            default is None.

        Returns
        -------
        None
            Calling this method configures the internal settings of
            the active AutoTrader instance.
        """
        self._verbosity = verbosity
        self._feed = feed
        self._req_liveprice = req_liveprice
        self._broker_name = broker if broker is not None else self._broker_name
        self._execution_method = execution_method
        self._notify = notify
        self._notification_provider = (
            notification_provider
            if notification_provider is not None
            else self._notification_provider
        )
        self._home_dir = home_dir if home_dir is not None else os.getcwd()
        self._allow_dancing_bears = allow_dancing_bears
        self._allow_duplicate_bars = allow_duplicate_bars
        self._account_id = account_id
        self._environment = environment
        self._show_plot = show_plot
        self._jupyter_notebook = jupyter_notebook
        self._run_mode = mode
        self._timestep = (
            pd.Timedelta(update_interval).to_pytimedelta()
            if update_interval is not None
            else self._timestep
        )
        self._data_indexing = data_index_time
        self._global_config_dict = global_config
        self._instance_str = instance_str
        self._broker_verbosity = broker_verbosity
        self._base_currency = home_currency
        self._deploy_time = deploy_time
        self._max_workers = max_workers

    def add_strategy(
        self,
        config_filename: str = None,
        config_dict: dict = None,
        strategy=None,
        shutdown_method: str = None,
    ) -> None:
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
                raise Exception(
                    "Providing the shutdown method requires "
                    + "the home directory to have been configured. "
                    + "please either specify it, or simply call "
                    + "the configure method before adding a strategy."
                )

        else:
            # Home directory has been set, continue
            if config_dict is None:
                # Config YAML filepath provided
                config_file_path = os.path.join(
                    self._home_dir, "config", config_filename
                )
                new_strategy = read_yaml(config_file_path + ".yaml")
            else:
                # Config dictionary provided directly
                new_strategy = config_dict

            # Construct strategy name
            try:
                name = new_strategy["NAME"]
            except (TypeError, KeyError):
                print(
                    "Please specify the name of your strategy via the "
                    + "'NAME' key of the strategy configuration."
                )
                sys.exit()

            # Check for other required keys
            # TODO - review required keys (WATCHLIST? INTERVAL and
            # PERIOD only when feed not none)
            required_keys = ["CLASS", "INTERVAL", "PERIOD"]
            for key in required_keys:
                if key not in new_strategy:
                    print(
                        f"Please include the '{key}' key in your strategy configuration."
                    )
                    sys.exit(0)

            if name in self._strategy_configs:
                print(
                    "Warning: duplicate strategy name deteced. Please check "
                    + "the NAME field of your strategy configuration file and "
                    + "make sure it is not the same as other strategies being "
                    + "run from this instance."
                )
                print("Conflicting name:", name)

            # Check PERIOD type
            if isinstance(new_strategy["PERIOD"], float):
                # Convert to integer
                new_strategy["PERIOD"] = int(new_strategy["PERIOD"])

            elif isinstance(new_strategy["PERIOD"], str):
                # Period provided as time range, convert to int using INTERVAL
                new_strategy["PERIOD"] = int(
                    pd.Timedelta(new_strategy["PERIOD"])
                    / pd.Timedelta(new_strategy["INTERVAL"])
                )

            # Save to AutoTrader instance
            self._strategy_configs[name] = new_strategy
            self._shutdown_methods[name] = shutdown_method

            # Set timestep from strategy config
            try:
                strat_granularity = pd.Timedelta(
                    new_strategy["INTERVAL"]
                ).to_pytimedelta()
            except:
                print(
                    f"Strategy configuration error: invalid time interval: '{new_strategy['INTERVAL']}'."
                )
                sys.exit(0)

            if self._strategy_timestep is None:
                # Timestep hasn't been set yet; set it
                self._strategy_timestep = strat_granularity

            else:
                # Timestep has been set, overwrite only with a smaller granularity
                if strat_granularity < self._strategy_timestep:
                    self._strategy_timestep = strat_granularity

        if strategy is not None:
            self._strategy_classes[strategy.__name__] = strategy

    def virtual_account_config(
        self,
        verbosity: int = 0,
        initial_balance: float = 1000,
        spread: float = 0,
        commission: float = 0,
        spread_units: str = "price",
        commission_scheme: str = "percentage",
        maker_commission: float = None,
        taker_commission: float = None,
        leverage: int = 1,
        hedging: bool = False,
        margin_call_fraction: float = 0,
        default_slippage_model: Callable = None,
        slippage_models: dict = None,
        picklefile: str = None,
        exchange: str = None,
        tradeable_instruments: list = None,
        refresh_freq: str = "1s",
        home_currency: str = None,
        papertrade: bool = True,
    ) -> None:
        """Configures the virtual broker's initial state to allow livetrading
        on the virtual broker. If you wish to create multiple virtual broker
        instances, call this method for each virtual account.

        Parameters
        ----------
        verbosity : int, optional
            The verbosity of the broker. The default is 0.
        initial_balance : float, optional
            The initial balance of the account. The default is 1000.
        spread : float, optional
            The bid/ask spread to use in backtest (specified in units defined
            by the spread_units argument). The default is 0.
        spread_units : str, optional
            The unit of the spread specified. Options are 'price', meaning that
            the spread is quoted in price units, or 'percentage', meaning that
            the spread is quoted as a percentage of the market price. The default
            is 'price'.
        commission : float, optional
            Trading commission as percentage per trade. The default is 0.
        commission_scheme : str, optional
            The method with which to apply commissions to trades made. The options
            are (1) 'percentage', where the percentage specified by the commission
            argument is applied to the notional trade value, (2) 'fixed_per_unit',
            where the monetary value specified by the commission argument is
            multiplied by the number of units in the trade, and (3) 'flat', where
            a flat monetary value specified by the commission argument is charged
            per trade made, regardless of size. The default is 'percentage'.
        maker_commission : float, optional
            The commission to charge on liquidity-making orders. The default is
            None, in which case the nominal commission argument will be used.
        taker_commission: float, optional
            The commission to charge on liquidity-taking orders. The default is
            None, in which case the nominal commission argument will be used.
        leverage : int, optional
            Account leverage. The default is 1.
        hedging : bool, optional
            Allow hedging in the virtual broker (opening simultaneous
            trades in oposing directions). The default is False.
        margin_call_fraction : float, optional
            The fraction of margin usage at which a margin call will occur.
            The default is 0.
        default_slippage_model : Callable, optional
            The default model to use when calculating the percentage slippage
            on the fill price, for a given order size. The default functon
            returns zero.
        slippage_models : dict, optional
            A dictionary of callable slippage models, keyed by instrument.
        picklefile : str, optional
            The filename of the picklefile to load state from. If you do not
            wish to load from state, leave this as None. The default is None.
        exchange : str, optional
            The name of the exchange to use for execution. This gets passed to
            an instance of AutoData to update prices and use the realtime
            orderbook for virtual order execution. The default is None.
        tradeable_instruments : list, optional
            A list containing strings of the instruments tradeable through the
            exchange specified. This is used to determine which exchange orders
            should be submitted to when trading across multiple exchanges. This
            should account for all instruments provided in the watchlist. The
            default is None.
        refresh_freq : str, optional
            The timeperiod to sleep for in between updates of the virtual broker
            data feed when manually papertrading. The default is '1s'.
        home_currency : str, optional
            The home currency of the account. The default is None.
        papertrade : bool, optional
            A boolean to flag when the account is to be used for papertrading
            (real-time trading on paper). The default is True.
        """

        # TODO - allow specifying spread dictionary to have custom spreads for
        # different products

        # Enforce virtual broker and paper trading environment
        if exchange is not None:
            broker_name = exchange
        else:
            # TODO - catch attempt to create multiple instances with same exchange
            broker_name = "virtual"

        if broker_name != "virtual" and broker_name not in self._broker_name:
            # Unrecognised broker
            print(
                f"Please specify the broker '{broker_name}' in the "
                + "configure method before configuring its virtual account."
            )
            sys.exit(0)
            # self._broker_name += broker_name + ', '

        self._papertrading = False if self._backtest_mode else papertrade
        self._broker_refresh_freq = refresh_freq

        if tradeable_instruments is not None:
            self._virtual_tradeable_instruments[broker_name] = tradeable_instruments

        # Construct configuration dictionary
        config = {
            # Broker configuration
            "verbosity": verbosity,
            "initial_balance": initial_balance,
            "leverage": leverage,
            "spread": spread,
            "spread_units": spread_units,
            "commission": commission,
            "commission_scheme": commission_scheme,
            "maker_commission": maker_commission,
            "taker_commission": taker_commission,
            "hedging": hedging,
            "base_currency": home_currency,
            "paper_mode": self._papertrading,
            "public_trade_access": False,  # Not yet implemented
            "margin_closeout": margin_call_fraction,
            "default_slippage_model": default_slippage_model,
            "slippage_models": slippage_models,
            "picklefile": picklefile,
            # Extra parameters
            "execution_feed": exchange,
        }

        # Append
        # TODO - check keys for already existing
        self._virtual_broker_config[broker_name] = config

    def backtest(
        self,
        start: str = None,
        end: str = None,
        start_dt: datetime = None,
        end_dt: datetime = None,
        warmup_period: str = "0s",
    ) -> None:
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
        warmup_period : str, optional
            A string describing the warmup period to be used. This is
            equivalent to the minimum period of time required to collect
            sufficient data for the strategy. The default is '0s'.

        Notes
        ------
            Start and end times must be specified as the same type. For
            example, both start and end arguments must be provided together,
            or alternatively, start_dt and end_dt must both be provided.
        """
        # Convert start and end strings to datetime objects
        if start_dt is None and end_dt is None:
            start_dt = datetime.strptime(start + "+0000", "%d/%m/%Y%z")
            end_dt = datetime.strptime(end + "+0000", "%d/%m/%Y%z")

        # Assign attributes
        self._backtest_mode = True
        self._data_start = start_dt
        self._data_end = end_dt
        self._warmup_period = pd.Timedelta(warmup_period).to_pytimedelta()

    def optimise(
        self, opt_params: list, bounds: list, Ns: int = 4, force_download: bool = False
    ) -> None:
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
            opt_params = opt_params.split(",")

        self._optimise_mode = True
        self._opt_params = opt_params
        self._bounds = bounds
        self._Ns = Ns

        if self._local_data is None:
            raise Exception(
                "Local data files have not been provided. "
                + "Please do so using AutoTrader.add_data(), "
                + "or set force_download to True to proceed."
            )

    def add_data(
        self,
        data_dict: dict = None,
        mapper_func: callable = None,
        quote_data: dict = None,
        data_directory: str = "price_data",
        abs_dir_path: str = None,
        auxdata: dict = None,
        stream_object=None,
        dynamic_data: bool = False,
    ) -> None:
        """Specify local data to run AutoTrader on.

        Parameters
        ----------
        data_dict : dict, optional
            A dictionary containing the filenames of the datasets
            to be used. The default is None.
        mapper_func : callable, optional
            A callable used to provide the absolute filepath to the data
            given the instrument name (as it appears in the watchlist)
            as an input argument. The default is None.
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
            be refreshed each timestep of a backtest. This can be useful when
            backtesting strategies with futures contracts, which expire and
            must be rolled. The default is False.

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
        self._data_directory = data_directory
        dir_path = (
            abs_dir_path
            if abs_dir_path is not None
            else os.path.join(self._home_dir, data_directory)
        )

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
                        MTF_data[timeframe] = os.path.join(
                            dir_path, data_dict[product][timeframe]
                        )

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
                    raise Exception(
                        "Only a single quote-data file should be "
                        + "provided per instrument traded."
                    )

                else:
                    local_quote_data[product] = os.path.join(
                        dir_path, quote_data[product]
                    )

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

        if mapper_func is not None:
            self._data_path_mapper = mapper_func

        # Assign data stream object
        if stream_object is not None:
            self._data_stream_object = stream_object

        # Fix attributes
        self._feed = "local"
        self._dynamic_data = dynamic_data

    def scan(
        self,
        strategy_filename: str = None,
        strategy_dict: dict = None,
        scan_index: str = None,
    ) -> None:
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
            self.add_strategy(config_filename=strategy_filename)
        elif strategy_dict is not None:
            self.add_strategy(strategy_dict=strategy_dict)

        # If scan index provided, use that. Else, use strategy watchlist
        scan_index = "Strategy watchlist"

        self._scan_mode = True
        self._scan_index = scan_index
        self._check_data_alignment = False

    def run(self) -> AbstractBroker:
        """Performs essential checks and runs AutoTrader."""
        # Print Banner
        if int(self._verbosity) > 0:
            print_banner()

        # Define home_dir if undefined
        if self._home_dir is None:
            self._home_dir = os.getcwd()

        # Load uninitiated strategies
        for strat_dict in self._uninitiated_strat_dicts:
            self.add_strategy(strategy_dict=strat_dict)
        for strat_config_file in self._uninitiated_strat_files:
            self.add_strategy(config_filename=strat_config_file)

        if self._scan_watchlist is not None:
            # Scan watchlist has not overwritten strategy watchlist
            self._update_strategy_watchlist()

        # Check for added strategies
        if (
            len(self._strategy_configs) == 0
            and not self._papertrading
            and int(self._verbosity) > 1
        ):
            print(
                "Warning: no strategy has been provided. Do so by using the"
                + " 'add_strategy' method of AutoTrader."
            )

        if sum([self._backtest_mode, self._scan_mode]) > 1:
            print(
                "Error: backtest mode and scan mode are both set to True,"
                + " but only one of these can run at a time."
            )
            print("Please check your inputs and try again.")
            sys.exit(0)

        # Check self._timestep
        if self._timestep is None:
            # Set timestep based on strategy inferred timestep
            self._timestep = self._strategy_timestep

        # Remove any trailing commas in self._broker_name
        self._broker_name = self._broker_name.strip().strip(",")

        # Check for multiple brokers
        self._no_brokers = len(self._broker_name.split(","))
        self._multiple_brokers = self._no_brokers > 1
        # TODO - check len(self._virtual_broker_config)

        # Check self._broker_name
        if self._broker_name == "":
            # Broker has not been assigned
            if self._backtest_mode or self._papertrading or self._scan_mode:
                # Use virtual broker
                self._broker_name = "virtual"

            else:
                # Livetrading
                print(
                    "Please specify the name(s) of the broker(s) "
                    + "you wish to trade with."
                )
                sys.exit()

        if self._backtest_mode:
            if self._notify > 0:
                print(
                    "Warning: notify set to {} ".format(self._notify)
                    + "during backtest. Setting to zero to prevent notifications."
                )
                self._notify = 0

            # Check that the backtest does not request future data
            if self._data_end > datetime.now(tz=self._data_end.tzinfo):
                print(
                    "Warning: you have requested backtest data into the "
                    + "future. The backtest end date will be adjsuted to "
                    + "the current time."
                )
                self._data_end = datetime.now(tz=self._data_end.tzinfo)

            # Check if the broker has been configured
            if len(self._virtual_broker_config) != self._no_brokers:
                # Virtual accounts have not been configured for the brokers specified
                if len(self._virtual_broker_config) == 0:
                    # Use default values for all virtual accounts
                    for exchange in self._broker_name.split(","):
                        self.virtual_account_config(papertrade=False, exchange=exchange)
                else:
                    # Partially configured accounts
                    raise Exception(
                        "Please configure the virtual accounts for "
                        + "each broker you plan to used.\n"
                        + f" Number of brokers specifed: {self._no_brokers}\n"
                        + f" Number of virtual accounts configured: {len(self._virtual_broker_config)}"
                    )

        # Check notification settings
        if self._notify > 0 and self._notification_provider is None:
            print(
                "Please specify a notification provided via the " + "configure method."
            )
            sys.exit()

        # Preliminary checks complete, continue initialisation
        if self._optimise_mode:
            # Run optimisation
            if self._backtest_mode:
                self._run_optimise()
            else:
                print("Please set backtest parameters to run optimisation.")

        else:
            # Trading
            if not self._backtest_mode and "virtual" in self._broker_name:
                # Not in backtest mode, yet virtual broker is selected
                if not self._papertrading and not self._scan_mode:
                    # Not papertrading or scanning either
                    print(
                        "Live-trade mode requires setting the "
                        + "broker. Please do so using the "
                        + "AutoTrader configure method. If you "
                        + "would like to use the virtual broker "
                        + "for papertrading, please "
                        + "configure the virtual broker account(s) "
                        + "with the virtual_account_config method."
                    )
                    sys.exit()

            # Load global (account) configuration
            if self._global_config_dict is not None:
                # Use global config dict provided
                global_config = self._global_config_dict
            else:
                # Try load from file
                global_config_fp = os.path.join(self._home_dir, "config", "keys.yaml")
                if os.path.isfile(global_config_fp):
                    global_config = read_yaml(global_config_fp)
                else:
                    global_config = None

                # Assign
                self._global_config_dict = global_config

            # Create notifier instance
            if "telegram" in self._notification_provider.lower():
                # Use telegram
                if "TELEGRAM" not in self._global_config_dict:
                    print("Please configure your telegram bot in keys.yaml.")
                    sys.exit()

                else:
                    # Check keys provided
                    required_keys = ["api_key", "chat_id"]
                    for key in required_keys:
                        if key not in self._global_config_dict["TELEGRAM"]:
                            print(f"Please provide {key} under TELEGRAM in keys.yaml.")
                            sys.exit()

                tg_module = importlib.import_module(f"autotrader.comms.tg")
                self._notifier = tg_module.Telegram(
                    api_token=self._global_config_dict["TELEGRAM"]["api_key"],
                    chat_id=self._global_config_dict["TELEGRAM"]["chat_id"],
                )

            # Check data feed requirements
            if self._feed is None:
                # No data feed specified
                if self._backtest_mode:
                    raise Exception(
                        "No data feed specified! Please do so using "
                        + "AutoTrader.configure(feed=), or provide local data via "
                        + "AutoTrader.add_data()."
                    )

            elif global_config is None and self._feed.lower() in ["oanda", "ib"]:
                # No global configuration provided, but data feed requires authentication
                print(
                    f'Data feed "{self._feed}" requires global '
                    + "configuration. If a config file already "
                    + "exists, make sure to specify the home_dir. "
                    + "Alternatively, provide a configuration dictionary "
                    + "directly via AutoTrader.configure()."
                )
                sys.exit()

            # Check global config requirements
            if sum([self._backtest_mode, self._scan_mode, self._papertrading]) == 0:
                # Livetrade mode
                if global_config is None:
                    # No global_config
                    print(
                        "No global configuration found (required for "
                        + "livetrading). Either provide a global configuration dictionary "
                        + "via the configure method, or create a keys.yaml file in your "
                        + "config/ directory."
                    )
                    sys.exit()

                if self._broker_name == "":
                    print(
                        "Please specify the brokers you would like to "
                        + "trade with via the configure method."
                    )
                    sys.exit()

                # Check broker
                supported_exchanges = ["virtual", "oanda", "ib", "ccxt", "dydx"]
                inputted_brokers = self._broker_name.lower().replace(" ", "").split(",")
                for broker in inputted_brokers:
                    if broker.split(":")[0] not in supported_exchanges:
                        print(
                            f"Unsupported broker requested: {self._broker_name}\n"
                            + "Please check the broker(s) specified in configure method and "
                            + "virtual_account_config."
                        )
                        sys.exit()

            # All checks passed, proceed to run main
            if self._verbosity > 1:
                print("All preliminary checks complete, proceeding.")
            self._main()

            if self._papertrading or len(self._bots_deployed) == 0:
                # Return broker instance
                self.broker = self._broker
                return self._broker

    def plot_settings(
        self,
        max_indis_over: int = 3,
        max_indis_below: int = 2,
        fig_tools: str = "pan,wheel_zoom,box_zoom,undo,redo,reset,save,crosshair",
        ohlc_height: int = 400,
        ohlc_width: int = 800,
        top_fig_height: int = 150,
        bottom_fig_height: int = 150,
        jupyter_notebook: bool = False,
        show_cancelled: bool = True,
        chart_timeframe: str = "default",
        chart_theme: str = "caliber",
        use_strat_plot_data: bool = False,
        portfolio_chart: bool = False,
    ) -> None:
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
        self._max_indis_over = max_indis_over
        self._max_indis_below = max_indis_below
        self._fig_tools = fig_tools
        self._ohlc_height = ohlc_height
        self._ohlc_width = ohlc_width
        self._top_fig_heigh = top_fig_height
        self._bottom_fig_height = bottom_fig_height
        self._jupyter_notebook = jupyter_notebook
        self._show_cancelled = show_cancelled
        self._chart_timefram = chart_timeframe
        self._chart_theme = chart_theme
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
            symbol = bot.instrument
            if isinstance(symbol, list):
                # Porfolio-trading bot
                symbol = "portfolio"
            bots[symbol] = bot

        if instrument is not None:
            # Retrieve bot requested
            try:
                bots = bots[instrument]
            except:
                raise Exception(
                    f"There were no bots found to be trading '{instrument}'."
                )
        else:
            if len(bots) == 1:
                # Single bot backtest, return directly
                bots = bots[list(bots.keys())[0]]

        return bots

    def print_trade_results(self, trade_results: TradeAnalysis = None) -> None:
        """Prints trade results.

        Parameters
        ----------
        trade_results : TradeAnalysis
            The trade analysis results class object.

        Returns
        -------
        None
            Trade results will be printed.
        """
        if trade_results is None:
            trade_results = self.trade_results

        trade_summary = trade_results.summary()
        if "start" in trade_summary:
            start_date = trade_summary["start"].strftime("%b %d %Y %H:%M:%S")
            end_date = trade_summary["end"].strftime("%b %d %Y %H:%M:%S")
            duration = trade_summary["end"] - trade_summary["start"]

            starting_balance = trade_summary["starting_balance"]
            ending_balance = trade_summary["ending_balance"]
            ending_NAV = trade_summary["ending_NAV"]
            abs_return = trade_summary["abs_return"]
            pc_return = trade_summary["pc_return"]
            max_drawdown = trade_summary["max_drawdown"]

            no_trades = trade_summary["no_trades"]
            no_long_trades = trade_summary["no_long_trades"]
            no_short_trades = trade_summary["no_short_trades"]
            if no_trades > 0:
                win_rate = trade_summary["all_trades"]["win_rate"]
                max_win = trade_summary["all_trades"]["max_win"]
                avg_win = trade_summary["all_trades"]["avg_win"]
                max_loss = trade_summary["all_trades"]["max_loss"]
                avg_loss = trade_summary["all_trades"]["avg_loss"]
                longest_win_streak = trade_summary["all_trades"]["win_streak"]
                longest_lose_streak = trade_summary["all_trades"]["lose_streak"]
                total_fees = trade_summary["all_trades"]["total_fees"]
                total_volume = trade_summary["all_trades"]["total_volume"]
                adv = total_volume / duration.days

            print("\n----------------------------------------------")
            print("               Trading Results")
            print("----------------------------------------------")
            print("Start date:              {}".format(start_date))
            print("End date:                {}".format(end_date))
            print("Duration:                {}".format(duration))
            print("Starting balance:        ${}".format(round(starting_balance, 2)))
            print("Ending balance:          ${}".format(round(ending_balance, 2)))
            print("Ending NAV:              ${}".format(round(ending_NAV, 2)))
            print(
                "Total return:            ${} ({}%)".format(
                    round(abs_return, 2), round(pc_return, 1)
                )
            )
            print("Maximum drawdown:        {}%".format(round(max_drawdown * 100, 2)))
            if no_trades > 0:
                print("Total no. trades:        {}".format(no_trades))
                print("No. long trades:         {}".format(no_long_trades))
                print("No. short trades:        {}".format(no_short_trades))
                print("Total fees paid:         ${}".format(round(total_fees, 3)))
                print("Total volume traded:     ${}".format(round(total_volume, 2)))
                print("Average daily volume:    ${}".format(round(adv, 2)))
                # print("Win rate:                {}%".format(round(win_rate, 1)))
                # print("Max win:                 ${}".format(round(max_win, 2)))
                # print("Average win:             ${}".format(round(avg_win, 2)))
                # print("Max loss:                -${}".format(round(max_loss, 2)))
                # print("Average loss:            -${}".format(round(avg_loss, 2)))
                # print(
                #     "Longest winning streak:  {} positions".format(longest_win_streak)
                # )
                # print(
                #     "Longest losing streak:   {} positions".format(longest_lose_streak)
                # )
                # if len(trade_results.position_summary) > 0:
                #     avg_pos_dur = np.mean(
                #         trade_results.position_summary.loc["avg_duration"].values
                #     )
                #     print(
                #         "Avg. position duration:  {}".format(
                #             avg_pos_dur,
                #         )
                #     )

                no_open = trade_summary["no_open"]
                if no_open > 0:
                    print("Positions still open:    {}".format(no_open))

            else:
                print("\n No trades made.")

            no_cancelled = trade_summary["no_cancelled"]
            if no_cancelled > 0:
                print("Cancelled orders:        {}".format(no_cancelled))

            # if len(trade_results.position_summary) > 0:
            #     # Long positions
            #     no_long = trade_results.position_summary.sum(axis=1, numeric_only=True)[
            #         "no_long"
            #     ]
            #     print("\n          Summary of long positions")
            #     print("----------------------------------------------")
            #     if no_long > 0:
            #         # avg_long_win = trade_summary["long_positions"]["avg_long_win"]
            #         # max_long_win = trade_summary["long_positions"]["max_long_win"]
            #         # avg_long_loss = trade_summary["long_positions"]["avg_long_loss"]
            #         # max_long_loss = trade_summary["long_positions"]["max_long_loss"]
            #         # long_wr = trade_summary["long_positions"]["long_wr"]
            #         avg_long_dur = np.mean(
            #             trade_results.position_summary.loc["avg_long_duration"].values
            #         )

            #         print("No. long positions:      {}".format(no_long))
            #         print("Avg. position duration:  {}".format(avg_long_dur))
            #         # print("Win rate:                {}%".format(round(long_wr, 1)))
            #         # print("Max win:                 ${}".format(round(max_long_win, 2)))
            #         # print("Average win:             ${}".format(round(avg_long_win, 2)))
            #         # print("Max loss:                -${}".format(round(max_long_loss, 2)))
            #         # print("Average loss:            -${}".format(round(avg_long_loss, 2)))
            #     else:
            #         print("There were no long positions.")

            #     # Short trades
            #     no_short = trade_results.position_summary.sum(
            #         axis=1, numeric_only=True
            #     )["no_short"]
            #     print("\n         Summary of short positions")
            #     print("----------------------------------------------")
            #     if no_short > 0:
            #         # avg_short_win = trade_summary["short_positions"]["avg_short_win"]
            #         # max_short_win = trade_summary["short_positions"]["max_short_win"]
            #         # avg_short_loss = trade_summary["short_positions"]["avg_short_loss"]
            #         # max_short_loss = trade_summary["short_positions"]["max_short_loss"]
            #         # short_wr = trade_summary["short_positions"]["short_wr"]
            #         avg_short_dur = np.mean(
            #             trade_results.position_summary.loc["avg_long_duration"].values
            #         )

            #         print("No. short positions:     {}".format(no_short))
            #         print("Avg. position duration:  {}".format(avg_short_dur))
            #         # print("Win rate:                {}%".format(round(short_wr, 1)))
            #         # print("Max win:                 ${}".format(round(max_short_win, 2)))
            #         # print("Average win:             ${}".format(round(avg_short_win, 2)))
            #         # print("Max loss:                -${}".format(round(max_short_loss, 2)))
            #         # print("Average loss:            -${}".format(round(avg_short_loss, 2)))

            #     else:
            #         print("There were no short positions.")

            # Check for multiple instruments
            if len(trade_results.instruments_traded) > 1:
                # Mutliple instruments traded
                instruments = trade_results.instruments_traded
            #     trade_history = trade_results.isolated_position_history

            #     total_no_trades = []
            #     max_wins = []
            #     max_losses = []
            #     avg_wins = []
            #     avg_losses = []
            #     profitable_trades = []
            #     win_rates = []
            #     for i in range(len(instruments)):
            #         instrument_trades = trade_history[
            #             trade_history.instrument == instruments[i]
            #         ]
            #         no_trades = len(instrument_trades)
            #         total_no_trades.append(no_trades)
            #         max_wins.append(instrument_trades.profit.max())
            #         max_losses.append(instrument_trades.profit.min())
            #         avg_wins.append(
            #             instrument_trades.profit[instrument_trades.profit > 0].mean()
            #         )
            #         avg_losses.append(
            #             instrument_trades.profit[instrument_trades.profit < 0].mean()
            #         )
            #         profitable_trades.append((instrument_trades.profit > 0).sum())
            #         win_rates.append(
            #             100 * profitable_trades[i] / no_trades if no_trades > 0 else 0.0
            #         )

            #     results = pd.DataFrame(
            #         data={
            #             "Instrument": instruments,
            #             "Max. Win": max_wins,
            #             "Max. Loss": max_losses,
            #             "Avg. Win": avg_wins,
            #             "Avg. Loss": avg_losses,
            #             "Win Rate": win_rates,
            #         }
            #     ).fillna(0)

            #     print("\n Instrument Breakdown:")
            #     print(results.to_string(index=False))

        else:
            print("No updates to report.")

    def plot_backtest(self, bot=None) -> None:
        """Plots trade results of an AutoTrader Bot.

        Parameters
        ----------
        bot : AutoTrader bot instance, optional
            AutoTrader bot class containing trade results. The default
            is None.

        Returns
        -------
        None
            A chart will be generated and shown.
        """

        def portfolio_plot():
            ap = self._instantiate_autoplot()
            ap._portfolio_plot(self.trade_results)

        def single_instrument_plot(bot):
            data = bot._check_strategy_for_plot_data(self._use_strat_plot_data)
            ap = self._instantiate_autoplot(data)
            ap.plot(trade_results=bot.trade_results)

        if bot is None:
            # No bot has been provided, select automatically
            if (
                len(self.trade_results.instruments_traded) > 1
                or len(self._bots_deployed) > 1
                or self._plot_portolio_chart
            ):
                # Multi-bot backtest
                portfolio_plot()
            else:
                # Single bot backtest
                bot = self._bots_deployed[0]
                single_instrument_plot(bot)
        else:
            # A bot has been provided
            single_instrument_plot(bot)

    def _main(self) -> None:
        """Run AutoTrader with configured settings."""
        # Check tradeable instruments
        if (
            self._multiple_brokers
            and len(self._virtual_tradeable_instruments) != self._no_brokers
            and self._backtest_mode
        ):
            print(
                "Please define the tradeable instruments for "
                + "each virtual account configured."
            )
            sys.exit()

        # Get broker configuration
        if self._backtest_mode or self._papertrading:
            names_list = [f"virtual:{i}" for i in self._broker_name.split(",")]
            broker_names = ",".join(names_list)
        else:
            broker_names = self._broker_name
        broker_config = get_broker_config(
            global_config=self._global_config_dict,
            broker=broker_names,
            environment=self._environment,
        )

        if self._account_id is not None:
            if self._multiple_brokers:
                print(
                    "Cannot use provided account ID when "
                    + "trading across multiple exchanges. Please specify the "
                    + "desired account in the keys config."
                )
                sys.exit()
            else:
                # Overwrite default account in config dicts
                broker_config["ACCOUNT_ID"] = self._account_id
                self._global_config_dict["custom_account_id"] = self._account_id

        # Append broker verbosity to broker_config
        if self._multiple_brokers:
            for broker, config in broker_config.items():
                config["verbosity"] = self._broker_verbosity
        else:
            broker_config["verbosity"] = self._broker_verbosity

        # Connect to exchanges
        if self._verbosity > 1:
            print("Connecting to exchanges...")
        self._assign_broker(broker_config)
        if self._verbosity > 1:
            print("  Done.")

        # Initialise broker histories
        self._broker_histories = {
            key: {
                "NAV": [],
                "equity": [],
                "margin": [],
                "open_interest": [],
                "long_exposure": [],
                "short_exposure": [],
                "long_unrealised_pnl": [],
                "short_unrealised_pnl": [],
                "long_pnl": [],
                "short_pnl": [],
                "time": [],
            }
            for key in self._brokers_dict
        }

        # Assign trading bots to each strategy
        if self._verbosity > 1:
            print("Spawning trading bots...")
        for strategy, config in self._strategy_configs.items():
            # Check for portfolio strategy
            portfolio = config["PORTFOLIO"] if "PORTFOLIO" in config else False
            watchlist = [config["WATCHLIST"]] if portfolio else config["WATCHLIST"]
            for instrument in watchlist:
                if portfolio:
                    data_dict = self._local_data
                    quote_data_path = self._local_quote_data
                    auxdata = self._auxdata
                else:
                    data_dict = (
                        self._local_data[instrument]
                        if self._local_data is not None
                        else None
                    )
                    quote_data_path = (
                        self._local_quote_data[instrument]
                        if self._local_quote_data is not None
                        else None
                    )
                    auxdata = (
                        self._auxdata[instrument] if self._auxdata is not None else None
                    )

                strategy_class = config["CLASS"]
                strategy_dict = {
                    "config": config,
                    "class": self._strategy_classes[strategy_class]
                    if strategy_class in self._strategy_classes
                    else None,
                    "shutdown_method": self._shutdown_methods[strategy],
                }
                bot = AutoTraderBot(
                    instrument,
                    strategy_dict,
                    self._broker,
                    self._data_start,
                    data_dict,
                    quote_data_path,
                    auxdata,
                    self,
                )
                self._bots_deployed.append(bot)

        if int(self._verbosity) > 0:
            if self._backtest_mode:
                print("BACKTEST MODE")
            else:
                if self._scan_mode:
                    print("SCAN MODE")
                elif self._papertrading:
                    trade_mode = "auto" if len(self._bots_deployed) > 0 else "manual"
                    extra_str = f"{trade_mode} trade in {self._environment} environment"
                    print(f"PAPERTRADE MODE ({extra_str})")
                else:
                    trade_mode = "auto" if len(self._bots_deployed) > 0 else "manual"
                    extra_str = f"{trade_mode} trade in {self._environment} environment"
                    print(f"LIVETRADE MODE ({extra_str})")
                print(
                    "Current time: {}".format(
                        datetime.now().strftime("%A, %B %d %Y, " + "%H:%M:%S")
                    )
                )

            for bot in self._bots_deployed:
                if isinstance(bot.instrument, str):
                    instr_str = bot.instrument
                else:
                    instr_str = (
                        bot.instrument
                        if len(bot.instrument) < 5
                        else f"a portfolio of {len(bot.instrument)} instruments"
                    )
                print(
                    f"\nAutoTraderBot assigned to trade {instr_str}",
                    f"with {bot._broker_name} broker using {bot._strategy_name}.",
                )

        # Begin trading
        self._trade_update_loop()

    def _clear_strategies(self) -> None:
        """Removes all strategies saved in autotrader instance."""
        self._strategy_configs = {}

    def _clear_bots(self) -> None:
        """Removes all deployed bots in autotrader instance."""
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
        if self._chart_timeframe == "default":
            ap = AutoPlot(data)
        else:
            # Instantiate AutoPlot with requested chart timeframe
            if self._chart_timeframe in self._bots_deployed[0].MTF_data.keys():
                # Valid timeframe requested
                ap = AutoPlot(self._bots_deployed[0].MTF_data[self._chart_timeframe])
                ap._add_backtest_price_data(
                    data
                )  # provide nominal timeframe data for merge operations
            else:
                warning_str = (
                    f"The chart timeframe requested ({self._chart_timeframe}) was not found "
                    + "in the MTF data. Please ensure that the timeframe provided matches "
                    + "the format provided in the strategy configuration file, or the local "
                    + "data provided."
                )
                raise Exception(warning_str)

        # Assign attributes
        ap.configure(
            max_indis_over=self._max_indis_over,
            max_indis_below=self._max_indis_below,
            fig_tools=self._fig_tools,
            ohlc_height=self._ohlc_height,
            ohlc_width=self._ohlc_width,
            top_fig_height=self._top_fig_height,
            bottom_fig_height=self._bottom_fig_height,
            jupyter_notebook=self._jupyter_notebook,
            show_cancelled=self._show_cancelled,
            chart_theme=self._chart_theme,
            use_strat_plot_data=self._use_strat_plot_data,
        )

        return ap

    def _update_strategy_watchlist(self) -> None:
        """Updates the watchlist of each strategy with the scan watchlist."""
        for strategy in self._strategy_configs:
            self._strategy_configs[strategy]["WATCHLIST"] = self._scan_watchlist

    def _assign_broker(self, broker_config: dict) -> None:
        """Configures and assigns appropriate broker(s) for trading."""
        # Check for multiple brokers
        if not self._multiple_brokers:
            # Put broker config in dict to allow single iteration
            broker_config = {self._broker_name: broker_config}

        # Instantiate brokers
        brokers = {}
        brokers_utils = {}
        for broker_key, config in broker_config.items():
            # Import relevant broker and utilities modules
            if self._backtest_mode or self._papertrading:
                # Use virtual broker
                broker_name = "virtual"
            else:
                # Use real broker
                broker_name = broker_key.lower().split(":")[0]

            # Construct utils args
            utils_args = {}
            utils_name = broker_key.lower().split(":")[0]
            if utils_name == "ccxt":
                utils_args["exchange"] = broker_key.lower().split(":")[1]

            # Import relevant modules
            broker_module = importlib.import_module(
                f"autotrader.brokers.{broker_name}.broker"
            )
            utils_module = importlib.import_module(
                f"autotrader.brokers.{utils_name}.utils"
            )

            # Create broker and utils instances
            utils = utils_module.Utils(**utils_args)
            broker = broker_module.Broker(config, utils)

            if self._backtest_mode or self._papertrading:
                # Using virtual broker, configure account
                try:
                    account_config = self._virtual_broker_config[broker_key]
                except KeyError:
                    # Broker hasn't been configured properly
                    raise Exception(
                        f"Broker '{broker_key}' has not been "
                        + "configured. Please do so using the virtual_account_config "
                        + f"method, making sure to specify exchange='{broker_key}'."
                    )

                execution_feed = account_config["execution_feed"]
                feed = self._feed if execution_feed is None else execution_feed
                autodata_config = {
                    "feed": feed,
                    "environment": self._environment,
                    "global_config": self._global_config_dict,
                    "allow_dancing_bears": self._allow_dancing_bears,
                    "base_currency": self._base_currency,
                }
                broker.configure(**account_config, autodata_config=autodata_config)

            # Append to brokers dict
            brokers[broker_key] = broker
            brokers_utils[broker_key] = utils

        # Save broker dict
        self._brokers_dict = brokers

        # Check
        if not self._multiple_brokers:
            # Extract single broker
            brokers = broker
            brokers_utils = utils

        self._broker = brokers
        self._broker_utils = brokers_utils

    def _run_optimise(self) -> None:
        """Runs optimisation of strategy parameters."""

        # Modify verbosity for optimisation
        verbosity = self._verbosity
        self._verbosity = 0
        self._show_plot = False
        self.objective = "profit + MDD"

        # Look in self._strategy_configs for config
        if len(self._strategy_configs) > 1:
            print("Error: please optimise one strategy at a time.")
            print("Exiting.")
            sys.exit(0)
        else:
            config_dict = self._strategy_configs[list(self._strategy_configs.keys())[0]]

        my_args = (config_dict, self._opt_params, self._verbosity)

        start = timeit.default_timer()
        result = brute(
            func=self._optimisation_helper_function,
            ranges=self._bounds,
            args=my_args,
            Ns=self._Ns,
            full_output=True,
        )
        stop = timeit.default_timer()

        opt_params = result[0]
        opt_value = result[1]

        print("\nOptimisation complete.")
        print("Time to run: {}s".format(round((stop - start), 3)))
        print("Optimal parameters:")
        print(opt_params)
        print("Objective:")
        print(opt_value)

        # Reset verbosity
        self._verbosity = verbosity

    def _optimisation_helper_function(
        self, params: list, config_dict: dict, opt_params: list, verbosity: int
    ) -> float:
        """Helper function for optimising strategy parameters in AutoTrader.
        This function will parse the ordered params into the config dict.
        """
        for parameter in config_dict["PARAMETERS"]:
            if parameter in opt_params:
                config_dict["PARAMETERS"][parameter] = params[
                    opt_params.index(parameter)
                ]
            else:
                continue

        self._clear_strategies()
        self._clear_bots()
        self.add_strategy(config_dict=config_dict)
        self._main()

        try:
            trade_results = self.trade_results.summary()
            objective = -trade_results["all_trades"]["ending_NAV"]
        except:
            objective = 1000

        print("Parameters/objective:", params, "/", round(objective, 3))

        return objective

    def _check_bot_data(self) -> None:
        """Function to compare lengths of bot data."""
        data_lengths = [len(bot.data) for bot in self._bots_deployed]
        if min(data_lengths) != np.mean(data_lengths):
            print(
                "Warning: mismatched data lengths detected. "
                + "Correcting via row reduction."
            )
            self._normalise_bot_data()
            print("  Done.\n")

    def _normalise_bot_data(self) -> None:
        """Function to normalise the data of mutliple bots so that their
        indexes are equal, allowing backtesting in periodic update mode.
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

    def _get_instance_id(self, dir_name: str = "active_bots"):
        """Returns an ID for the active AutoTrader instance."""
        dirpath = os.path.join(self._home_dir, dir_name)

        # Check if active_bots directory exists
        if not os.path.isdir(dirpath):
            # Directory does not exist, create it
            os.mkdir(dirpath)
            instance_id = 1

        else:
            # Directory exists, find highest instance
            instances = [
                f
                for f in os.listdir(dirpath)
                if os.path.isfile(os.path.join(dirpath, f))
            ]

            last_id = 0
            for instance in instances:
                if "autotrader_instance_" in instance:
                    # Ignore custom instance strings
                    last_id = int(instance.split("_")[-1])

            instance_id = last_id + 1

        return instance_id

    def _check_instance_file(
        self,
        instance_str: str,
        initialisation: bool = False,
        dir_name: str = "active_bots",
        live_check: bool = True,
    ):
        """Checks if the AutoTrader instance exists."""
        if initialisation:
            # Create the file
            filepath = os.path.join(self._home_dir, dir_name, instance_str)
            with open(filepath, mode="w") as f:
                f.write("This instance of AutoTrader contains the following bots:\n")
                for bot in self._bots_deployed:
                    f.write(bot._strategy_name + f" ({bot.instrument})\n")
            instance_file_exists = True

            if int(self._verbosity) > 0 and live_check:
                print(f"Active AutoTrader instance file: active_bots/{instance_str}")

        else:
            dirpath = os.path.join(self._home_dir, dir_name)
            instances = [
                f
                for f in os.listdir(dirpath)
                if os.path.isfile(os.path.join(dir_name, f))
            ]
            instance_file_exists = instance_str in instances

        if int(self._verbosity) > 0 and not instance_file_exists and live_check:
            print(
                f"Instance file '{instance_str}' deleted. AutoTrader",
                "will now shut down.",
            )

        return instance_file_exists

    def _manualtrade(self):
        """Runs the broker updates when manual trading."""
        # Check trading environment
        if self._papertrading:
            # Toggle broker monitoring on
            print(
                f"Running virtual broker updates at {self._broker_refresh_freq} intervals."
            )
            print("To stop papertrading, use at.shutdown().")

            self._maintain_broker_thread = True
            sleep_time = pd.Timedelta(self._broker_refresh_freq).total_seconds()

            # # Check for multiple brokers
            # if not self._multiple_brokers:
            #     brokers = {self._broker_name: self._broker}
            # else:
            #     brokers = self._broker

            # Run update loop
            while self._maintain_broker_thread:
                try:
                    for broker_name, broker in self._brokers_dict.items():
                        # Update orders and positions
                        broker._update_all()

                        # Update broker histories
                        hist_dict = self._broker_histories[broker_name]
                        hist_dict["NAV"].append(broker._NAV)
                        hist_dict["equity"].append(broker._equity)
                        hist_dict["margin"].append(broker._margin_available)
                        hist_dict["long_exposure"].append(broker._long_exposure)
                        hist_dict["short_exposure"].append(broker._short_exposure)
                        hist_dict["long_unrealised_pnl"].append(
                            broker._long_unrealised_pnl
                        )
                        hist_dict["short_unrealised_pnl"].append(
                            broker._short_unrealised_pnl
                        )
                        hist_dict["long_pnl"].append(broker._long_realised_pnl)
                        hist_dict["short_pnl"].append(broker._short_realised_pnl)
                        hist_dict["open_interest"].append(broker._open_interest)
                        # TODO - check timezone below
                        hist_dict["time"].append(datetime.now(timezone.utc))

                        # Dump history file to pickle
                        # TODO - check pickle bool?
                        with open(f".paper_broker_hist", "wb") as file:
                            pickle.dump(self._broker_histories, file)

                        time.sleep(sleep_time)
                except Exception as e:
                    print(e)
            else:
                if int(self._verbosity) > 0:
                    print("Broker update thread killed.")

    def shutdown(self):
        """Shutdown the active AutoTrader instance."""

        if int(self._verbosity) > 0 and self._backtest_mode:
            backtest_end_time = timeit.default_timer()

        # Kill broker update thread
        self._maintain_broker_thread = False

        # Run strategy-specific shutdown routines
        for bot in self._bots_deployed:
            bot._strategy_shutdown()

        # Run instance shut-down routine
        if self._backtest_mode:
            # Create overall backtest results
            if len(self._bots_deployed) == 1:
                price_history = self._bots_deployed[0].data
            else:
                price_history = None
            self.trade_results = TradeAnalysis(
                broker=self._broker,
                broker_histories=self._broker_histories,
                price_history=price_history,
            )

            # Create trade results for each bot
            for bot in self._bots_deployed:
                bot._create_trade_results(broker_histories=self._broker_histories)

            if int(self._verbosity) > 0:
                print(
                    "Backtest complete (runtime "
                    + f"{round((backtest_end_time - self._backtest_start_time), 3)} s)."
                )
                self.print_trade_results()

            if self._show_plot and len(self.trade_results.trade_history) > 0:
                self.plot_backtest()

        elif self._scan_mode and self._show_plot:
            # Show plots for scanned instruments
            for bot in self._bots_deployed:
                ap = self._instantiate_autoplot(bot.data)
                ap.plot(indicators=bot.strategy.indicators, instrument=bot.instrument)
                time.sleep(0.3)

        else:
            # Live trade complete, run livetrade specific shutdown routines
            if self._broker_name.lower() == "ib":
                self._broker._disconnect()

            elif self._papertrading:
                # Paper trade through virtual broker
                self.trade_results = TradeAnalysis(
                    broker=self._broker, broker_histories=self._broker_histories
                )
                self.print_trade_results(self.trade_results)

                picklefile_list = [
                    config["picklefile"] if config["picklefile"] is not None else ""
                    for _, config in self._virtual_broker_config.items()
                ]
                picklefiles = "\n ".join(picklefile_list)
                check_str = picklefiles.strip().split("\n")
                if len(check_str) > 1 or check_str[0] != "":
                    print(
                        f"\nThe following pickle files have been created:\n {picklefiles}"
                        + "\nUse the `unpickle_broker` utility to access these."
                    )

                # Plotting
                if self._show_plot:
                    ap = self._instantiate_autoplot()
                    ap._portfolio_plot(self.trade_results)

    def _trade_update_loop(self):
        """Runs the mode-dependent trade update loop."""
        if int(self._verbosity) > 0 and self._backtest_mode:
            print("\nTrading...\n")
            self._backtest_start_time = timeit.default_timer()

        if len(self._bots_deployed) == 0:
            # No strategy was added; manual trading
            broker_thread = Thread(target=self._manualtrade)
            broker_thread.start()

        else:
            # Automated trading
            if self._run_mode.lower() == "continuous":
                # Running in continuous update mode
                if self._backtest_mode:
                    # Backtesting
                    end_time = self._data_end  # datetime
                    timestamp = self._data_start + self._warmup_period  # datetime
                    pbar = tqdm(
                        total=int((self._data_end - timestamp).total_seconds()),
                        position=0,
                        leave=True,
                    )
                    while timestamp <= end_time:
                        # Update each bot with latest data to generate signal
                        for bot in self._bots_deployed:
                            bot._update(timestamp=timestamp)

                        # Update histories
                        for name, broker in self._brokers_dict.items():
                            hist_dict = self._broker_histories[name]
                            hist_dict["NAV"].append(broker._NAV)
                            hist_dict["equity"].append(broker._equity)
                            hist_dict["margin"].append(broker._margin_available)
                            hist_dict["open_interest"].append(broker._open_interest)
                            hist_dict["long_exposure"].append(broker._long_exposure)
                            hist_dict["short_exposure"].append(broker._short_exposure)
                            hist_dict["long_unrealised_pnl"].append(
                                broker._long_unrealised_pnl
                            )
                            hist_dict["short_unrealised_pnl"].append(
                                broker._short_unrealised_pnl
                            )
                            hist_dict["long_pnl"].append(broker._long_realised_pnl)
                            hist_dict["short_pnl"].append(broker._short_realised_pnl)
                            hist_dict["time"].append(timestamp)

                        # Iterate through time
                        timestamp += self._timestep
                        pbar.update(self._timestep.total_seconds())
                    pbar.close()

                else:
                    # Live trading
                    instance_id = self._get_instance_id()
                    instance_str = (
                        f"autotrader_instance_{instance_id}"
                        if self._instance_str is None
                        else self._instance_str
                    )
                    instance_file_exists = self._check_instance_file(instance_str, True)

                    # Get deploy timestamp
                    if self._deploy_time is not None:
                        deploy_time = self._deploy_time.timestamp()
                        if self._verbosity > 0 and datetime.now() < self._deploy_time:
                            print(f"\nDeploying bots at {self._deploy_time}.")

                    else:
                        deploy_time = time.time()

                    # Wait until deployment time
                    while datetime.now().timestamp() < deploy_time - 0.5:
                        time.sleep(0.5)

                    while instance_file_exists:
                        # Bot instance file exists
                        if self._verbosity > 0:
                            print(f"\nUpdating trading bots.")

                        try:
                            # Update bots
                            # TODO - threadpool executor
                            for bot in self._bots_deployed:
                                try:
                                    # TODO - why UTC? Allow setting manually
                                    bot._update(timestamp=datetime.now(timezone.utc))

                                    if int(self._verbosity) > 0:
                                        print(
                                            f"\nBot update complete: {bot._strategy_name}"
                                        )

                                except:
                                    if int(self._verbosity) > 0:
                                        print(
                                            "Error: failed to update bot running "
                                            + f"{bot._strategy_name} ({bot.instrument})"
                                        )
                                        traceback.print_exc()

                            if self._papertrading:
                                # Update broker histories
                                for name, broker in self._brokers_dict.items():
                                    hist_dict = self._broker_histories[name]
                                    hist_dict["NAV"].append(broker._NAV)
                                    hist_dict["equity"].append(broker._equity)
                                    hist_dict["margin"].append(broker._margin_available)
                                    hist_dict["long_exposure"].append(
                                        broker._long_exposure
                                    )
                                    hist_dict["short_exposure"].append(
                                        broker._short_exposure
                                    )
                                    hist_dict["long_unrealised_pnl"].append(
                                        broker._long_unrealised_pnl
                                    )
                                    hist_dict["short_unrealised_pnl"].append(
                                        broker._short_unrealised_pnl
                                    )
                                    hist_dict["long_pnl"].append(
                                        broker._long_realised_pnl
                                    )
                                    hist_dict["short_pnl"].append(
                                        broker._short_realised_pnl
                                    )
                                    hist_dict["open_interest"].append(
                                        broker._open_interest
                                    )
                                    # TODO - check timezone below
                                    hist_dict["time"].append(datetime.now(timezone.utc))

                                # Dump history file to pickle
                                # TODO - check pickle bool?
                                with open(f".paper_broker_hist", "wb") as file:
                                    pickle.dump(self._broker_histories, file)

                            # Go to sleep until next update
                            sleep_time = self._timestep.total_seconds() - (
                                (time.time() - deploy_time)
                                % self._timestep.total_seconds()
                            )
                            if int(self._verbosity) > 0:
                                print(
                                    f"AutoTrader sleeping until next update at {datetime.now()+timedelta(seconds=sleep_time)}."
                                )
                            time.sleep(sleep_time)

                            # Check if instance file still exists
                            instance_file_exists = self._check_instance_file(
                                instance_str
                            )

                        except KeyboardInterrupt:
                            print("\nKilling bot(s).")
                            instance_filepath = os.path.join(
                                self._home_dir, "active_bots", instance_str
                            )
                            try:
                                os.remove(instance_filepath)
                            except FileNotFoundError:
                                print(f"Intance file '{instance_str}' already deleted.")
                            break

            elif self._run_mode.lower() == "periodic":
                # Trading in periodic update mode
                if self._backtest_mode:
                    # Backtesting
                    self._check_bot_data()
                    start_range, end_range = self._bots_deployed[
                        0
                    ]._get_iteration_range()
                    for i in range(start_range, end_range):
                        # Update each bot with latest data to generate signal
                        for bot in self._bots_deployed:
                            bot._update(i=i)

                        # Update histories
                        for name, broker in self._brokers_dict.items():
                            hist_dict = self._broker_histories[name]
                            hist_dict["NAV"].append(broker._NAV)
                            hist_dict["equity"].append(broker._equity)
                            hist_dict["margin"].append(broker._margin_available)
                            hist_dict["open_interest"].append(broker._open_interest)
                            hist_dict["long_exposure"].append(broker._long_exposure)
                            hist_dict["short_exposure"].append(broker._short_exposure)
                            hist_dict["long_unrealised_pnl"].append(
                                broker._long_unrealised_pnl
                            )
                            hist_dict["short_unrealised_pnl"].append(
                                broker._short_unrealised_pnl
                            )
                            hist_dict["long_pnl"].append(broker._long_realised_pnl)
                            hist_dict["short_pnl"].append(broker._short_realised_pnl)
                            hist_dict["time"].append(broker._latest_time)

                else:
                    # Live trading
                    for bot in self._bots_deployed:
                        bot._update(i=-1)  # Process most recent signal

            # Run shutdown routines
            self.shutdown()

    @staticmethod
    def papertrade_snapshot(
        broker_picklefile: str = ".virtual_broker",
        history_picklefile: str = ".paper_broker_hist",
    ):
        """Prints a snapshot of the virtual broker from a single pickle. and
        returns the TradeAnalysis object."""
        broker = unpickle_broker(broker_picklefile)
        with open(history_picklefile, "rb") as file:
            broker_hist = pickle.load(file)

        # Extract relevant broker history

        # TODO - review functionality for multiple brokers: will need to pass
        # in as dict. Consider pickling self._brokers_dict

        results = TradeAnalysis(broker, broker_hist)
        at = AutoTrader()
        at.print_trade_results(results)
        return results

    def save_state(self):
        """Dumps the current AutoTrader instance to a pickle."""
        instance_id = self._get_instance_id(dir_name="pickled_instances")

        instance_name = (
            f"autotrader_instance_{instance_id}"
            if self._instance_str is None
            else self._instance_str
        )
        instance_file_exists = self._check_instance_file(
            instance_str=instance_name, dir_name="pickled_instances", live_check=False
        )

        write = "y"
        if instance_file_exists:
            # The file already exists, check to overwrite
            write = input(
                f"The instance file '{instance_name}' already "
                + "exists. Would you like to overwrite it? ([y]/n)  "
            )

        if "y" in write.lower():
            # Write to file
            try:
                filepath = f"pickled_instances/{instance_name}"
                with open(filepath, "wb") as file:
                    pickle.dump(self, file)
            except pickle.PicklingError:
                print("Error - cannot pickle this AutoTrader instance.")

    @staticmethod
    def load_state(instance_name, verbosity: int = 0):
        """Loads a pickled AutoTrader instance from file."""
        try:
            filepath = f"pickled_instances/{instance_name}"
            with open(filepath, "rb") as file:
                at = pickle.load(file)
            return at
        except Exception as e:
            print(f"Something went wrong while tring to load '{instance_name}'.")

            if verbosity > 0:
                print("Exception:", e)
