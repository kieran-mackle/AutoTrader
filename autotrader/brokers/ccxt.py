import time
import ccxt
import pandas as pd
from datetime import datetime, timezone
from autotrader.utilities import get_logger
from autotrader.brokers.broker import Broker
from autotrader.brokers.trading import OrderBook
from autotrader.brokers.trading import Order, Trade, Position


class Broker(Broker):
    def __init__(self, config: dict) -> None:
        """AutoTrader Broker Class constructor."""
        # Unpack config and connect to broker-side API
        self.exchange: str = config["exchange"]
        exchange_instance = getattr(ccxt, self.exchange)
        if "api_key" in config:
            ccxt_config = {
                "apiKey": config["api_key"],
                "secret": config["secret"],
                "options": config["options"],
                "password": config["password"],
            }
        else:
            ccxt_config = {}

        # Create logger
        self._logger = get_logger(
            name=f"{self.exchange}_broker", **config["logging_options"]
        )

        # Instantiate exchange connection
        self.api: ccxt.Exchange = exchange_instance(ccxt_config)

        # Set sandbox mode
        self._sandbox_str = ""
        if config.get("sandbox_mode", False):
            self.api.set_sandbox_mode(True)
            self._sandbox_str = " (sandbox mode)"

        # Load markets
        self._logger.info(f"Loading instruments for {self.exchange}.")
        markets = self.api.load_markets()
        self.base_currency = config["base_currency"]

        # Assign data broker
        self._data_broker = self

        # Stored instrument precisions
        self._instrument_precisions = {}

    def __repr__(self):
        return (
            f"AutoTrader-{self.exchange[0].upper()}"
            + f"{self.exchange[1:].lower()} interface"
            + self._sandbox_str
        )

    def __str__(self):
        return self.__repr__()

    @property
    def data_broker(self):
        return self._data_broker

    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account."""
        return self.api.fetch_balance()[self.base_currency]["total"]

    def get_balance(self, instrument: str = None) -> float:
        """Returns account balance."""
        # TODO - check a pair hasnt been requested
        instrument = self.base_currency if instrument is None else instrument
        balances = self.api.fetch_balance()
        if instrument in balances:
            return balances[instrument]["total"]
        else:
            return 0

    def place_order(self, order: Order, **kwargs) -> None:
        """Place an order."""
        order()

        # Check order meets limits
        limits: dict = self.api.markets.get(order.instrument, {}).get("limits", {})
        if limits.get("amount") is not None:
            if order.size < limits["amount"]["min"]:
                # Order too small
                self._logger.warning(f"Order below minimum size: {order}")
                return None

        # Add order params
        self._add_params(order)

        # Submit order to broker
        if order.order_type == "modify":
            placed_order = self._modify_order(order)

        else:
            # Regular order
            side = "buy" if order.direction > 0 else "sell"

            # Submit the order
            try:
                placed_order = self.api.create_order(
                    symbol=order.instrument,
                    type=order.order_type,
                    side=side,
                    amount=abs(order.size),
                    price=order.order_limit_price,
                    params=order.ccxt_params,
                )
            except Exception as e:
                placed_order = e

        return placed_order

    def get_orders(
        self, instrument: str = None, order_status: str = "open", **kwargs
    ) -> dict[str, Order]:
        """Returns orders associated with the account."""
        for _ in range(2):
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
                        orders = self.api.fetch_open_orders(instrument, **kwargs)

                    elif order_status == "cancelled":
                        # Fetch cancelled orders
                        orders = self.api.fetch_canceled_and_closed_orders(
                            instrument, **kwargs
                        )

                    elif order_status == "closed":
                        # Fetch closed orders
                        orders = self.api.fetch_closed_orders(instrument, **kwargs)

                    elif order_status == "conditional":
                        # Fetch conditional orders
                        orders = self.api.fetch_open_orders(
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
            cancelled_order = self.api.cancel_order(id=order_id, **kwargs)

        except ccxt.errors.NetworkError:
            # Throttle then try again
            time.sleep(1)
            cancelled_order = self.api.cancel_order(id=order_id, **kwargs)

        except Exception as e:
            cancelled_order = e

        return cancelled_order

    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account."""
        try:
            trades_list = self.api.fetch_my_trades(instrument, **kwargs)
        except ccxt.errors.NetworkError:
            # Throttle then try again
            time.sleep(1)
            trades_list = self.api.fetch_my_trades(instrument, **kwargs)

        # Convert to native Trades
        trades = self._convert_list(trades_list, item_type="trade")
        return trades

    def get_positions(self, instrument: str = None, **kwargs) -> dict[str, Position]:
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
                        positions = self.api.fetch_positions(
                            symbols=None, params=kwargs
                        )
                        positions = self._convert_list(positions, item_type="position")

                    else:
                        raise Exception(
                            f"Exchange {self.exchange} does not have "
                            + "fetchPositions method."
                        )
                else:
                    # Get position in instrument provided
                    if self.api.has["fetchPosition"]:
                        position = self.api.fetch_position(instrument, params=kwargs)
                        if position is not None:
                            positions = {instrument: self._native_position(position)}
                        else:
                            positions = {}

                    elif self.api.has["fetchPositions"]:
                        positions = self.api.fetch_positions(
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

    def get_candles(
        self,
        instrument: str,
        granularity: str,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Retrieves historical price data of a instrument from an exchange
        instance of the CCXT package.

        Parameters
        ----------
        instrument : str
            The instrument to fetch data for.

        granularity : str
            The candlestick granularity (eg. "1m", "15m", "1h", "1d").

        count : int, optional
            The number of candles to fetch (maximum 5000). The default is None.

        start_time : datetime, optional
            The data start time. The default is None.

        end_time : datetime, optional
            The data end time. The default is None.

        Returns
        -------
        data : DataFrame
            The price data, as an OHLCV DataFrame.
        """
        # Check requested start and end times
        if end_time is not None and end_time > datetime.now(tz=end_time.tzinfo):
            raise Exception("End time cannot be later than the current time.")

        if start_time is not None and start_time > datetime.now(tz=start_time.tzinfo):
            raise Exception("Start time cannot be later than the current time.")

        if start_time is not None and end_time is not None and start_time > end_time:
            raise Exception("Start time cannot be later than the end time.")

        # Check granularity was provided
        if granularity is None:
            granularity = "1m"

        def fetch_between_dates():
            # Fetches data between two dates
            max_count = 1000
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)

            data = []
            while start_ts < end_ts:
                count = min(
                    max_count,
                    1
                    + (end_ts - start_ts)
                    / pd.Timedelta(granularity).total_seconds()
                    / 1000,
                )
                raw_data = self.api.fetch_ohlcv(
                    instrument,
                    timeframe=granularity,
                    since=start_ts,
                    limit=int(count),
                    params=kwargs,
                )
                # Append data
                data += raw_data

                # Increment start_ts
                start_ts = raw_data[-1][0] if len(raw_data) > 1 else end_ts

                # Sleep to throttle
                time.sleep(0.5)

            return data

        if count is not None:
            if start_time is None and end_time is None:
                # Fetch N most recent candles
                raw_data = self.api.fetch_ohlcv(
                    instrument, timeframe=granularity, limit=count, params=kwargs
                )
            elif start_time is not None and end_time is None:
                # Fetch N candles since start_time
                start_ts = (
                    None if start_time is None else int(start_time.timestamp() * 1000)
                )
                raw_data = self.api.fetch_ohlcv(
                    instrument,
                    timeframe=granularity,
                    since=start_ts,
                    limit=count,
                    params=kwargs,
                )
            elif end_time is not None and start_time is None:
                raise Exception(
                    "Fetching data from end_time and count is " + "not yet supported."
                )
            else:
                raw_data = fetch_between_dates()

        else:
            # Count is None
            try:
                assert start_time is not None and end_time is not None
                raw_data = fetch_between_dates()

            except AssertionError:
                raise Exception(
                    "When no count is provided, both start_time "
                    + "and end_time must be provided."
                )

        # Process data
        data = pd.DataFrame(
            raw_data, columns=["time", "Open", "High", "Low", "Close", "Volume"]
        ).set_index("time")
        data.index = pd.to_datetime(data.index, unit="ms")

        # TODO - normalise to UTC?

        return data

    def get_orderbook(
        self, instrument: str, limit: int = None, params: dict = None, **kwargs
    ) -> OrderBook:
        """Returns the orderbook"""
        params = params if params else {}
        response = self.api.fetch_order_book(
            symbol=instrument, limit=limit, params=params
        )

        # Unify format
        orderbook: dict[str, list] = {}
        for side in ["bids", "asks"]:
            orderbook[side] = []
            for level in response[side]:
                orderbook[side].append({"price": level[0], "size": level[1]})

        return OrderBook(instrument, orderbook)

    def get_public_trades(
        self,
        instrument: str,
        since: int = None,
        limit: int = None,
        params: dict = None,
        **kwargs,
    ):
        """Get the public trade history for an instrument."""
        params = params if params else {}
        ccxt_trades = self.api.fetch_trades(
            instrument, since=since, limit=limit, params=params
        )

        # Convert to standard form
        trades = []
        for trade in ccxt_trades:
            unified_trade = {
                "direction": 1 if trade["side"] == "buy" else -1,
                "price": float(trade["price"]),
                "size": float(trade["amount"]),
                "time": datetime.fromtimestamp(trade["timestamp"] / 1000),
            }
            trades.append(unified_trade)

        return trades

    def get_funding_rate(self, instrument: str, params: dict = None, **kwargs):
        """Returns the current funding rate."""
        params = params if params else {}
        response = self.api.fetch_funding_rate(instrument, params=params)
        fr_dict = {
            "symbol": instrument,
            "rate": response["fundingRate"],
            "time": response["fundingDatetime"],
        }
        return fr_dict

    def _ccxt_funding_history(
        self,
        instrument: str,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        params: dict = None,
    ):
        """Fetches the funding rate history."""
        params = params if params else {}

        def response_to_df(response):
            """Converts response to DataFrame."""
            times = []
            rates = []
            for chunk in response:
                times.append(pd.Timestamp(chunk["timestamp"], unit="ms"))
                rates.append(chunk["fundingRate"])
            return pd.DataFrame(data={"rate": rates}, index=times)

        def fetch_between_dates():
            # Fetches data between two dates
            count = 500
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)

            rate_hist = pd.DataFrame()
            while start_ts <= end_ts:
                response = self.api.fetch_funding_rate_history(
                    symbol=instrument, since=start_ts, limit=count, params=params
                )

                # Append results
                df = response_to_df(response)
                rate_hist = pd.concat([rate_hist, df])

                # Increment start_ts
                start_ts = int(df.index[-1].timestamp() * 1000)

                # Sleep for API limit
                time.sleep(1)

            return rate_hist

        if count is not None:
            if start_time is None and end_time is None:
                # Fetch N most recent candles
                response = self.api.fetch_funding_rate_history(
                    symbol=instrument, limit=count, params=params
                )
                rate_hist = response_to_df(response)
            elif start_time is not None and end_time is None:
                # Fetch N candles since start_time
                start_ts = (
                    None if start_time is None else int(start_time.timestamp() * 1000)
                )
                response = self.api.fetch_funding_rate_history(
                    symbol=instrument, since=start_ts, limit=count, params=params
                )
                rate_hist = response_to_df(response)
            elif end_time is not None and start_time is None:
                raise Exception(
                    "Fetching data from end_time and count is " + "not yet supported."
                )
            else:
                rate_hist = fetch_between_dates()

        else:
            # Count is None
            if start_time is not None and end_time is not None:
                rate_hist = fetch_between_dates()
            else:
                response = self.api.fetch_funding_rate_history(
                    symbol=instrument,
                    params=params,
                )
                rate_hist = response_to_df(response)

        return rate_hist

    def get_trade_details(self, trade_ID: str) -> dict:
        """Returns the details of the trade specified by trade_ID."""
        raise NotImplementedError(
            "This method is not available, and will "
            + "be deprecated with a future release. Please use the "
            + "get_trades method instead."
        )

    def _add_params(self, order: Order):
        """Translates an order to add CCXT parameters for the specific exchange."""
        if self.exchange.lower() == "bybit":
            # https://bybit-exchange.github.io/docs/v5/order/create-order
            if order.take_profit:
                self._safe_add(order.ccxt_params, "takeProfit", order.take_profit)
                self._safe_add(order.ccxt_params, "tpslMode", "Partial")
            if order.stop_loss:
                self._safe_add(order.ccxt_params, "stopLoss", order.stop_loss)
                self._safe_add(order.ccxt_params, "tpslMode", "Partial")
        # TODO - support more exchanges

    @staticmethod
    def _safe_add(map: dict, key: str, value: any):
        """Adds a value to a map only if it is not already in there."""
        if key not in map:
            map[key] = value

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

    def _modify_order(self, order: Order):
        """Modify the size, type and price of an existing order."""
        side = "buy" if order.direction > 0 else "sell"
        try:
            modified_order = self.api.edit_order(
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

    def get_precision(self, instrument: str, *args, **kwargs):
        """Returns the precision of the instrument."""
        # TODO - this method has been disabled as it was not properly handling precisions
        return None

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

    def _get_market(self, instrument: str, *args, **kwargs):
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

    def get_stepsize(self, instrument: str, *args, **kwargs):
        """Returns the stepsize for an instrument."""
        market = self._get_market(instrument)
        stepsize = float(market["limits"]["amount"]["min"])
        return stepsize

    def get_min_notional(self, instrument: str, *args, **kwargs):
        """Returns the minimum notional value a trade should hold."""
        market = self._get_market(instrument)
        min_notional = float(market["limits"]["cost"]["min"])
        return min_notional

    def get_ticksize(self, instrument: str, *args, **kwargs):
        """Returns the ticksize for an instrument."""
        market = self._get_market(instrument)
        try:
            ticksize = float(market["info"]["filters"][0]["tickSize"])
        except:
            raise Exception("Cannot retrieve ticksize.")
        return ticksize
