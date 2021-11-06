#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module: brokers.binanceapi.binance_api
Purpose: AutoTrader broker wrapper script for Binance API
Author: Kieran Mackle
'''

from binance.client import Client
# from binance import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException, BinanceOrderException


class Binance():
    def __init__(self, binance_config, *args, **kwargs):
        ''' Initiate Binance client. '''
        
        API_KEY = binance_config["API_KEY"]
        SECRET_KEY = binance_config["SECRET_KEY"]
        self.client = Client(API_KEY, SECRET_KEY)
        self.client.API_URL = binance_config["API_URL"]
        
        self.base_asset = 'BNB'
        
        # TODO - flag spot vs. margin trading
        
        
    def place_order(self, order_details):
        '''
        Parses order_details dict and handles order, as passed from AutoBot.
        
        input order_details is a dictionary containing the following:
            order_details["direction"]          Direction of order (-1 or 1)
            order_details["order_type"]         Order type (market, limit, stop-limit)
            order_details["order_time"]         Order time (datetime)
            order_details["strategy"]           Parent strategy name
            order_details["instrument"]         Instrument
            order_details["size"]               Order position size (tradeable units)
            order_details["order_price"]        Order price
            order_details["order_limit_price"]  Limit order price
            order_details["order_stop_price"]   Stop limit order price
            order_details["HCF"]                Home conversion factor
            order_details["stop_loss"]          Stop loss price
            order_details["stop_distance"]      Stop loss distance in pips
            order_details["stop_type"]          Stop loss type (limit, trailing)
            order_details["take_profit"]        Take profit price
            order_details["take_distance"]      Take profit distance in pips
            order_details["related_orders"]     Related order ID's
        '''
        
        instrument = order_details["instrument"]
        order_side = 'BUY' if order_details["direction"] == 1 else 'SELL'
        size = order_details["size"]
        
        if order_details["order_type"] == 'market':
            response = self._create_order(instrument = instrument,
                                          order_type = 'MARKET',
                                          order_side = order_side,
                                          size = size)
            
        elif order_details["order_type"] == 'stop-limit':
            # TODO - below not yet implemented
            response = self._create_order(instrument = instrument,
                                          order_type = 'OCO',
                                          order_side = order_side,
                                          size = size)
            
        elif order_details["order_type"] == 'limit':
            response = self._create_order(instrument = instrument,
                                          order_type = 'LIMIT',
                                          order_side = order_side,
                                          size = size, 
                                          price = order_details["order_limit_price"])
        else:
            print("Order type not recognised.")
            return    
        
        # TODO - add check
        
        return response
    
    
    def _create_order(self, instrument, order_type, order_side, size, 
                      price=None, time_in_force=None):
        '''
        Sends order to Binance.
        '''
        
        try:
            response = self.client.create_order(symbol = instrument,
                                                side = order_side,
                                                type = order_type,
                                                timeInForce = time_in_force,
                                                quantity = size,
                                                price = price)
        
        except BinanceAPIException as e:
            # API exception has occured
            response = e
            
        except BinanceOrderException as e:
            # Order exception has occured
            response = e
        
        return response
    
        
    def get_NAV(self):
        ''' Returns Net Asset Value of account. '''
        
    
    def get_price(self, instrument, **kwargs):
        ''' Returns current price.'''
        
        response = self.client.get_symbol_ticker(symbol=instrument)
        
        return response
    
    
    def get_pending_orders(self, symbol=None):
        ''' Get all pending orders in the account. '''
        
        response = self.client.get_open_orders(symbol=symbol)
        
        return response
    
    def cancel_pending_order(self, order_id):
        ''' Cancels pending order by ID. '''
        response = self.client.cancel_order(symbol='ETHUSDT', orderId=order_id)
        
        return response
    
    def get_open_positions(self, instrument = None):
        ''' Gets the current positions open on the account. '''
        
    
    def place_stop_limit_order(self, order_details):
        ''' Places a stop-limit order. '''
        

    def get_stop_loss_details(self, order_details):
        ''' Constructs stop loss details dictionary. '''
    
    def get_take_profit_details(self, order_details):
        ''' Constructs take profit details dictionary. '''
        

    def get_data(self, pair, period, interval):
        ''' Gets candlestick price data. '''
        
    
    def get_balance(self, asset=None):
        ''' Returns account balance of instrument. '''
        
        asset = self.base_asset if asset is None else asset
        
        response = self.client.get_asset_balance(asset = asset)
        
        return response
    
    def get_summary(self):
        ''' Returns account summary. '''
        response = self.client.get_account()
        
        return response
        
    def get_symbol_info(self, symbol):
        ''' Returns information about the symbol. '''
        response = self.client.get_symbol_info(symbol)
    
        return response
    
    
    def get_position(self, instrument):
        ''' Gets position from Oanda. '''
    
    def close_position(self, instrument, long_units=None, short_units=None,
                       **dummy_inputs):
        ''' Closes all open trades on an instrument. '''
        
    
