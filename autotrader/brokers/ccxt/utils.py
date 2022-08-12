from autotrader.brokers.broker_utils import BrokerUtils


class Utils(BrokerUtils):
    def __init__(self, exchange: str = None, **kwargs):
        if exchange is not None:
            self.connect_to_exchange(exchange)

        # Stored instrument precisions
        self._instrument_precisions = {}

    def connect_to_exchange(self, exchange: str):
        try:
            import ccxt

            self.api = getattr(ccxt, exchange)()
            self.markets = self.api.load_markets()
        except ImportError:
            raise Exception("Please install ccxt to connect " + "to CCXT.")
        # Except network error?

    def __repr__(self):
        return "AutoTrader-CCXT Broker Utilities"

    def __str__(self):
        return "AutoTrader-CCXT Broker Utilities"

    def get_precision(self, instrument, *args, **kwargs):
        """Returns the precision of the instrument."""
        if instrument in self._instrument_precisions:
            # Precision already fetched, use stored value
            unified_response = self._instrument_precisions[instrument]
        else:
            # Fetch precision
            market = self._get_market(instrument)
            precision = market["precision"]
            unified_response = {
                "size": precision["amount"],
                "price": precision["price"],
            }

            # Store for later use
            self._instrument_precisions[instrument] = unified_response

        return unified_response

    def _get_market(self, instrument, *args, **kwargs):
        """Returns the raw get_market response from a CCXT exchange"""
        return self.markets[instrument]
