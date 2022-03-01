class Strategy:
    def __init__(self, params, data, pair):
        """Define all indicators used in the strategy.
        """
        self.name   = "Template Strategy"
        self.data   = data
        self.params = params
        self.pair = pair
        
        # Define any indicators used in the strategy
        
        # Construct indicators dict for plotting
        self.indicators = {'Indicator Name': {'type': 'indicatortype',
                                              'data': 'indicatordata'},
                           }
        
        
    def generate_signal(self, i, current_position):
        """Define strategy logic to determine entry signals.
        """
        
        # Example long market order:
        signal_dict = {'order_type': 'market',
                       'direction': 1}
        
        # Direction can be 1 for long trades, or -1 for short trades
        
        return signal_dict
    