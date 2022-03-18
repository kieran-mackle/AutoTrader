# Running AutoTrader In Continuous Mode

If there is no lookahead bias in the strategy, the results should be identical between each mode.

|           | Periodic Mode | Continuous Mode |
| --------- | ------------- | --------------- |
| Strategy instantiation | Every update | Once during deployment |
| Data indexing | Index based | Time based |
| Lookahead risk | High | Low |


Periodic mode is data-dependent, continuous mode is timeperiod-dependent. Periodic more can 
only test on the data procided, continous mode can have evolving data. 


````{tab} Periodic Mode
```python
    def generate_signal(self, i, **kwargs):
        """Define strategy to determine entry signals.
        """
        
        if self.data.Close.values[i] > self.ema[i] and \ 
            self.MACD_CO[i] == 1 and \
            self.MACD_CO_vals[i] < 0:
                exit_dict = self.generate_exit_levels(signal=1, i=i)
                new_order = Order(direction=1,
                                  stop_loss=exit_dict['stop_loss'],
                                  take_profit=exit_dict['take_profit'])
                
        elif self.data.Close.values[i] < self.ema[i] and \
            self.MACD_CO[i] == -1 and \
            self.MACD_CO_vals[i] > 0:
                exit_dict = self.generate_exit_levels(signal=-1, i=i)
                new_order = Order(direction=-1,
                                  stop_loss=exit_dict['stop_loss'],
                                  take_profit=exit_dict['take_profit'])

        else:
            new_order = Order()
        
        return new_order
```
````
````{tab} Continuous Mode
```python
    def generate_signal(self, data):
        """Define strategy to determine entry signals.
        """
        
        # Feature calculation
        self.calculate_features(data)
        
        i = -1
        if self.data.Close.values[i] > self.ema[i] and \
            self.MACD_CO[i] == 1 and \
            self.MACD_CO_vals[i] < 0:
                exit_dict = self.generate_exit_levels(signal=1, i=i)
                new_order = Order(direction=1,
                                  stop_loss=exit_dict['stop_loss'],
                                  take_profit=exit_dict['take_profit'])
                
        elif self.data.Close.values[i] < self.ema[i] and \
            self.MACD_CO[i] == -1 and \
            self.MACD_CO_vals[i] > 0:
                exit_dict = self.generate_exit_levels(signal=-1, i=i)
                new_order = Order(direction=-1,
                                  stop_loss=exit_dict['stop_loss'],
                                  take_profit=exit_dict['take_profit'])

        else:
            new_order = Order()
        
        return new_order
    
    def calculate_features(self, data):
        
        # Save data for other functions
        self.data = data
        
        # 200EMA
        self.ema = TA.EMA(data, self.params['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, self.params['MACD_fast'], 
                            self.params['MACD_slow'], self.params['MACD_smoothing'])
        self.MACD_CO = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
        self.MACD_CO_vals = indicators.cross_values(self.MACD.MACD, 
                                                    self.MACD.SIGNAL,
                                                    self.MACD_CO)
        
        # Price swings
        self.swings = indicators.find_swings(data)
```
````

