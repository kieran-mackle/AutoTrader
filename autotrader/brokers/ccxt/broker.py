import ccxt
from datetime import datetime
from autotrader.brokers.trading import Order
from autotrader.brokers.broker_utils import BrokerUtils


class Broker:
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor.
        """
        
        self.utils = utils if utils is not None else BrokerUtils()
        
        # Unpack config and connect to broker-side API
        self.exchange = config['exchange']
        exchange_instance = getattr(ccxt, self.exchange)
        self.api = exchange_instance({'apiKey': config['api_key'],
                                      'secret': config['secret']})
        
        # Load markets
        markets = self.api.load_markets()
        
        if config['sandbox_mode']:
            self.api.set_sandbox_mode(True)
        
        self.base_currency = config['base_currency']
        
        pause = 0
        
    
    def __repr__(self):
        return f'AutoTrader-{self.exchange[0].upper()}'+\
            f'{self.exchange[1:].lower()} interface'
    
    
    def __str__(self):
        return self.__repr__()
    
    
    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account.
        """
        return self.api.fetchBalance()[self.base_currency]['total']
    
    
    def get_balance(self) -> float:
        """Returns account balance.
        """
        return self.api.fetchBalance()[self.base_currency]['total']
        
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Disassemble order_details dictionary to place order.
        """
        # Call order to set order time
        order()
        
        # Submit order to broker
        
    
    def get_orders(self, instrument: str = None, 
                   order_status: str = 'open', **kwargs) -> dict:
        """Returns orders associated with the account.
        """
        if instrument is None:
            raise Exception("Instrument must be specified.")
        
        if order_status == 'open':
            # Fetch open orders (waiting to be filled)
            orders = self.api.fetchOpenOrders(instrument)
            
            
        elif order_status == 'cancelled':
            # Fetch cancelled orders                
            orders = self.api.fetchCanceledOrders(instrument)
        
        elif order_status == 'closed':
            # Fetch closed orders
            orders = self.api.fetchClosedOrders(instrument)
        
        # Convert
        orders = self._convert_list(orders, orders=True)
        
        return orders
    
    
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
    
    
    def _native_order(self, order):
        """Returns a CCXT order as a native AutoTrader Order."""
        direction = 1 if order['side'] == 'buy' else -1
        order_type = order['info']['type'].lower()
        
        if order_type == 'limit':
            limit_price = order['price']
        else:
            limit_price = None
        
        native_order = Order(instrument=order['symbol'],
                             direction=direction, 
                             order_type=order_type,
                             status=order['status'],
                             size=abs(order['amount']),
                             id=order['id'],
                             order_limit_price=limit_price,
                             order_stop_price=order['stopPrice'],
                             order_time=datetime.fromtimestamp(order['timestamp']/1000),
                             )
        return native_order
    
    
    def _native_trade(self, trade):
        """Returns a CCXT trade as a native AutoTrader Trade."""
        pass
    
    
    def _convert_list(self, items, orders: bool = False, trades: bool = False):
        """Converts a list of trades or orders to a dictionary."""
        
        native_func = '_native_order' if orders else '_native_trade'
        converted = {}
        for item in items:
            native = getattr(self, native_func)(item)
            converted[native.id] = native
        
        return converted
    