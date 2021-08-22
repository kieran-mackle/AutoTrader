# -*- coding: utf-8 -*-
"""

Oanda API Wrapper
=================

"""

import v20
from autotrader.brokers.oanda import utils
import datetime
import pandas as pd
import numpy as np


class Oanda():
    def __init__(self, oanda_config, utils):
        ''' Create v20 context. '''
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
        
    
    def get_price(self, instrument, **dummy_inputs):
        ''' Returns current price (bid+ask) and home conversion factors.'''
        response = self.api.pricing.get(accountID = self.ACCOUNT_ID, 
                                   instruments = instrument
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
    
    def get_pending_orders(self, instrument=None):
        ''' Get all pending orders in the account. '''
        response = self.api.order.list_pending(accountID = self.ACCOUNT_ID, 
                                          instrument=instrument)
        
        oanda_pending_orders = response.body['orders']
        pending_orders = {}
        
        for order in oanda_pending_orders:
            if order.type != 'TAKE_PROFIT' and order.type != 'STOP_LOSS':
                new_order = {}
                new_order['order_ID']           = order.id
                new_order['order_type']         = order.type
                new_order['order_stop_price']   = order.price
                new_order['order_limit_price']  = order.price
                new_order['direction']          = np.sign(order.units)
                new_order['order_time']         = order.createTime
                new_order['strategy']           = None
                new_order['instrument']         = order.instrument
                new_order['size']               = order.units
                new_order['order_price']        = order.price
                new_order['granularity']        = None
                new_order['take_profit']        = order.takeProfitOnFill.price
                new_order['take_distance']      = None
                new_order['stop_type']          = None
                new_order['stop_distance']      = None
                new_order['stop_loss']          = None
                new_order['related_orders']     = None
                
                if instrument is not None and order.instrument == instrument:
                    pending_orders[order.id] = new_order
                elif instrument is None:
                    pending_orders[order.id] = new_order
            
        return pending_orders
    
    def cancel_pending_order(self, order_id):
        ''' Cancels pending order by ID. '''
        self.api.order.cancel(accountID = self.ACCOUNT_ID, orderSpecifier=str(order_id))
    
    def get_open_positions(self, instrument = None):
        ''' Gets the current positions open on the account. '''
        
        response = self.api.trade.list_open(accountID=self.ACCOUNT_ID)
        
        oanda_open_trades = response.body['trades']
        open_trades = {}
        
        for order in oanda_open_trades:
            new_order = {}
            new_order['order_ID']           = order.id
            new_order['order_stop_price']   = order.price
            new_order['order_limit_price']  = order.price
            new_order['direction']          = np.sign(order.currentUnits)
            new_order['order_time']         = order.openTime
            new_order['instrument']         = order.instrument
            new_order['size']               = order.currentUnits
            new_order['order_price']        = order.price
            new_order['entry_price']        = order.price
            new_order['order_type']         = None
            new_order['strategy']           = None
            new_order['granularity']        = None
            new_order['take_profit']        = None
            new_order['take_distance']      = None
            new_order['stop_type']          = None
            new_order['stop_distance']      = None
            new_order['stop_loss']          = None
            new_order['related_orders']     = None
            
            if instrument is not None and order.instrument == instrument:
                open_trades[order.id] = new_order
            elif instrument is None:
                open_trades[order.id] = new_order
        
        return open_trades
    
    def place_order(self, order_details):
        '''
        Parses order_details dict and handles order.
        '''
        
        if order_details["order_type"] == 'market':
            response = self.place_market_order(order_details)
        elif order_details["order_type"] == 'stop-limit':
            response = self.place_stop_limit_order(order_details)
        elif order_details["order_type"] == 'limit':
            response = self.place_limit_order(order_details)
        else:
            print("Order type not recognised.")
            return
        
        # Check response
        output = self.check_response(response)
        
        return response
        
    def place_market_order(self, order_details):
        ''' Places market order. '''
        stop_loss_details = self.get_stop_loss_details(order_details)
        take_profit_details = self.get_take_profit_details(order_details)
        
        response = self.api.order.market(accountID = self.ACCOUNT_ID,
                                         instrument = order_details["instrument"],
                                         units = order_details["size"],
                                         takeProfitOnFill = take_profit_details,
                                         stopLossOnFill = stop_loss_details,
                                         )
        return response
    
    def place_stop_limit_order(self, order_details):
        '''
        Places MarketIfTouchedOrder with Oanda.
        https://developer.oanda.com/rest-live-v20/order-df/
        '''
        stop_loss_details = self.get_stop_loss_details(order_details)
        take_profit_details = self.get_take_profit_details(order_details)
        
        # Check and correct order stop price
        price = self.check_precision(order_details["instrument"], 
                                     order_details["order_stop_price"])
        
        # Need to test cases when no stop/take is provided (as None type)
        response = self.api.order.market_if_touched(accountID   = self.ACCOUNT_ID,
                                                    instrument  = order_details["instrument"],
                                                    units       = order_details["size"],
                                                    price       = str(price),
                                                    takeProfitOnFill = take_profit_details,
                                                    stopLossOnFill = stop_loss_details
                                                    )
        return response
    
    def place_limit_order(self, order_details):
        ''' (NOT YET IMPLEMENTED) PLaces limit order. '''
        return

    def get_stop_loss_details(self, order_details):
        ''' Constructs stop loss details dictionary. '''
        # https://developer.oanda.com/rest-live-v20/order-df/#OrderType
        
        if order_details["stop_type"] is not None:
            price = self.check_precision(order_details["instrument"], 
                                         order_details["stop_loss"])
            
            if order_details["stop_type"] == 'trailing':
                # Trailing stop loss order
                stop_loss_details = {"price": str(price),
                                     "type": "TRAILING_STOP_LOSS"}
            else:
                stop_loss_details = {"price": str(price)}
        else:
            stop_loss_details = None
        
        return stop_loss_details
    
    def get_take_profit_details(self, order_details):
        ''' Constructs take profit details dictionary. '''
        if order_details["take_profit"] is not None:
            price = self.check_precision(order_details["instrument"], 
                                         order_details["take_profit"])
            take_profit_details = {"price": str(price)}
        else:
            take_profit_details = None
        
        return take_profit_details

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
        ''' Returns account balance. '''
        response = self.api.account.get(accountID=self.ACCOUNT_ID)
        
        return response.body["account"].balance
    
    
    def get_summary(self):
        ''' Returns account summary. '''
        # response = self.api.account.get(accountID=self.ACCOUNT_ID)
        response = self.api.account.summary(accountID=self.ACCOUNT_ID)
        # print(response.body['account'])
        
        return response
    
    
    def close_position(self, instrument, long_units=None, short_units=None,
                       **dummy_inputs):
        ''' Closes all open positions on an instrument '''
        # Check if the position is long or short
        position    = self.get_open_positions(instrument)['position']
        if long_units is None:
            long_units  = position.long.units
        if short_units is None:
            short_units = position.short.units
        
        if long_units > 0:
            response = self.api.position.close(accountID=self.ACCOUNT_ID, 
                                               instrument=instrument, 
                                               longUnits="ALL")
            # # Check response
            # output = self.check_response(response)
        
        elif short_units > 0: 
            response = self.api.position.close(accountID=self.ACCOUNT_ID, 
                                               instrument=instrument,
                                               shortUnits="ALL")
            # # Check response
            # output = self.check_response(response)
        
        else:
            print("There is no current position with {} to close.".format(instrument))
            response = None
        
        return response
    
    
    def get_precision(self, pair):
        ''' Returns the allowable precision for a given pair '''
        response = self.api.account.instruments(accountID = self.ACCOUNT_ID, 
                                                instruments = pair)
        
        precision = response.body['instruments'][0].displayPrecision
        
        return precision

    
    def check_precision(self, pair, price):
        ''' Modify a price based on required ordering precision for pair. ''' 
        N               = self.get_precision(pair)
        corrected_price = round(price, N)
        
        return corrected_price
        
    
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
    
    def get_NAV(self):
        ''' Returns Net Asset Value of account. '''
        response = self.api.account.get(accountID=self.ACCOUNT_ID)
        return response.body["account"].NAV
