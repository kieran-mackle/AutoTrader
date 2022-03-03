from __future__ import annotations
import numpy as np
from datetime import datetime
# Broker utils


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
        
        self.strategy = None
        self.granularity = None
        
        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])
        
        # Inferable attributes
        if self.order_price is not None:
            self._infer_attributes(self.order_price)
            
        # Meta-data
        self.order_id = None
        self.submitted = False
        self.filled = False
        self.active = False
        self.status = None
    
    
    def __repr__(self):
        aux_str = ''
        if self.submitted:
            aux_str = '(submitted)'
        if self.filled:
            aux_str = '(filled)'
        
        if self.size is not None:
            return f'{self.size} unit {self.order_type} order {aux_str}'
        else:
            return self.__str__()
        
    
    def __str__(self):
        return 'AutoTrader Order'
    
    
    def _infer_attributes(self, order_price: float, order_time: datetime, 
                          broker, HCF: float = 1, risk_pc: float = 0,
                          sizing: str | float = 'risk') -> None:
        """Infers unassigned attributes.
        """
        
        # Assign attributes
        self.HCF = HCF
        self.order_price = order_price
        self.order_time = order_time
        
        # Define 'working_price' to calculate size and TP
        if self.order_type == 'limit' or self.order_type == 'stop-limit':
            working_price = self.order_limit_price
        else:
            working_price = order_price
        
        # Calculate stop loss price
        pip_value = broker.utils.get_pip_ratio(self.instrument)
        if not self.stop_loss and self.stop_distance:
            # Stop loss provided as pip distance, convert to price
            self.stop_loss = working_price - np.sign(self.direction)*\
                self.stop_distance*pip_value
        
        # Set stop type
        if self.stop_loss is not None:
            self.stop_type = self.stop_type if self.stop_type is \
                not None else 'limit'

        # Calculate take profit price
        if not self.take_profit and self.take_distance:
            # Take profit pip distance specified, convert to price
            self.take_profit = working_price + np.sign(self.direction)*\
                self.take_distance*pip_value
        else:
            # Take profit price specified, or no take profit specified at all
            self.take_profit = self.take_profit
        
        # Calculate size
        amount_risked = broker.get_balance() * risk_pc / 100
        if self.size:
            # Size provided
            size = self.size
        else:
            # Size not provided, need to calculate it
            if self._strategy_params['sizing'] == 'risk':
                size = broker.utils.get_size(self.instrument, amount_risked, 
                                             working_price, self.stop_loss, 
                                             HCF, self.stop_distance)
            # ~ OTHER SIZING METHODS GO HERE ~
                
        # Vectorise and save size
        self.size = self.direction * size


    @classmethod
    def from_dict(cls, order_dict: dict) -> Order:
        return Order(**order_dict)


class Trade(Order):
    """AutoTrader Trade.
    """
    def __init__(self):
        
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
        
    
    def __str__(self):
        return 'AutoTrader Trade'


if __name__ == '__main__':
    order_signal_dict = {'instrument': 'EUR_USD','order_type': 'market', 
                         'direction': 1, 'stop_loss': 1.22342}
    o = Order.from_dict(order_signal_dict)