import ccxt
from datetime import datetime
from autotrader.brokers.ccxt.utils import Utils, BrokerUtils
from autotrader.brokers.trading import Order, Trade, Position


class Broker:
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor."""
        # Unpack config and connect to broker-side API
        self.exchange = config["exchange"]
        exchange_instance = getattr(ccxt, self.exchange)
        self.api = exchange_instance(
            {"apiKey": config["api_key"], "secret": config["secret"]}
        )
        self.utils = utils if utils is not None else Utils()

        # Load markets
        markets = self.api.load_markets()

        if config["sandbox_mode"]:
            self.api.set_sandbox_mode(True)

        self.base_currency = config["base_currency"]

    def __repr__(self):
        return (
            f"AutoTrader-{self.exchange[0].upper()}"
            + f"{self.exchange[1:].lower()} interface"
        )

    def __str__(self):
        return self.__repr__()

    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account."""
        return self.api.fetchBalance()[self.base_currency]["total"]

    def get_balance(self, instrument: str = None) -> float:
        """Returns account balance."""
        instrument = self.base_currency if instrument is None else instrument
        return self.api.fetchBalance()[instrument]["total"]

    def place_order(self, order: Order, **kwargs) -> None:
        """Disassemble order_details dictionary to place order."""
        # Call order to set order time
        order()

        # Submit order to broker
        if order.order_type == "modify":
            placed_order = self._modify_order(order)
        elif order.order_type in [
            "close",
            "reduce",
        ]:
            raise NotImplementedError(
                f"Order type '{order.order_type}' has not "
                + "been implemented for CCXT yet."
            )
        else:
            side = "buy" if order.direction > 0 else "sell"
            placed_order = self.api.createOrder(
                symbol=order.instrument,
                type=order.order_type,
                side=side,
                amount=order.size,
                price=order.order_limit_price,
            )
        return placed_order

    def get_orders(
        self, instrument: str = None, order_status: str = "open", **kwargs
    ) -> dict:
        """Returns orders associated with the account."""
        if order_status == "open":
            # Fetch open orders (waiting to be filled)
            orders = self.api.fetchOpenOrders(instrument)

        elif order_status == "cancelled":
            # Fetch cancelled orders
            orders = self.api.fetchCanceledOrders(instrument)

        elif order_status == "closed":
            # Fetch closed orders
            orders = self.api.fetchClosedOrders(instrument)

        # Convert
        orders = self._convert_list(orders, item_type="order")

        return orders

    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels order by order ID."""
        cancelled_order = self.api.cancelOrder(order_id)
        return cancelled_order

    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account."""
        trades_list = self.api.fetchMyTrades(instrument)
        trades = self._convert_list(trades_list, item_type="trade")
        return trades

    def get_trade_details(self, trade_ID: str) -> dict:
        """Returns the details of the trade specified by trade_ID."""
        raise NotImplementedError(
            "This method is not available, and will "
            + "be deprecated with a future release. Please use the "
            + "get_trades method instead."
        )

    def get_positions(self, instrument: str = None, **kwargs) -> dict:
        """Gets the current positions open on the account.

        Note that not all exchanges exhibit the same behaviour, and
        so caution must be taken when interpreting results. It is recommended
        to use the api directly and test with the exchange you plan to use
        to valid functionality.

        Parameters
        ----------
        instrument : str, optional
            The trading instrument name (symbol). The default is None.

        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.

        """
        if instrument is None:
            # Get all positions
            if self.api.has["fetchPositions"]:
                positions = self.api.fetchPositions(symbols=None, params=kwargs)
                positions = self._convert_list(positions, item_type="position")
            else:
                raise Exception(
                    f"Exchange {self.exchange} does not have "
                    + "fetchPositions method."
                )
        else:
            # Get position in instrument provided
            if self.api.has["fetchPosition"]:
                position = self.api.fetchPosition(instrument, params=kwargs)
                positions = self._native_position(position)
            elif self.api.has["fetchPositions"]:
                positions = self.api.fetchPositions(symbols=None, params=kwargs)
                positions = self._convert_list(positions, item_type="position")
                positions = {instrument: positions[instrument]}
            else:
                raise Exception(
                    f"Exchange {self.exchange} does not have " + "fetchPosition method."
                )

        return positions

    def get_orderbook(self, instrument: str) -> dict:
        """Returns the orderbook"""
        response = self.api.fetchOrderBook(symbol=instrument)

        # Unify format
        orderbook = {}
        for side in ["bids", "asks"]:
            orderbook[side] = []
            for level in response[side]:
                orderbook[side].append({"price": level[0], "size": level[1]})
        return orderbook

    def _native_order(self, order):
        """Returns a CCXT order as a native AutoTrader Order."""
        direction = 1 if order["side"] == "buy" else -1
        order_type = order["type"].lower()

        if order_type == "limit":
            limit_price = order["price"]
        else:
            limit_price = None

        native_order = Order(
            instrument=order["symbol"],
            direction=direction,
            order_type=order_type,
            status=order["status"],
            size=abs(order["amount"]),
            id=order["id"],
            order_limit_price=limit_price,
            order_stop_price=order["stopPrice"],
            order_time=datetime.fromtimestamp(order["timestamp"] / 1000),
        )
        return native_order

    def _native_trade(self, trade):
        """Returns a CCXT trade as a native AutoTrader Trade."""
        direction = 1 if trade["side"] == "buy" else -1

        # parent_order_id = trade['info']['orderId']
        parent_order_id = trade["info"]["orderID"]

        native_trade = Trade(
            instrument=trade["symbol"],
            order_price=None,
            order_time=None,
            order_type=None,
            size=abs(trade["amount"]),
            fill_time=datetime.fromtimestamp(trade["timestamp"] / 1000),
            fill_price=float(trade["price"]),
            fill_direction=direction,
            fee=trade["fee"]["cost"],
            id=trade["id"],
            order_id=parent_order_id,
        )

        return native_trade

    def _native_position(self, position):
        """Returns a CCXT position structure as a native
        AutoTrader Position.
        """
        native_position = Position(
            instrument=position["symbol"],
            net_position=position["contracts"],
            PL=position["unrealizedPnl"],
            entry_price=position["entryPrice"],
        )
        return native_position

    def _convert_list(self, items, item_type="order"):
        """Converts a list of trades or orders to a dictionary."""
        native_func = f"_native_{item_type}"
        id_key = "instrument" if item_type == "position" else "id"
        converted = {}
        for item in items:
            native = getattr(self, native_func)(item)
            converted[getattr(native, id_key)] = native
        return converted

    def _modify_order(self, order):
        """Modify the size, type and price of an existing order."""
        # TODO - support changing order_type, not sure how it will be carried
        side = "buy" if order.direction > 0 else "sell"
        modified_order = self.api.editOrder(
            id=order.related_orders[0],
            symbol=order.instrument,
            side=side,
            type=None,
            amount=order.size,
            price=order.order_limit_price,
        )
        return modified_order
