import os
import time
import pandas as pd
from typing import Union
from decimal import Decimal
from autotrader.brokers.trading import Order
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from autotrader.brokers.broker_utils import OrderBook

try:
    import ccxt
except ImportError:
    pass


class AutoData:
    """AutoData class to retrieve price data.

    Attributes
    ----------
    _home_curreny : str
        the home currency of the account (used for retrieving quote data)

    _allow_dancing_bears : bool
        Allow incomplete candlesticks in data retrieval.

    """

    def __init__(
        self,
        data_config: dict = None,
        allow_dancing_bears: bool = False,
        home_currency: str = None,
        **kwargs,
    ) -> None:
        """Instantiates AutoData.

        Parameters
        ----------
        data_config : dict, optional
            The configuration dictionary for the data source to be used. This
            is created automatically in autotrader.utilities.get_data_config.
            The default is None.
        allow_dancing_bears : bool, optional
            A flag to allow incomplete bars to be returned in the data. The
            default is False.
        home_currency : str, optional
            The home currency to use when fetching quote data. The default
            is None.
        kwargs : optional

        Returns
        -------
        None
            AutoData will be instantiated and ready to fetch price data.
        """
        # Merge kwargs and data_config
        if data_config is None and kwargs is not None:
            data_config = {}
        for key, item in kwargs.items():
            data_config.setdefault(key, item)

        def configure_local_feed(data_config):
            """Configures the attributes for a local data feed."""
            self._feed = "local"
            self.api = None
            self._data_directory = (
                data_config["data_dir"] if "data_dir" in data_config else None
            )
            self._spread_units = (
                data_config["spread_units"]
                if "spread_units" in data_config
                else "percentage"
            )
            self._spread = data_config["spread"] if "spread" in data_config else 0

        if not data_config:
            configure_local_feed({})
        else:
            self._feed = data_config["data_source"].lower()

            if data_config["data_source"].lower() == "oanda":
                API = data_config["API"]
                ACCESS_TOKEN = data_config["ACCESS_TOKEN"]
                self.ACCOUNT_ID = data_config["ACCOUNT_ID"]
                port = data_config["PORT"]

                try:
                    import v20

                    self.api = v20.Context(hostname=API, token=ACCESS_TOKEN, port=port)
                except ImportError:
                    raise Exception("Please install v20 to use the Oanda data feed.")

            elif data_config["data_source"].lower() == "ib":
                host = data_config["host"]
                port = data_config["port"]
                client_id = data_config["clientID"] + 1
                read_only = data_config["read_only"]
                account = data_config["account"]

                try:
                    import ib_insync
                    from autotrader.brokers.ib.utils import Utils as IB_Utils

                    self.api = ib_insync.IB()
                    self.IB_Utils = IB_Utils
                    self.api.connect(
                        host=host,
                        port=port,
                        clientId=client_id,
                        readonly=read_only,
                        account=account,
                    )
                except ImportError:
                    raise Exception("Please install ib_insync to use the IB data feed.")

            elif data_config["data_source"].lower() == "ccxt":
                try:
                    import ccxt

                    self._ccxt_exchange = data_config["exchange"]

                    if "api" in kwargs:
                        # Use API instance provided
                        self.api = kwargs["api"]

                    else:
                        # Check if exchange options were provided
                        if "config" in data_config:
                            # Use config dictionary provided directly
                            ccxt_config = data_config["config"]
                        elif "secret" in data_config and "api_key" in data_config:
                            # Create config dict with api key and secret
                            ccxt_config = {
                                "secret": data_config["secret"],
                                "apiKey": data_config["api_key"],
                            }
                        else:
                            # Create empty config dict
                            ccxt_config = {}

                        # Add any other keys to the config
                        extra_keys = ["options", "password"]
                        for key in extra_keys:
                            if key in data_config:
                                ccxt_config[key] = data_config[key]

                        # Create CCXT instance
                        exchange_module = getattr(ccxt, data_config["exchange"])
                        self.api = exchange_module(config=ccxt_config)

                        # Check sandbox mode
                        if "sandbox_mode" in data_config:
                            self.api.set_sandbox_mode(data_config["sandbox_mode"])

                        # Load markets
                        markets = self.api.load_markets()

                except ImportError:
                    raise Exception("Please install ccxt to use the CCXT data feed.")

            elif data_config["data_source"].lower() == "dydx":
                try:
                    from dydx3 import Client

                    self.api = Client(host="https://api.dydx.exchange")
                except ImportError:
                    raise Exception(
                        "Please install dydx-v3-python to use the dydx data feed."
                    )

            elif data_config["data_source"].lower() == "yahoo":
                try:
                    import yfinance as yf

                    self.api = yf.download
                except ImportError:
                    raise Exception(
                        "Please install yfinance to use "
                        + "the Yahoo Finance data feed."
                    )

            elif data_config["data_source"].lower() == "local":
                configure_local_feed(data_config)

            elif data_config["data_source"].lower() == "none":
                # No data feed required
                self.api = None

            else:
                raise Exception(f"Unknown data source '{self._feed}'.")

        self._allow_dancing_bears = allow_dancing_bears
        self._home_currency = home_currency

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        feed_str = self._ccxt_exchange if self._feed == "ccxt" else self._feed
        return f"AutoData ({feed_str} feed)"

    def fetch(
        self,
        instrument: str,
        granularity: str = None,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        """Unified OHLC data retrieval api.

        Parameters
        -----------
        instrument : str, list
            The instrument to fetch data for, or a list of instruments.
        granularity : str
            The granularity of the data to fetch.
        count : int, optional
            The number of OHLC bars to fetch. The default is None.
        start_time : datetime, optional
            The start date of the data to fetch. The default is None.
        end_time : datetime, optional
            The end date of the data to fetch. The default is None.

        Returns
        -------
        data : pd.DataFrame, dict[pd.DataFrame]
            The OHLC data.
        """
        func = getattr(self, f"_{self._feed}")
        if isinstance(instrument, list):
            max_workers = kwargs["workers"] if "workers" in kwargs else None
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for i in instrument:
                    futures[i] = executor.submit(
                        func,
                        instrument=i,
                        granularity=granularity,
                        count=count,
                        start_time=start_time,
                        end_time=end_time,
                        *args,
                        **kwargs,
                    )
            data = {}
            for instrument, future in futures.items():
                try:
                    data[instrument] = future.result()
                except Exception as e:
                    print(f"Could not fetch data for {instrument}: {e}")

        else:
            # Single instrument
            data = func(
                instrument,
                granularity=granularity,
                count=count,
                start_time=start_time,
                end_time=end_time,
                *args,
                **kwargs,
            )

        return data

    def _quote(self, *args, **kwargs):
        """Unified quote data retrieval api."""
        func = getattr(self, f"_{self._feed}_quote_data")
        data = func(*args, **kwargs)
        return data

    def L1(self, instrument=None, *args, **kwargs):
        """Unified level 1 data retrieval api."""
        # Get orderbook
        orderbook = self.L2(instrument, *args, **kwargs)

        # Construct response
        response = {
            "bid": orderbook.bids["price"][0],
            "ask": orderbook.asks["price"][0],
            "bid_size": orderbook.bids["size"][0],
            "ask_size": orderbook.asks["size"][0],
        }

        return response

    def L2(self, instrument=None, *args, **kwargs):
        """Unified level 2 data retrieval api."""
        func = getattr(self, f"_{self._feed}_orderbook")
        data = func(instrument, *args, **kwargs)
        if self._feed == "local":
            book = data
        else:
            book = OrderBook(instrument, data)
        return book

    def trades(self, instrument, *args, **kwargs):
        func = getattr(self, f"_{self._feed}_trades")
        trades = func(instrument, *args, **kwargs)
        return trades

    def _oanda(
        self,
        instrument: str,
        granularity: str,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> pd.DataFrame:
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
                # start_time+end_time+count
                # print("Warning: ignoring count input since start_time and",
                #        "end_time times have been specified.")
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

    def _oanda_liveprice(self, order: Order, **kwargs) -> dict:
        """Returns current price (bid+ask) and home conversion factors."""
        response = self.api.pricing.get(
            accountID=self.ACCOUNT_ID, instruments=order.instrument
        )
        ask = response.body["prices"][0].closeoutAsk
        bid = response.body["prices"][0].closeoutBid
        negativeHCF = response.body["prices"][
            0
        ].quoteHomeConversionFactors.negativeUnits
        positiveHCF = response.body["prices"][
            0
        ].quoteHomeConversionFactors.positiveUnits

        price = {
            "ask": ask,
            "bid": bid,
            "negativeHCF": negativeHCF,
            "positiveHCF": positiveHCF,
        }

        return price

    def _oanda_orderbook(self, instrument, time=None, *args, **kwargs):
        """Returns the orderbook from Oanda."""
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

    def _get_extended_oanda_data(self, instrument, granularity, from_time, to_time):
        """Returns historical data between a date range."""
        max_candles = 5000

        my_int = self._granularity_to_seconds(granularity, "oanda")
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

    def _oanda_quote_data(
        self,
        data: pd.DataFrame,
        pair: str,
        granularity: str,
        start_time: datetime,
        end_time: datetime,
        count: int = None,
    ):
        """Function to retrieve price conversion data."""
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

        base_currency = pair[:3]
        quote_currency = pair[-3:]

        if self._home_currency is None or quote_currency == self._home_currency:
            # Use data as quote data
            quote_data = data

        else:
            if self._home_currency == base_currency:
                # Disturb the data by machine precision to prompt HCF calculation
                quote_data = (1 + 1e-15) * data

            else:
                # Try download quote data
                conversion_pair = self._home_currency + "_" + quote_currency
                if conversion_pair == pair:
                    # Same instrument
                    quote_data = data

                else:
                    # Different instrument, fetch data
                    try:
                        # Directly
                        quote_data = self.oanda(
                            instrument=conversion_pair,
                            granularity=granularity,
                            start_time=start_time,
                            end_time=end_time,
                            count=count,
                        )
                    except:
                        # Failed
                        try:
                            # Invert conversion pair
                            conversion_pair = quote_currency + "_" + self._home_currency
                            inverse_quote_data = self.oanda(
                                instrument=conversion_pair,
                                granularity=granularity,
                                start_time=start_time,
                                end_time=end_time,
                                count=count,
                            )
                            quote_data = (
                                1 / inverse_quote_data[["Open", "High", "Low", "Close"]]
                            )

                        except:
                            # Failed, just used original data
                            quote_data = data

        return quote_data

    def _check_oanda_response(self, response):
        """Placeholder method to check Oanda API response."""
        if response.status != 200:
            print(response.reason)

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

    @staticmethod
    def _granularity_to_seconds(granularity: str, feed: str):
        """Converts the granularity to time in seconds."""
        if feed.lower() == "oanda":
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

        elif feed.lower() == "yahoo":
            # Note: will not work for week or month granularities

            letter = granularity[-1]
            number = float(granularity[:-1])

            conversions = {"m": 60, "h": 60 * 60, "d": 60 * 60 * 24}

            my_int = conversions[letter] * number

        return my_int

    def _yahoo(
        self,
        instrument: str,
        granularity: str = None,
        count: int = None,
        start_time: str = None,
        end_time: str = None,
    ) -> pd.DataFrame:
        """Retrieves historical price data from yahoo finance.

        Parameters
        ----------
        instrument : str
            Ticker to dowload data for.
        granularity : str, optional
            The candlestick granularity. The default is None.
        count : int, optional
            The number of bars to fetch. The default is None.
        start_time : str, optional
            The start time as YYYY-MM-DD string or datetime object. The default
            is None.
        end_time : str, optional
            The end_time as YYYY-MM-DD string or datetime object. The default
            is None.

        Returns
        -------
        data : pd.DataFrame
            The price data, as an OHLC DataFrame.

        Notes
        -----
        If you are encountering a JSON error when using the yahoo finance API,
        try updating by running: pip install yfinance --upgrade --no-cache-dir

        Intraday data cannot exceed 60 days.
        """
        gran_map = {
            60: "1m",
            120: "2m",
            300: "5m",
            900: "15m",
            1800: "30m",
            3600: "60m",
            5400: "90m",
            3600: "1h",
            86400: "1d",
            432000: "5d",
            604800: "1wk",
            2419200: "1mo",
            7257600: "3mo",
        }
        try:
            granularity = gran_map[pd.Timedelta(granularity).total_seconds()]
        except KeyError:
            raise Exception(
                f"The specified granularity of '{granularity}' is not "
                + "valid for Yahoo Finance."
            )

        if count is not None and start_time is None and end_time is None:
            # Convert count to start and end dates (assumes end=now)
            end_time = datetime.now()
            start_time = end_time - timedelta(
                seconds=self._granularity_to_seconds(granularity, "yahoo") * 1.5 * count
            )

        # Fetch data
        data = self.api(
            tickers=instrument, start=start_time, end=end_time, interval=granularity
        )

        # Remove excess data
        if count is not None and start_time is None and end_time is None:
            data = data.tail(count)

        if data.index.tzinfo is None:
            # Data is naive, add UTC timezone
            data.index = data.index.tz_localize(timezone.utc)

        return data

    def _yahoo_orderbook(self, *args, **kwargs):
        raise Exception("Orderbook data is not available from Yahoo Finance.")

    def _yahoo_quote_data(
        self,
        data: pd.DataFrame,
        pair: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
        count: int = None,
    ):
        """Returns nominal price data - quote conversion not supported for
        Yahoo finance API.
        """
        return data

    def _check_IB_connection(self):
        """Checks if there is an active connection to IB."""
        self.api.sleep(0)
        connected = self.api.isConnected()
        if not connected:
            raise ConnectionError("No active connection to IB.")

    def _ib(
        self,
        instrument: str,
        granularity: str,
        count: int,
        start_time: datetime = None,
        end_time: datetime = None,
        order: Order = None,
        durationStr: str = "10 mins",
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        """Fetches data from IB.

        Parameters
        ----------
        instrument : str
            The product being traded.
        granularity : str
            The granularity of the price bars.
        count : int
            The number of bars to fetch.
        start_time : datetime, optional
            The data start time. The default is None.
        end_time : datetime, optional
            The data end time. The default is None.
        order : Order, optional
            The order object. The default is None.

        Raises
        ------
        NotImplementedError
            DESCRIPTION.

        Returns
        -------
        df : TYPE
            DESCRIPTION.

        Warnings
        --------
        This method is not recommended due to its high API poll rate.

        References
        ----------
        https://ib-insync.readthedocs.io/api.html?highlight=reqhistoricaldata#
        """
        raise NotImplementedError(
            "Historical market data from IB is not yet supported."
        )
        # TODO - implement
        contract = IB_Utils.build_contract(order)

        dt = ""
        barsList = []
        while True:
            bars = self.api.reqHistoricalData(
                contract,
                endDateTime=dt,
                durationStr=durationStr,
                barSizeSetting=granularity,
                whatToShow="MIDPOINT",
                useRTH=True,
                formatDate=1,
            )
            if not bars:
                break
            barsList.append(bars)
            dt = bars[0].date

        # Convert bars to DataFrame
        allBars = [b for bars in reversed(barsList) for b in bars]
        df = self.api.util.df(allBars)
        return df

    def _ib_liveprice(self, order: Order, snapshot: bool = False, **kwargs) -> dict:
        """Returns current price (bid+ask) and home conversion factors.

        Parameters
        ----------
        order: Order
            The AutoTrader Order.
        snapshot : bool, optional
            Request a snapshot of the price. The default is False.

        Returns
        -------
        dict
            A dictionary containing the bid and ask prices.
        """
        self._check_IB_connection()
        contract = self.IB_Utils.build_contract(order)
        self.api.qualifyContracts(contract)
        ticker = self.api.reqMktData(contract, snapshot=snapshot)
        while ticker.last != ticker.last:
            self.api.sleep(1)
        self.api.cancelMktData(contract)
        price = {
            "ask": ticker.ask,
            "bid": ticker.bid,
            "negativeHCF": 1,
            "positiveHCF": 1,
        }
        return price

    @staticmethod
    def _pseduo_liveprice(last: float, quote_price: float = None) -> dict:
        """Returns an artificial live bid and ask price, plus conversion
        factors.

        Parameters
        ----------
        last : float
            The last price of the product being traded.
        quote_price : float, optional
            The quote price of the product being traded against the account
            home currency. The default is None.

        Returns
        -------
        dict
            DESCRIPTION.

        """
        # TODO - build bid/ask spread into here, review virtual broker
        if quote_price is not None:
            # Use quote price to determine HCF
            if last == quote_price:
                # Quote currency matches account home currency
                negativeHCF = 1
                positiveHCF = 1
            else:
                # Quote data
                negativeHCF = 1 / quote_price
                positiveHCF = 1 / quote_price

        else:
            # No quote price provided
            negativeHCF = 1
            positiveHCF = 1

        price = {
            "ask": last,
            "bid": last,
            "negativeHCF": negativeHCF,
            "positiveHCF": positiveHCF,
        }

        return price

    def _local(
        self,
        instrument: str,
        start_time: Union[str, datetime] = None,
        end_time: Union[str, datetime] = None,
        utc: bool = True,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        """Reads and returns local price data.

        Parameters
        ----------
        instrument : str
            Either the absolute filepath of the local price data file, or, if
            a data directory was provided in the data_config dictionary, simply
            the name of the data file.
        start_time : str | datetime, optional
            The data start date. The default is None.
        end_time : str | datetime, optional
            The data end date. The default is None.
        utc : bool, optional
            Localise data to UTC. The default is True.

        Returns
        -------
        data : pd.DataFrame
            The price data, as an OHLC DataFrame.
        """
        filepath = (
            instrument
            if self._data_directory is None
            else os.path.join(self._data_directory, instrument)
        )

        data = pd.read_csv(filepath, index_col=0)
        data.index = pd.to_datetime(data.index, utc=utc)

        if start_time is not None and end_time is not None:
            # Filter by date range
            data = AutoData._check_data_period(data, start_time, end_time)

        return data

    def _local_orderbook(self, instrument=None, *args, **kwargs):
        """Returns an artificial orderbook based on the last bar of
        local price data.

        Parameters
        ----------
        instrument : str, optional
            The filename (absolute, or relative if data_dir was provided with
            data_config dictionary) of the instrument data. Only required if
            'midprice' argument is not provided.
        spread : float, optional
            The bid/ask spread value.
        spread_units : float, optional
            The units to which the spread refers to. Can be either 'price' or
            'percentage'.
        midprice : float, optional
            The midprice to use as a reference price.
        """
        spread_units = (
            kwargs["spread_units"] if "spread_units" in kwargs else self._spread_units
        )
        spread = kwargs["spread"] if "spread" in kwargs else self._spread

        # Get latest price
        if "midprice" in kwargs:
            midprice = kwargs["midprice"]
        else:
            # Load from OHLC data
            data = self._local(instrument)
            midprice = data.iloc[-1].Close

        if spread_units == "price":
            bid = midprice - 0.5 * spread
            ask = midprice + 0.5 * spread
        elif spread_units == "percentage":
            bid = midprice * (1 - 0.5 * spread / 100)
            ask = midprice * (1 + 0.5 * spread / 100)

        # Quantize
        bid = Decimal(bid).quantize(Decimal(str(midprice)))
        ask = Decimal(ask).quantize(Decimal(str(midprice)))

        # TODO - ability to add levels by book parameters
        data = {
            "bids": [
                {"price": bid, "size": 1e100},
            ],
            "asks": [
                {"price": ask, "size": 1e100},
            ],
        }
        orderbook = OrderBook(instrument, data)

        return orderbook

    def _local_quote_data(
        self,
        data: pd.DataFrame,
        pair: str,
        granularity: str,
        start_time: datetime,
        end_time: datetime,
        count: int = None,
    ):
        """Returns the original price data for a local data feed."""
        return data

    @staticmethod
    def _check_data_period(
        data: pd.DataFrame, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Checks and returns the dataset matching the backtest start and
        end dates (as close as possible).
        """
        return data[(data.index >= start_date) & (data.index <= end_date)]

    def _ccxt(
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
            raise Exception("Please specify candlestick granularity.")

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
                raw_data = self.api.fetchOHLCV(
                    instrument,
                    timeframe=granularity,
                    since=start_ts,
                    limit=int(count),
                    params=kwargs,
                )
                # Append data
                data += raw_data

                # Increment start_ts
                start_ts = raw_data[-1][0]

                # Sleep for API limit
                time.sleep(1)

            return data

        if count is not None:
            if start_time is None and end_time is None:
                # Fetch N most recent candles
                raw_data = self.api.fetchOHLCV(
                    instrument, timeframe=granularity, limit=count, params=kwargs
                )
            elif start_time is not None and end_time is None:
                # Fetch N candles since start_time
                start_ts = (
                    None if start_time is None else int(start_time.timestamp() * 1000)
                )
                raw_data = self.api.fetchOHLCV(
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

        return data

    def _ccxt_quote_data(
        self,
        data: pd.DataFrame,
        pair: str = None,
        granularity: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        count: int = None,
    ):
        """Returns the original price data for a CCXT data feed."""
        return data

    def _ccxt_orderbook(self, instrument, limit=None, *args, **kwargs):
        """Returns the orderbook from a CCXT supported exchange."""
        try:
            response = self.api.fetchOrderBook(symbol=instrument)
        except ccxt.errors.ExchangeError as e:
            raise Exception(e)

        # Unify format
        orderbook = {}
        for side in ["bids", "asks"]:
            orderbook[side] = []
            for level in response[side]:
                orderbook[side].append({"price": level[0], "size": level[1]})
        return orderbook

    def _ccxt_trades(self, instrument):
        """Returns public trades from a CCXT exchange."""
        ccxt_trades = self.api.fetchTrades(instrument)

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

    def _ccxt_funding_rate(self, instrument: str):
        """Returns the current funding rate."""
        response = self.api.fetchFundingRate(instrument)

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
        params: dict = {},
    ):
        """Fetches the funding rate history."""

        def response2df(response):
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
                response = self.api.fetchFundingRateHistory(
                    symbol=instrument, since=start_ts, limit=count, params=params
                )

                # Append results
                df = response2df(response)
                rate_hist = pd.concat([rate_hist, df])

                # Increment start_ts
                start_ts = int(df.index[-1].timestamp() * 1000)

                # Sleep for API limit
                time.sleep(1)

            return rate_hist

        if count is not None:
            if start_time is None and end_time is None:
                # Fetch N most recent candles
                response = self.api.fetchFundingRateHistory(
                    symbol=instrument, limit=count, params=params
                )
                rate_hist = response2df(response)
            elif start_time is not None and end_time is None:
                # Fetch N candles since start_time
                start_ts = (
                    None if start_time is None else int(start_time.timestamp() * 1000)
                )
                response = self.api.fetchFundingRateHistory(
                    symbol=instrument, since=start_ts, limit=count, params=params
                )
                rate_hist = response2df(response)
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
                response = self.api.fetchFundingRateHistory(
                    symbol=instrument,
                    params=params,
                )
                rate_hist = response2df(response)

        return rate_hist

    def _dydx(
        self,
        instrument: str,
        granularity: str,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        """Retrieves historical price data of a instrument from dYdX.

        Parameters
        ----------
        instrument : str
            The instrument/market to fetch data for.
        granularity : str
            The candlestick granularity (1DAY, 4HOURS, 1HOUR, 30MINS, 15MINS,
                                         5MINS, or 1MIN).
        count : int, optional
            The number of candles to fetch (maximum of 100). The default is None.
        start_time : datetime, optional
            The data start time. The default is None.
        end_time : datetime, optional
            The data end time. The default is None.
        Returns
        -------
        data : DataFrame
            The price data, as an OHLCV DataFrame.
        """

        # Check granularity was provided
        if granularity is None:
            raise Exception("Please specify candlestick granularity.")

        gran_str = granularity
        gran_map = {
            60: "1MIN",
            300: "5MINS",
            900: "15MINS",
            1800: "30MINS",
            3600: "1HOUR",
            14400: "4HOURS",
            86400: "1DAY",
        }
        granularity = gran_map[pd.Timedelta(granularity).total_seconds()]

        def fetch_between_dates():
            # Fetches data between two dates
            data = []
            start = start_time
            last = start
            timestep = pd.Timedelta(gran_str)
            while last < end_time:
                raw_data = self.api.public.get_candles(
                    instrument,
                    resolution=granularity,
                    to_iso=start.isoformat(),
                ).data["candles"]
                # Append data
                data += raw_data[::-1]

                # Increment end time
                last = datetime.strptime(data[-1]["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
                start = last + 100 * timestep

                if len(raw_data) > 0:
                    # Sleep to prevent API rate-limiting
                    time.sleep(0.1)
                else:
                    start = end_time

            return data

        def fetch_count(N):
            count = min(100, N)
            raw_data = self.api.public.get_candles(
                instrument, resolution=granularity, limit=count
            ).data["candles"]
            data = raw_data[::-1]
            first_time = datetime.strptime(
                data[0]["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            while len(data) < N:
                count = min(100, N - len(data))
                raw_data = self.api.public.get_candles(
                    instrument,
                    resolution=granularity,
                    to_iso=first_time.isoformat(),
                    limit=count,
                ).data["candles"]
                # Append data
                data += raw_data[::-1]
                first_time = datetime.strptime(
                    raw_data[-1]["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                time.sleep(0.1)

            return data

        if count is not None:
            if start_time is None and end_time is None:
                # Fetch N most recent candles
                raw_data = fetch_count(count + 10)
            elif start_time is not None and end_time is None:
                # Fetch N candles since start_time
                raw_data = self.api.public.get_candles(
                    market=instrument,
                    resolution=granularity,
                    from_iso=start_time.isoformat(),
                    limit=count,
                ).data["candles"][::-1]
            elif end_time is not None and start_time is None:
                raw_data = self.api.public.get_candles(
                    market=instrument,
                    resolution=granularity,
                    to_iso=end_time.isoformat(),
                    limit=count,
                ).data["candles"][::-1]
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
        data = pd.DataFrame(raw_data)
        data.rename(
            columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"},
            inplace=True,
        )
        data.index = pd.to_datetime(data["updatedAt"], format="%Y-%m-%dT%H:%M:%S.%fZ")
        data.drop(
            ["startedAt", "updatedAt", "market", "resolution"], axis=1, inplace=True
        )
        data = data.apply(pd.to_numeric, errors="ignore")
        data.drop_duplicates(inplace=True)
        data.sort_index(inplace=True)
        return data

    def _dydx_quote_data(
        self,
        data: pd.DataFrame,
        pair: str,
        granularity: str,
        start_time: datetime,
        end_time: datetime,
        count: int = None,
    ):
        """Returns the original price data for a dYdX data feed."""
        return data

    def _dydx_orderbook(self, instrument, *args, **kwargs):
        """Returns the orderbook from dYdX."""
        response = self.api.public.get_orderbook(market=instrument)
        orderbook = response.data
        return orderbook

    def _dydx_trades(self, instrument):
        """Returns public trades from dYdX."""
        response = self.api.public.get_trades(instrument)
        dydx_trades = response.data["trades"]

        # Convert to standard form
        trades = []
        for trade in dydx_trades:
            unified_trade = {
                "direction": 1 if trade["side"] == "BUY" else -1,
                "price": float(trade["price"]),
                "size": float(trade["size"]),
                "time": datetime.strptime(trade["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            }
            trades.append(unified_trade)

        return trades

    def _none(self, *args, **kwargs):
        """Dummy method for none 'data' feed"""
        return None

    def _none_quote_data(self, *args, **kwargs):
        return None

    def _none_orderbook(self, *args, **kwargs):
        return None
