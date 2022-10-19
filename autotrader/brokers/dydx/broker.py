import pandas as pd
from decimal import Decimal
from datetime import datetime
from autotrader import AutoData
from dydx3 import Client, constants
from autotrader.brokers.broker import AbstractBroker
from autotrader.brokers.broker_utils import OrderBook
from autotrader.brokers.dydx.utils import Utils, BrokerUtils
from autotrader.brokers.trading import Order, Position, Trade


class Broker(AbstractBroker):
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor."""
        self._utils = utils if utils is not None else Utils()

        # Unpack config to obtain STARK and API keys
        client = Client(
            host="http://localhost:8080", eth_private_key=config["ETH_PRIV_KEY"]
        )
        STARK_KEYS = client.onboarding.derive_stark_key(config["ETH_ADDRESS"])
        API_KEY = client.onboarding.recover_default_api_key_credentials(
            config["ETH_ADDRESS"]
        )

        # Connect to dYdX API
        self.api = Client(
            host="https://api.dydx.exchange",
            api_key_credentials=API_KEY,
            stark_private_key=STARK_KEYS["private_key"],
            stark_public_key=STARK_KEYS["public_key"],
            stark_public_key_y_coordinate=STARK_KEYS["public_key_y_coordinate"],
            eth_private_key=config["ETH_PRIV_KEY"],
            default_ethereum_address=config["ETH_ADDRESS"],
        )

        # Create AutoData instance
        self.autodata = AutoData(data_source="dydx")

    def __repr__(self):
        return "AutoTrader-dYdX interface"

    def __str__(self):
        return "AutoTrader-dYdX interface"

    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account."""
        account = self._get_account()
        return float(account["equity"])

    def get_balance(self) -> float:
        """Returns account balance."""
        return self.get_NAV()

    def place_order(self, order: Order, **kwargs) -> None:
        """Disassemble order_details dictionary to place order."""
        # TODO - build in checking of constants.__dict__ for instrument

        # Call order to set order time
        order()

        # Extract information for submission to dydx
        order = self._check_order_precision(order)
        side = "BUY" if order.direction > 0 else "SELL"
        order_type = order.order_type.upper()
        expiration = int((pd.Timedelta("30days") + datetime.now()).timestamp())
        order_price = (
            str(order.order_limit_price)
            if order.order_limit_price is not None
            else None
        )
        trigger_price = (
            str(order.order_stop_price) if order.order_stop_price is not None else None
        )
        position_id = self._get_account()["positionId"]
        limit_fee = order.limit_fee

        kwargs = {}
        if trigger_price is not None:
            kwargs["trigger_price"] = trigger_price
        if order_type == "MARKET":
            kwargs["time_in_force"] = "IOC"

        # TODO - allow more kwargs to be parsed from order

        if order_price is None:
            # Create order price
            midprice = self.autodata.L2(order.instrument).midprice
            multiple = 1.05 if side == "BUY" else 0.95
            order_price = (Decimal(multiple) * midprice).quantize(midprice)

        # Submit order to dydx
        order = self.api.private.create_order(
            position_id=position_id,
            market=order.instrument,
            side=side,
            order_type=order_type,
            post_only=order.post_only,
            size=str(order.size),
            price=str(order_price),
            limit_fee=limit_fee,
            expiration_epoch_seconds=expiration,
            **kwargs,
        )

        return self._native_order(order.data["order"])

    def get_orders(self, instrument: str = None, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account.

        kwargs can include status, side, type, limit, createdBeforeOrAt and returnLatestOrders. See
        https://docs.dydx.exchange/?python#get-orders for more details.
        """
        orders = self.api.private.get_orders(market=instrument, **kwargs)
        orders = self._conver_order_list(orders.data["orders"])
        return orders

    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels order by order ID."""
        cancelled_order = self.api.private.cancel_order(order_id)
        return self._native_order(cancelled_order.data["cancelOrder"])

    def cancel_all_orders(self, instrument: str = None, **kwargs):
        cancelled_orders = self.api.private.cancel_all_orders(market=instrument)
        return cancelled_orders

    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account."""
        fills = self.api.private.get_fills(market=instrument)
        trades = self._convert_fills(fills.data["fills"])
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

        Parameters
        ----------
        instrument : str, optional
            The trading instrument name (symbol). The default is None.

        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """
        status = kwargs["status"].upper() if "status" in kwargs else "OPEN"
        positions = self.api.private.get_positions(market=instrument, status=status)
        positions = self._convert_position_list(positions.data["positions"])
        return positions

    def get_markets(self):
        # Get Markets
        markets = self.api.public.get_markets()
        market_df = pd.DataFrame(markets.data["markets"])
        return market_df

    def get_orderbook(self, instrument: str) -> OrderBook:
        # Get Orderbook
        orderbook = self.autodata.L2(instrument=instrument)
        return orderbook

    def get_market_stats(self):
        # Get Market Statistics
        market_statistics = self.api.public.get_stats(
            market=constants.MARKET_ADA_USD,
            days=1,
        )
        return market_statistics

    def get_funding(self, dtime):
        # Funding Data
        historical_funding = self.api.public.get_historical_funding(
            market=constants.MARKET_BTC_USD, effective_before_or_at=dtime
        )

        funding_df = pd.DataFrame(historical_funding.data["historicalFunding"])
        funding_df["rate"] = pd.to_numeric(funding_df["rate"], errors="coerce")
        funding_df["price"] = pd.to_numeric(funding_df["price"], errors="coerce")
        funding_df["effectiveAt"] = pd.to_datetime(
            funding_df["effectiveAt"], format="%Y-%m-%dT%H:%M:%S.%f"
        )
        funding_df["rate"] = funding_df["rate"] * 100

        return funding_df

    def get_candles(
        self,
    ):
        # Candlestick Data
        candles = self.api.public.get_candles(
            market=constants.MARKET_BTC_USD,
            resolution="1MIN",
        )
        candles = pd.DataFrame(candles.data["candles"])
        candles.apply(pd.to_numeric, errors="ignore").info()
        return candles

    def _get_account(self, eth_address: str = None):
        if eth_address is None:
            eth_address = self.api.default_address
        account = self.api.private.get_account(eth_address)
        return account.data["account"]

    def _get_market(self, instrument: str):
        """Returns the dydx market constant from an instrument."""
        pass

    def _native_order(self, dydx_order):
        """Helper method to convert a dydx order into a native AutoTrader Order."""

        direction = 1 if dydx_order["side"] == "BUY" else -1
        order_limit_price = (
            float(dydx_order["price"]) if dydx_order["price"] is not None else None
        )
        order_stop_price = (
            float(dydx_order["triggerPrice"])
            if dydx_order["triggerPrice"] is not None
            else None
        )
        order = Order(
            instrument=dydx_order["market"],
            order_type=dydx_order["type"],
            status=dydx_order["status"].lower(),
            id=dydx_order["id"],
            direction=direction,
            size=float(dydx_order["size"]),
            order_limit_price=order_limit_price,
            order_stop_price=order_stop_price,
        )
        return order

    def _conver_order_list(self, order_list):
        orders = {}
        for order in order_list:
            native_order = self._native_order(order)
            orders[native_order.id] = native_order
        return orders

    def _native_position(self, dydx_position):
        """Converts a dydx position to a native AutoTrader Position."""
        if dydx_position["side"] == "SHORT":
            position_units = {
                "short_units": float(dydx_position["size"]),
                "short_PL": dydx_position["unrealizedPnl"],
            }
        else:
            position_units = {
                "long_units": float(dydx_position["size"]),
                "long_PL": dydx_position["unrealizedPnl"],
            }

        native_position = Position(
            instrument=dydx_position["market"],
            net_position=float(dydx_position["size"]),
            PL=dydx_position["unrealizedPnl"],
            entry_price=float(dydx_position["entryPrice"]),
            **position_units,
        )
        return native_position

    def _convert_position_list(self, dydx_position_list):
        positions = {}
        for position in dydx_position_list:
            positions[position["market"]] = self._native_position(position)
        return positions

    def _native_trade(self, dydx_fill: dict):
        """Converts a dydx fill to a native AutoTrader trade."""
        direction = 1 if dydx_fill["side"] == "BUY" else -1

        native_trade = Trade(
            instrument=dydx_fill["market"],
            order_price=None,
            order_time=None,
            order_type=dydx_fill["type"].lower(),
            size=float(dydx_fill["size"]),
            fill_time=dydx_fill["createdAt"],
            fill_price=float(dydx_fill["price"]),
            fill_direction=direction,
            fee=dydx_fill["fee"],
            id=dydx_fill["id"],
            order_id=dydx_fill["orderId"],
        )

        return native_trade

    def _convert_fills(self, dydx_fills: list):
        """Converts an array of fills to a Trades dictionary."""
        trades = {}
        for trade in dydx_fills:
            trades[trade["id"]] = self._native_trade(trade)
        return trades

    def get_instrument_details(self, instrument):
        """Returns details of the instrument provided."""
        markets = self.api.public.get_markets()
        try:
            details = markets.data["markets"][instrument]
        except KeyError:
            raise Exception(f"The requested instrument '{instrument}' is invalid.")
        return details

    def _check_order_precision(self, order: Order):
        """Enforces that an order has an allowable precision for price and size."""
        details = self.get_instrument_details(order.instrument)
        stepsize = float(details["stepSize"])
        ticksize = float(details["tickSize"])
        order.size = Decimal(str(order.size)) - Decimal(str(order.size)) % Decimal(
            str(stepsize)
        )

        if order.order_type == "limit":
            order.order_limit_price = Decimal(str(order.order_limit_price)).quantize(
                Decimal(str(ticksize))
            )

        elif order.order_type == "stop-limit":
            order.order_limit_price = Decimal(str(order.order_limit_price)).quantize(
                Decimal(str(ticksize))
            )
            order.order_stop_price = Decimal(str(order.order_stop_price)).quantize(
                Decimal(str(ticksize))
            )

        return order
