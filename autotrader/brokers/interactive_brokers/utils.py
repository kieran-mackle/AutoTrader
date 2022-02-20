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