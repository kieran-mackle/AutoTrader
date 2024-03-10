import os
import sys
import yaml
import time
import pickle
import logging
import autotrader
import numpy as np
import pandas as pd
from art import tprint
from abc import abstractmethod
from typing import Union, Optional
from datetime import datetime, timedelta
from prometheus_client import start_http_server, Gauge
from autotrader.brokers.broker import AbstractBroker, Broker

try:
    from ccxt_download.utilities import load_data
    from ccxt_download.constants import DEFAULT_DOWNLOAD_DIR, CANDLES
except:
    pass


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
    with open(filepath, "w") as outfile:
        yaml.dump(data, outfile, default_flow_style=False)


def print_banner():
    tprint("AutoTrader", font="tarty1")


def get_broker_config(
    broker: str,
    global_config: Optional[dict] = None,
    environment: Optional[str] = "paper",
) -> dict:
    """Returns a broker configuration dictionary.

    Parameters
    ----------
    broker : str
        The name(s) of the broker/exchange. Specify multiple exchanges using
        comma separation.

    global_config : dict
        The global configuration dictionary.

    environment : str, optional
        The trading evironment ('demo' or 'real').

    """
    all_config = {}
    inputted_brokers = broker.lower().replace(" ", "").split(",")

    # Check global_config
    if global_config is None:
        try:
            global_config = read_yaml("config/keys.yaml")
        except:
            pass

    for broker in inputted_brokers:
        # Check for CCXT
        if broker.split(":")[0].lower() == "ccxt":
            broker_key = broker
            broker, exchange = broker.lower().split(":")
        elif broker.split(":")[0].lower() == "virtual":
            broker_key = ":".join(broker.split(":")[1:])
            broker = "virtual"
        else:
            broker_key = broker

        supported_brokers = ["oanda", "ib", "ccxt", "virtual"]
        if broker.lower() not in supported_brokers:
            raise Exception(f"Unsupported broker: '{broker}'")

        if broker != "ccxt" and environment.lower() not in ["live", "paper"]:
            raise Exception("Trading environment must either be 'live' or 'paper'.")

        # Live trading
        if broker.lower() == "oanda":
            api_key = "LIVE" if environment.lower() == "live" else "PRACTICE"
            oanda_conf = global_config["OANDA"]

            # Initialise config dict
            config = {"PORT": oanda_conf["PORT"]}

            # Unpack
            if f"{api_key}_API" in oanda_conf:
                config["API"] = oanda_conf[f"{api_key}_API"]
            else:
                raise Exception(
                    f"Please define {api_key}_API in your "
                    + f"account configuration for {environment} trading."
                )

            if f"{api_key}_ACCESS_TOKEN" in oanda_conf:
                config["ACCESS_TOKEN"] = oanda_conf[f"{api_key}_ACCESS_TOKEN"]
            else:
                raise Exception(
                    f"Please define {api_key}_ACCESS_TOKEN in "
                    + f"your account configuration for {environment} trading."
                )

            config["ACCOUNT_ID"] = (
                oanda_conf["DEFAULT_ACCOUNT_ID"]
                if "custom_account_id" not in global_config
                else global_config["custom_account_id"]
            )

        elif broker.lower() == "ib":
            config = {
                "host": (
                    global_config["host"] if "host" in global_config else "127.0.0.1"
                ),
                "port": global_config["port"] if "port" in global_config else 7497,
                "clientID": (
                    global_config["clientID"] if "clientID" in global_config else 1
                ),
                "account": (
                    global_config["account"] if "account" in global_config else ""
                ),
                "read_only": (
                    global_config["read_only"]
                    if "read_only" in global_config
                    else False
                ),
            }

        elif broker.lower() == "ccxt":
            if global_config is not None and broker_key.upper() in global_config:
                # Use configuration provided in config
                config_data = global_config[broker_key.upper()]

            else:
                # Use public-only connection
                config_data = {}

            # Select config based on environment
            if environment.lower() in config_data:
                config_data = config_data[environment.lower()]
            elif "mainnet" in config_data and environment.lower() == "live":
                config_data = config_data["mainnet"]
            elif "testnet" in config_data and environment.lower() == "paper":
                config_data = config_data["testnet"]

            api_key = config_data["api_key"] if "api_key" in config_data else None
            secret = config_data["secret"] if "secret" in config_data else None
            currency = (
                config_data["base_currency"]
                if "base_currency" in config_data
                else "USDT"
            )
            sandbox_mode = False if environment.lower() == "live" else True
            config = {
                "data_source": "ccxt",
                "exchange": exchange,
                "api_key": api_key,
                "secret": secret,
                "sandbox_mode": sandbox_mode,
                "base_currency": currency,
            }
            other_args = {"options": {}, "password": None}
            for key, default_val in other_args.items():
                if key in config_data:
                    config[key] = config_data[key]
                else:
                    config[key] = default_val

        elif broker.lower() == "virtual":
            config = {}

        else:
            raise Exception(f"No configuration available for {broker}.")

        # Append to full config
        all_config[broker_key] = config

    # Check length
    if len(all_config) == 1:
        all_config = config

    return all_config


def get_data_config(feed: str, global_config: Optional[dict] = None, **kwargs) -> dict:
    """Returns a data configuration dictionary for AutoData.
    Parameters
    ----------
    feed : str
        The name of the data feed.

    global_config : dict
        The global configuration dictionary.
    """
    # TODO - review if this is needed - probably can merge with broker config above
    if feed is None:
        print("Please specify a data feed.")
        sys.exit(0)

    # Check for CCXT
    if feed.split(":")[0].lower() == "ccxt":
        feed, exchange = feed.lower().split(":")

    # Check feed
    supported_feeds = ["oanda", "ib", "ccxt", "yahoo", "local", "none"]
    if feed.lower() not in supported_feeds:
        raise Exception(f"Unsupported data feed: '{feed}'")

    # Check global_config
    if global_config is None:
        try:
            global_config = read_yaml("config/keys.yaml")
        except:
            pass

    # Check for required authentication
    auth_feeds = ["oanda", "ib"]
    if feed.lower() in auth_feeds and global_config is None:
        raise Exception(
            f"Data feed '{feed}' requires authentication. "
            + "Please provide authentication details in the global config."
        )

    # Construct configuration dict
    config = {"data_source": feed.lower()}

    if feed.lower() == "oanda":
        environment = kwargs["environment"] if "environment" in kwargs else "paper"
        api_key = "LIVE" if environment.lower() == "live" else "PRACTICE"
        oanda_conf = global_config["OANDA"]

        # Unpack
        if f"{api_key}_API" in oanda_conf:
            config["API"] = oanda_conf[f"{api_key}_API"]
        else:
            raise Exception(
                f"Please define {api_key}_API in your "
                + f"account configuration for {environment} trading."
            )

        if f"{api_key}_ACCESS_TOKEN" in oanda_conf:
            config["ACCESS_TOKEN"] = oanda_conf[f"{api_key}_ACCESS_TOKEN"]
        else:
            raise Exception(
                f"Please define {api_key}_ACCESS_TOKEN in "
                + f"your account configuration for {environment} trading."
            )

        config["PORT"] = oanda_conf["PORT"]
        config["ACCOUNT_ID"] = (
            oanda_conf["DEFAULT_ACCOUNT_ID"]
            if "custom_account_id" not in global_config
            else global_config["custom_account_id"]
        )

    elif feed.lower() == "ib":
        config["host"] = (
            global_config["host"] if "host" in global_config else "127.0.0.1"
        )
        config["port"] = global_config["port"] if "port" in global_config else 7497
        config["clientID"] = (
            global_config["clientID"] if "clientID" in global_config else 1
        )
        config["account"] = (
            global_config["account"] if "account" in global_config else ""
        )
        config["read_only"] = (
            global_config["read_only"] if "read_only" in global_config else False
        )

    elif feed.lower() == "ccxt":
        # Try add authentication with global config
        if global_config is not None:
            # Global config is available
            try:
                # Try get api keys
                environment = (
                    kwargs["environment"] if "environment" in kwargs else "paper"
                )
                config = get_broker_config(
                    broker=f"{feed.lower()}:{exchange}",
                    global_config=global_config,
                    environment=environment,
                )
            except:
                # Didn't work, just set exchange
                config["exchange"] = exchange
        else:
            # No global config available, just set exchange
            config["exchange"] = exchange

    return config


def get_streaks(trade_summary):
    """Calculates longest winning and losing streaks from trade summary."""
    profit_list = trade_summary[trade_summary["status"] == "closed"].profit.values
    longest_winning_streak = 1
    longest_losing_streak = 1
    streak = 1

    for i in range(1, len(profit_list)):
        if np.sign(profit_list[i]) == np.sign(profit_list[i - 1]):
            streak += 1

            if np.sign(profit_list[i]) > 0:
                # update winning streak
                longest_winning_streak = max(longest_winning_streak, streak)
            else:
                # Update losing
                longest_losing_streak = max(longest_losing_streak, streak)

        else:
            streak = 1

    return longest_winning_streak, longest_losing_streak


def unpickle_broker(picklefile: Optional[str] = ".virtual_broker"):
    """Unpickles a virtual broker instance for post-processing."""
    with open(picklefile, "rb") as file:
        instance = pickle.load(file)
    return instance


class CustomLoggingFormatter(logging.Formatter):
    """Custom logging formatter (for StreamHandlers only)."""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    default_fmt = "%(asctime)s | %(levelname)8s | %(name)8s | %(message)s (%(filename)s:%(lineno)d)"

    def __init__(self, fmt=None):
        super().__init__()

        self.fmt = fmt if fmt else self.default_fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(
    name: str,
    stdout: Optional[bool] = True,
    stdout_level: Optional[Union[int, str]] = logging.INFO,
    file: Optional[bool] = False,
    file_level: Optional[Union[int, str]] = logging.INFO,
    log_dir: Optional[str] = "autotrader_logs",
):
    """Get (or create) a logger."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Check for and clear any existing handlers on this logger
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create new handlers
    handlers = []

    # Check for logging to file
    if file:
        # Check log directory exists
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        logfile_path = os.path.join(log_dir, f"{name}.log")
        fh = logging.FileHandler(logfile_path, mode="a")
        fh.setLevel(file_level)
        fh.setFormatter(logging.Formatter(CustomLoggingFormatter.default_fmt))
        handlers.append(fh)

    # Check for logging to stdout
    if stdout:
        sh = logging.StreamHandler()
        stdout_level = stdout_level if stdout_level else logging.ERROR
        sh.setLevel(stdout_level)
        sh.setFormatter(CustomLoggingFormatter())
        handlers.append(sh)

    # Add handler to logger
    for h in handlers:
        logger.addHandler(h)

    return logger


class TradeAnalysis:
    """AutoTrader trade analysis class.

    Attributes
    ----------
    instruments_traded : list
        The instruments traded during the trading period.

    account_history : pd.DataFrame
        A timeseries history of the account during the trading period.

    holding_history : pd.DataFrame
        A timeseries summary of holdings during the trading period, by portfolio
        allocation fraction.

    order_history : pd.DataFrame
        A timeseries history of orders placed during the trading period.

    cancelled_orders : pd.DataFrame
        Orders which were cancelled during the trading period.

    trade_history : pd.DataFrame
        A history of all trades (fills) made during the trading period.

    """

    def __init__(
        self,
        broker,
        broker_histories: dict,
        instrument: str = None,
        price_history: pd.DataFrame = None,
    ):
        # Meta data
        self.brokers_used = None
        self.broker_results = None
        self.instruments_traded = None

        # Histories
        self.account_history = None
        self.position_history = None
        self.position_summary = None
        self.order_history = None
        self.cancelled_orders = None
        self.trade_history = None
        self.price_history = price_history

        # Perform analysis
        self.analyse_account(broker, broker_histories, instrument)

    def __str__(self):
        return "AutoTrader Trading Results"

    def __repr__(self):
        return "AutoTrader Trading Results"

    def analyse_account(
        self,
        broker,
        broker_histories: dict,
        instrument: Optional[str] = None,
    ) -> None:
        """Analyses trade account and creates summary of key details."""
        if not isinstance(broker, dict):
            # Single broker - create dummy dict
            broker_instances = {list(broker_histories.keys())[0]: broker}
        else:
            # Multiple brokers passed in as dict
            broker_instances = broker

        # Process results from each broker instance
        broker_results = {}
        for broker_name, broker in broker_instances.items():
            # Construct trade and order summaries
            all_orders = {}
            for status in ["pending", "open", "filled", "cancelled"]:
                orders = broker.get_orders(order_status=status)
                all_orders.update(orders)

            orders = TradeAnalysis.create_trade_summary(
                orders=all_orders, instrument=instrument, broker_name=broker_name
            )
            trade_history = TradeAnalysis.create_fill_summary(
                fills=broker._fills, broker_name=broker_name
            )

            account_history = pd.DataFrame(
                data=broker_histories[broker_name],
            )
            account_history.set_index("time", inplace=True)

            position_history = TradeAnalysis.create_position_history(
                trade_history=trade_history,
                account_history=account_history,
            )

            position_summary = TradeAnalysis._create_position_summary(
                broker._positions, broker._closed_positions
            )

            # Calculate drawdown
            account_history["drawdown"] = (
                account_history.NAV / account_history.NAV.cummax() - 1
            )

            # Save results for this broker instance
            broker_results[broker_name] = {
                "instruments_traded": list(orders.instrument.unique()),
                "account_history": self._decimal_to_float(account_history),
                "position_history": self._decimal_to_float(position_history),
                "position_summary": self._decimal_to_float(position_summary),
                "order_history": self._decimal_to_float(orders),
                "cancelled_orders": self._decimal_to_float(
                    orders[orders.status == "cancelled"]
                ),
                "trade_history": self._decimal_to_float(trade_history),
            }

        # Save all results
        self.broker_results = broker_results

        # Aggregate across broker instances
        self._aggregate_across_brokers(broker_results)

    @staticmethod
    def _decimal_to_float(df: pd.DataFrame):
        """Cast all numeric types to floats to support plotting."""
        for col in df:
            try:
                df[col] = df[col].astype(float)
            except:
                pass
        return df

    @staticmethod
    def create_position_history(
        trade_history: pd.DataFrame,
        account_history: pd.DataFrame,
    ) -> pd.DataFrame:
        """Creates a history of positions held, recording number of units held
        at each timestamp.
        """
        # Use fills to reconstruct position history, in terms of units held
        instruments_traded = list(trade_history["instrument"].unique())

        position_histories_dict = {}
        for instrument in instruments_traded:
            instrument_trade_hist = trade_history[
                trade_history["instrument"] == instrument
            ]
            directional_trades = (
                instrument_trade_hist["direction"] * instrument_trade_hist["size"]
            )
            net_position_hist = directional_trades.cumsum()

            # Filter out duplicates
            net_position_hist = net_position_hist[
                ~net_position_hist.index.duplicated(keep="last")
            ]

            # Reindex to account history index
            # TODO - match index timezone info
            net_position_hist = net_position_hist[~net_position_hist.index.isna()]
            try:
                net_position_hist = net_position_hist.reindex(
                    index=account_history.index, method="ffill"
                ).fillna(0)
            except:
                print("Could not reindex position history on account history index.")

            # Save result
            position_histories_dict[instrument] = net_position_hist

        # If no trades, create empty dataframe
        if len(instruments_traded) == 0:
            position_histories_dict = {
                "empty": pd.DataFrame(index=account_history.index)
            }

        position_histories = pd.concat(position_histories_dict, axis=1)
        return position_histories

    @staticmethod
    def _create_position_summary(open_positions, closed_positions):
        """Creates a summary of positions held."""
        # # Analyse closed positions (currently unused)
        # open_positions_summary = {}
        # for instrument, position in open_positions.items():
        #     directions = [p.direction for p in positions]

        #     # Save analysis
        #     open_positions_summary[instrument] = {
        #         "directions": directions,
        #         "no_long": directions.count(1),
        #         "no_short": directions.count(-1),
        #     }

        # Analyse closed positions
        closed_positions_results = {}
        closed_positions_summary = {}
        for instrument, positions in closed_positions.items():
            directions = [p.direction for p in positions]
            durations = [p.exit_time - p.entry_time for p in positions]

            # Save analysis
            closed_positions_results[instrument] = {
                "directions": directions,
                "durations": durations,
            }
            closed_positions_summary[instrument] = {
                "no_long": directions.count(1),
                "no_short": directions.count(-1),
            }
            if len(durations) > 0:
                closed_positions_summary[instrument]["avg_duration"] = np.mean(
                    durations
                )
                if directions.count(1) > 0:
                    closed_positions_summary[instrument]["avg_long_duration"] = np.mean(
                        np.array(durations)[np.array(directions) == 1]
                    )
                else:
                    closed_positions_summary[instrument]["avg_long_duration"] = None
                if directions.count(-1) > 0:
                    closed_positions_summary[instrument]["avg_short_duration"] = (
                        np.mean(np.array(durations)[np.array(directions) == -1])
                    )
                else:
                    closed_positions_summary[instrument]["avg_short_duration"] = None

        # Create summary dataframe
        summary = pd.DataFrame(
            data=closed_positions_summary,
        )

        return summary

    def _aggregate_across_brokers(self, broker_results):
        """Aggregates trading history across all broker instances."""
        brokers_used = []
        instruments_traded = []
        cancelled_orders = pd.DataFrame()
        position_history = pd.DataFrame()
        position_summary = pd.DataFrame()
        order_history = pd.DataFrame()
        trade_history = pd.DataFrame()
        account_history = None
        for broker, results in broker_results.items():
            orders = results["order_history"]
            brokers_used.append(broker)

            # Append unique instruments traded
            unique_instruments = orders.instrument.unique()
            [
                (
                    instruments_traded.append(instrument)
                    if instrument not in instruments_traded
                    else None
                )
                for instrument in unique_instruments
            ]

            # Aggregate account history
            if account_history is None:
                # Initialise
                account_history = results["account_history"]
            else:
                # Reindex each dataset
                original_index = results["account_history"].reindex(
                    index=account_history.index, method="ffill"
                )
                new_index = account_history.reindex(
                    index=results["account_history"].index, method="ffill"
                )
                if len(original_index) >= len(new_index):
                    # Use original index
                    account_history += original_index
                else:
                    # Use new index
                    account_history = new_index + results["account_history"]

            # Concatenate trades, orders and trade_history
            cancelled_orders = pd.concat(
                [cancelled_orders, results["cancelled_orders"]]
            )
            order_history = pd.concat([order_history, results["order_history"]])
            trade_history = pd.concat([trade_history, results["trade_history"]])
            position_history = pd.concat(
                [position_history, results["position_history"]]
            )
            # TODO - implement position summary for multiple exchanges
            position_summary = results["position_summary"]

        # Assign attributes
        self.brokers_used = brokers_used
        self.instruments_traded = instruments_traded
        self.account_history = account_history
        self.position_history = position_history
        self.position_summary = position_summary
        self.order_history = order_history
        self.cancelled_orders = cancelled_orders
        self.trade_history = trade_history

    @staticmethod
    def create_fill_summary(fills: list, broker_name: str = None):
        """Creates a dataframe of fill history."""
        # Initialise lists
        fill_dict = {
            "order_time": [],
            "order_price": [],
            "order_type": [],
            "fill_time": [],
            "fill_price": [],
            "direction": [],
            "size": [],
            "fee": [],
            "instrument": [],
            "id": [],
            "order_id": [],
        }
        for fill in fills:
            fill_dict["order_time"].append(fill.order_time)
            fill_dict["order_price"].append(fill.order_price)
            fill_dict["fill_time"].append(fill.fill_time)
            fill_dict["fill_price"].append(fill.fill_price)
            fill_dict["direction"].append(fill.direction)
            fill_dict["size"].append(fill.size)
            fill_dict["fee"].append(fill.fee)
            fill_dict["instrument"].append(fill.instrument)
            fill_dict["id"].append(fill.id)
            fill_dict["order_id"].append(fill.order_id)
            fill_dict["order_type"].append(fill.order_type)

        fill_df = pd.DataFrame(data=fill_dict, index=fill_dict["fill_time"])
        fill_df["broker"] = broker_name

        return fill_df

    @staticmethod
    def create_trade_summary(
        trades: dict = None,
        orders: dict = None,
        instrument: str = None,
        broker_name: str = None,
    ) -> pd.DataFrame:
        """Creates a summary dataframe for trades and orders."""
        # TODO - review this, could likely be cleaner
        instrument = None if isinstance(instrument, list) else instrument

        if trades is not None:
            iter_dict = trades
        else:
            iter_dict = orders

        iter_dict = {} if iter_dict is None else iter_dict

        product = []
        status = []
        ids = []
        times_list = []
        order_type = []
        order_price = []
        size = []
        direction = []
        stop_price = []
        take_price = []
        reason = []

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
            order_type.append(item.order_type)
            order_price.append(item.order_price)
            stop_price.append(item.stop_loss)
            take_price.append(item.take_profit)
            reason.append(item.reason)

        if trades is not None:
            for trade_id, trade in iter_dict.items():
                entry_time.append(trade.time_filled)
                fill_price.append(trade.fill_price)
                profit.append(trade.profit)
                portfolio_balance.append(trade.balance)
                exit_times.append(trade.exit_time)
                exit_prices.append(trade.exit_price)
                fees.append(trade.fees)
                if trade.status == "closed":
                    if type(trade.exit_time) == str:
                        exit_dt = datetime.strptime(
                            trade.exit_time, "%Y-%m-%d %H:%M:%S%z"
                        )
                        entry_dt = datetime.strptime(
                            trade.time_filled, "%Y-%m-%d %H:%M:%S%z"
                        )
                        trade_duration.append(
                            exit_dt.timestamp() - entry_dt.timestamp()
                        )
                    elif isinstance(trade.exit_time, pd.Timestamp):
                        trade_duration.append(
                            (trade.exit_time - trade.time_filled).total_seconds()
                        )
                    elif trade.exit_time is None:
                        # Weird edge case
                        trade_duration.append(None)
                    else:
                        trade_duration.append(
                            trade.exit_time.timestamp() - trade.time_filled.timestamp()
                        )
                else:
                    trade_duration.append(None)

            dataframe = pd.DataFrame(
                {
                    "instrument": product,
                    "status": status,
                    "ID": ids,
                    "order_price": order_price,
                    "order_time": times_list,
                    "fill_time": entry_time,
                    "fill_price": fill_price,
                    "size": size,
                    "direction": direction,
                    "stop_loss": stop_price,
                    "take_profit": take_price,
                    "profit": profit,
                    "balance": portfolio_balance,
                    "exit_time": exit_times,
                    "exit_price": exit_prices,
                    "trade_duration": trade_duration,
                    "fees": fees,
                },
                index=pd.to_datetime(entry_time),
            )

            # Fill missing values for balance
            dataframe.balance.fillna(method="ffill", inplace=True)

        else:
            # Order summary
            dataframe = pd.DataFrame(
                {
                    "instrument": product,
                    "status": status,
                    "order_id": ids,
                    "order_type": order_type,
                    "order_price": order_price,
                    "order_time": times_list,
                    "size": size,
                    "direction": direction,
                    "stop_loss": stop_price,
                    "take_profit": take_price,
                    "reason": reason,
                },
                index=pd.to_datetime(times_list),
            )

        dataframe = dataframe.sort_index()

        # Add broker name column
        dataframe["broker"] = broker_name

        # Filter by instrument
        if instrument is not None:
            dataframe = dataframe[dataframe["instrument"] == instrument]

        return dataframe

    def summary(self) -> dict:
        """Constructs a trading summary for printing."""
        # Initialise trade results dict
        trade_results = {}

        # Analyse account history
        if len(self.account_history) > 0:
            # The account was open for some nonzero time period
            starting_balance = self.account_history["equity"].iloc[0]
            ending_balance = self.account_history["equity"].iloc[-1]
            ending_NAV = self.account_history["NAV"].iloc[-1]
            abs_return = ending_balance - starting_balance
            pc_return = 100 * abs_return / starting_balance
            floating_pnl = ending_NAV - ending_balance
            max_drawdown = min(self.account_history.drawdown)

            # Save results to dict
            trade_results["start"] = self.account_history.index[0]
            trade_results["end"] = self.account_history.index[-1]
            trade_results["starting_balance"] = starting_balance
            trade_results["ending_balance"] = ending_balance
            trade_results["ending_NAV"] = ending_NAV
            trade_results["abs_return"] = abs_return
            trade_results["pc_return"] = pc_return
            trade_results["floating_pnl"] = floating_pnl
            trade_results["max_drawdown"] = max_drawdown

        # All trades
        no_trades = len(self.trade_history)
        trade_results["no_trades"] = no_trades
        trade_results["no_long_trades"] = len(
            self.trade_history[self.trade_history["direction"] > 0]
        )
        trade_results["no_short_trades"] = len(
            self.trade_history[self.trade_history["direction"] < 0]
        )

        if no_trades > 0:
            # Initialise all_trades dict
            trade_results["all_trades"] = {}

            # Calculate positions still open
            # TODO - debug below with multi asset backtest
            try:
                trade_results["no_open"] = sum(self.position_history.iloc[-1] > 0)
            except:
                trade_results["no_open"] = 0

            # Analyse winning positions
            # wins = self.isolated_position_history[
            #     self.isolated_position_history.profit > 0
            # ]
            # avg_win = np.mean(wins.profit)
            # max_win = np.max(wins.profit)

            # Analyse losing positions
            # loss = self.isolated_position_history[
            #     self.isolated_position_history.profit < 0
            # ]
            # avg_loss = abs(np.mean(loss.profit))
            # max_loss = abs(np.min(loss.profit))

            # Performance
            # win_rate = 100 * len(wins) / no_trades
            # longest_win_streak, longest_lose_streak = get_streaks(
            #     self.isolated_position_history
            # )
            # try:
            #     avg_trade_duration = np.nanmean(
            #         self.isolated_position_history.trade_duration.values
            #     )
            #     trade_results["all_trades"]["avg_trade_duration"] = str(
            #         timedelta(seconds=int(avg_trade_duration))
            #     )
            # except TypeError:
            #     # Position has not been closed yet
            #     trade_results["all_trades"]["avg_trade_duration"] = None

            # Trade durations
            # duration_list = [
            #     i
            #     for i in self.isolated_position_history.trade_duration.values
            #     if i is not None
            # ]
            # if len(duration_list) > 0:
            #     min_trade_duration = np.nanmin(duration_list)
            #     max_trade_duration = np.nanmax(duration_list)
            # else:
            #     min_trade_duration = None
            #     max_trade_duration = None

            # Fees
            total_fees = self.trade_history.fee.sum()

            # Volume traded
            total_volume = (
                self.trade_history["size"] * self.trade_history["fill_price"]
            ).values.sum()

            # trade_results["all_trades"]["avg_win"] = avg_win
            # trade_results["all_trades"]["max_win"] = max_win
            # trade_results["all_trades"]["avg_loss"] = avg_loss
            # trade_results["all_trades"]["max_loss"] = max_loss
            # trade_results["all_trades"]["win_rate"] = win_rate
            # trade_results["all_trades"]["win_streak"] = longest_win_streak
            # trade_results["all_trades"]["lose_streak"] = longest_lose_streak
            trade_results["all_trades"]["avg_win"] = 0
            trade_results["all_trades"]["max_win"] = 0
            trade_results["all_trades"]["avg_loss"] = 0
            trade_results["all_trades"]["max_loss"] = 0
            trade_results["all_trades"]["win_rate"] = 0
            trade_results["all_trades"]["win_streak"] = 0
            trade_results["all_trades"]["lose_streak"] = 0
            trade_results["all_trades"]["total_volume"] = total_volume
            max_trade_duration = None
            min_trade_duration = None

            if max_trade_duration is not None:
                trade_results["all_trades"]["longest_trade"] = str(
                    timedelta(seconds=int(max_trade_duration))
                )
            else:
                trade_results["all_trades"]["longest_trade"] = str(None)

            if min_trade_duration is not None:
                trade_results["all_trades"]["shortest_trade"] = str(
                    timedelta(seconds=int(min_trade_duration))
                )
            else:
                trade_results["all_trades"]["shortest_trade"] = str(None)

            trade_results["all_trades"]["total_fees"] = total_fees

        # Cancelled orders
        trade_results["no_cancelled"] = len(self.cancelled_orders)

        # Long positions
        # long_positions = self.isolated_position_history[
        #     self.isolated_position_history["direction"] > 0
        # ]
        # no_long = len(long_positions)
        # trade_results["long_positions"] = {}
        # trade_results["long_positions"]["total"] = no_long
        # if no_long > 0:
        #     long_wins = long_positions[long_positions.profit > 0]
        #     avg_long_win = np.mean(long_wins.profit)
        #     max_long_win = np.max(long_wins.profit)
        #     long_loss = long_positions[long_positions.profit < 0]
        #     avg_long_loss = abs(np.mean(long_loss.profit))
        #     max_long_loss = abs(np.min(long_loss.profit))
        #     long_wr = 100 * len(long_positions[long_positions.profit > 0]) / no_long

        #     trade_results["long_positions"]["avg_long_win"] = avg_long_win
        #     trade_results["long_positions"]["max_long_win"] = max_long_win
        #     trade_results["long_positions"]["avg_long_loss"] = avg_long_loss
        #     trade_results["long_positions"]["max_long_loss"] = max_long_loss
        #     trade_results["long_positions"]["long_wr"] = long_wr

        # # Short positions
        # short_positions = self.isolated_position_history[
        #     self.isolated_position_history["direction"] < 0
        # ]
        # no_short = len(short_positions)
        # trade_results["short_positions"] = {}
        # trade_results["short_positions"]["total"] = no_short
        # if no_short > 0:
        #     short_wins = short_positions[short_positions.profit > 0]
        #     avg_short_win = np.mean(short_wins.profit)
        #     max_short_win = np.max(short_wins.profit)
        #     short_loss = short_positions[short_positions.profit < 0]
        #     avg_short_loss = abs(np.mean(short_loss.profit))
        #     max_short_loss = abs(np.min(short_loss.profit))
        #     short_wr = 100 * len(short_positions[short_positions.profit > 0]) / no_short

        #     trade_results["short_positions"]["avg_short_win"] = avg_short_win
        #     trade_results["short_positions"]["max_short_win"] = max_short_win
        #     trade_results["short_positions"]["avg_short_loss"] = avg_short_loss
        #     trade_results["short_positions"]["max_short_loss"] = max_short_loss
        #     trade_results["short_positions"]["short_wr"] = short_wr

        return trade_results


class AbstractDataStream(Broker):
    """Custom data feed base class. Wrapper around broker object without any
    private trading methods."""

    @abstractmethod
    def __init__(self, config: dict[str, any]) -> None:
        pass


class DataStream(AbstractDataStream):
    """Custom data feed base class. Wrapper around broker object without any
    private trading methods."""

    def __init__(self, config: dict[str, any]) -> None:
        self._data_broker = self

    @property
    def data_broker(self):
        return self._data_broker

    def __repr__(self):
        return "DataStreamer"

    def __str__(self):
        return "DataStreamer"


class LocalDataStream(DataStream):
    """Local data stream object."""

    def __init__(self, config: dict[str, any]) -> None:
        # Unpack parameters
        self._directory = config["directory"]
        self._data_dict: dict[str, str] = config["data_dict"]
        self._data_path_mapper = config["data_path_mapper"]

    def get_candles(
        self,
        instrument: str,
        granularity: str = None,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        # TODO - test with portfolio

        # Get filepath
        if self._data_dict:
            # Local using filenames specified
            filepath = self._data_dict.get(instrument)

        elif self._data_path_mapper:
            # Use mapper function
            prefix = self._data_path_mapper(instrument)
            filepath = os.path.join(self._directory, f"{prefix}.csv")

        else:
            # Use instrument directory
            filepath = os.path.join(self._directory, f"{instrument}.csv")

        # Load
        candles = pd.read_csv(filepath, index_col=0, parse_dates=True)

        return candles

    def get_orderbook(self, instrument: str, *args, **kwargs):
        raise Exception("Orderbook data is not available from the local datastreamer.")

    def get_public_trades(self, instrument: str, *args, **kwargs):
        raise Exception(
            "Public trade data is not available from the local datastreamer."
        )


class CcxtDownloadStreamer(DataStream):
    """Data Streamer for CCXT Download."""

    def __init__(self, config: dict[str, any]):
        # Save CCXT-Download attributes
        self.data_directory = DEFAULT_DOWNLOAD_DIR
        self._cache_length = 3

        # Initialise cache
        self._cache: dict[str, pd.DataFrame] = {}

    def get_candles(
        self,
        instrument: str,
        granularity: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        # TODO - need to check data ranges, same as in virtual broker?
        if instrument not in self._cache:
            # Load from data lake
            candles = load_data(
                exchange="bybit",  # TODO - need to get this from somewhere
                data_type=CANDLES,
                data_type_id=granularity,
                symbols=[instrument],
                start_date=start_time,
                end_date=end_time,
            )
            self._cache[instrument] = candles

        else:
            candles = self._cache[instrument]

        return candles

    def get_orderbook(self, instrument: str, *args, **kwargs):
        candles = self._cache[instrument]
        # Use local orderbook method.
        return candles

    def get_public_trades(self, instrument: str, *args, **kwargs):
        # TODO - implement
        return []


class TradeWatcher:
    """Watches trade snapshots to detect new trades."""

    def __init__(self) -> None:
        self.last_trade_time = None
        self.latest_trades = []

    def update(self, trades):
        """Updates the trades being monitored for change."""
        if trades[0]["time"] != self.last_trade_time:
            # Trade update
            self.last_trade_time = trades[0]["time"]

            for trade in trades:
                if trade["time"] != self.last_trade_time:
                    break
                self.latest_trades.append(trade)

    def get_latest_trades(self):
        """Returns the latest (unseen) trades."""
        latest_trades = self.latest_trades
        self.latest_trades = []
        return latest_trades


class Monitor:
    def __init__(
        self,
        config_filepath: Optional[str] = None,
        config: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> None:
        """Construct a Monitor instance.

        Parameters
        ----------
        config_filepath : str, None
            The absolute filepath of the monitor yaml configuration file.
            The default is None.

        config : dict, optional
            The monitor configuration dictionary. The default is None.
        """
        # Initialise attributes
        self.port = None
        self.broker = None
        self.picklefile = None
        self.environment = None
        self.initial_nav = None
        self.max_nav = None
        self.sleep_time = None

        if config_filepath is not None:
            # Read monitor config
            print("Loading monitor configuration from file.")
            config = read_yaml(config_filepath)

        elif config is None and config_filepath is None:
            # Use kwargs as config
            config = kwargs

        # Overwrite config with kwargs
        for key, val in kwargs.items():
            if val is not None:
                config[key] = val

        # Check config keys
        required_keys = [
            "port",
            "environment",
            "initial_nav",
            "max_nav",
            "sleep_time",
        ]
        for key in required_keys:
            if key not in config.keys():
                print(f"Error: missing configuration key: '{key}'")
                sys.exit()

        # Check for broker key
        if "picklefile" in config and config["picklefile"] is not None:
            self.picklefile = config["picklefile"]
        else:
            try:
                self.broker = config["broker"]
            except KeyError:
                print("Please specify the broker name or pickle file path to monitor.")
                sys.exit()

        # Unpack config and assign attributes
        for key, val in config.items():
            setattr(self, key, val)

    def _initialise(self) -> None:
        """Initialise the monitor."""
        # Set up instrumentation
        self.nav_gauge = Gauge("nav_gauge", "Net Asset Value gauge.")
        self.drawdown_gauge = Gauge("drawdown_gauge", "Current drawdown gauge.")
        self.max_pos_gauge = Gauge(
            "max_position_gauge", "Maximum position notional gauge."
        )
        self.max_pos_frac_gauge = Gauge(
            "max_pos_frac_gauge", "Maximum position NAV fraction gauge."
        )
        self.abs_PnL_gauge = Gauge("abs_pnl_gauge", "Absolute ($) PnL gauge.")
        self.rel_PnL_gauge = Gauge("rel_pnl_gauge", "Relative (%) PnL gauge.")
        self.pos_gauge = Gauge("pos_gauge", "Number of open positions gauge.")
        self.total_exposure_gauge = Gauge(
            "total_exposure_gauge", "Total exposure gauge."
        )
        self.net_exposure_gauge = Gauge("net_exposure_gauge", "Total exposure gauge.")
        self.leverage_gauge = Gauge("leverage_gauge", "Total leverage gauge.")

        # Start up the server to expose the metrics
        try:
            Monitor.start_server(self.port)
        except OSError:
            print(f"Server on port {self.port} already in use. Terminating to restart.")

            # Kill existing server
            from psutil import process_iter
            from signal import SIGKILL  # or SIGTERM

            for proc in process_iter():
                for conns in proc.connections(kind="inet"):
                    if conns.laddr.port == self.port:
                        proc.send_signal(SIGKILL)  # or SIGKILL

            # Start server
            Monitor.start_server(self.port)

    def run(
        self,
    ) -> None:
        """Runs the monitor indefinitely."""
        # Initialise
        self._initialise()

        # Begin monitor loop
        broker = None
        print(f"Monitoring with {self.sleep_time} second updates.")
        deploy_time = datetime.now().timestamp()
        while True:
            try:
                # Get broker object
                broker = self.get_broker(broker)

                # Query broker
                nav = broker.get_NAV()
                if self.initial_nav is None:
                    self.initial_nav = nav
                if self.max_nav is None:
                    self.max_nav = nav

                positions = broker.get_positions()
                pnl = nav - self.initial_nav
                rel_pnl = pnl / self.initial_nav

                # Calculate drawdown
                if nav > self.max_nav:
                    self.max_nav = nav
                drawdown = -min(0, -(self.max_nav - nav) / self.max_nav)

                # Calculate total exposure
                total_exposure = 0
                net_exposure = 0
                max_pos_notional = 0
                pos_pnl = {}
                for instrument, position in positions.items():
                    pos_pnl[instrument] = position.pnl
                    pos_notional = abs(position.notional)
                    total_exposure += pos_notional
                    net_exposure += position.direction * position.notional

                    if pos_notional > max_pos_notional:
                        # Update maximum position notional value
                        max_pos_notional = pos_notional

                # Calculate max position fraction
                max_pos_frac = max_pos_notional / nav

                # Calculate leverage
                leverage = total_exposure / nav

                # Update metrics
                self.nav_gauge.set(nav)
                self.abs_PnL_gauge.set(pnl)
                self.rel_PnL_gauge.set(rel_pnl)
                self.pos_gauge.set(len(positions))
                self.total_exposure_gauge.set(total_exposure)
                self.net_exposure_gauge.set(net_exposure)
                self.leverage_gauge.set(leverage)
                self.drawdown_gauge.set(drawdown)
                self.max_pos_gauge.set(max_pos_notional)
                self.max_pos_frac_gauge.set(max_pos_frac)

                # Sleep
                time.sleep(
                    self.sleep_time - ((time.time() - deploy_time) % self.sleep_time)
                )

            except KeyboardInterrupt:
                print("\n\nStopping monitoring.")
                break

            except Exception as e:
                # Print exception
                print(e)

                # Also sleep briefly
                time.sleep(3)

                # Reconnect to broker
                broker = self.get_broker(None)

    @staticmethod
    def start_server(port):
        """Starts the http server for Prometheus."""
        start_http_server(port)
        print(f"Server started on port {port}.")

    def get_broker(self, broker) -> AbstractBroker:
        """Returns the broker object."""
        if self.picklefile is not None:
            # Load broker instance from pickle
            broker = unpickle_broker(self.picklefile)

        elif broker is not None:
            # Use existing broker instance
            pass

        else:
            # Create broker instance
            print(f"Connecting to {self.broker} ({self.environment} environment)...")
            at = autotrader.AutoTrader()
            at.configure(verbosity=0)
            at.configure(broker=self.broker, environment=self.environment, verbosity=0)
            broker = at.run()
            print("  Done.")
        return broker
