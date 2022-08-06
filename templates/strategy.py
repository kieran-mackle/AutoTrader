from autotrader.brokers.trading import Order


class Strategy:
    def __init__(self, instrument, parameters, **kwargs):
        """Initialise the strategy."""
        self.name = "Template Strategy"
        self.instrument = instrument
        self.params = parameters

        # Construct indicators dict for plotting
        self.indicators = {
            "Indicator Name": {"type": "indicatortype", "data": "indicatordata"},
        }

    def generate_signal(self, data):
        """Define strategy logic to transform data into trading signals."""

        # Initialise empty order list
        orders = []

        # The data passed into this method is the most up-to-date data.

        # Example long market order:
        long_market_order = Order(direction=1)
        orders.append(long_market_order)

        # Example short limit order:
        short_limit = Order(direction=-1, order_type="limit", order_limit_price=1.0221)
        orders.append(short_limit)

        # Return any orders generated
        # If no orders are generated, return an empty list [], an empty dict {},
        # or a blank order Order().
        return orders
