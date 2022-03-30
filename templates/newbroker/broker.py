from autotrader.brokers.trading import Order
from autotrader.brokers.broker_utils import BrokerUtils

"""
Notes:
    - Public methods are called from outside the broker module, and so must
      retain functionality of input arguments. If necessary, they can simply
      be wrapper methods.
    - Private methods are broker-specific.
"""

class Broker:
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor.
        """
        
        self.utils = utils if utils is not None else BrokerUtils()
        
        # Unpack config and connect to broker-side API
        
    
    def __repr__(self):
        return 'AutoTrader Broker interface'
    
    
    def __str__(self):
        return 'AutoTrader Broker interface'
    
    
    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account.
        """
        pass
    
    
    def get_balance(self) -> float:
        """Returns account balance.
        """
        pass
        
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Disassemble order_details dictionary to place order.
        """
        # Call order to set order time
        order()
        
        # Submit order to broker
        
    
    def get_orders(self, instrument: str = None, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account.
        """
        pass
    
    
    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels order by order ID.
        """
        pass
    
    
    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account. 
        """
        pass
    
    
    def get_trade_details(self, trade_ID: str) -> dict:
        """Returns the details of the trade specified by trade_ID.
        """
        pass
    
    
    def get_positions(self, instrument: str = None, **kwargs) -> dict:
        """Gets the current positions open on the account.
        
        Parameters
        ----------
        instrument : str, optional
            The trading instrument name (symbol). The default is None.
            
        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """
        pass
    
    
    # Define here any private methods to support the public methods above
    
    