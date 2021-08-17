# -*- coding: utf-8 -*-
"""

Dedicated data retrieval class.

"""

import pandas as pd
import v20
import yfinance as yf


class GetData():
    """
    GetData class to retrieve price data.


    Attributes
    ----------
    home_curreny : str
        the home currency of the account (used for retrieving quote data)

    Methods
    -------
    oanda(instrument, granularity, count=None, start_time=None, end_time=None):
        Retrieves historical price data of a instrument from Oanda v20 API.
        
    yahoo(self, instrument, granularity=None, start_time=None, end_time=None):
        Retrieves historical price data from yahoo finance. 
    
    """
    
    def __init__(self, broker_config=None):
        
        if broker_config is not None:
            if broker_config['data_source'] == 'OANDA':
                API                     = broker_config["API"]
                ACCESS_TOKEN            = broker_config["ACCESS_TOKEN"]
                port                    = broker_config["PORT"]
                self.api                = v20.Context(hostname=API, 
                                                      token=ACCESS_TOKEN, 
                                                      port=port)
        
        self.home_currency      = None
        

    def oanda(self, instrument, granularity, count=None, start_time=None, end_time=None):
        ''' 
        
        Retrieves historical price data of a instrument from Oanda v20 API.
        
        
            Parameters:
                instrument (str): the instrument to fetch data for 
                    
                granularity (str): candlestick granularity (eg. "M15", "H4", "D")
                
                count (int): number of candles to fetch (maximum 5000)
                
                start_time (datetime object): data start time 
                
                end_time (datetime object): data end time 
            
            Note:
                If a candlestick count is provided, only one of start time or end
                time should be provided. If neither is provided, the N most
                recent candles will be provided.
            
            Examples:
                data = GetData.oanda("EUR_USD", granularity="M15", start_time=from_dt, end_time=to_dt)
                
                data = GetData.oanda("EUR_USD", granularity="M15", start_time=from_dt, count=2110)
                
                data = GetData.oanda("EUR_USD", granularity="M15", end_time=to_dt, count=2110)
                
                data = GetData.oanda("EUR_USD", granularity="M15", count=2110)
        
        '''
        # what if I wanted to request 25,000 candles, rather than specifying 
        # a time range? Would need to modify function again...
        #       Ignore this as an edge case for now. 
        # This would basically be the inverse of what I have already done, 
        # instead of stepping forward, I would step backward with partial_to
        # times until my requested count is hit.
        
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
        ''' Returns historical data between a date range. '''
        # Currently does not accept count input, but in the future...
        
        max_candles     = 5000
        
        my_int          = self.granularity_to_seconds(granularity)
        end_time        = to_time - my_int
        partial_from    = from_time
        response        = self.api.instrument.candles(instrument,
                                                 granularity = granularity,
                                                 fromTime = partial_from,
                                                 count = max_candles
                                                 )
        data            = self.response_to_df(response)
        last_time       = data.index[-1].timestamp()
        
        while last_time < end_time:
            partial_from    = last_time
            response        = self.api.instrument.candles(instrument,
                                                     granularity = granularity,
                                                     fromTime = partial_from,
                                                     count = max_candles
                                                     )
            
            partial_data    = self.response_to_df(response)
            data            = data.append(partial_data)
            last_time       = data.index[-1].timestamp()
            
        return data
    
    
    def oanda_quote_data(self, data, pair, granularity, start_time, end_time):
        '''
            Function to retrieve price conversion data.
        '''
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
        ''' Function to convert api response into a pandas dataframe. '''
        
        candles = response.body["candles"]
        times = []
        close_price, high_price, low_price, open_price = [], [], [], []
        
        for candle in candles:
            if candle.complete:
                times.append(candle.time)
                close_price.append(float(candle.mid.c))
                high_price.append(float(candle.mid.h))
                low_price.append(float(candle.mid.l))
                open_price.append(float(candle.mid.o))
        
        dataframe = pd.DataFrame({"Open": open_price, "High": high_price, "Low": low_price, "Close": close_price})
        dataframe.index = pd.to_datetime(times)
        
        return dataframe
    
    def granularity_to_seconds(self, granularity):
        '''Converts the granularity to time in seconds'''
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
        
        return my_int
    
    
    def yahoo(self, instrument, granularity=None, start_time=None, end_time=None):
        '''
            Retrieves historical price data from yahoo finance. 
            
                Parameters:
                    instrument (str, list): list of tickers to download
                    
                    start_string (str): start time as YYYY-MM-DD string or _datetime. 
                    
                    end_string (str): end_time as YYYY-MM-DD string or _datetime. 
                    
                    granularity (str): candlestick granularity
                        valid intervals: 
                            1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo.
                
                Notes:
                    1. If you are encountering a JSON error when using the yahoo
                       finance API, try updating by running:
                           pip install yfinance --upgrade --no-cache-dir
                    2. Intraday data cannot exceed 60 days.
        
        '''
        
        data = yf.download(tickers  = instrument, 
                           start    = start_time, 
                           end      = end_time,
                           interval = granularity)
        
        return data
    
    def yahoo_quote_data(self, data, pair, interval, from_date, to_date):
        ''' 
            Returns nominal price data - quote conversion not supported for 
            Yahoo finance API.
        '''
        return data
    
    