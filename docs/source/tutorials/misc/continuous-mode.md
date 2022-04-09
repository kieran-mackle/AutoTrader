# Running AutoTrader In Continuous Mode

AutoTrader `v0.6.0` introduced continuous mode, making deploying bots to livetrade even easier. This
mode has a few key differences in how it runs [behind the scenes](autotrader-run-modes), but this page 
is intended to show how the different modes impact the strategy. Instantiation between each mode is the
same, but instead of using an integer index `i` to iterate through the data, continous mode provides
your strategy with the most up-to-date data at a given timestamp. In theory, if your code has no look-ahead,
the same results will be achieved regardless of the run mode used. See the code below to note the
differences in the `generate_signal` method of the [strategy](trading-strategy) class.


````{tab} Periodic Mode
```python
    def __init__(self, parameters, data, instrument):
        self.data = data
        
        # 200EMA
        self.ema = TA.EMA(data, parameters['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, parameters['MACD_fast'], 
                            parameters['MACD_slow'], parameters['MACD_smoothing'])
        self.MACD_CO = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
        self.MACD_CO_vals = indicators.cross_values(self.MACD.MACD, 
                                                    self.MACD.SIGNAL,
                                                    self.MACD_CO)
        
        # Price swings
        self.swings = indicators.find_swings(data)


    def generate_signal(self, i, **kwargs):
        """Define strategy to determine entry signals.
        """
        
        if self.data.Close.values[i] > self.ema[i] and \ 
            self.MACD_CO[i] == 1 and \
            self.MACD_CO_vals[i] < 0:
                new_order = Order(direction=1)
                
        elif self.data.Close.values[i] < self.ema[i] and \
            self.MACD_CO[i] == -1 and \
            self.MACD_CO_vals[i] > 0:
                new_order = Order(direction=-1)

        else:
            new_order = Order()
        
        return new_order
```
````
````{tab} Continuous Mode
```python
    def calculate_features(self, data):
        self.data = data
        
        # 200EMA
        self.ema = TA.EMA(data, self.parameters['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, self.parameters['MACD_fast'], 
                            self.parameters['MACD_slow'], self.parameters['MACD_smoothing'])
        self.MACD_CO = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
        self.MACD_CO_vals = indicators.cross_values(self.MACD.MACD, 
                                                    self.MACD.SIGNAL,
                                                    self.MACD_CO)
        
        # Price swings
        self.swings = indicators.find_swings(data)


    def generate_signal(self, data):
        """Define strategy to determine entry signals.
        """
        self.calculate_features(data) # Feature calculation on new data
        
        if self.data.Close.values[-1] > self.ema[-1] and \
            self.MACD_CO[-1] == 1 and \
            self.MACD_CO_vals[-1] < 0:
                new_order = Order(direction=1)
                
        elif self.data.Close.values[-1] < self.ema[-1] and \
            self.MACD_CO[-1] == -1 and \
            self.MACD_CO_vals[-1] > 0:
                new_order = Order(direction=-1)

        else:
            new_order = Order()
        
        return new_order
```
````

Note that a helper function `calculate_features` has been used to calculate the strategies indicators
each time new data comes in when using continuous mode. In contrast, this would usually happen in the 
`__init__` method of a strategy running in periodic mode.