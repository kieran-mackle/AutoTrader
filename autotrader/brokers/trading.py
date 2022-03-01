from __future__ import annotations


class Order:
    """AutoTrader Order
    """
    def __init__(self, order_type: str = 'market', direction: int = 0, 
                 **kwargs) -> Order:
        
        # Required attributes
        self.order_type = order_type
        self.direction = direction
        
        # Unpack kwargs
        for item in kwargs:
            setattr(self, item, kwargs[item])
        
        # Inferable attributes
        # whatever hasn't been assigned...
        
        
        self.order_time = None
        self.instrument = None
        self.order_price = None
        
        self.size = None
        self.HCF = None
        
        self.granularity = None
        self.stop_type = None
        self.stop_loss = None
        self.stop_distance = None
        
        self.take_profit = None
        
        self.related_orders = None
        
        # Plus other keys...
        self.order_limit_price = None
        self.order_limit_price = None
        
        self.strategy = None
        
        self.submitted = False
        self.filled = False
    
    
    def __repr__(self):
        aux_str = ''
        if self.submitted:
            aux_str = '(submitted)'
        if self.filled:
            aux_str = '(filled)'
        
        if self.direction is not None:
            return f'{self.size} unit {self.order_type} order {aux_str}'
        else:
            return self.__str__()
        
    
    def __str__(self):
        return 'AutoTrader Order'
    
    
    @classmethod
    def from_dict(cls, order_dict: dict) -> Order:
        order = Order()
        for key in order_dict:
            setattr(order, key, order_dict[key])
        return order


class Trade(Order):
    """AutoTrader Trade
    """
    def __init__(self):
        pass
    
    def __str__(self):
        return 'AutoTrader Trade'
