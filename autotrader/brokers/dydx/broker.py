import dydx3
import pandas as pd
from autotrader.brokers.trading import Order
from autotrader.brokers.broker_utils import BrokerUtils


class Broker:
    def __init__(self, config: dict, utils: BrokerUtils = None) -> None:
        """AutoTrader Broker Class constructor.
        """
        
        self.utils = utils if utils is not None else BrokerUtils()
        
        # Unpack config and connect to broker-side API
        self.api = dydx3.Client(host='https://api.dydx.exchange',
                api_key_credentials=config['API_KEY'],
                stark_private_key=config['STARK_KEYS']['private_key'],
                stark_public_key=config['STARK_KEYS']['public_key'],
                stark_public_key_y_coordinate=config['STARK_KEYS']['public_key_y_coordinate'],
                eth_private_key=config['ETH_PRIV_KEY'],
                default_ethereum_address=config['ETH_ADDR']
                )
        
    
    def __repr__(self):
        return 'AutoTrader-dYdX interface'
    
    
    def __str__(self):
        return 'AutoTrader-dYdX interface'
    
    
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
        orderbook = self.api.public.get_orderbook(market=dydx3.constants.MARKET_SOL_USD)
        return orderbook


    def get_market_stats(self):
        # Get Market Statistics
        market_statistics = self.api.public.get_stats(market=dydx3.constants.MARKET_ADA_USD,
                                                    days=1,)
        return market_statistics


    def get_funding(self, dtime):
        # Funding Data
        historical_funding = self.api.public.get_historical_funding(market=dydx3.constants.MARKET_BTC_USD,
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
        candles = self.api.public.get_candles(market=dydx3.constants.MARKET_BTC_USD,
                                            resolution='1MIN',)
        candles = pd.DataFrame(candles.data["candles"])
        candles.apply(pd.to_numeric, errors='ignore').info()
        return candles
    
    
    def _get_account(self, eth_address):
        account = self.api.private.get_account(eth_address)
        return account.data['account']
    