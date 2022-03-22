import ib_insync
from datetime import datetime
from autotrader.brokers.trading import Order
from dateutil.relativedelta import relativedelta
from autotrader.brokers.broker_utils import BrokerUtils


class Utils(BrokerUtils):
    def __init__(self):
        pass
    
        
    def __repr__(self):
        return 'AutoTrader-InteractiveBrokers Utilities'
    
    
    def __str__(self):
        return 'AutoTrader-InteractiveBrokers Utilities'
    
    
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
    def build_contract(order: Order) -> ib_insync.contract.Contract:
        """Builds IB contract from the order details.
        """
        instrument = order.instrument
        security_type = order.secType
        
        # Get contract object
        contract_object = getattr(ib_insync, security_type)
        
        if security_type == 'Stock':
            # symbol='', exchange='', currency=''
            exchange = order.exchange if order.exchange else 'SMART'
            currency = order.currency if order.currency else 'USD'
            contract = contract_object(symbol=instrument, exchange=exchange, currency=currency)
            
        elif security_type == 'Options':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
            
        elif security_type == 'Future':
            # Requires order_details{'instrument', 'exchange', 'contract_month'}
            exchange = order.exchange if order.exchange else 'GLOBEX'
            currency = order.currency if order.currency else 'USD'
            contract_month = order.contract_month
            local_symbol = order.localSymbol if order.localSymbol else '' 
            contract = contract_object(symbol=instrument, 
                                       exchange=exchange, 
                                       currency=currency,
                                       lastTradeDateOrContractMonth=contract_month,
                                       localSymbol=local_symbol)
            
        elif security_type == 'ContFuture':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
            
        elif security_type == 'Forex':
            # pair='', exchange='IDEALPRO', symbol='', currency='', **kwargs)
            exchange = order.exchange if order.exchange else 'IDEALPRO'
            contract = contract_object(pair=instrument, exchange=exchange)
            
        elif security_type == 'Index':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
            
        elif security_type == 'CFD':
            # symbol='', exchange='', currency='',
            exchange = order.exchange if order.exchange else 'SMART'
            currency = order.currency if order.currency else 'USD'
            contract = contract_object(symbol=instrument, exchange=exchange, currency=currency)
            
        elif security_type == 'Commodity':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
        elif security_type == 'Bond':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
        elif security_type == 'FuturesOption':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
        elif security_type == 'MutualFund':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
        elif security_type == 'Warrant':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
        elif security_type == 'Bag':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
        elif security_type == 'Crypto':
            raise NotImplementedError(f"Contract building for {security_type.lower()} trading is not supported yet.")
        
        return contract
    
    
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
        
        