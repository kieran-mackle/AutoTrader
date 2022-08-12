from autotrader.brokers.broker_utils import BrokerUtils


class Utils(BrokerUtils):
    def __init__(self, **kwargs):
        pass

    def __repr__(self):
        return "AutoTrader Virtual Broker Utilities"

    def __str__(self):
        return "AutoTrader Virtual Broker Utilities"

    def get_precision(self, instrument, *arg, **kwargs):
        """Returns the precision of the specified instrument."""
        unified_response = {"size": 2, "price": 5}
        return unified_response
