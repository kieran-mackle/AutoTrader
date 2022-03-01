import v20
import pandas as pd
import yfinance as yf
from typing import Union
from datetime import datetime, timedelta


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
    oanda():
        Retrieves historical price data of a instrument from Oanda v20 API.
        
    yahoo():
        Retrieves historical price data from yahoo finance. 
    """
    
    def __init__(self, broker_config: dict = None, 
                 allow_dancing_bears: bool = False) -> None:
        
        if broker_config is not None:
            if broker_config['data_source'] == 'OANDA':
                API = broker_config["API"]
                ACCESS_TOKEN = broker_config["ACCESS_TOKEN"]
                port = broker_config["PORT"]
                self.api = v20.Context(hostname=API, token=ACCESS_TOKEN, port=port)
            # Define API for other data sources
            
        self.allow_dancing_bears = allow_dancing_bears
        self.home_currency = None
        

    def oanda(self, instrument: str, granularity: str, count: int = None, 
              start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
        """Retrieves historical price data of a instrument from Oanda v20 API.

        Parameters
        ----------
        instrument : str
            the instrument to fetch data for.
        granularity : str
            candlestick granularity (eg. "M15", "H4", "D").
        count : int, optional
            number of candles to fetch (maximum 5000). The default is None.
        start_time : datetime, optional
            data start time. The default is None.
        end_time : datetime, optional
            data end time. The default is None.

        Returns
        -------
        data : DataFrame
            The price data, as an OHLC DataFrame.
            
        Notes
        -----
            If a candlestick count is provided, only one of start time or end
            time should be provided. If neither is provided, the N most
            recent candles will be provided.
        
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
                response    = self.api.instrument.candles(instrument,
                                             granularity = granularity,
                                             count = count
                                             )
                data        = self.response_to_df(response)
                
            elif start_time is not None and end_time is None:
                # start_time + count
                from_time   = start_time.timestamp()
                response    = self.api.instrument.candles(instrument,
                                             granularity = granularity,
                                             count = count,
                                             fromTime = from_time
                                             )
                data        = self.response_to_df(response)
            
            elif end_time is not None and start_time is None:
                # end_time + count
                to_time     = end_time.timestamp()
                response    = self.api.instrument.candles(instrument,
                                             granularity = granularity,
                                             count = count,
                                             toTime = to_time
                                             )
                data        = self.response_to_df(response)
                
            else:
                # start_time+end_time+count
                print("Warning: ignoring count input since start_time and",
                       "end_time times have been specified.")
                from_time       = start_time.timestamp()
                to_time         = end_time.timestamp()
            
                # try to get data 
                response        = self.api.instrument.candles(instrument,
                                                         granularity = granularity,
                                                         fromTime = from_time,
                                                         toTime = to_time
                                                         )
                
                # If the request is rejected, max candles likely exceeded
                if response.status != 200:
                    data        = self.get_extended_oanda_data(instrument,
                                                         granularity,
                                                         from_time,
                                                         to_time)
                else:
                    data        = self.response_to_df(response)
                
        else:
            # count is None
            # Assume that both start_time and end_time have been specified.
            from_time       = start_time.timestamp()
            to_time         = end_time.timestamp()
            
            # try to get data 
            response        = self.api.instrument.candles(instrument,
                                                     granularity = granularity,
                                                     fromTime = from_time,
                                                     toTime = to_time
                                                     )
            
            # If the request is rejected, max candles likely exceeded
            if response.status != 200:
                data        = self.get_extended_oanda_data(instrument,
                                                     granularity,
                                                     from_time,
                                                     to_time)
            else:
                data        = self.response_to_df(response)

        return data
    
    
    def get_extended_oanda_data(self, instrument, granularity, from_time, to_time):
        """Returns historical data between a date range."""
        max_candles = 5000
        
        my_int = self.granularity_to_seconds(granularity, 'oanda')
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
    
    
    def oanda_quote_data(self, data, pair, granularity, start_time, end_time):
        """Function to retrieve price conversion data.
        """
        quote_currency  = pair[-3:]
        
        if self.home_currency is None or quote_currency == self.home_currency:
            quote_data = data
        else:
            conversion_pair = self.home_currency + "_" + quote_currency
            quote_data = self.oanda(instrument  = conversion_pair,
                                    granularity = granularity,
                                    start_time  = start_time,
                                    end_time    = end_time)
        
        return quote_data
    
    
    def response_to_df(self, response):
        """Function to convert api response into a pandas dataframe.
        """
        candles = response.body["candles"]
        times = []
        close_price, high_price, low_price, open_price = [], [], [], []
        
        for candle in candles:
            if self.allow_dancing_bears:
                times.append(candle.time)
                close_price.append(float(candle.mid.c))
                high_price.append(float(candle.mid.h))
                low_price.append(float(candle.mid.l))
                open_price.append(float(candle.mid.o))
                
            else:
                if candle.complete:
                    times.append(candle.time)
                    close_price.append(float(candle.mid.c))
                    high_price.append(float(candle.mid.h))
                    low_price.append(float(candle.mid.l))
                    open_price.append(float(candle.mid.o))
        
        dataframe = pd.DataFrame({"Open": open_price, "High": high_price, "Low": low_price, "Close": close_price})
        dataframe.index = pd.to_datetime(times)
        dataframe.drop_duplicates(inplace=True)
        
        return dataframe
    
    
    @staticmethod
    def granularity_to_seconds(granularity: str, feed: str):
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
                           'D': 60*60*24
                           }
            
            my_int = conversions[letter] * number
            
        elif feed.lower() == 'yahoo':
            # Note: will not work for week or month granularities
            
            letter = granularity[-1]
            number = float(granularity[:-1])
            
            conversions = {'m': 60,
                           'h': 60*60,
                           'd': 60*60*24
                           }
            
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
            DESCRIPTION. The default is None.
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
        - If you are encountering a JSON error when using the yahoo finance API,
        try updating by running
        
        >>> pip install yfinance --upgrade --no-cache-dir
        
        - Intraday data cannot exceed 60 days.
        """
        
        if count is not None:
            # Convert count to start and end dates (currently assumes end=now)
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=self.granularity_to_seconds(granularity, 'yahoo')*count)
        
        data = yf.download(tickers  = instrument, 
                           start    = start_time, 
                           end      = end_time,
                           interval = granularity)
        
        return data
    
    
    def yahoo_quote_data(self, data, pair, interval, from_date, to_date):
        """Returns nominal price data - quote conversion not supported for 
            Yahoo finance API.
        """
        return data
    
    
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
    
    
    def _check_oanda_response(self, response):
        """Placeholder method to check Oanda API response.
        """
        if response.status != 200:
            print(response.reason)
    
    
    @staticmethod
    def _check_data_period(data: pd.DataFrame, start_date: datetime, 
                           end_date: datetime) -> pd.DataFrame:
        """Checks and returns the dataset matching the backtest start and 
        end dates (as close as possible).
        """
        return data[(data.index >= start_date) & (data.index <= end_date)]