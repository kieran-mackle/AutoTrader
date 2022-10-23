import os
import importlib
import traceback
import pandas as pd
from datetime import datetime, timezone
from autotrader.autodata import AutoData
from autotrader.brokers.trading import Order
from concurrent.futures import ThreadPoolExecutor
from autotrader.utilities import get_data_config, TradeAnalysis


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
    backtest_results : TradeAnalysis
        A class containing results from the bot in backtest. This
        is available only after a backtest.
    """

    def __init__(
        self,
        instrument: str,
        strategy_dict: dict,
        broker,
        deploy_dt: datetime,
        data_dict: dict,
        quote_data_path: str,
        auxdata: dict,
        autotrader_instance,
    ) -> None:
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

        # Assign local attributes
        self.instrument = instrument
        self._broker = broker

        # # Define execution framework
        if self._execution_method is None:
            self._execution_method = self._submit_order

        # Check for muliple brokers and construct mapper
        if self._multiple_brokers:
            # Trading across multiple venues
            self._brokers = self._broker
            self._instrument_to_broker = {}
            for (
                broker_name,
                tradeable_instruments,
            ) in self._virtual_tradeable_instruments.items():
                for instrument in tradeable_instruments:
                    if instrument in self._instrument_to_broker:
                        # Instrument is already in mapper, add broker
                        self._instrument_to_broker[instrument].append(
                            self._brokers[broker_name]
                        )
                    else:
                        # New instrument, add broker
                        self._instrument_to_broker[instrument] = [
                            self._brokers[broker_name]
                        ]

        else:
            # Trading through a single broker
            self._brokers = {self._broker_name: self._broker}

            # Map instruments to broker
            self._instrument_to_broker = {}
            instruments = [instrument] if isinstance(instrument, str) else instrument
            for instrument in instruments:
                self._instrument_to_broker[instrument] = [self._broker]

        # Unpack strategy parameters and assign to strategy_params
        strategy_config = strategy_dict["config"]
        interval = strategy_config["INTERVAL"]
        period = strategy_config["PERIOD"]
        risk_pc = strategy_config["RISK_PC"] if "RISK_PC" in strategy_config else None
        sizing = strategy_config["SIZING"] if "SIZING" in strategy_config else None
        params = (
            strategy_config["PARAMETERS"] if "PARAMETERS" in strategy_config else {}
        )
        strategy_params = params
        strategy_params["granularity"] = (
            strategy_params["granularity"]
            if "granularity" in strategy_params
            else interval
        )
        strategy_params["risk_pc"] = (
            strategy_params["risk_pc"] if "risk_pc" in strategy_params else risk_pc
        )
        strategy_params["sizing"] = (
            strategy_params["sizing"] if "sizing" in strategy_params else sizing
        )
        strategy_params["period"] = (
            strategy_params["period"] if "period" in strategy_params else period
        )
        strategy_params["INCLUDE_POSITIONS"] = (
            strategy_config["INCLUDE_POSITIONS"]
            if "INCLUDE_POSITIONS" in strategy_config
            else False
        )
        strategy_config["INCLUDE_BROKER"] = (
            strategy_config["INCLUDE_BROKER"]
            if "INCLUDE_BROKER" in strategy_config
            else False
        )
        strategy_config["INCLUDE_STREAM"] = (
            strategy_config["INCLUDE_STREAM"]
            if "INCLUDE_STREAM" in strategy_config
            else False
        )
        self._strategy_params = strategy_params

        # Import Strategy
        if strategy_dict["class"] is not None:
            strategy = strategy_dict["class"]
        else:
            strat_module = strategy_config["MODULE"]
            strat_name = strategy_config["CLASS"]
            strat_package_path = os.path.join(self._home_dir, "strategies")
            strat_module_path = os.path.join(strat_package_path, strat_module) + ".py"
            strat_spec = importlib.util.spec_from_file_location(
                strat_module, strat_module_path
            )
            strategy_module = importlib.util.module_from_spec(strat_spec)
            strat_spec.loader.exec_module(strategy_module)
            strategy = getattr(strategy_module, strat_name)

        # Strategy shutdown routine
        self._strategy_shutdown_method = strategy_dict["shutdown_method"]

        # Get data feed configuration
        data_config = get_data_config(
            feed=self._feed,
            global_config=self._global_config_dict,
            environment=self._environment,
        )

        # Data retrieval
        self._quote_data_file = quote_data_path  # Either str or None
        self._data_filepaths = data_dict  # Either str or dict, or None
        self._auxdata_files = auxdata  # Either str or dict, or None

        if self._feed == "none":
            # None data-feed being used, allow duplicate bars
            self._allow_duplicate_bars = True

        # Check for portfolio strategy
        trade_portfolio = (
            strategy_config["PORTFOLIO"] if "PORTFOLIO" in strategy_config else False
        )

        portfolio = strategy_config["WATCHLIST"] if trade_portfolio else False

        # Fetch data
        self._get_data = AutoData(
            data_config, self._allow_dancing_bears, self._base_currency
        )

        # Create instance of data stream object
        stream_attributes = {
            "data_filepaths": self._data_filepaths,
            "quote_data_file": self._quote_data_file,
            "auxdata_files": self._auxdata_files,
            "strategy_params": self._strategy_params,
            "get_data": self._get_data,
            "data_start": self._data_start,
            "data_end": self._data_end,
            "instrument": self.instrument,
            "feed": self._feed,
            "portfolio": portfolio,
            "data_path_mapper": self._data_path_mapper,
            "data_dir": self._data_directory,
            "backtest_mode": self._backtest_mode,
        }
        self.Stream = self._data_stream_object(**stream_attributes)

        # Initial data call
        self._refresh_data(deploy_dt)

        # Instantiate Strategy
        strategy_inputs = {
            "parameters": params,
            "data": self._strat_data,
            "instrument": self.instrument,
        }

        if strategy_config["INCLUDE_BROKER"]:
            strategy_inputs["broker"] = self._broker
            strategy_inputs["broker_utils"] = self._broker_utils

        if strategy_config["INCLUDE_STREAM"]:
            strategy_inputs["data_stream"] = self.Stream

        my_strat = strategy(**strategy_inputs)

        # Assign strategy to local attributes
        self._last_bars = None
        self._strategy = my_strat
        self._strategy_name = (
            strategy_config["NAME"]
            if "NAME" in strategy_config
            else "(unnamed strategy)"
        )

        # Assign strategy attributes for tick-based strategy development
        if self._backtest_mode:
            self._strategy._backtesting = True
            self.trade_results = None
        if interval.split(",")[0] == "tick":
            self._strategy._tick_data = True

    def __repr__(self):
        # TODO - alter str for portfolio bots
        if isinstance(self.instrument, list):
            return "Portfolio AutoTraderBot"
        else:
            return f"{self.instrument} AutoTraderBot"

    def __str__(self):
        return "AutoTraderBot instance"

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

        if self._run_mode == "continuous":
            # Running in continuous update mode
            strat_data, current_bars, quote_bars, sufficient_data = self._check_data(
                timestamp, self._data_indexing
            )
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
            # There is a sufficient amount of data, and it includes new data
            if self._backtest_mode or self._papertrading:
                # Update virtual broker with latest price bars
                self._update_virtual_broker(current_bars)

            # Get strategy orders
            strategy_orders = self._strategy.generate_signal(strat_object)

            # Check and qualify orders
            orders = self._check_orders(strategy_orders)
            self._qualify_orders(orders, current_bars, quote_bars)

            if not self._scan_mode:
                # Submit orders
                if self._max_workers is not None:
                    workers = min(self._max_workers, len(orders))
                else:
                    workers = None
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = []
                    for order in orders:
                        try:
                            order_time = current_bars[order.instrument].name
                        except:
                            if self._feed == "none":
                                order_time = datetime.now(timezone.utc)
                            else:
                                order_time = current_bars[order.data_name].name

                        # Submit order to relevant exchange
                        futures.append(
                            executor.submit(
                                self._execution_method,
                                broker=self._brokers[order.exchange],
                                order=order,
                                order_time=order_time,
                            )
                        )

                # Check for exceptions
                for f in futures:
                    try:
                        f.result()
                    except Exception as e:
                        traceback_str = "".join(traceback.format_tb(e.__traceback__))
                        exception_str = (
                            f"AutoTrader exception when submitting order: {e}"
                        )
                        print_str = exception_str + "\nTraceback:\n" + traceback_str
                        print(print_str)

            if self._papertrading:
                # Update virtual broker again to trigger any orders
                self._update_virtual_broker(current_bars)

            if int(self._verbosity) > 1:
                try:
                    current_time = current_bars[
                        list(current_bars.keys())[0]
                    ].name.strftime("%b %d %Y %H:%M:%S")
                except:
                    current_time = datetime.now().strftime("%b %d %Y %H:%M:%S")
                if len(orders) > 0:
                    for order in orders:
                        direction = "long" if order.direction > 0 else "short"
                        order_string = (
                            f"{current_time}: {order.instrument} "
                            + f"{direction} {order.order_type} order of "
                            + f"{order.size} units placed."
                        )
                        print(order_string)
                else:
                    if int(self._verbosity) > 2:
                        print(
                            f"{current_time}: No signal detected ({self.instrument})."
                        )

            # Check for orders placed and/or scan hits
            if int(self._notify) > 0 and not (self._backtest_mode or self._scan_mode):
                for order in orders:
                    self._notifier.send_order(order)

            # Check scan results
            if self._scan_mode:
                # Report AutoScan results
                if int(self._verbosity) > 0 or int(self._notify) == 0:
                    # Scan reporting with no notifications requested
                    if len(orders) == 0:
                        print("{}: No signal detected.".format(self.instrument))

                    else:
                        # Scan detected hits
                        print("Scan hits:")
                        for order in orders:
                            print(order)

                if int(self._notify) > 0:
                    # Notifications requested
                    for order in orders:
                        self._notifier.send_message(f"Scan hit: {order}")

        else:
            if int(self._verbosity) > 1:
                print(
                    "\nThe strategy has not been updated as there is either "
                    + "insufficient data, or no new data. If you believe "
                    + "this is an error, try setting allow_dancing_bears to "
                    + "True, or set allow_duplicate_bars to True in "
                    + "AutoTrader.configure().\n"
                    + f"Sufficient data: {sufficient_data}\n"
                    + f"New data: {new_data}"
                )

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
        if self._feed != "none" and len(data) == 0:
            raise Exception("Error retrieving data.")

        # Data assignment
        if multi_data is None:
            strat_data = data
        else:
            strat_data = multi_data

        # Auxiliary data assignment
        if auxdata is not None:
            strat_data = {"base": strat_data, "aux": auxdata}

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
                if "order_type" in orders:
                    # Single order dict provided
                    if "instrument" not in orders:
                        orders["instrument"] = self.instrument
                    checked_orders.append(Order._from_dict(orders))

                elif len(orders) > 0:
                    # Multiple orders provided
                    for key, item in orders.items():
                        if isinstance(item, dict) and "order_type" in item:
                            # Convert order dict to Order object
                            if "instrument" not in item:
                                item["instrument"] = self.instrument
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
                    if isinstance(item, dict) and "order_type" in item:
                        # Convert order dict to Order object
                        if "instrument" not in item:
                            item["instrument"] = self.instrument
                        checked_orders.append(Order._from_dict(item))
                    elif isinstance(item, Order):
                        # Native Order object, append as is
                        checked_orders.append(item)
                    else:
                        raise Exception(f"Invalid order submitted: {item}")
            else:
                raise Exception(f"Invalid order/s submitted: '{orders}' received")

            return checked_orders

        def add_strategy_data(orders):
            # Append strategy parameters to each order
            for order in orders:
                order.instrument = (
                    self.instrument if not order.instrument else order.instrument
                )
                order.strategy = (
                    self._strategy.name
                    if "name" in self._strategy.__dict__
                    else self._strategy_name
                )
                order.granularity = self._strategy_params["granularity"]
                order._sizing = self._strategy_params["sizing"]
                order._risk_pc = self._strategy_params["risk_pc"]

        def check_order_details(orders: list) -> None:
            # Check details for order type have been provided
            for ix, order in enumerate(orders):
                order.instrument = (
                    order.instrument
                    if order.instrument is not None
                    else self.instrument
                )
                if order.order_type in ["market", "limit", "stop-limit", "reduce"]:
                    if not order.direction:
                        # Order direction was not provided, delete order
                        del orders[ix]
                        continue

                # Check that an exchange has been specified
                if order.exchange is None:
                    # Exchange not specified
                    if self._multiple_brokers:
                        # Trading across multiple venues
                        raise Exception(
                            "The exchange to which an order is to be "
                            + "submitted must be specified when trading across "
                            + "multiple venues. Please include the 'exchange' "
                            + "argument when creating an order."
                        )
                    else:
                        # Trading on single venue, auto fill
                        order.exchange = self._broker_name

        # Perform checks
        checked_orders = check_type(orders)
        add_strategy_data(checked_orders)
        check_order_details(checked_orders)

        return checked_orders

    def _qualify_orders(
        self, orders: list, current_bars: dict, quote_bars: dict
    ) -> None:
        """Passes price data to order to populate missing fields."""

        for order in orders:
            # Get relevant broker
            broker = self._brokers[order.exchange]

            # Fetch precision for instrument
            try:
                precision = broker._utils.get_precision(order.instrument)
            except Exception as e:
                # Print exception
                print("AutoTrader exception when qualifying order:", e)

                # Skip this order
                continue

            if self._feed != "none":
                # Get order price from current bars
                if self._req_liveprice:
                    # Fetch current price
                    liveprice_func = getattr(
                        self._get_data, f"_{self._feed.lower()}_liveprice"
                    )
                    last_price = liveprice_func(order)
                else:
                    # Fetch pseudo-current price
                    try:
                        # Use instrument
                        last_price = self._get_data._pseduo_liveprice(
                            last=current_bars[order.instrument].Close,
                            quote_price=quote_bars[order.instrument].Close,
                        )
                    except:
                        # Use data name
                        last_price = self._get_data._pseduo_liveprice(
                            last=current_bars[order.data_name].Close,
                            quote_price=quote_bars[order.data_name].Close,
                        )

                if order.order_type not in ["close", "reduce", "modify"]:
                    if order.direction < 0:
                        order_price = last_price["bid"]
                        HCF = last_price["negativeHCF"]
                    else:
                        order_price = last_price["ask"]
                        HCF = last_price["positiveHCF"]
                else:
                    # Close, reduce or modify order type, provide dummy inputs
                    order_price = last_price["ask"]
                    HCF = last_price["positiveHCF"]

            else:
                # Do not provide order price yet
                order_price = None
                HCF = None

            # Call order to update
            order(broker=broker, order_price=order_price, HCF=HCF, precision=precision)

    def _update_virtual_broker(self, current_bars: dict) -> None:
        """Updates virtual broker with latest price data."""
        # TODO - the conditional here should allow specifically updating by L1,
        # not only when feed=none
        if self._feed == "none":
            # None data feed provided, use L1 to update
            for instrument, brokers in self._instrument_to_broker.items():
                for broker in brokers:
                    broker._update_instrument(instrument)

        else:
            # Using OHLC data feed
            for product, bar in current_bars.items():
                brokers = self._instrument_to_broker[product]
                for broker in brokers:
                    broker._update_positions(instrument=product, candle=bar)

    def _create_trade_results(self, broker_histories: dict) -> dict:
        """Constructs bot-specific trade summary for post-processing."""
        trade_results = TradeAnalysis(self._broker, broker_histories, self.instrument)
        trade_results.indicators = (
            self._strategy.indicators if hasattr(self._strategy, "indicators") else None
        )
        trade_results.data = self.data
        trade_results.interval = self._strategy_params["granularity"]
        self.trade_results = trade_results

    def _get_iteration_range(self) -> int:
        """Checks mode of operation and returns data iteration range. For backtesting,
        the entire dataset is iterated over. For livetrading, only the latest candle
        is used. ONLY USED IN BACKTESTING NOW.
        """
        start_range = self._strategy_params["period"]
        end_range = len(self.data)

        if len(self.data) < start_range:
            raise Exception(
                "There are not enough bars in the data to "
                + "run the backtest with the current strategy "
                + "configuration settings. Either extend the "
                + "backtest period, or reduce the PERIOD key of "
                + "your strategy configuration."
            )

        return start_range, end_range

    @staticmethod
    def _check_ohlc_data(
        ohlc_data: pd.DataFrame,
        timestamp: datetime,
        indexing: str = "open",
        tail_bars: int = None,
        check_for_future_data: bool = True,
    ) -> pd.DataFrame:
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
            if indexing.lower() == "open":
                past_data = ohlc_data[ohlc_data.index < timestamp]
            elif indexing.lower() == "close":
                past_data = ohlc_data[ohlc_data.index <= timestamp]
            else:
                raise Exception(f"Unrecognised indexing type '{indexing}'.")
        else:
            past_data = ohlc_data

        if tail_bars is not None:
            past_data = past_data.tail(tail_bars)

        return past_data

    def _check_auxdata(
        self,
        auxdata: dict,
        timestamp: datetime,
        indexing: str = "open",
        tail_bars: int = None,
        check_for_future_data: bool = True,
    ) -> dict:
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
                processed_auxdata[key] = self._check_ohlc_data(
                    item, timestamp, indexing, tail_bars, check_for_future_data
                )
            else:
                processed_auxdata[key] = item
        return processed_auxdata

    def _check_data(self, timestamp: datetime, indexing: str = "open") -> dict:
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

        def get_current_bars(
            data: pd.DataFrame,
            quote_data: bool = False,
            processed_strategy_data: dict = None,
        ) -> dict:
            """Returns the current bars of data. If the inputted data is for
            quote bars, then the quote_data boolean will be True.
            """
            if len(data) > 0:
                current_bars = self.Stream.get_trading_bars(
                    data=data,
                    quote_bars=quote_data,
                    timestamp=timestamp,
                    processed_strategy_data=processed_strategy_data,
                )
            else:
                current_bars = None
            return current_bars

        def process_strat_data(original_strat_data, check_for_future_data):
            sufficient_data = True

            if isinstance(original_strat_data, dict):
                if "aux" in original_strat_data:
                    # Auxiliary data is being used
                    base_data = original_strat_data["base"]
                    processed_auxdata = self._check_auxdata(
                        original_strat_data["aux"],
                        timestamp,
                        indexing,
                        no_bars,
                        check_for_future_data,
                    )
                else:
                    # MTF data
                    base_data = original_strat_data

                # Process base OHLC data
                processed_basedata = {}
                if isinstance(base_data, dict):
                    # Base data is multi-timeframe; process each timeframe
                    for granularity, data in base_data.items():
                        processed_basedata[granularity] = self._check_ohlc_data(
                            data, timestamp, indexing, no_bars, check_for_future_data
                        )
                elif isinstance(base_data, pd.DataFrame) or isinstance(
                    base_data, pd.Series
                ):
                    # Base data is a timeseries already, check directly
                    processed_basedata = self._check_ohlc_data(
                        base_data, timestamp, indexing, no_bars, check_for_future_data
                    )

                # Combine the results of the conditionals above
                strat_data = {}
                if "aux" in original_strat_data:
                    strat_data["aux"] = processed_auxdata
                    strat_data["base"] = processed_basedata
                else:
                    strat_data = processed_basedata

                # Extract current bar
                first_tf_data = processed_basedata[list(processed_basedata.keys())[0]]
                current_bars = get_current_bars(
                    first_tf_data, processed_strategy_data=strat_data
                )

                # Check that enough bars have accumulated
                if len(first_tf_data) < no_bars:
                    sufficient_data = False

            elif isinstance(original_strat_data, pd.DataFrame):
                strat_data = self._check_ohlc_data(
                    original_strat_data,
                    timestamp,
                    indexing,
                    no_bars,
                    check_for_future_data,
                )
                current_bars = get_current_bars(
                    strat_data, processed_strategy_data=strat_data
                )

                # Check that enough bars have accumulated
                if len(strat_data) < no_bars:
                    sufficient_data = False

            elif original_strat_data is None:
                # Using none data
                strat_data = None
                current_bars = {}
                sufficient_data = True

            else:
                raise Exception("Unrecognised data type. Cannot process.")

            return strat_data, current_bars, sufficient_data

        # Define minimum number of bars for strategy to run
        no_bars = self._strategy_params["period"]

        if self._backtest_mode:
            check_for_future_data = True
            if self._dynamic_data:
                self._refresh_data(timestamp)
        else:
            # Livetrading
            self._refresh_data(timestamp)
            check_for_future_data = False

        strat_data, current_bars, sufficient_data = process_strat_data(
            self._strat_data, check_for_future_data
        )

        # Process quote data
        if isinstance(self.quote_data, dict):
            processed_quote_data = {}
            for instrument in self.quote_data:
                processed_quote_data[instrument] = self._check_ohlc_data(
                    self.quote_data[instrument],
                    timestamp,
                    indexing,
                    no_bars,
                    check_for_future_data,
                )
            quote_data = processed_quote_data[instrument]  # Dummy

        elif isinstance(self.quote_data, pd.DataFrame):
            quote_data = self._check_ohlc_data(
                self.quote_data, timestamp, indexing, no_bars, check_for_future_data
            )
            processed_quote_data = {self.instrument: quote_data}

        elif self.quote_data is None:
            # Using 'none' data feed
            quote_bars = current_bars
            return strat_data, current_bars, quote_bars, sufficient_data

        else:
            raise Exception("Unrecognised data type. Cannot process.")

        # Get quote bars
        quote_bars = get_current_bars(quote_data, True, processed_quote_data)

        return strat_data, current_bars, quote_bars, sufficient_data

    def _check_last_bar(self, current_bars: dict) -> bool:
        """Checks for new data to prevent duplicate signals."""
        if self._allow_duplicate_bars:
            new_data = True
        else:
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
        if "plot_data" in strat_params and use_strat_plot_data:
            plot_data = strat_params["plot_data"]
        else:
            plot_data = self.data

        return plot_data

    def _strategy_shutdown(
        self,
    ):
        if self._strategy_shutdown_method is not None:
            try:
                shutdown_method = getattr(
                    self._strategy, self._strategy_shutdown_method
                )
                shutdown_method()
            except AttributeError:
                print(
                    f"\nShutdown method '{self._strategy_shutdown_method}' not found!"
                )

    def _replace_data(self, data: pd.DataFrame) -> None:
        """Function to replace the data assigned locally and to the strategy.
        Called when there is a mismatch in data lengths during multi-instrument
        backtests in periodic update mode.
        """
        self.data = data
        self._strategy.data = data

    @staticmethod
    def _submit_order(broker, order, *args, **kwargs):
        "The default order execution method."
        broker.place_order(order, *args, **kwargs)
