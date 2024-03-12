import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod
from autotrader.brokers.broker import Broker
from autotrader.comms.notifier import Notifier
from typing import List, Union, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from autotrader import Order


class Strategy(ABC):
    @abstractmethod
    def __init__(
        self,
        parameters: dict,
        instrument: str,
        broker: Broker,
        notifier: Notifier,
        *args,
        **kwargs
    ) -> None:
        """Instantiate the strategy. This gets called from the AutoTraderBot assigned to
        this strategy.

        Parameters
        ----------
        parameters : dict
            The strategy parameters.

        instrument : str
            The instrument to trade.

        broker : Broker
            The broker connection.

        notifier : Notifier | None
            The notifier object. If notify is not set > 0, then this will be a NoneType object.
        """
        super().__init__()

    @abstractmethod
    def generate_signal(self, dt: datetime) -> Optional[Union["Order", List["Order"]]]:
        """Generate trading signals based on the data supplied."""

    def stop_trading():
        """Self destruct this instance of AutoTrader to stop any further trading."""
        pass

    def create_plotting_indicators(self, data: pd.DataFrame):
        """This method gets called with an entire backtest dataset to allow you to
        plot indicators."""
