#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from autotrader.brokers.broker_utils import BrokerUtils

class Utils(BrokerUtils):
    def __init__(self):
        pass
    
        
    def check_response(self, response):
        """Checks API response for errors.

        Parameters
        ----------
        response : TYPE
            DESCRIPTION.

        Returns
        -------
        output : TYPE
            DESCRIPTION.
        """
        
        if response.status != 201:
            message = response.body['errorMessage']
        else:
            message = "Success."
            
        output = {'Status': response.status, 
                  'Message': message}
        
        return output
    
    def check_precision(self, pair, price):
        ''' Modify a price based on required ordering precision for pair. ''' 
        N               = self.get_precision(pair)
        corrected_price = round(price, N)
        
        return corrected_price
    
    
    def get_precision(self, pair):
        ''' Returns the allowable precision for a given pair '''
        
        response = self.api.account.instruments(accountID = self.ACCOUNT_ID, 
                                                instruments = pair)
        
        precision = response.body['instruments'][0].displayPrecision
        
        return precision
    
    
    def check_trade_size(self, pair, units):
        ''' Checks the requested trade size against the minimum trade size 
            allowed for the currency pair. '''
        response = self.api.account.instruments(accountID=self.ACCOUNT_ID, 
                                                instruments = pair)
        # minimum_units = response.body['instruments'][0].minimumTradeSize
        trade_unit_precision = response.body['instruments'][0].tradeUnitsPrecision
        
        return round(units, trade_unit_precision)
    