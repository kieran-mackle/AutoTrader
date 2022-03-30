from autotrader.brokers.trading import Order

class Strategy:
    def __init__(self, params, data, pair, **kwargs):
        """Define all indicators used in the strategy.
        """
        self.name = "Template Strategy"
        self.data = data
        self.params = params
        self.pair = pair
        
        # Define any indicators used in the strategy
        
        # Construct indicators dict for plotting
        self.indicators = {'Indicator Name': {'type': 'indicatortype',
                                              'data': 'indicatordata'},
                           }
        
        
    def generate_signal(self, data):
        """Define strategy logic to determine entry signals.
        """
        
        # Example long market order
        order = Order(direction=1)
        
        return order
    