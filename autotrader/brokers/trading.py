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
        
        # Need to think about how all attributes will be assigned when building
        # order from dict
        
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
        self.take_distance = None
        
        self.related_orders = None
        
        # Plus other keys...
        self.order_limit_price = None
        self.order_limit_price = None
        
        self.strategy = None
        
        self.submitted = False
        self.filled = False
    
    
    def _infer_attributes(self):
        """Infers unassigned attributes.
        """
        
        order_price = 0 # TODO - comes from price data dict... maybe fill in
        # on broker side
        
        # Define 'working_price' to calculate size and TP
        if self.order_type == 'limit' or self.order_type == 'stop-limit':
            working_price = self.order_limit_price
        else:
            working_price = order_price
        
        # Calculate exit levels
        pip_value = self._broker_utils.get_pip_ratio(instrument)
        stop_distance = self.stop_distance                      # Might be None
        take_distance = self.take_distance
        
        # Calculate stop loss price
        if not self.stop_loss and self.stop_distance:
            # Stop loss provided as pip distance, convert to price
            stop_price = working_price - np.sign(self.direction)*stop_distance*pip_value
        else:
            # Stop loss provided as price or does not exist
            stop_price = self.stop_loss
        
        # Set stop type
        if stop_price is not None:
            stop_type = self.stop_type if self.stop_type is not None else 'limit'
        else:
            # No stop loss specified
            stop_type = None
            
        # Calculate take profit price
        if not self.take_profit and self.take_distance:
            # Take profit pip distance specified
            take_profit = working_price + np.sign(self.direction)*take_distance*pip_value
        else:
            # Take profit price specified, or no take profit specified at all
            take_profit = self.take_profit
        
        # Calculate risked amount
        amount_risked = self._broker.get_balance() * self._strategy_params['risk_pc'] / 100
        
        # Calculate size
        if self.size:
            # Size provided
            size = self.size
        else:
            # Size not provided, need to calculate it
            if self._strategy_params['sizing'] == 'risk':
                size = self._broker_utils.get_size(instrument,
                                                 amount_risked, 
                                                 working_price, 
                                                 stop_price, 
                                                 HCF,
                                                 stop_distance)
            else:
                size = self._strategy_params['sizing']
    
        # Construct order dict by building on signal_dict
        # order_details["order_time"]     = datetime_stamp
        # order_details["strategy"]       = self._strategy.name
        # order_details["instrument"]     = order_signal_dict['instrument'] if 'instrument' in order_signal_dict else instrument
        # order_details["size"]           = signal*size
        # order_details["order_price"]    = order_price
        # order_details["HCF"]            = HCF
        # order_details["granularity"]    = self._strategy_params['granularity']
        # order_details["stop_distance"]  = stop_distance
        # order_details["stop_loss"]      = stop_price
        # order_details["take_profit"]    = take_profit
        # order_details["stop_type"]      = stop_type
        # order_details["related_orders"] = order_signal_dict['related_orders'] if 'related_orders' in order_signal_dict else None


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
            # TODO - maybe pass all keys in as kwargs? If possible...
            # Could just add order_dict arg in __init__ which gets unpacked
            # similar to kwargs anyway
            
        return order


class Trade(Order):
    """AutoTrader Trade
    """
    def __init__(self):
        pass
    
    def __str__(self):
        return 'AutoTrader Trade'


if __name__ == '__main__':
    order_dict = {'direction': -1, 'size': 1242, 'stop_loss': 1.1224}
    o = Order.from_dict(order_dict)