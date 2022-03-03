from __future__ import annotations
import numpy as np
from datetime import datetime
# Broker utils


class Order:
    """AutoTrader Order
    """
    def __init__(self, instrument: str, direction: int,
                 order_type: str = 'market', **kwargs) -> Order:
        
        # TODO - remove order prefix from attributes, so its not order.order_type, rather order.type
        # This will have implications to order_signal_dict keys
        
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
        
        self.reason = None
        
        self.strategy = None
        self.granularity = None
        
        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])
        
        # Enforce stop type
        if self.stop_loss is not None:
            self.stop_type = self.stop_type if self.stop_type is \
                not None else 'limit'
                
        # Meta-data
        self.order_id = None
        self.status = None      # options: pending -> open -> cancelled | filled # What is pending vs open?
    
    
    def __repr__(self):
        aux_str = ''
        if self.submitted:
            aux_str = ' (submitted)'
        if self.filled:
            aux_str = ' (filled)'
        
        if self.size is not None:
            return f'{round(self.size,3)} unit {self.instrument} {self.order_type} order{aux_str}'
        else:
            return self.__str__()
        
    
    def __str__(self):
        return 'AutoTrader Order'
    
    
    def __call__(self, broker, order_price, 
                 order_time: datetime = datetime.now()) -> None:
        # TODO - when is this being called?
        self.order_price = order_price
        self.order_time = order_time
        
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
        
    
    def _calculate_exit_prices(self, broker, working_price: float = None) -> None:
        
        # TODO - avoid requiring broker - some might locally allow passing eg. 
        # pip distance SL, in which case, it does not need to be converted here, 
        # it can just be converted in the broker class.
        working_price = working_price if working_price is not None \
            else self._working_price
            
        pip_value = broker.utils.get_pip_ratio(self.instrument)

        # Calculate stop loss price
        if not self.stop_loss and self.stop_distance:
            # Stop loss provided as pip distance, convert to price
            self.stop_loss = working_price - np.sign(self.direction)*\
                self.stop_distance*pip_value
        
        # Calculate take profit price
        if not self.take_profit and self.take_distance:
            # Take profit pip distance specified, convert to price
            self.take_profit = working_price + np.sign(self.direction)*\
                self.take_distance*pip_value
        

    def _calculate_position_size(self, broker, working_price: float = None, 
                                 HCF: float = 1, risk_pc: float = 0,
                                 sizing: str | float = 'risk') -> None:
        
        working_price = working_price if working_price is not None \
            else self._working_price
        
        if not self.size:
            amount_risked = broker.get_NAV() * risk_pc / 100
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
        pass
    
    
    def as_dict(self) -> dict:
        """Converts Order object to dictionary.

        Returns
        -------
        dict
            DESCRIPTION.

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
    """
    def __init__(self, order: Order) -> Trade:
        
        # Inherit Order attributes
        self._inheret_order(order)
        order.filled = True
        
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
        self.trade_id = None # TODO - order.id, trade.order_id + trade.id
        self.status = None # options: open -> closed | (partially closed?)
        
    
    def __repr__(self):
        return f'{round(self.size,3)} unit {self.instrument} trade'
        
    
    def __str__(self):
        return 'AutoTrader Trade'
    
    
    def _inheret_order(self, order: Order) -> None:
        for attribute, value in order.__dict__.items():
            setattr(self, attribute, value)
            
    @classmethod
    def _split(cls, trade):
        """Splits parent trade into new trade object for partial trade 
        closures."""
        pass


class Position:
    def __init__(self):
        pass


if __name__ == '__main__':
    order_signal_dict = {'instrument': 'EUR_USD','order_type': 'market', 
                         'direction': 1, 'stop_loss': 1.22342}
    o = Order._from_dict(order_signal_dict)