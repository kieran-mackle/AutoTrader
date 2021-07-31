# -*- coding: utf-8 -*-
"""

Oanda API Wrapper
=================

"""

import v20
from autotrader.brokers.oanda import utils
import datetime
import pandas as pd


class Oanda():
    def __init__(self, oanda_config):
        # Create v20 context
        API             = oanda_config["API"]
        ACCESS_TOKEN    = oanda_config["ACCESS_TOKEN"]
        port            = oanda_config["PORT"]
        self.ACCOUNT_ID = oanda_config["ACCOUNT_ID"]
        self.api        = v20.Context(hostname=API, 
                                      token=ACCESS_TOKEN, 
                                      port=port)
        
        STREAM_API      = "stream-fxpractice.oanda.com"
        self.stream     = v20.Context(hostname=STREAM_API, 
                                      token=ACCESS_TOKEN, 
                                      port=443)
        
        self.open_positions     = {}
        
    
    def get_price(self, pair):
        
        response = self.api.pricing.get(accountID = self.ACCOUNT_ID, 
                                   instruments = pair
                                   )
        ask = response.body["prices"][0].closeoutAsk
        bid = response.body["prices"][0].closeoutBid
        negativeHCF = response.body["prices"][0].quoteHomeConversionFactors.negativeUnits
        positiveHCF = response.body["prices"][0].quoteHomeConversionFactors.positiveUnits
    
        price = {"ask": ask,
                 "bid": bid,
                 "negativeHCF": negativeHCF,
                 "positiveHCF": positiveHCF
                 }
    
        return price
    
    
    def place_order(self, order_details):
        ''' Places a market order with a stop loss and take profit. '''
        
        # Extract order details
        pair            = order_details["instrument"]
        stop_price      = order_details["stop_loss"]
        take_price      = order_details["take_profit"]
        size            = order_details["size"]
        
        # Check stop and take levels for precision requirements
        stop_price, take_price = self.check_precision(pair,
                                                      stop_price, 
                                                      take_price
                                                      )
        
        # Place order
        response = self.api.order.market(accountID = self.ACCOUNT_ID,
                              instrument = pair,
                              units = size,
                              takeProfitOnFill = {"price": str(take_price)},
                              stopLossOnFill = {"price": str(stop_price)},
                              )
        
        # Check response
        output = self.check_response(response)
        
        return response 
        

    def get_data(self, pair, period, interval):
        # print("Getting data for {}".format(pair))
        response    = self.api.instrument.candles(pair,
                                             granularity = interval,
                                             count = period,
                                             dailyAlignment = 0
                                             )
        
        data        = utils.response_to_df(response)
        
        return data
    
    
    def get_balance(self):
        response = self.api.account.get(accountID=self.ACCOUNT_ID)
        
        return response.body["account"].balance
    
    
    def get_positions(self, pair = None):
        ''' Gets the current positions open on the account. '''
        
        if pair is not None:
            
            response = self.api.position.get(accountID = self.ACCOUNT_ID, 
                                             instrument = pair)
            no_positions = 1
        else:
            response = self.api.position.list_open(accountID = self.ACCOUNT_ID)
            no_positions = len(response.body['positions'])
        
        return response.body
    
    
    def get_summary(self):
        
        # response = self.api.account.get(accountID=self.ACCOUNT_ID)
        response = self.api.account.summary(accountID=self.ACCOUNT_ID)
        # print(response.body['account'])
        
        return response
    
    
    def close_position(self, pair):
        ''' Closes all open positions on an instrument '''
        # Check if the position is long or short
        position    = self.get_positions(pair)['position']
        long_units  = position.long.units
        short_units = position.short.units
        
        if long_units > 0:
            response = self.api.position.close(accountID=self.ACCOUNT_ID, 
                                               instrument=pair, 
                                               longUnits="ALL")
            # # Check response
            # output = self.check_response(response)
        
        elif short_units > 0: 
            response = self.api.position.close(accountID=self.ACCOUNT_ID, 
                                               instrument=pair,
                                               shortUnits="ALL")
            # # Check response
            # output = self.check_response(response)
        
        else:
            print("There is no current position with {} to close.".format(pair))
            response = None
        
        return response
    
    
    def get_precision(self, pair):
        ''' Returns the allowable precision for a given pair '''
        response = self.api.account.instruments(accountID = self.ACCOUNT_ID, 
                                                instruments = pair)
        
        precision = response.body['instruments'][0].displayPrecision
        
        return precision
    
    
    def check_precision(self, pair, original_stop, original_take):
        ''' Modify stop/take based on pair for required ordering precision. ''' 
        N               = self.get_precision(pair)
        take_price      = round(original_take, N)
        stop_price      = round(original_stop, N)
        
        return stop_price, take_price
        
    
    def check_response(self, response):
        ''' Checks API response (currently only for placing orders) '''
        if response.status != 201:
            message = response.body['errorMessage']
        else:
            message = "Success."
            
        output = {'Status': response.status, 
                  'Message': message}
        
        return output
    
    def update_data(self, pair, granularity, data):
        ''' Attempts to construct the latest candle when there is a delay in the 
            api feed.
        '''
        
        granularity_details = self.deconstruct_granularity(granularity)
        secs = granularity_details['seconds']
        mins = granularity_details['minutes']
        hrs  = granularity_details['hours']
        days = granularity_details['days']
        
        # TODO: make this a function of original granularity
        # Done, but now I think, maybe this should always be something like S5?
        small_granularity = self.get_reduced_granularity(granularity_details, 
                                                         25)
        
        # Get data equivalent of last candle's granularity
        time_now        = datetime.datetime.now()
        start_time      = time_now - datetime.timedelta(seconds = secs,
                                                        minutes = mins,
                                                        hours = hrs,
                                                        days = days)
        latest_data     = self.get_historical_data(pair, 
                                                   small_granularity, 
                                                   start_time.timestamp(), 
                                                   time_now.timestamp())
        
        # Get latest price data
        latest_close    = latest_data.Close.values[0]
        
        open_price      = data.Close.values[-1]
        close_price     = latest_close
        high_price      = max(latest_data.High.values)
        low_price       = min(latest_data.Low.values)
        last_time       = data.index[-1]
        stripped_time   = datetime.datetime.strptime(last_time.strftime("%Y-%m-%d %H:%M:%S%z"),
                                                      "%Y-%m-%d %H:%M:%S%z")
        new_time        = stripped_time + datetime.timedelta(seconds = secs,
                                                              minutes = mins,
                                                              hours = hrs,
                                                              days = days)
        
        new_candle      = pd.DataFrame({'Open'  : open_price, 
                                        'High'  : high_price,
                                        'Low'   : low_price,
                                        'Close' : close_price},
                                        index=[new_time])
        
        
        new_data        = pd.concat([data, new_candle])
        
        return new_data
    
    
    def get_historical_data(self, pair, interval, from_time, to_time):
        response        = self.api.instrument.candles(pair,
                                                      granularity = interval,
                                                      fromTime = from_time,
                                                      toTime = to_time
                                                      )
        
        data = utils.response_to_df(response)
        
        return data
    
    
    def deconstruct_granularity(self, granularity):
        ''' Returns a dict with the seconds, minutes, hours and days
            corresponding to a granularity. 
        '''
        
        # Get letter to determine timeframe (eg. M)
        letter = granularity[0]
        
        # Get timeframe multiple (eg. 15)
        if len(granularity) > 1:
            number = float(granularity[1:])
        else:
            number = 1
        
        
        if letter == 'S':
            seconds     = number
            minutes     = 0
            hours       = 0
            days        = 0
        
        elif letter == 'M':
            seconds     = 0
            minutes     = number
            hours       = 0
            days        = 0
            
        elif letter == 'H':
            seconds     = 0
            minutes     = 0
            hours       = number
            days        = 0
            
        else:
            seconds     = 0
            minutes     = 0
            hours       = 0
            days        = number
        
        granularity_details = {'seconds': seconds,
                               'minutes': minutes,
                               'hours': hours,
                               'days': days}
        
        return granularity_details

    def get_reduced_granularity(self, granularity_details, fraction):
        '''Returns a candlestick granularity as a fraction of given granularity'''
        secs = granularity_details['seconds']
        mins = granularity_details['minutes']
        hrs  = granularity_details['hours']
        days = granularity_details['days']
        
        total_seconds = secs + 60*mins + 60*60*hrs + 60*60*24*days
        
        fractional_seconds = total_seconds/fraction
        
        seconds = fractional_seconds
        minutes = fractional_seconds/60
        hours = fractional_seconds/(60*60)
        days = fractional_seconds/(60*60*24)
        
        if days > 1:
            letter = 'D'
            number = 1
            reduced_granularity = letter
            
        elif hours > 1:
            base   = 2
            letter = 'H'
            number = base*round(hours/base)
            if number > 12:
                number = 12
            reduced_granularity = letter + str(number)
                
        elif minutes > 1:
            base   = 15 
            letter = 'M'
            number = base*round(minutes/base)
            if number > 30:
                number = 30
            reduced_granularity = letter + str(number)
            
        else: 
            base   = 15 
            letter = 'S'
            number = base*round(seconds/base)
            if number > 30:
                number = 30
            reduced_granularity = letter + str(number)
        
        if reduced_granularity[1:] == '0':
            reduced_granularity = reduced_granularity[0] + '1'
        
        return reduced_granularity