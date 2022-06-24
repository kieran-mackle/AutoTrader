import pandas as pd
from datetime import datetime
from dydx3 import Client, constants
from autotrader.brokers.trading import Order
from autotrader.brokers.broker_utils import BrokerUtils


class Broker:
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor.
        """
        
        self.utils = utils if utils is not None else BrokerUtils()
        
        # Unpack config and connect to broker-side API
        self.api = Client(host='https://api.dydx.exchange',
                api_key_credentials=config['API_KEY'],
                stark_private_key=config['STARK_KEYS']['private_key'],
                stark_public_key=config['STARK_KEYS']['public_key'],
                stark_public_key_y_coordinate=config['STARK_KEYS']['public_key_y_coordinate'],
                eth_private_key=config['ETH_PRIV_KEY'],
                default_ethereum_address=config['ETH_ADDR']
                )
        
        order = Order(instrument='ALGO-USD', 
                      size=10, order_type='limit',
                      order_limit_price=0.2, direction=1, 
                      post_only=True)
        db = 0
        
    
    def __repr__(self):
        return 'AutoTrader-dYdX interface'
    
    
    def __str__(self):
        return 'AutoTrader-dYdX interface'
    
    
    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account.
        """
        account = self._get_account()
        return float(account['equity'])
    
    
    def get_balance(self) -> float:
        """Returns account balance.
        """
        return self.get_NAV()
        
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Disassemble order_details dictionary to place order.
        """
        # TODO - build in checking of constants.__dict__ for instrument
        
        # TODO - error with trigger_price
        
        # Call order to set order time
        order()
        
        # Extract information for submission to dydx
        side = 'BUY' if order.direction > 0 else 'SELL'
        order_type = order.order_type.upper()
        expiration = int((pd.Timedelta('30days') + datetime.now()).timestamp())
        order_price = str(order.order_limit_price) if \
            order.order_limit_price is not None else None
        trigger_price = str(order.order_stop_price) if \
            order.order_stop_price is not None else None
        position_id = self._get_account()['positionId']
        
        # Submit order to dydx
        order = self.api.private.create_order(position_id=position_id, 
                                              market=order.instrument, 
                                              side=side,
                                              order_type=order_type, 
                                              post_only=order.post_only, 
                                              size=str(order.size), 
                                              price=order_price, 
                                              limit_fee='0.015',
                                              trigger_price=trigger_price,
                                              expiration_epoch_seconds=expiration)
        
        return self._native_order(order.data['order'])
        
    
    def get_orders(self, instrument: str = None, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account.
        
        kwargs can include status, side, type, limit, createdBeforeOrAt and returnLatestOrders. See
        https://docs.dydx.exchange/?python#get-orders for more details.
        """
        orders = self.api.private.get_orders(market=instrument, **kwargs)
        orders = self._conver_order_list(orders.data['orders'])
        return orders
    
    
    def cancel_order(self, order_id: int, **kwargs) -> None:
        """Cancels order by order ID.
        """
        cancelled_order = self.api.private.cancel_order(order_id)
        
        return self._native_order(cancelled_order.data['order'])
    
    
    def cancel_all_orders(self, instrument: str = None, **kwargs):
        cancelled_orders = self.api.private.cancel_all_orders(market=instrument)
        return cancelled_orders
    
    
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
        # TODO - use instrument provided
        positions = self.api.private.get_positions()
        return positions
    
    
    def get_markets(self):
        # Get Markets
        markets = self.api.public.get_markets()
        market_df = pd.DataFrame(markets.data['markets'])
        return market_df


    def get_orderbook(self):
        # Get Orderbook
        orderbook = self.api.public.get_orderbook(market=constants.MARKET_SOL_USD)
        return orderbook


    def get_market_stats(self):
        # Get Market Statistics
        market_statistics = self.api.public.get_stats(market=constants.MARKET_ADA_USD,
                                                    days=1,)
        return market_statistics


    def get_funding(self, dtime):
        # Funding Data
        historical_funding = self.api.public.get_historical_funding(market=constants.MARKET_BTC_USD,
                                                              effective_before_or_at=dtime
                                                              )

        funding_df = pd.DataFrame(historical_funding.data["historicalFunding"])
        funding_df['rate'] = pd.to_numeric(funding_df['rate'], errors='coerce')
        funding_df['price'] = pd.to_numeric(funding_df['price'], errors='coerce')
        funding_df['effectiveAt'] = pd.to_datetime(funding_df['effectiveAt'], format='%Y-%m-%dT%H:%M:%S.%f')
        funding_df['rate'] = funding_df['rate'] * 100
        
        return funding_df


    def get_candles(self,):
        # Candlestick Data
        candles = self.api.public.get_candles(market=constants.MARKET_BTC_USD,
                                            resolution='1MIN',)
        candles = pd.DataFrame(candles.data["candles"])
        candles.apply(pd.to_numeric, errors='ignore').info()
        return candles
    
    
    def _get_account(self, eth_address: str = None):
        if eth_address is None:
            eth_address = self.api.default_address
        account = self.api.private.get_account(eth_address)
        return account.data['account']
    
    
    def _get_market(self, instrument: str):
        """Returns the dydx market constant from an instrument."""
        pass
        
    
    def _native_order(self, dydx_order):
        """Helper method to convert a dydx order into a native AutoTrader Order."""
        
        direction = 1 if dydx_order['side'] == 'BUY' else -1
        order_limit_price = float(dydx_order['price']) if \
            dydx_order['price'] is not None else None
        order_stop_price = float(dydx_order['triggerPrice']) if \
            dydx_order['triggerPrice'] is not None else None
        order = Order(instrument=dydx_order['market'],
                      order_type=dydx_order['type'],
                      status=dydx_order['status'].lower(),
                      id=dydx_order['id'],
                      direction=direction,
                      size=float(dydx_order['size']),
                      order_limit_price=order_limit_price,
                      order_stop_price=order_stop_price,
                      )
        return order
    
    
    def _conver_order_list(self, order_list):
        orders = {}
        for order in order_list:
            native_order = self._native_order(order)
            orders[native_order.id] = native_order
        return orders
        