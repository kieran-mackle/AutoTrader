import os
import importlib
import traceback
from datetime import datetime
from autotrader.strategy import Strategy
from autotrader.brokers.trading import Order
from autotrader.brokers.broker import Broker
from typing import TYPE_CHECKING, Literal, Union
from autotrader.utilities import TradeAnalysis, get_logger
from autotrader.brokers.virtual import Broker as VirtualBroker

if TYPE_CHECKING:
    from autotrader import AutoTrader
    from autotrader.comms.notifier import Notifier


class AutoTraderBot:
    """AutoTrader Trading Bot, responsible for a trading strategy."""

    def __init__(
        self,
        instrument: str,
        strategy_dict: dict,
        broker: Union[dict[str, Broker], Broker],
        autotrader_instance: "AutoTrader",
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

        autotrader_instance : AutoTrader
            The parent AutoTrader instance.

        Raises
        ------
        Exception
            When there is an error retrieving the instrument data.
        """
        # Type hint inherited attributes
        self._multiple_brokers: bool
        self._global_config_dict: dict[str, any]
        self._environment: Literal["paper", "live"]
        self._broker_name: str
        self._feed: str
        self._base_currency: str
        self._data_path_mapper: dict
        self._backtest_mode: bool
        self._data_directory: str
        self._papertrading: bool
        self._scan_mode: bool
        self._notify: int
        self._verbosity: int
        self._notifier: "Notifier"
        self._virtual_tradeable_instruments: dict[str, list[str]]
        self._logger_kwargs: dict
        self._data_start: datetime
        self._data_end: datetime
        self._dynamic_data: bool

        # Inherit user options from autotrader
        for attribute, value in autotrader_instance.__dict__.items():
            setattr(self, attribute, value)

        # Create autobot logger
        self.logger = get_logger(name="autobot", **self._logger_kwargs)

        # Assign local attributes
        self.instrument = instrument
        self._broker: Broker = broker

        # Define execution framework
        if self._execution_method is None:
            self._execution_method = self._submit_order

        # Check for muliple brokers and construct mapper
        if self._multiple_brokers:
            # Trading across multiple venues
            self._brokers: list[Broker] = self._broker
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

        # Check for portfolio strategy
        trade_portfolio = (
            strategy_config["PORTFOLIO"] if "PORTFOLIO" in strategy_config else False
        )

        portfolio = strategy_config["WATCHLIST"] if trade_portfolio else False

        # Initialise the broker with a cache of data, if backtesting over
        # full dataset, or otherwise just the window specified in the strategy.
        # Initialise broker datasets
        for instrument, brokers in self._instrument_to_broker.items():
            for broker in brokers:
                broker._initialise_data(
                    **{
                        "instrument": instrument,
                        "data_start": self._data_start,
                        "data_end": self._data_end,
                        "granularity": interval,
                    }
                )

        # Build strategy instantiation arguments
        strategy_inputs = {
            "parameters": params,
            "instrument": self.instrument,
            "broker": self._broker,
            "notifier": self._notifier,
        }

        # Instantiate Strategy
        my_strat: Strategy = strategy(**strategy_inputs)

        # Assign strategy to local attributes
        self._last_bars = None
        self._strategy = my_strat
        self._strategy_name = (
            strategy_config["NAME"]
            if "NAME" in strategy_config
            else "(unnamed strategy)"
        )

        # Assign stop trading method to strategy
        self._strategy.stop_trading = autotrader_instance._remove_instance_file

        # Call indicators plotting method
        if self._backtest_mode:
            data = self._broker._data_cache[self.instrument]
            my_strat.create_plotting_indicators(data)

        # Assign strategy attributes for tick-based strategy development
        # TODO - improve type hints using strategy base class
        if self._backtest_mode:
            self._strategy._backtesting = True
            self.trade_results = None
        if interval.split(",")[0] == "tick":
            self._strategy._tick_data = True

    def __repr__(self):
        if isinstance(self.instrument, list):
            return "Portfolio AutoTraderBot"
        else:
            return f"{self.instrument} AutoTraderBot"

    def __str__(self):
        return "AutoTraderBot instance"

    def _update(self, timestamp: datetime) -> None:
        """Update strategy with the latest data and generate a trade signal.

        Parameters
        ----------
        timestamp : datetime, optional
            The current update time.
        """
        if self._backtest_mode or self._papertrading:
            # Update virtual broker
            self._update_virtual_broker(dt=timestamp)

        # Call strategy for orders
        try:
            strategy_orders = self._strategy.generate_signal(timestamp)
        except Exception as e:
            self.logger.error(f"Error when updating strategy: {e}")
            self.logger.info(traceback.format_exc())
            strategy_orders = []

        # Check and qualify orders
        orders = self._check_orders(strategy_orders)
        self._qualify_orders(orders)

        if not self._scan_mode:
            # Submit orders
            for order in orders:
                # Submit order to relevant exchange
                try:
                    self._execution_method(
                        broker=self._brokers[order.exchange],
                        order=order,
                        order_time=timestamp,
                    )
                except Exception as e:
                    traceback_str = "".join(traceback.format_tb(e.__traceback__))
                    exception_str = f"AutoTrader exception when submitting order: {e}"
                    print_str = exception_str + "\nTraceback:\n" + traceback_str
                    self.logger.error(print_str)

        # If paper trading, update virtual broker again to trigger any orders
        if self._papertrading:
            self._update_virtual_broker(dt=timestamp)

        # Log message
        current_time = timestamp.strftime("%b %d %Y %H:%M:%S")
        if len(orders) > 0:
            for order in orders:
                direction = "long" if order.direction > 0 else "short"
                order_string = (
                    f"{current_time}: {order.instrument} "
                    + f"{direction} {order.order_type} order of "
                    + f"{order.size} units placed."
                )
                self.logger.info(order_string)
        else:
            self.logger.debug(
                f"{current_time}: No signal detected ({self.instrument})."
            )

        # Check for orders placed and/or scan hits
        if int(self._notify) > 0 and not (self._backtest_mode or self._scan_mode):
            # TODO - what is this conditional?
            for order in orders:
                self._notifier.send_order(order)

        # Check scan results
        if self._scan_mode:
            # Report AutoScan results
            if int(self._verbosity) > 0 or int(self._notify) == 0:
                # Scan reporting with no notifications requested
                if len(orders) == 0:
                    print(f"{self.instrument}: No signal detected.")

                else:
                    # Scan detected hits
                    print("Scan hits:")
                    for order in orders:
                        print(order)

            if int(self._notify) > 0:
                # Notifications requested
                for order in orders:
                    self._notifier.send_message(f"Scan hit: {order}")

    def _check_orders(self, orders) -> list[Order]:
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

        def add_strategy_data(orders: list[Order]):
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

        def check_order_details(orders: list[Order]) -> None:
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

                if order.size is None and order.order_type != "modify":
                    raise Exception("Must provide order size.")

        # Perform checks
        if orders is not None:
            checked_orders = check_type(orders)
            add_strategy_data(checked_orders)
            check_order_details(checked_orders)
            return checked_orders
        else:
            # Return empty list
            return []

    def _qualify_orders(self, orders: list[Order]) -> None:
        """Prepare orders for submission."""
        for order in orders:
            # Get relevant broker
            broker: Broker = self._brokers[order.exchange]

            # Determine current price to assign to order
            if self._feed != "none":
                # Get order price from current orderbook
                orderbook = broker.get_orderbook(
                    instrument=order.instrument,
                )

                # Check order type to assign variables
                if order.direction < 0:
                    order_price = orderbook.bids.loc[0]["price"]
                else:
                    order_price = orderbook.asks.loc[0]["price"]

            else:
                # Do not provide order price yet
                order_price = None

            # Call order to update
            order(order_price=order_price)

    def _update_virtual_broker(self, dt: datetime) -> None:
        """Updates the virtual broker state. Only called when backtesting or paper trading."""
        for instrument, brokers in self._instrument_to_broker.items():
            for broker in brokers:
                broker: VirtualBroker
                broker._update_positions(instrument=instrument, dt=dt)

    def _create_trade_results(self, broker_histories: dict) -> dict:
        """Constructs bot-specific trade summary for post-processing."""
        trade_results = TradeAnalysis(self._broker, broker_histories, self.instrument)
        trade_results.indicators = (
            self._strategy.indicators if hasattr(self._strategy, "indicators") else None
        )
        trade_results.data = self._broker._data_cache[self.instrument]
        trade_results.interval = self._strategy_params["granularity"]
        self.trade_results = trade_results

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
            plot_data = self._broker.get_candles(instrument=self.instrument)

        return plot_data

    def _strategy_shutdown(
        self,
    ):
        """Perform the strategy shutdown routines, if they exist."""
        if self._strategy_shutdown_method is not None:
            try:
                shutdown_method = getattr(
                    self._strategy, self._strategy_shutdown_method
                )
                shutdown_method()
            except AttributeError:
                self.logger.error(
                    f"\nShutdown method '{self._strategy_shutdown_method}' not found!"
                )

    @staticmethod
    def _submit_order(broker: Broker, order: Order, *args, **kwargs):
        "The default order execution method."
        broker.place_order(order, *args, **kwargs)
