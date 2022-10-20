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

            size_precision = precision["amount"]
            price_precision = precision["price"]

            # Check for any decimals
            if "." in str(size_precision):
                size_precision = str(size_precision)[::-1].find(".")
            if "." in str(price_precision):
                price_precision = str(price_precision)[::-1].find(".")

            unified_response = {
                "size": size_precision,
                "price": price_precision,
            }

            # Store for later use
            self._instrument_precisions[instrument] = unified_response

        return unified_response

    def _get_market(self, instrument, *args, **kwargs):
        """Returns the raw get_market response from a CCXT exchange"""
        if instrument in self.markets:
            market = self.markets[instrument]
        elif instrument.split(":")[0] in self.markets:
            market = self.markets[instrument.split(":")[0]]
        elif f"{instrument.split('USDT')[0]}/USDT" in self.markets:
            market = self.markets[f"{instrument.split('USDT')[0]}/USDT"]
        else:
            raise Exception(
                f"{instrument} does not appear to be listed. "
                + "Please double check the naming."
            )
        return market

    def get_stepsize(self, instrument, *args, **kwargs):
        """Returns the stepsize for an instrument."""
        market = self._get_market(instrument)
        stepsize = float(market["limits"]["amount"]["min"])
        return stepsize

    def get_min_notional(self, instrument, *args, **kwargs):
        """Returns the minimum notional value a trade should hold."""
        market = self._get_market(instrument)
        min_notional = float(market["limits"]["cost"]["min"])
        return min_notional

    def get_ticksize(self, instrument, *args, **kwargs):
        """Returns the ticksize for an instrument."""
        market = self._get_market(instrument)
        try:
            ticksize = float(market["info"]["filters"][0]["tickSize"])
        except:
            raise Exception("Cannot retrieve ticksize.")
        return ticksize
