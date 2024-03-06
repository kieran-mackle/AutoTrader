from datetime import datetime
from abc import ABC, abstractmethod
from autotrader.brokers.broker import Broker
from typing import List, Union, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from autotrader import Order


class Strategy(ABC):
    @abstractmethod
    def __init__(
        self, parameters: dict, instrument: str, broker: Broker, *args, **kwargs
    ) -> None:
        super().__init__()

    @abstractmethod
    def generate_signal(self, dt: datetime) -> Optional[Union["Order", List["Order"]]]:
        """Generate trading signals based on the data supplied."""

    def stop_trading():
        """Self destruct this instance of AutoTrader to stop any further trading."""
        pass
