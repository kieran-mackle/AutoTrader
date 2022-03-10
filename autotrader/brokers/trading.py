from __future__ import annotations
import numpy as np
from datetime import datetime
from autotrader.brokers.broker_utils import BrokerUtils


class Order:
    """AutoTrader Order
    """
    def __init__(self, instrument: str, direction: int,
                 order_type: str = 'market', **kwargs) -> Order:
        
        # Required attributes
        self.instrument = instrument
        self.order_type = order_type
        self.direction = direction
        self.size = None
        self.order_price = None
        self.order_time = None
        self.order_limit_price = None
        self.order_limit_price = None
        
        self.HCF = None
        
        self.stop_type = None
        self.stop_loss = None
        self.stop_distance = None
        
        self.take_profit = None
        self.take_distance = None
        
        self.related_orders = None
        
        # IB properties
        self.currency = None
        self.secType = None
        self.exchange = None
        self.contract_month = None
        self.local_symbol = None
        
        self.reason = None
        
        self.strategy = None
        self.granularity = None
        self._sizing = None
        self._risk_pc = None
        
        # Meta-data
        self.id = None
        self.status = None # options: pending -> open -> cancelled | filled
        
        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])
        
        # Enforce stop type
        if self.stop_loss is not None:
            self.stop_type = self.stop_type if self.stop_type is \
                not None else 'limit'
    
    
    def __repr__(self):
        if self.size is not None:
            return f'{round(self.size,3)} unit {self.instrument} {self.order_type} order'
        else:
            return self.__str__()
        
    
    def __str__(self):
        return f'{self.instrument} {self.order_type} Order'
    
    
    def __call__(self, broker = None, order_price: float = None, 
                 order_time: datetime = datetime.now(), 
                 HCF: float = 1) -> None:
        """Order object, called to initialise prior to submission to broker.

        Parameters
        ----------
        broker : TYPE, optional
            DESCRIPTION. The default is None.
        order_price : float, optional
            DESCRIPTION. The default is None.
        order_time : datetime, optional
            DESCRIPTION. The default is datetime.now().
        HCF : float, optional
            DESCRIPTION. The default is 1.

        Returns
        -------
        None
            DESCRIPTION.
        """
        self.order_price = order_price if order_price else self.order_price
        self.order_time = order_time if order_time else self.order_time
        self.HCF = HCF if HCF else self.HCF
        
        self._set_working_price()
        self._calculate_exit_prices(broker)
        self._calculate_position_size(broker)
        
        self.status = 'submitted'
        self.submitted = True
        
        
    def _set_working_price(self, order_price: float = None) -> None:
        """Sets the Orders' working price, for calculating exit targets.

        Parameters
        ----------
        order_price : float, optional
            The order price.

        Returns
        -------
        None
            The working price will be saved as a class attribute.
        """
        order_price = order_price if order_price is not None \
            else self.order_price
        if self.order_type == 'limit' or self.order_type == 'stop-limit':
            self._working_price = self.order_limit_price
        else:
            self._working_price = order_price
        
    
    def _calculate_exit_prices(self, broker = None, 
                               working_price: float = None) -> None:
        """Calculates the prices of the exit targets from the pip distance
        values.

        Parameters
        ----------
        broker : TYPE, optional
            The autotrade-broker instance. The default is None.
        working_price : float, optional
            The working price used to calculate amount risked. The default is 
            None.

        Returns
        -------
        None
            The exit prices will be assigned to the order instance.
        """
        working_price = working_price if working_price is not None \
            else self._working_price
        
        if broker is None:
            utils = BrokerUtils()
        else:
            utils = broker.utils
        pip_value = utils.get_pip_ratio(self.instrument)

        # Calculate stop loss price
        if self.stop_loss is None and self.stop_distance is not None:
            # Stop loss provided as pip distance, convert to price
            self.stop_loss = working_price - np.sign(self.direction)*\
                self.stop_distance*pip_value
        
        # Calculate take profit price
        if self.take_profit is None and self.take_distance is not None:
            # Take profit pip distance specified, convert to price
            self.take_profit = working_price + np.sign(self.direction)*\
                self.take_distance*pip_value
        

    def _calculate_position_size(self, broker = None, working_price: float = None, 
                                 HCF: float = 1, risk_pc: float = 0,
                                 sizing: str | float = 'risk', 
                                 amount_risked: float = None) -> None:
        """Calculates trade size for order.

        Parameters
        ----------
        broker : TYPE, optional
            The autotrade-broker instance. The default is None.
        working_price : float, optional
            The working price used to calculate amount risked. The default is None.
        HCF : float, optional
            The home conversion factor. The default is 1.
        risk_pc : float, optional
            The percentage of the account NAV to risk on the trade. The default is 0.
        sizing : str | float, optional
            The sizing option. The default is 'risk'.
        amount_risked : float, optional
            The dollar amount risked on the trade. The default is None.

        Returns
        -------
        None
            The trade size will be assigned to the order instance.
        """ 
        working_price = working_price if working_price is not None \
            else self._working_price
        HCF = self.HCF if self.HCF is not None \
            else HCF
        sizing = self._sizing if self._sizing is not None \
            else sizing 
        risk_pc = self._risk_pc if self._risk_pc is not None \
            else risk_pc
        
        if self.size is None:
            amount_risked = amount_risked if amount_risked else \
                broker.get_NAV() * risk_pc / 100
            # Size not provided, need to calculate it
            if sizing == 'risk':
                size = broker.utils.get_size(self.instrument, amount_risked, 
                                             working_price, self.stop_loss, 
                                             HCF, self.stop_distance)
            else:
                self.size = sizing
            
            # Vectorise and save size
            self.size = self.direction * size
    
    
    def _check_precision(self,):
        # TODO - implement
        raise NotImplementedError("This method has not been implemented yet.")
    
    
    def _validate(self,):
        # TODO - add order validation method, ie. for IB, check all attributes are
        # assigned (eg. sectype, etc)
        raise NotImplementedError("This method has not been implemented yet.")
    
    
    def as_dict(self) -> dict:
        """Converts Order object to dictionary.

        Returns
        -------
        dict
            The order instance returned as a dict object.

        Notes
        -----
        This method enables legacy code operation, returning order/trade
        objects as a dictionary.
        """
        return self.__dict__
    

    @classmethod
    def _from_dict(cls, order_dict: dict) -> Order:
        return Order(**order_dict)


class Trade(Order):
    """AutoTrader Trade.
    
    Notes
    -----
    When a trade is created from an Order, the Order will be marked as filled.
    """
    def __init__(self, order: Order = None) -> Trade:
        
        # Trade data
        self.unrealised_PL = None
        self.margin_required = None
        self.time_filled = None
        self.fill_price = None
        
        self.last_price = None
        self.last_time = None
        
        self.profit = None
        self.balance = None
        self.exit_price = None
        self.exit_time = None
        self.fees = None
        
        # Meta data
        self.parent_id = None # ID of order which spawned trade
        self.id = None 
        self.status = None # options: open -> closed
        self.split = False
        
        # Inherit order attributes
        if order:
            self._inheret_order(order)
            order.status = 'filled'
            self.parent_id = order.id
        
    
    def __repr__(self):
        return f'{round(self.size,3)} unit {self.instrument} trade'
        
    
    def __str__(self):
        return 'AutoTrader Trade'
    
    
    def _inheret_order(self, order: Order) -> None:
        for attribute, value in order.__dict__.items():
            setattr(self, attribute, value)
            
    @classmethod
    def _split(cls, trade: Trade, split_units: float) -> Trade:
        """Splits parent trade into new trade object for partial trade 
        closures.
        
        split units are given to the new trade.
        """
        split_trade = cls()
        for attribute, value in trade.__dict__.items():
            setattr(split_trade, attribute, value)
        
        # Reset ID
        split_trade.parent_id = trade.order_id
        split_trade.order_id = None
        
        # Transfer units
        split_trade.size = split_units
        trade.size -= split_units
        
        # Mark original trade as split
        trade.split = True
        
        return split_trade


class Position:
    def __init__(self, **kwargs):
        self.instrument = None
        self.long_units = None
        self.long_PL = None
        self.long_margin = None
        self.short_units = None
        self.short_PL = None
        self.short_margin = None
        self.total_margin = None
        self.trade_IDs = None
        
        for item in kwargs:
            setattr(self, item, kwargs[item])
    
    def __repr__(self):
        return f'AutoTrader Position in {self.instrument}'
        
    
    def __str__(self):
        return 'AutoTrader Position'
    
    
    def as_dict(self) -> dict:
        """Converts Position object to dictionary.

        Returns
        -------
        dict
            The Position instance returned as a dict object.

        Notes
        -----
        This method enables legacy code operation, returning order/trade
        objects as a dictionary.
        """
        return self.__dict__


if __name__ == '__main__':
    order_signal_dict = {'instrument': 'EUR_USD','order_type': 'market', 
                         'direction': 1, 'stop_loss': 1.22342}
    o = Order._from_dict(order_signal_dict)