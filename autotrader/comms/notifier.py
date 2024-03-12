from abc import ABC, abstractmethod
from autotrader.brokers.trading import Order


class Notifier(ABC):
    @abstractmethod
    def __init__(self, logger_kwargs: dict = None, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def send_order(self, order: Order, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def send_message(self, message: str, *args, **kwargs) -> None:
        pass
