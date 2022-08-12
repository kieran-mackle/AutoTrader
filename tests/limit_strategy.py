from autotrader import Order, LimitOrder


class LimitStrategy:
    def __init__(self, **kwargs):
        self.orders_fired = False

    def generate_signal(self, data):
        orders = []
        if not self.orders_fired:
            last_close = data["Close"][-1]
            short_order = LimitOrder(
                direction=-1,
                order_limit_price=last_close + 0.0050,
            )
            long_order = LimitOrder(
                direction=1,
                order_limit_price=last_close - 0.0050,
            )

            orders = [long_order, short_order]
            self.orders_fired = True

        return orders
