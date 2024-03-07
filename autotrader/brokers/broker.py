import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod
from autotrader.brokers.trading import Order, OrderBook


class AbstractBroker(ABC):
    @abstractmethod
    def __init__(self, config: dict) -> None:
        """AutoTrader Broker Class constructor."""

    @abstractmethod
    def __repr__(self):
        return "AutoTrader Broker interface"

    @abstractmethod
    def __str__(self):
        return "AutoTrader Broker interface"

    @property
    @abstractmethod
    def data_broker(self) -> "AbstractBroker":
        pass

    @abstractmethod
    def get_NAV(self, *args, **kwargs) -> float:
        """Returns the net asset/liquidation value of the account."""

    @abstractmethod
    def get_balance(self, *args, **kwargs) -> float:
        """Returns account balance."""

    @abstractmethod
    def place_order(self, order: Order, *args, **kwargs) -> None:
        """Translate order and place via exchange API."""

    @abstractmethod
    def get_orders(self, instrument: str = None, *args, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account."""

    @abstractmethod
    def cancel_order(self, order_id: int, *args, **kwargs) -> None:
        """Cancels order by order ID."""

    @abstractmethod
    def get_trades(self, instrument: str = None, *args, **kwargs) -> dict:
        """Returns the trades (fills) made by the account."""

    @abstractmethod
    def get_positions(self, instrument: str = None, *args, **kwargs) -> dict:
        """Gets the current positions open on the account.

        Parameters
        ----------
        instrument : str, optional
            The trading instrument name (symbol). The default is None.

        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """

    @abstractmethod
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
        """Get the historical OHLCV candles for an instrument."""

    @abstractmethod
    def get_orderbook(self, instrument: str, *args, **kwargs) -> OrderBook:
        """Get the orderbook for an instrument."""

    @abstractmethod
    def get_public_trades(self, instrument: str, *args, **kwargs):
        """Get the public trade history for an instrument."""

    @abstractmethod
    def _initialise_data(self, *args, **kwargs):
        """Initialise the broker data."""

    @abstractmethod
    def get_precision(self, instrument: str):
        """Return the price and amount precision for an instrument."""


class Broker(AbstractBroker):
    def configure(self, *args, **kwargs):
        """Generic configure method, placeholder for typehinting. Only required
        for the virtual broker."""

    def get_NAV(self, *args, **kwargs) -> float:
        raise NotImplementedError

    def get_balance(self, *args, **kwargs) -> float:
        raise NotImplementedError

    def place_order(self, order: Order, *args, **kwargs) -> None:
        raise NotImplementedError

    def get_orders(self, instrument: str = None, *args, **kwargs) -> dict:
        raise NotImplementedError

    def cancel_order(self, order_id: int, *args, **kwargs) -> None:
        raise NotImplementedError

    def get_trades(self, instrument: str = None, *args, **kwargs) -> dict:
        raise NotImplementedError

    def get_positions(self, instrument: str = None, *args, **kwargs) -> dict:
        raise NotImplementedError

    def _initialise_data(self, *args, **kwargs):
        pass

    def get_precision(self, instrument: str):
        return None
