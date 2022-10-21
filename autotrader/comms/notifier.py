from autotrader import Order
from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def send_order(self, order: Order, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def send_message(self, message: str, *args, **kwargs) -> None:
        pass
