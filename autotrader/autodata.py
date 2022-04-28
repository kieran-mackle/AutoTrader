import v20
import ib_insync
import pandas as pd
import yfinance as yf
from typing import Union
from autotrader.brokers.trading import Order
from datetime import datetime, timedelta, timezone
from autotrader.brokers.ib.utils import Utils as IB_Utils


class GetData:
    """GetData class to retrieve price data.

    Attributes
    ----------
    home_curreny : str
        the home currency of the account (used for retrieving quote data)
    
    allow_dancing_bears : bool
        Allow incomplete candlesticks in data retrieval.

    Methods
    -------
    oanda()
        Retrieves historical price data of a instrument from Oanda.
    yahoo()
        Retrieves historical price data from Yahoo Finance via yfinance.
    local()
        Reads local price data.
    """
    
    def __init__(self, broker_config: dict = None, 
                 allow_dancing_bears: bool = False,
                 home_currency: str = None) -> None:
        """Instantiates GetData.

        Parameters
        ----------
        broker_config : dict, optional
            The configuration dictionary for the broker to be used. The 
            default is None.
        allow_dancing_bears : bool, optional
            A flag to allow incomplete bars to be returned in the data. The 
            default is False.
        home_currency : str, optional
            The home currency to use when fetching quote data. The default 
            is None.

        Returns
        -------
        None
            GetData will be instantiated and ready to fetch price data.

        """
        if broker_config is not None:
            if broker_config['data_source'] == 'OANDA':
                API = broker_config["API"]
                ACCESS_TOKEN = broker_config["ACCESS_TOKEN"]
                port = broker_config["PORT"]
                self.api = v20.Context(hostname=API, token=ACCESS_TOKEN, port=port)
            
            elif broker_config['data_source'] == 'IB':
                host = broker_config['host']
                port = broker_config['port'] 
                client_id = broker_config['clientID'] + 1
                read_only = broker_config['read_only']
                account = broker_config['account']
                
                self.ibapi = ib_insync.IB()
                self.ibapi.connect(host=host, port=port, clientId=client_id, 
                                   readonly=read_only, account=account)
            
        self.allow_dancing_bears = allow_dancing_bears
        self.home_currency = home_currency
        

    def oanda(self, instrument: str, granularity: str, count: int = None, 
              start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
        """Retrieves historical price data of a instrument from Oanda v20 API.

        Parameters
        ----------
        instrument : str
            The instrument to fetch data for.
        granularity : str
            The candlestick granularity (eg. "M15", "H4", "D").
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
        
        Examples
        --------
        >>> data = GetData.oanda("EUR_USD", granularity="M15", 
                                 start_time=from_dt, end_time=to_dt)
            
        >>> data = GetData.oanda("EUR_USD", granularity="M15",
                                 start_time=from_dt, count=2110)
        
        >>> data = GetData.oanda("EUR_USD", granularity="M15",
                                 end_time=to_dt, count=2110)
        
        >>> data = GetData.oanda("EUR_USD", granularity="M15", 
                                 count=2110)
        """
        if count is not None:
            # either of count, start_time+count, end_time+count (or start_time+end_time+count)
            # if count is provided, count must be less than 5000
            if start_time is None and end_time is None:
                # fetch count=N most recent candles
                response = self.api.instrument.candles(instrument,
                                                       granularity = granularity,
                                                       count = count)
                data = self.response_to_df(response)
                
            elif start_time is not None and end_time is None:
                # start_time + count
                from_time = start_time.timestamp()
                response = self.api.instrument.candles(instrument,
                                                       granularity = granularity,
                                                       count = count,
                                                       fromTime = from_time)
                data = self.response_to_df(response)
            
            elif end_time is not None and start_time is None:
                # end_time + count
                to_time = end_time.timestamp()
                response = self.api.instrument.candles(instrument,
                                             granularity = granularity,
                                             count = count,
                                             toTime = to_time)
                data = self.response_to_df(response)
                
            else:
                # start_time+end_time+count
                # print("Warning: ignoring count input since start_time and",
                #        "end_time times have been specified.")
                from_time = start_time.timestamp()
                to_time = end_time.timestamp()
            
                # try to get data 
                response = self.api.instrument.candles(instrument,
                                                       granularity = granularity,
                                                       fromTime = from_time,
                                                       toTime = to_time)
                
                # If the request is rejected, max candles likely exceeded
                if response.status != 200:
                    data = self._get_extended_oanda_data(instrument,
                                                         granularity,
                                                         from_time,
                                                         to_time)
                else:
                    data = self.response_to_df(response)
                
        else:
            # count is None
            # Assume that both start_time and end_time have been specified.
            from_time = start_time.timestamp()
            to_time = end_time.timestamp()
            
            # try to get data 
            response = self.api.instrument.candles(instrument,
                                                   granularity = granularity,
                                                   fromTime = from_time,
                                                   toTime = to_time)
            
            # If the request is rejected, max candles likely exceeded
            if response.status != 200:
                data = self._get_extended_oanda_data(instrument,
                                                     granularity,
                                                     from_time,
                                                     to_time)
            else:
                data = self.response_to_df(response)

        return data
    
    
    def oanda_liveprice(self, order: Order, **kwargs) -> dict:
        """Returns current price (bid+ask) and home conversion factors.
        """
        response = self.api.pricing.get(accountID = self.ACCOUNT_ID, 
                                        instruments = order.instrument)
        ask = response.body["prices"][0].closeoutAsk
        bid = response.body["prices"][0].closeoutBid
        negativeHCF = response.body["prices"][0].quoteHomeConversionFactors.negativeUnits
        positiveHCF = response.body["prices"][0].quoteHomeConversionFactors.positiveUnits
    
        price = {"ask": ask,
                 "bid": bid,
                 "negativeHCF": negativeHCF,
                 "positiveHCF": positiveHCF}
    
        return price
    
    
    def _get_extended_oanda_data(self, instrument, granularity, from_time, to_time):
        """Returns historical data between a date range."""
        max_candles = 5000
        
        my_int = self._granularity_to_seconds(granularity, 'oanda')
        end_time = to_time - my_int
        partial_from = from_time
        response = self.api.instrument.candles(instrument,
                                               granularity = granularity,
                                               fromTime = partial_from,
                                               count = max_candles)
        data = self.response_to_df(response)
        last_time = data.index[-1].timestamp()
        
        while last_time < end_time:
            partial_from = last_time
            response = self.api.instrument.candles(instrument,
                                                   granularity = granularity,
                                                   fromTime = partial_from,
                                                   count = max_candles)
            
            partial_data = self.response_to_df(response)
            data = data.append(partial_data)
            last_time = data.index[-1].timestamp()
            
        return data
    
    
    def _oanda_quote_data(self, data: pd.DataFrame, pair: str, granularity: str, 
                         start_time: datetime, end_time: datetime):
        """Function to retrieve price conversion data.
        """
        base_currency = pair[:3]
        quote_currency = pair[-3:]
        
        if self.home_currency is None or quote_currency == self.home_currency:
            # Use data as quote data
            quote_data = data
            
        else:
            if self.home_currency == base_currency:
                # Invert data to get quote data
                quote_data = 1/data
                
            else:
                # Try download quote data
                try:
                    conversion_pair = self.home_currency + "_" + quote_currency
                    if conversion_pair != pair:
                        # Do not re-download the same data
                        quote_data = self.oanda(instrument  = conversion_pair,
                                                granularity = granularity,
                                                start_time  = start_time,
                                                end_time    = end_time)
                    else:
                        quote_data = data
                        
                except:
                    # Download failed, revert to original data
                    quote_data = data
        
        return quote_data
    
    
    def _check_oanda_response(self, response):
        """Placeholder method to check Oanda API response.
        """
        if response.status != 200:
            print(response.reason)
    
    
    def response_to_df(self, response):
        """Function to convert api response into a pandas dataframe.
        """
        try:
            candles = response.body["candles"]
        except KeyError:
            raise Exception("Error dowloading data - please check instrument"+\
                            " format and try again.")
            
        times = []
        close_price, high_price, low_price, open_price, volume = [],[],[],[],[]
        
        if self.allow_dancing_bears:
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
        
        dataframe = pd.DataFrame({"Open": open_price, 
                                  "High": high_price, 
                                  "Low": low_price, 
                                  "Close": close_price,
                                  "Volume": volume})
        dataframe.index = pd.to_datetime(times)
        dataframe.drop_duplicates(inplace=True)
        
        return dataframe
    
    
    @staticmethod
    def _granularity_to_seconds(granularity: str, feed: str):
        """Converts the granularity to time in seconds.
        """
        if feed.lower() == 'oanda':
            allowed_granularities = ('S5', 'S10', 'S15', 'S30',
                                       'M1', 'M2', 'M4', 'M5', 'M10', 'M15', 'M30',
                                       'H1', 'H2', 'H3', 'H4', 'H6', 'H8', 'H12',
                                       'D', 'W', 'M')
            
            if granularity not in allowed_granularities:
                raise Exception(f"Invalid granularity '{granularity}' for "+\
                                "{feed} data feed.")
            
            letter = granularity[0]
            
            if len(granularity) > 1:
                number = float(granularity[1:])
            else:
                number = 1
            
            conversions = {'S': 1,
                           'M': 60,
                           'H': 60*60,
                           'D': 60*60*24}
            
            my_int = conversions[letter] * number
            
        elif feed.lower() == 'yahoo':
            # Note: will not work for week or month granularities
            
            letter = granularity[-1]
            number = float(granularity[:-1])
            
            conversions = {'m': 60,
                           'h': 60*60,
                           'd': 60*60*24}
            
            my_int = conversions[letter] * number
        
        return my_int
    

    def yahoo(self, instrument: str, granularity: str = None, count: int = None, 
              start_time: str = None, end_time: str = None) -> pd.DataFrame:
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
        
        if count is not None and start_time is None and end_time is None:
            # Convert count to start and end dates (assumes end=now)
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=self._granularity_to_seconds(granularity, 'yahoo')*count)
        
        data = yf.download(tickers  = instrument, 
                           start    = start_time, 
                           end      = end_time,
                           interval = granularity)
        
        if data.index.tzinfo is None:
            # Data is naive, add UTC timezone
            data.index = data.index.tz_localize(timezone.utc)
        
        return data
    
    
    def yahoo_liveprice(self,):
        raise Exception("Live price is not available from yahoo API.")
        
    
    def _yahoo_quote_data(self, data: pd.DataFrame, pair: str, interval: str,
                         from_date: datetime, to_date: datetime):
        """Returns nominal price data - quote conversion not supported for 
        Yahoo finance API.
        """
        return data
    
    
    def _check_IB_connection(self):
        """Checks if there is an active connection to IB.
        """
        self.ibapi.sleep(0)
        connected = self.ibapi.isConnected()
        if not connected:
            raise ConnectionError("No active connection to IB.")
    
    
    def ib(self, instrument: str, granularity: str, count: int,
           start_time: datetime = None, end_time: datetime = None,
           order: Order = None, durationStr: str = '10 mins', **kwargs) -> pd.DataFrame:
        """

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
        raise NotImplementedError("Historical market data from IB is not yet supported.")
        # TODO - implement
        contract = IB_Utils.build_contract(order)
        
        dt = ''
        barsList = []
        while True:
            bars = self.ibapi.reqHistoricalData(
                contract,
                endDateTime=dt,
                durationStr=durationStr,
                barSizeSetting=granularity,
                whatToShow='MIDPOINT',
                useRTH=True,
                formatDate=1)
            if not bars:
                break
            barsList.append(bars)
            dt = bars[0].date
        
        # Convert bars to DataFrame
        allBars = [b for bars in reversed(barsList) for b in bars]
        df = self.ibapi.util.df(allBars)
        return df
    
    
    def ib_liveprice(self, order: Order, snapshot: bool = False, **kwargs) -> dict:
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
        contract = IB_Utils.build_contract(order)
        self.ibapi.qualifyContracts(contract)
        ticker = self.ibapi.reqMktData(contract, snapshot=snapshot)
        while ticker.last != ticker.last: self.ibapi.sleep(1)
        self.ibapi.cancelMktData(contract)
        price = {"ask": ticker.ask,
                 "bid": ticker.bid,
                 "negativeHCF": 1,
                 "positiveHCF": 1,}
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
                negativeHCF = quote_price
                positiveHCF = quote_price
                
        else:
            # No quote price provided
            negativeHCF = 1
            positiveHCF = 1
        
        price = {"ask": last,
                 "bid": last,
                 "negativeHCF": negativeHCF,
                 "positiveHCF": positiveHCF}
        
        return price
    
    
    @staticmethod
    def local(filepath: str, start_date: Union[str, datetime] = None, 
              end_date: Union[str, datetime] = None, utc: bool = True) -> pd.DataFrame:
        """Read local price data.

        Parameters
        ----------
        filepath : str
            The absolute filepath of the local price data.
        start_date : str | datetime, optional
            The data start date. The default is None.
        end_date : str | datetime, optional
            The data end data. The default is None.
        utc : bool, optional
            Localise data to UTC. The default is True.

        Returns
        -------
        data : pd.DataFrame
            The price data, as an OHLC DataFrame.
        """
        data = pd.read_csv(filepath, index_col = 0)
        data.index = pd.to_datetime(data.index, utc=utc)
        
        if start_date is not None and end_date is not None:
            # Filter by date range
            data = GetData._check_data_period(data, start_date, 
                                              end_date)
            
        return data
    
    
    @staticmethod
    def _check_data_period(data: pd.DataFrame, start_date: datetime, 
                           end_date: datetime) -> pd.DataFrame:
        """Checks and returns the dataset matching the backtest start and 
        end dates (as close as possible).
        """
        return data[(data.index >= start_date) & (data.index <= end_date)]
