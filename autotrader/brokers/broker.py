from abc import ABC, abstractmethod
from autotrader.brokers.trading import Order
from autotrader.brokers.broker_utils import BrokerUtils


class AbstractBroker(ABC):
    @abstractmethod
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor."""
        pass

    @abstractmethod
    def __repr__(self):
        return "AutoTrader Broker interface"

    @abstractmethod
    def __str__(self):
        return "AutoTrader Broker interface"

    @abstractmethod
    def get_NAV(self, *args, **kwargs) -> float:
        """Returns the net asset/liquidation value of the account."""
        pass

    @abstractmethod
    def get_balance(self, *args, **kwargs) -> float:
        """Returns account balance."""
        pass

    @abstractmethod
    def place_order(self, order: Order, *args, **kwargs) -> None:
        """Translate order and place via exchange API."""
        pass

    @abstractmethod
    def get_orders(self, instrument: str = None, *args, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: int, *args, **kwargs) -> None:
        """Cancels order by order ID."""
        pass

    @abstractmethod
    def get_trades(self, instrument: str = None, *args, **kwargs) -> dict:
        """Returns the trades (fills) made by the account."""
        pass

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
        pass
