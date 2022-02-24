#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
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
    
    
    @staticmethod
    def accsum_to_dict(account: str = None, data: list = None) -> dict:
        """Returns account summary list as a dictionary.

        Parameters
        ----------
        account : str
            DESCRIPTION.
        data : list
            DESCRIPTION.

        Returns
        -------
        out
            DESCRIPTION.
        """
        
        if account is None:
            account = 'All'
            
        out = {}
        for av in data:
            if av.account == account:
                out[av.tag] = {'value': av.value,
                               'currency': av.currency,
                               'modelCode': av.modelCode}
        
        return out
    
    @staticmethod
    def positionlist_to_dict(positions: list) -> dict:
        """Returns position list as a dictionary.

        Parameters
        ----------
        positions : list
            DESCRIPTION.

        Returns
        -------
        dict
            DESCRIPTION.

        """
        pass
    
    
    @staticmethod
    def _futures_expiry(dt: datetime = datetime.now(), months: int = 1) -> str:
        """Returns a string of format YYYYMM corresponding to the leading 
        contract month, from the inputted datetime object.

        Parameters
        ----------
        dt : datetime, optional
            The datetime object to convert to string. The default is datetime.now().
        months : int, optional
            The month offset from dt. The default is 1.

        Returns
        -------
        str
            A string corresponding to the expiry.
        """
        # TODO - if current date is past last trade date... error
        expiry_dt = dt + relativedelta(months=months)
        return expiry_dt.strftime('%Y') + expiry_dt.strftime('%m')
        
        