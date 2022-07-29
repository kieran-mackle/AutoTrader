from decimal import Decimal
from autotrader.brokers.broker_utils import BrokerUtils


class Utils(BrokerUtils):
    def __init__(self):
        # Create Client instance
        try:
            from dydx3 import Client
            self.api = Client(host='https://api.dydx.exchange')
        except ImportError:
            raise Exception("Please install dydx-v3-python to connect "+\
                            "to dydx API.")
        # Except network error?
    
    
    def __repr__(self):
        return 'AutoTrader-dYdX Broker Utilities'
    
    
    def __str__(self):
        return 'AutoTrader-dYdX Broker Utilities'
    
    
    def get_precision(self, instrument, *arg, **kwargs):
        """Returns the precision of the specified instrument."""
        market = self._get_market(instrument=instrument)
        unified_response = {'size': -Decimal(market['tickSize']).as_tuple().exponent,
                            'price': -Decimal(market['stepSize']).as_tuple().exponent}
        return unified_response

    
    def _get_market(self, instrument, *args, **kwargs):
        """Returns the raw get_market response from dYdX"""
        response = self.api.public.get_markets(instrument)
        return response.data['markets'][instrument]