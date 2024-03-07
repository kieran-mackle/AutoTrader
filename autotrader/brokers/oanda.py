import sys
import time
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from autotrader.brokers.broker import Broker
from autotrader.brokers.trading import Order, IsolatedPosition, Position, Trade

try:
    import v20
except ImportError:
    raise Exception("Please use 'pip install v20' to trade using Oanda v20 API.")


class Broker(Broker):
    def __init__(self, config: dict):
        """Create v20 context."""
        self.API = config["API"]
        self.ACCESS_TOKEN = config["ACCESS_TOKEN"]
        self.port = config["PORT"]
        self.ACCOUNT_ID = config["ACCOUNT_ID"]
        self.api = v20.Context(
            hostname=self.API, token=self.ACCESS_TOKEN, port=self.port
        )

        self.STREAM_API = "stream-fxpractice.oanda.com"
        self.stream = v20.Context(
            hostname=self.STREAM_API, token=self.ACCESS_TOKEN, port=self.port
        )
        self.open_positions = {}

        # Assign data broker
        self._data_broker = self

    def __repr__(self):
        return "AutoTrader-Oanda Broker Interface"

    def __str__(self):
        return "AutoTrader-Oanda Broker Interface"

    @property
    def data_broker(self):
        return self._data_broker

    def get_NAV(self) -> float:
        """Returns Net Asset Value of account."""
        self._check_connection()
        response = self.api.account.get(accountID=self.ACCOUNT_ID)
        return response.body["account"].NAV

    def get_balance(self) -> float:
        """Returns account balance."""
        self._check_connection()
        response = self.api.account.get(accountID=self.ACCOUNT_ID)
        return response.body["account"].balance

    def place_order(self, order: Order, **kwargs):
        """Submits order to broker."""
        self._check_connection()

        # Call order to set order time
        order()

        # Submit order
        if order.order_type == "market":
            response = self._place_market_order(order)
        elif order.order_type == "stop-limit":
            response = self._place_stop_limit_order(order)
        elif order.order_type == "limit":
            response = self._place_limit_order(order)
        elif order.order_type == "close":
            response = self._close_position(order.instrument)
        elif order.order_type == "modify":
            response = self._modify_trade(order)
        else:
            print("Order type not recognised.")

        # Check response
        # output = self._check_response(response)

        return response

    def get_orders(self, instrument=None, **kwargs) -> dict:
        """Get all pending orders in the account."""
        self._check_connection()
        response = self.api.order.list_pending(
            accountID=self.ACCOUNT_ID, instrument=instrument
        )
        oanda_pending_orders = response.body["orders"]
        orders = {}

        for order in oanda_pending_orders:
            if order.type != "TAKE_PROFIT" and order.type != "STOP_LOSS":
                new_order = {}
                new_order["id"] = order.id
                new_order["status"] = "open"
                new_order["order_type"] = order.type
                new_order["order_stop_price"] = order.price
                new_order["order_limit_price"] = order.price
                new_order["direction"] = np.sign(order.units)
                new_order["order_time"] = order.createTime
                new_order["instrument"] = order.instrument
                new_order["size"] = abs(order.units)
                new_order["order_price"] = order.price

                # Check for take profit
                if order.takeProfitOnFill is not None:
                    new_order["take_profit"] = order.takeProfitOnFill.price

                # Check for stop loss
                if order.stopLossOnFill is not None:
                    new_order["stop_loss"] = order.stopLossOnFill.price
                    new_order["stop_type"] = "limit"

                if instrument is not None and order.instrument == instrument:
                    orders[order.id] = Order._from_dict(new_order)
                elif instrument is None:
                    orders[order.id] = Order._from_dict(new_order)

        return orders

    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels pending order by ID."""
        self._check_connection()
        self.api.order.cancel(accountID=self.ACCOUNT_ID, orderSpecifier=str(order_id))

    def get_trades(self, instrument=None, **kwargs) -> list:
        """Returns the trades (fills) made by the account."""
        self._check_connection()
        response = self.api.trade.list_open(
            accountID=self.ACCOUNT_ID, state="CLOSED", instrument=instrument
        )
        oanda_trades = response.body["trades"]

        trades = {}
        for trade in oanda_trades:
            trade_dict = self._oanda_trade_to_dict(trade)

            native_trade = Trade(
                instrument=trade_dict["instrument"],
                order_price=None,
                order_time=None,
                order_type=None,
                size=float(trade_dict["size"]),
                fill_time=trade_dict["time_filled"],
                fill_price=float(trade_dict["fill_price"]),
                fill_direction=trade_dict["direction"],
                fee=trade_dict["fees"],
                id=trade_dict["id"],
            )

            trades[trade.id] = native_trade

        return trades

    def get_positions(self, instrument: str = None, **kwargs) -> dict:
        """Gets the current positions open on the account."""
        self._check_connection()
        response = self.api.position.list_open(accountID=self.ACCOUNT_ID)
        oanda_open_positions = response.body["positions"]
        open_positions = {}
        for position in oanda_open_positions:
            pos = {
                "instrument": position.instrument,
                "long_units": position.long.units,
                "long_PL": position.long.unrealizedPL,
                "long_margin": None,
                "short_units": position.short.units,
                "short_PL": position.short.unrealizedPL,
                "short_margin": None,
                "total_margin": position.marginUsed,
            }

            # fetch trade ID'strade_IDs
            trade_IDs = []
            if abs(pos["long_units"]) > 0:
                for ID in position.long.tradeIDs:
                    trade_IDs.append(ID)
            if abs(pos["short_units"]) > 0:
                for ID in position.short.tradeIDs:
                    trade_IDs.append(ID)

            pos["trade_IDs"] = trade_IDs

            if instrument is not None and position.instrument == instrument:
                open_positions[position.instrument] = Position(**pos)
            elif instrument is None:
                open_positions[position.instrument] = Position(**pos)

        return open_positions

    def get_candles(
        self,
        instrument: str,
        granularity: str = None,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        """Get the historical OHLCV candles for an instrument."""
        """Retrieves historical price data of a instrument from Oanda v20 API.

        Parameters
        ----------
        instrument : str
            The instrument to fetch data for.

        granularity : str
            The candlestick granularity, specified as a TimeDelta string
            (eg. '30s', '5min' or '1d').

        count : int, optional
            The number of candles to fetch (maximum 5000). The default is None.

        start_time : datetime, optional
            The data start time. The default is None.

        end_time : datetime, optional
            The data end time. The default is None.

        Returns
        -------
        data : DataFrame
            The price data, as an OHLC DataFrame.

        Notes
        -----
            If a candlestick count is provided, only one of start time or end
            time should be provided. If neither is provided, the N most
            recent candles will be provided. If both are provided, the count
            will be ignored, and instead the dates will be used.
        """
        gran_map = {
            5: "S5",
            10: "S10",
            15: "S15",
            30: "S30",
            60: "M1",
            120: "M2",
            240: "M4",
            300: "M5",
            600: "M10",
            900: "M15",
            1800: "M30",
            3600: "H1",
            7200: "H2",
            10800: "H3",
            14400: "H4",
            21600: "H6",
            28800: "H8",
            43200: "H12",
            86400: "D",
            604800: "W",
            2419200: "M",
        }
        granularity = gran_map[pd.Timedelta(granularity).total_seconds()]

        if count is not None:
            # either of count, start_time+count, end_time+count (or start_time+end_time+count)
            # if count is provided, count must be less than 5000
            if start_time is None and end_time is None:
                # fetch count=N most recent candles
                response = self.api.instrument.candles(
                    instrument, granularity=granularity, count=count
                )
                data = self._response_to_df(response)

            elif start_time is not None and end_time is None:
                # start_time + count
                from_time = start_time.timestamp()
                response = self.api.instrument.candles(
                    instrument, granularity=granularity, count=count, fromTime=from_time
                )
                data = self._response_to_df(response)

            elif end_time is not None and start_time is None:
                # end_time + count
                to_time = end_time.timestamp()
                response = self.api.instrument.candles(
                    instrument, granularity=granularity, count=count, toTime=to_time
                )
                data = self._response_to_df(response)

            else:
                from_time = start_time.timestamp()
                to_time = end_time.timestamp()

                # try to get data
                response = self.api.instrument.candles(
                    instrument,
                    granularity=granularity,
                    fromTime=from_time,
                    toTime=to_time,
                )

                # If the request is rejected, max candles likely exceeded
                if response.status != 200:
                    data = self._get_extended_oanda_data(
                        instrument, granularity, from_time, to_time
                    )
                else:
                    data = self._response_to_df(response)

        else:
            # count is None
            # Assume that both start_time and end_time have been specified.
            from_time = start_time.timestamp()
            to_time = end_time.timestamp()

            # try to get data
            response = self.api.instrument.candles(
                instrument, granularity=granularity, fromTime=from_time, toTime=to_time
            )

            # If the request is rejected, max candles likely exceeded
            if response.status != 200:
                data = self._get_extended_oanda_data(
                    instrument, granularity, from_time, to_time
                )
            else:
                data = self._response_to_df(response)

        return data

    def get_orderbook(self, instrument: str, *args, **kwargs):
        """Get the orderbook for an instrument."""
        response = self.api.pricing.get(
            accountID=self.ACCOUNT_ID, instruments=instrument
        )
        prices = response.body["prices"][0].dict()

        # Unify format
        orderbook = {}
        for side in ["bids", "asks"]:
            orderbook[side] = []
            for level in prices[side]:
                orderbook[side].append(
                    {"price": level["price"], "size": level["liquidity"]}
                )
        return orderbook

    def get_public_trades(self, *args, **kwargs):
        """Get the public trade history for an instrument."""
        raise NotImplementedError

    def _get_extended_oanda_data(self, instrument, granularity, from_time, to_time):
        """Returns historical data between a date range."""
        max_candles = 5000

        my_int = self._granularity_to_seconds(granularity)
        end_time = to_time - my_int
        partial_from = from_time
        response = self.api.instrument.candles(
            instrument,
            granularity=granularity,
            fromTime=partial_from,
            count=max_candles,
        )
        data = self._response_to_df(response)
        last_time = data.index[-1].timestamp()

        while last_time < end_time:
            candles = min(max_candles, int((end_time - last_time) / my_int))
            partial_from = last_time
            response = self.api.instrument.candles(
                instrument,
                granularity=granularity,
                fromTime=partial_from,
                count=candles,
            )

            partial_data = self._response_to_df(response)
            data = pd.concat([data, partial_data])
            last_time = data.index[-1].timestamp()

        return data

    @staticmethod
    def _granularity_to_seconds(granularity: str):
        """Converts the granularity to time in seconds."""
        allowed_granularities = (
            "S5",
            "S10",
            "S15",
            "S30",
            "M1",
            "M2",
            "M4",
            "M5",
            "M10",
            "M15",
            "M30",
            "H1",
            "H2",
            "H3",
            "H4",
            "H6",
            "H8",
            "H12",
            "D",
            "W",
            "M",
        )

        if granularity not in allowed_granularities:
            raise Exception(
                f"Invalid granularity '{granularity}' for " + "{feed} data feed."
            )

        letter = granularity[0]

        if len(granularity) > 1:
            number = float(granularity[1:])
        else:
            number = 1

        conversions = {"S": 1, "M": 60, "H": 60 * 60, "D": 60 * 60 * 24}
        my_int = conversions[letter] * number

        return my_int

    def _response_to_df(self, response):
        """Function to convert api response into a pandas dataframe."""
        try:
            candles = response.body["candles"]
        except KeyError:
            raise Exception(
                "Error dowloading data - please check instrument"
                + " format and try again."
            )

        times = []
        close_price, high_price, low_price, open_price, volume = [], [], [], [], []

        if self._allow_dancing_bears:
            # Allow all candles
            for candle in candles:
                times.append(candle.time)
                close_price.append(float(candle.mid.c))
                high_price.append(float(candle.mid.h))
                low_price.append(float(candle.mid.l))
                open_price.append(float(candle.mid.o))
                volume.append(float(candle.volume))

        else:
            # Only allow complete candles
            for candle in candles:
                if candle.complete:
                    times.append(candle.time)
                    close_price.append(float(candle.mid.c))
                    high_price.append(float(candle.mid.h))
                    low_price.append(float(candle.mid.l))
                    open_price.append(float(candle.mid.o))
                    volume.append(float(candle.volume))

        dataframe = pd.DataFrame(
            {
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": close_price,
                "Volume": volume,
            }
        )
        dataframe.index = pd.to_datetime(times)
        dataframe.drop_duplicates(inplace=True)

        return dataframe

    def get_isolated_positions(self, instrument: str = None, **kwargs):
        """Returns isolated positions for the specified instrument.

        Parameters
        ----------
        instrument : str, optional
            The instrument to fetch trades under. The default is None.
        """
        self._check_connection()
        response = self.api.trade.list_open(accountID=self.ACCOUNT_ID)
        oanda_open_trades = response.body["trades"]

        open_trades = {}
        for trade in oanda_open_trades:
            new_trade = self._oanda_trade_to_dict(trade)

            # Filter by instrument
            if instrument is not None and trade.instrument in instrument:
                open_trades[trade.id] = IsolatedPosition(**new_trade)
            elif instrument is None:
                open_trades[trade.id] = IsolatedPosition(**new_trade)

        return open_trades

    @staticmethod
    def _oanda_trade_to_dict(trade) -> dict:
        """Converts an Oanda Trade object to a dictionary."""
        new_trade = {}
        related_orders = []
        new_trade["instrument"] = trade.instrument
        new_trade["time_filled"] = trade.openTime
        new_trade["fill_price"] = trade.price
        new_trade["size"] = abs(trade.currentUnits)
        new_trade["id"] = trade.id
        new_trade["direction"] = np.sign(trade.currentUnits)
        new_trade["margin_required"] = trade.marginUsed
        new_trade["unrealised_PL"] = trade.unrealizedPL
        new_trade["fees"] = trade.financing
        new_trade["status"] = trade.state.lower()

        # Check for take profit
        if trade.takeProfitOrder is not None:
            new_trade["take_profit"] = trade.takeProfitOrder.price
            related_orders.append(trade.takeProfitOrder.id)

        # Check for stop loss
        if trade.stopLossOrder is not None:
            new_trade["stop_loss"] = trade.stopLossOrder.price
            new_trade["stop_type"] = "limit"
            related_orders.append(trade.stopLossOrder.id)

        if related_orders is not None:
            new_trade["related_orders"] = related_orders

        return new_trade

    def get_trade_details(self, trade_ID: int):
        """Returns the details of the trade specified by trade_ID.
        WARNING: THIS METHOD HAS BEEN MADE REDUNDANT BY 'get_trades' METHOD.
        """
        raise DeprecationWarning(
            "This method is deprecated, and will "
            + "be removed in a future release. Please use the "
            + "get_trades method instead."
        )
        response = self.api.trade.list(accountID=self.ACCOUNT_ID, ids=int(trade_ID))
        trade = response.body["trades"][0]

        details = {
            "direction": int(np.sign(trade.currentUnits)),
            "order_time": datetime.datetime.strptime(
                trade.openTime[:-4], "%Y-%m-%dT%H:%M:%S.%f"
            ),
            "instrument": trade.instrument,
            "size": trade.currentUnits,
            "order_price": trade.price,
            "order_ID": trade.id,
            "time_filled": trade.openTime,
            "entry_price": trade.price,
            "unrealised_PL": trade.unrealizedPL,
            "margin_required": trade.marginUsed,
        }

        # Get associated trades
        related = []
        try:
            details["take_profit"] = trade.takeProfitOrder.price
            related.append(trade.takeProfitOrder.id)
        except:
            pass

        try:
            details["stop_loss"] = trade.stopLossOrder.price
            related.append(trade.stopLossOrder.id)
        except:
            pass
        details["related_orders"] = related

        # TODO - veryify functionality of below...
        return Trade(trade)

    def get_position(self, instrument: str) -> Position:
        """Gets position from Oanda."""
        self._check_connection()
        response = self.api.position.get(
            instrument=instrument, accountID=self.ACCOUNT_ID
        )
        # TODO - convert to position
        return response.body["position"]

    def get_summary(self):
        """Returns account summary."""
        self._check_connection()
        # response = self.api.account.get(accountID=self.ACCOUNT_ID)
        response = self.api.account.summary(accountID=self.ACCOUNT_ID)
        return response

    def get_data(self, pair: str, period: int, interval: str) -> pd.DataFrame:
        self._check_connection()
        response = self.api.instrument.candles(
            pair, granularity=interval, count=period, dailyAlignment=0
        )
        data = self.response_to_df(response)
        return data

    def check_trade_size(self, instrument: str, units: float) -> float:
        """Checks the requested trade size against the minimum trade size
        allowed for the currency pair.
        """
        response = self.api.account.instruments(
            accountID=self.ACCOUNT_ID, instruments=instrument
        )
        # minimum_units = response.body['instruments'][0].minimumTradeSize
        trade_unit_precision = response.body["instruments"][0].tradeUnitsPrecision
        return round(units, trade_unit_precision)

    def update_data(
        self, instrument: str, granularity: str, data: pd.DataFrame
    ) -> pd.DataFrame:
        """Attempts to construct the latest candle when there is a delay in the
        api feed.
        """
        self._check_connection()
        granularity_details = self.deconstruct_granularity(granularity)
        secs = granularity_details["seconds"]
        mins = granularity_details["minutes"]
        hrs = granularity_details["hours"]
        days = granularity_details["days"]

        small_granularity = self.get_reduced_granularity(granularity_details, 25)

        # Get data equivalent of last candle's granularity
        time_now = datetime.now()
        start_time = time_now - timedelta(
            seconds=secs, minutes=mins, hours=hrs, days=days
        )
        latest_data = self.get_historical_data(
            instrument, small_granularity, start_time.timestamp(), time_now.timestamp()
        )

        # Get latest price data
        latest_close = latest_data.Close.values[0]

        open_price = data.Close.values[-1]
        close_price = latest_close
        high_price = max(latest_data.High.values)
        low_price = min(latest_data.Low.values)
        last_time = data.index[-1]
        stripped_time = datetime.strptime(
            last_time.strftime("%Y-%m-%d %H:%M:%S%z"), "%Y-%m-%d %H:%M:%S%z"
        )
        new_time = stripped_time + timedelta(
            seconds=secs, minutes=mins, hours=hrs, days=days
        )

        new_candle = pd.DataFrame(
            {
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": close_price,
            },
            index=[new_time],
        )

        new_data = pd.concat([data, new_candle])

        return new_data

    def get_historical_data(self, instrument, interval, from_time, to_time):
        self._check_connection()

        response = self.api.instrument.candles(
            instrument, granularity=interval, fromTime=from_time, toTime=to_time
        )

        data = self.response_to_df(response)

        return data

    def deconstruct_granularity(self, granularity: str):
        """Returns a dict with the seconds, minutes, hours and days
        corresponding to a granularity.
        """

        # Get letter to determine timeframe (eg. M)
        letter = granularity[0]

        # Get timeframe multiple (eg. 15)
        if len(granularity) > 1:
            number = float(granularity[1:])
        else:
            number = 1

        if letter == "S":
            seconds = number
            minutes = 0
            hours = 0
            days = 0

        elif letter == "M":
            seconds = 0
            minutes = number
            hours = 0
            days = 0

        elif letter == "H":
            seconds = 0
            minutes = 0
            hours = number
            days = 0

        else:
            seconds = 0
            minutes = 0
            hours = 0
            days = number

        granularity_details = {
            "seconds": seconds,
            "minutes": minutes,
            "hours": hours,
            "days": days,
        }

        return granularity_details

    def get_reduced_granularity(self, granularity_details, fraction):
        """Returns a candlestick granularity as a fraction of given granularity"""
        secs = granularity_details["seconds"]
        mins = granularity_details["minutes"]
        hrs = granularity_details["hours"]
        days = granularity_details["days"]

        total_seconds = secs + 60 * mins + 60 * 60 * hrs + 60 * 60 * 24 * days

        fractional_seconds = total_seconds / fraction

        seconds = fractional_seconds
        minutes = fractional_seconds / 60
        hours = fractional_seconds / (60 * 60)
        days = fractional_seconds / (60 * 60 * 24)

        if days > 1:
            letter = "D"
            number = 1
            reduced_granularity = letter

        elif hours > 1:
            base = 2
            letter = "H"
            number = base * round(hours / base)
            if number > 12:
                number = 12
            reduced_granularity = letter + str(number)

        elif minutes > 1:
            base = 15
            letter = "M"
            number = base * round(minutes / base)
            if number > 30:
                number = 30
            reduced_granularity = letter + str(number)

        else:
            base = 15
            letter = "S"
            number = base * round(seconds / base)
            if number > 30:
                number = 30
            reduced_granularity = letter + str(number)

        if reduced_granularity[1:] == "0":
            reduced_granularity = reduced_granularity[0] + "1"

        return reduced_granularity

    def get_pip_location(self, instrument: str):
        """Returns the pip location of the requested instrument."""
        response = self.api.account.instruments(self.ACCOUNT_ID, instruments=instrument)
        return response.body["instruments"][0].pipLocation

    def _check_connection(self) -> None:
        """Connects to Oanda v20 REST API. An initial call is performed to check
        for a timeout error.
        """
        # TODO - improve this - currently doubles the poll rate
        for atempt in range(10):
            try:
                # Attempt basic task to check connection
                self.api.account.get(accountID=self.ACCOUNT_ID)

            except BaseException:
                # Error has occurred
                ex_type, ex_value, ex_traceback = sys.exc_info()

                # Extract unformatter stack traces as tuples
                trace_back = traceback.extract_tb(ex_traceback)

                # Format stacktrace
                stack_trace = list()

                for trace in trace_back:
                    trade_string = "File : %s , Line : %d, " % (
                        trace[0],
                        trace[1],
                    ) + "Func.Name : %s, Message : %s" % (trace[2], trace[3])
                    stack_trace.append(trade_string)

                print("\nWARNING FROM OANDA API: The following exception was caught.")
                print("Time: {}".format(datetime.now().strftime("%b %d %H:%M:%S")))
                print("Exception type : %s " % ex_type.__name__)
                print("Exception message : %s" % ex_value)
                print("Stack trace : %s" % stack_trace)
                print("  Attempting to reconnect to Oanda v20 API.")

                time.sleep(3)
                api = v20.Context(
                    hostname=self.API, token=self.ACCESS_TOKEN, port=self.port
                )
                self.api = api

            else:
                break

        else:
            print("FATAL: All attempts to connect to Oanda API have failed.")

    def _place_market_order(self, order: Order):
        """Places market order."""
        self._check_connection()
        stop_loss_order = self._get_stop_loss_order(order)
        take_profit_details = self._get_take_profit_details(order)

        # Check position size
        size = self.check_trade_size(order.instrument, order.size)

        response = self.api.order.market(
            accountID=self.ACCOUNT_ID,
            instrument=order.instrument,
            units=order.direction * size,
            takeProfitOnFill=take_profit_details,
            **stop_loss_order,
        )

        return response

    def _place_stop_limit_order(self, order):
        """Places MarketIfTouchedOrder with Oanda.
        https://developer.oanda.com/rest-live-v20/order-df/
        """
        # TODO - this submits market if touched, options below
        ordertype = "MARKET_IF_TOUCHED"  # 'MARKET_IF_TOUCHED' # 'STOP', 'LIMIT'
        self._check_connection()

        stop_loss_order = self._get_stop_loss_order(order)
        take_profit_details = self._get_take_profit_details(order)

        # Check and correct order stop price
        price = self._check_precision(order.instrument, order.order_stop_price)
        trigger_condition = order.trigger_price
        size = self.check_trade_size(order.instrument, order.size)

        # Need to test cases when no stop/take is provided (as None type)
        response = self.api.order.market_if_touched(
            accountID=self.ACCOUNT_ID,
            instrument=order.instrument,
            units=order.direction * size,
            price=str(price),
            type=ordertype,
            takeProfitOnFill=take_profit_details,
            triggerCondition=trigger_condition,
            **stop_loss_order,
        )
        return response

    def _place_stop_order(self, order: Order):
        """Places a stop order."""
        # TODO - implement this method
        self._check_connection()

        stop_loss_order = self._get_stop_loss_order(order)
        take_profit_details = self._get_take_profit_details(order)

        # Check and correct order stop price
        price = self._check_precision(order.instrument, order.order_stop_price)
        price_bound = self._check_precision(order.instrument, order.order_stop_price)

        trigger_condition = order.trigger_price
        size = self.check_trade_size(order.instrument, order.size)

        response = self.api.order.stop(
            accountID=self.ACCOUNT_ID,
            instrument=order.instrument,
            units=order.direction * size,
            price=str(price),
            priceBound=str(price_bound),
            triggerCondition=trigger_condition,
            takeProfitOnFill=take_profit_details,
            **stop_loss_order,
        )
        return response

    def _place_limit_order(self, order: Order):
        """PLaces a limit order."""
        self._check_connection()

        stop_loss_order = self._get_stop_loss_order(order)
        take_profit_details = self._get_take_profit_details(order)

        # Check and correct order stop price
        price = self._check_precision(order.instrument, order.order_limit_price)

        trigger_condition = order.trigger_price
        size = self.check_trade_size(order.instrument, order.size)

        response = self.api.order.limit(
            accountID=self.ACCOUNT_ID,
            instrument=order.instrument,
            units=order.direction * size,
            price=str(price),
            takeProfitOnFill=take_profit_details,
            triggerCondition=trigger_condition,
            **stop_loss_order,
        )
        return response

    def _modify_trade(self, order):
        """Modifies the take profit and/or stop loss of an existing trade.

        Parameters
        ----------
        order : TYPE
            DESCRIPTION.
        """
        # Get ID of trade to modify
        modify_trade_id = order.related_orders
        trade = self.api.trade.get(
            accountID=self.ACCOUNT_ID, tradeSpecifier=modify_trade_id
        ).body["trade"]

        if order.take_profit is not None:
            # Modify trade take-profit
            tpID = trade.takeProfitOrder.id

            # Cancel existing TP
            self.api.order.cancel(self.ACCOUNT_ID, tpID)

            # Create new TP
            tp_price = self._check_precision(order.instrument, order.take_profit)
            new_tp_order = self.api.order.TakeProfitOrder(
                tradeID=str(modify_trade_id), price=str(tp_price)
            )
            response = self.api.order.create(
                accountID=self.ACCOUNT_ID, order=new_tp_order
            )
            self._check_response(response)

        if order.stop_loss is not None:
            # Modify trade stop-loss
            slID = trade.stopLossOrder.id

            # Cancel existing SL
            self.api.order.cancel(self.ACCOUNT_ID, slID)

            # Create new SL
            sl_price = self._check_precision(order.instrument, order.stop_loss)
            new_sl_order = self.api.order.StopLossOrder(
                tradeID=str(modify_trade_id), price=str(sl_price)
            )
            response = self.api.order.create(
                accountID=self.ACCOUNT_ID, order=new_sl_order
            )
            self._check_response(response)

    def _get_stop_loss_order(self, order: Order) -> dict:
        """Constructs stop loss order dictionary."""
        self._check_connection()
        if order.stop_type is not None:
            price = self._check_precision(order.instrument, order.stop_loss)

            if order.stop_type == "trailing":
                # Trailing stop loss order
                SL_type = "trailingStopLossOnFill"

                # Calculate stop loss distance
                if order.stop_distance is None:
                    # Calculate stop distance from stop loss price provided
                    if order._working_price is not None:
                        working_price = order._working_price
                    else:
                        if order.order_type == "market":
                            # Get current market price
                            last = self._get_price(order.instrument)
                            working_price = (
                                last.closeoutBid
                                if order.direction < 0
                                else last.closeoutAsk
                            )
                        elif order.order_type in ["limit", "stop-limit"]:
                            working_price = order.order_limit_price
                    distance = abs(working_price - order.stop_loss)

                else:
                    # Calculate distance using provided pip distance
                    pip_value = 10 ** self.get_pip_location(order.instrument)
                    distance = abs(order.stop_distance * pip_value)

                # Construct stop loss order details
                distance = self._check_precision(order.instrument, distance)
                SL_details = {"distance": str(distance), "type": "TRAILING_STOP_LOSS"}
            else:
                SL_type = "stopLossOnFill"
                SL_details = {"price": str(price)}

            stop_loss_order = {SL_type: SL_details}

        else:
            stop_loss_order = {}

        return stop_loss_order

    def _get_take_profit_details(self, order: Order) -> dict:
        """Constructs take profit details dictionary."""
        self._check_connection()
        if order.take_profit is not None:
            price = self._check_precision(order.instrument, order.take_profit)
            take_profit_details = {"price": str(price)}
        else:
            take_profit_details = None

        return take_profit_details

    def _check_response(self, response):
        """Checks API response (currently only for placing orders)."""
        if response.status != 201:
            message = response.body["errorMessage"]
        else:
            message = "Success."

        output = {"Status": response.status, "Message": message}
        # TODO - print errors
        return output

    def _close_position(self, instrument, long_units=None, short_units=None, **kwargs):
        """Closes all open positions on an instrument."""
        self._check_connection()
        # Check if the position is long or short
        # Temp code to close all positions
        # Close all long units
        response = self.api.position.close(
            accountID=self.ACCOUNT_ID, instrument=instrument, longUnits="ALL"
        )

        # Close all short units
        response = self.api.position.close(
            accountID=self.ACCOUNT_ID, instrument=instrument, shortUnits="ALL"
        )

        # TODO - the code below makes no sense currently; specifically,
        # position.long.Units ????

        # open_position = self.get_open_positions(instrument)

        # if len(open_position) > 0:
        #     position = open_position['position']

        #     if long_units is None:
        #         long_units  = position.long.units
        #     if short_units is None:
        #         short_units = position.short.units

        #     if long_units > 0:
        #         response = self.api.position.close(accountID=self.ACCOUNT_ID,
        #                                            instrument=instrument,
        #                                            longUnits="ALL")

        #     elif short_units > 0:
        #         response = self.api.position.close(accountID=self.ACCOUNT_ID,
        #                                            instrument=instrument,
        #                                            shortUnits="ALL")

        #     else:
        #         print("There is no current position with {} to close.".format(instrument))
        #         response = None
        # else:
        #     response = None

        return response

    def _get_precision(self, instrument: str):
        """Returns the allowable precision for a given pair."""
        self._check_connection()
        response = self.api.account.instruments(
            accountID=self.ACCOUNT_ID, instruments=instrument
        )
        precision = response.body["instruments"][0].displayPrecision
        return precision

    def _check_precision(self, instrument, price):
        """Modify a price based on required ordering precision for pair."""
        N = self._get_precision(instrument)
        corrected_price = round(price, N)
        return corrected_price

    def _get_order_book(self, instrument: str):
        """Returns the order book of the instrument specified."""
        return self.get_orderbook(instrument)

    def _get_position_book(self, instrument: str):
        """Returns the position book of the instrument specified."""
        response = self.api.instrument.position_book(instrument)
        return response.body["positionBook"]

    def _get_price(self, instrument: str):
        """Returns the current price of the instrument."""
        response = self.api.pricing.get(
            accountID=self.ACCOUNT_ID, instruments=instrument
        )
        return response.body["prices"][0]

    @staticmethod
    def response_to_df(response: pd.DataFrame):
        """Function to convert api response into a pandas dataframe."""
        candles = response.body["candles"]
        times = []
        close_price, high_price, low_price, open_price = [], [], [], []

        for candle in candles:
            times.append(candle.time)
            close_price.append(float(candle.mid.c))
            high_price.append(float(candle.mid.h))
            low_price.append(float(candle.mid.l))
            open_price.append(float(candle.mid.o))

        dataframe = pd.DataFrame(
            {
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": close_price,
            }
        )
        dataframe.index = pd.to_datetime(times)

        return dataframe
