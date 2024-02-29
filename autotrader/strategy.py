from abc import ABC, abstractmethod
from typing import List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from autotrader import Order


class Strategy(ABC):
    @abstractmethod
    def __init__(self, parameters: dict, instrument: str, *args, **kwargs) -> None:
        super().__init__()

    @abstractmethod
    def generate_signal(self, *args, **kwargs) -> Union["Order", List["Order"]]:
        """Generate trading signals based on the data supplied."""

    def stop_trading():
        """Self destruct this instance of AutoTrader to stop any further trading."""
        pass
