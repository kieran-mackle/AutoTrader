from autotrader.brokers.broker_utils import BrokerUtils

class Broker:
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor.
        """
        
        self.utils = utils if utils is not None else BrokerUtils()
        
        # Upack config and connect to broker-side API
        
    
    def __repr__(self):
        return 'AutoTrader Broker interface'
    
    
    def __str__(self):
        return 'AutoTrader Broker interface'
    
    
    def get_summary(self):
        """Returns account summary.
        """
        pass
    
    
    def get_NAV(self):
        """Returns the net asset/liquidation value of the account.
        """
        pass
    
    
    def get_balance(self):
        """Returns account balance.
        """
        pass
        
    
    def get_trade_details(self, trade_ID: str):
        """Returns the details of the trade specified by trade_ID.
        """
        pass
    
    
    def get_price(self, symbol: str, snapshot: bool = True, **kwargs):
        """Returns current price (bid+ask) and home conversion factors.
        """
        pass
    
    
    def get_pending_orders(self, symbol=None):
        """Returns all pending orders (have not been filled) in the account.
        """
        pass
    
    
    def cancel_pending_order(self, order_id: int):
        """Cancels pending order by order ID.
        """
        pass
    
    
    def get_open_trades(self, symbol: str = None):
        """Returns the open trades held by the account. 
        """
        pass
    
    
    def get_open_positions(self, symbol: str = None, 
                           local_symbol: str = None) -> dict:
        """Gets the current positions open on the account.
        
        Parameters
        ----------
        symbol : str, optional
            The product symbol. The default is None.
        local_symbol : str, optional
            The exchange-local product symbol. The default is None.
            
        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """
        pass
    
    
    def place_order(self, order_details: dict) -> None:
        """Disassemble order_details dictionary to place order.
        """
        pass
        
    
    def get_historical_data(self, symbol: str, interval: str, 
                            from_time: str, to_time: str):
        """Returns historical price data.
        """
        pass
        
        
    # Define here any private methods to support the public methods above