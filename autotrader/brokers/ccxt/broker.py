import ccxt
import time
from autotrader import AutoData
from datetime import datetime, timezone
from autotrader.brokers.broker import AbstractBroker
from autotrader.brokers.broker_utils import OrderBook
from autotrader.brokers.ccxt.utils import Utils, BrokerUtils
from autotrader.brokers.trading import Order, Trade, Position


class Broker(AbstractBroker):
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor."""
        # Unpack config and connect to broker-side API
        self.exchange = config["exchange"]
        exchange_instance = getattr(ccxt, self.exchange)
        # TODO - allow expanded config here
        ccxt_config = {
            "apiKey": config["api_key"],
            "secret": config["secret"],
            "options": config["options"],
            "password": config["password"],
        }
        self.api = exchange_instance(ccxt_config)
        self._utils = utils if utils is not None else Utils()

        # Set sandbox mode
        self._sandbox_str = ""
        if config["sandbox_mode"]:
            self.api.set_sandbox_mode(True)
            self._sandbox_str = " (sandbox mode)"

        # Load markets
        markets = self.api.load_markets()

        self.base_currency = config["base_currency"]

        # Create AutoData instance
        self.autodata = AutoData(
            data_source="ccxt",
            exchange=self.exchange,
            api=self.api,
        )

    def __repr__(self):
        return (
            f"AutoTrader-{self.exchange[0].upper()}"
            + f"{self.exchange[1:].lower()} interface"
            + self._sandbox_str
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
                + "been implemented for the CCXT interface yet."
            )
        else:
            # Regular order
            side = "buy" if order.direction > 0 else "sell"
            # Submit the order
            placed_order = self.api.createOrder(
                symbol=order.instrument,
                type=order.order_type,
                side=side,
                amount=abs(order.size),
                price=order.order_limit_price,
                params=order.ccxt_params,
            )

        return placed_order

    def get_orders(
        self, instrument: str = None, order_status: str = "open", **kwargs
    ) -> dict:
        """Returns orders associated with the account."""

        for attempt in range(2):
            try:
                # Check for order id
                if "order_id" in kwargs:
                    # Fetch order by ID
                    if self.api.has["fetchOrder"]:
                        orders = [
                            self.api.fetch_order(
                                id=kwargs["order_id"], symbol=instrument
                            )
                        ]

                else:
                    # TODO - add exception handling
                    if order_status == "open":
                        # Fetch open orders (waiting to be filled)
                        orders = self.api.fetchOpenOrders(instrument, **kwargs)

                    elif order_status == "cancelled":
                        # Fetch cancelled orders
                        orders = self.api.fetchCanceledOrders(instrument, **kwargs)

                    elif order_status == "closed":
                        # Fetch closed orders
                        orders = self.api.fetchClosedOrders(instrument, **kwargs)

                    elif order_status == "conditional":
                        # Fetch conditional orders
                        orders = self.api.fetchOpenOrders(
                            instrument, params={"orderType": "conditional"}
                        )

                    else:
                        # Unrecognised order status
                        raise Exception(f"Unrecognised order status '{order_status}'.")

                # Completed without exception, break loop
                break

            except ccxt.errors.NetworkError:
                # Throttle then try again
                time.sleep(1)

        # Convert
        orders = self._convert_list(orders, item_type="order")

        return orders

    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels order by order ID."""
        try:
            cancelled_order = self.api.cancelOrder(id=order_id, **kwargs)

        except ccxt.errors.NetworkError:
            # Throttle then try again
            time.sleep(1)
            cancelled_order = self.api.cancelOrder(id=order_id, **kwargs)

        except Exception as e:
            cancelled_order = e

        return cancelled_order

    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account."""
        try:
            trades_list = self.api.fetchMyTrades(instrument, **kwargs)
        except ccxt.errors.NetworkError:
            # Throttle then try again
            time.sleep(1)
            trades_list = self.api.fetchMyTrades(instrument, **kwargs)

        # Convert to native Trades
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
        for attempt in range(2):
            try:
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
                        if position is not None:
                            positions = {instrument: self._native_position(position)}
                        else:
                            positions = {}

                    elif self.api.has["fetchPositions"]:
                        positions = self.api.fetchPositions(
                            symbols=[instrument], params=kwargs
                        )
                        positions = self._convert_list(positions, item_type="position")
                    else:
                        raise Exception(
                            f"Exchange {self.exchange} does not have "
                            + "fetchPosition method."
                        )

                # Completed without exception, break loop
                break

            except ccxt.errors.NetworkError:
                # Throttle then try again
                time.sleep(1)

        # Check for zero-positions
        positions_dict = {}
        for symbol, pos in positions.items():
            if pos.net_position != 0:
                positions_dict[symbol] = pos

        return positions_dict

    def get_orderbook(self, instrument: str) -> OrderBook:
        """Returns the orderbook"""
        try:
            orderbook = self.autodata.L2(instrument=instrument)
        except ccxt.errors.NetworkError:
            # Throttle then try again
            time.sleep(1)
            orderbook = self.autodata.L2(instrument=instrument)
        return orderbook

    def _native_order(self, order: dict):
        """Returns a CCXT order as a native AutoTrader Order."""
        direction = 1 if order["side"] == "buy" else -1
        order_type = order["type"].lower()

        if order_type == "limit":
            limit_price = order["price"]
        else:
            limit_price = None

        stop_price = (
            float(order["stopPrice"]) if order["stopPrice"] is not None else None
        )

        native_order = Order(
            instrument=order["symbol"],
            direction=direction,
            order_type=order_type,
            status=order["status"],
            size=abs(order["amount"]),
            id=order["id"],
            order_limit_price=limit_price,
            order_stop_price=stop_price,
            order_time=datetime.fromtimestamp(order["timestamp"] / 1000),
            ccxt_order=order,
        )
        return native_order

    def _native_trade(self, trade):
        """Returns a CCXT trade as a native AutoTrader Trade."""
        direction = 1 if trade["side"] == "buy" else -1
        order_id_keys = ["orderID", "orderId2"]
        oid_assigned = False
        for key in order_id_keys:
            if key in trade["info"]:
                parent_order_id = trade["info"][key]
                oid_assigned = True
                break

        if not oid_assigned:
            parent_order_id = None

        native_trade = Trade(
            instrument=trade["symbol"],
            order_price=None,
            order_time=None,
            order_type=None,
            size=abs(trade["amount"]),
            last_price=None,
            fill_time=datetime.fromtimestamp(trade["timestamp"] / 1000).astimezone(
                timezone.utc
            ),
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
        # Get symbol
        try:
            symbol = position["symbol"]
        except:
            symbol = position["info"]["symbol"]

        direction = 1 if position["side"] == "long" else -1

        # Construct position object
        # TODO - add more attributes
        native_position = Position(
            instrument=symbol,
            net_position=position["contracts"] * direction,
            net_exposure=position["notional"],
            notional=position["notional"],
            pnl=position["unrealizedPnl"],
            PL=position["unrealizedPnl"],
            entry_price=position["entryPrice"],
            direction=direction,
            ccxt=position,
            avg_price=position["entryPrice"],
            total_margin=position["initialMargin"],
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
        try:
            modified_order = self.api.editOrder(
                id=order.related_orders[0],
                symbol=order.instrument,
                side=side,
                type=None,
                amount=order.size,
                price=order.order_limit_price,
            )
        except Exception as e:
            modified_order = e
        return modified_order
