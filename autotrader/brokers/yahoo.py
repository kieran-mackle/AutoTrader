from __future__ import annotations
import pandas as pd
from autotrader.brokers.broker import Broker
from datetime import datetime, timezone, timedelta

try:
    import yfinance
except ImportError:
    raise Exception("Please install yfinance to use the Yahoo Finance data feed.")


class Broker(Broker):
    """Yahoo finance wrapper for data only."""

    def __init__(self, config: dict) -> None:
        self.api = yfinance.download

        # Create datastream object
        self._data_broker = self

    def __repr__(self):
        return "Yahoo Finance Broker Wrapper"

    def __str__(self):
        return super().__repr__()

    @property
    def data_broker(self):
        return self._data_broker

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
        else:
            # Convert to UTC
            data.index = data.index.tz_convert(timezone.utc)

        return data

    def get_orderbook(self, instrument: str, *args, **kwargs):
        raise Exception("Orderbook data is not available from Yahoo Finance.")

    def get_public_trades(self, instrument: str, *args, **kwargs):
        raise Exception("Public trade data is not available from Yahoo Finance.")

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

    @staticmethod
    def _granularity_to_seconds(granularity: str, feed: str):
        """Converts the granularity to time in seconds."""
        # Note: will not work for week or month granularities
        letter = granularity[-1]
        number = float(granularity[:-1])
        conversions = {"m": 60, "h": 60 * 60, "d": 60 * 60 * 24}
        my_int = conversions[letter] * number
        return my_int
