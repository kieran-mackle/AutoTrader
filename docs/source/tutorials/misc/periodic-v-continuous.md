(autotrader-run-modes)=
# Periodic versus Continuous Mode

AutoTrader has two run modes which control how data is handled and 
how frequently strategies are instantiated. The active run mode is 
controlled using [`configure`](autotrader-configure) method. A 
summary of these modes is provided in the table below, but the 
following sections discuss them in more detail.


|           | Periodic Mode | Continuous Mode |
| --------- | ------------- | --------------- |
| Strategy instantiation | Every update | Once during deployment |
| Data indexing | Index based | Time based |
| Lookahead risk | High | Low |
| Backtest time | Very fast | Slow |

```{important}
The input arguments to your strategy's `generate_signal` method 
change slightly depending on the run mode you are using. See the
[example](run-mode-comparison) below.
```


(autotrader-periodic-mode)=
## Periodic Update Mode
In periodic update mode, an integer index `i` is used to iterate through 
the data set to provide trading signals at different points in time. When
backtesting, this index will vary from `0` to `len(data)`. Upon each 
iteration, the method `generate_signal` from the strategy module is 
called to obtain a signal corresponding to the current timestep. When 
livetrading or scanning, this index will be `-1`, corresponding to the 
most recent data, as required for livetrading. This is adequate for
most strategies, but carries the risk of accidental data leakage when 
backtesting, since the strategy is instantiated with the entire dataset. 

After the trading bots are updated with the latest data in periodic 
update mode, they will self-terminate and the AutoTrader instance will 
become inactive. For this reason, AutoTrader must be run periodically to 
repeatedly deploy trading bots and act on the latest signal - hence the 
name 'periodic update mode'. For example, a strategy running on the 
4-hour timeframe, AutoTrader should be scheduled to run every 4 hours. 
Each time it runs, the trading bots will be provided with data of the 
latest 4-hour candles to run the strategy on. This task is easily 
automated using [cron](https://en.wikipedia.org/wiki/Cron), or even with a 
`while True` loop and `time.sleep`. A single bot update in this mode is 
illustrated in the chart below.


```{image} ../../assets/images/light-periodic-update-run.svg
:align: center
:class: only-light
```

```{image} ../../assets/images/dark-periodic-update-run.svg
:align: center
:class: only-dark
```

Noting this should bring to attention a point of difference between 
backtesting and livetrading using periodic update mode: strategies 
are instantiated once in backtests, but multiple times when 
livetrading. For some strategies this does not matter, but for others 
where you would like to maintain the strategies attributes it does. 
In such cases, continuous update mode may be better suited. 



(autotrader-continuous-mode)=
## Continuous Update Mode

In continuous update mode, a time marching algorithm is used in place 
of the integer indexing method used in periodic update mode. That is, 
time is slowly incremented forwards, and data is slowly revealed to 
the trading bots. More importantly, there is practically no difference
 between backtesting and livetrading from the perspective of the 
 trading bots; strategies are instantiated once in both mediums. 
 This means that strategies will maintain attributes from the time it 
 is deployed until the time it is terminated. Data is automatically 
 checked for lookahead bias in this mode, ensuring that the strategy 
 will not see any future data. This comes at the cost of extra 
 processing, meaning that backtesting in this mode is significantly slower.

The charts below illustrate this mode.

```{image} ../../assets/images/light-detached-bot.svg
:align: center
:class: only-light
```

```{image} ../../assets/images/dark-detached-bot.svg
:align: center
:class: only-dark
```

(autotrader-instance-file)=
### Livetrading Bot Management
When bots are deployed for livetrading in continuous mode, a directory 
named 'active_bots' will be created in the working directory. In this 
directory, an 'instance file' will be created for each active instance 
of AutoTrader. The contents of the instance file includes the trading
bots deployed in that instance, and the instruments they are trading. 
This provides a reference as to which AutoTrader instance contains 
which trading bots. To kill an active instance of AutoTrader, simply
delete (or rename) the instance file. This will safely terminate the 
active bots, and proceed with the 
[shutdown routines](strategy-shutdown-routine).

```{seealso}
The name of the instance file can be customised using the `instance_str` argument of the 
[configure](autotrader-configure) method.
```



(run-mode-comparison)=
## Example 
Instantiation between each mode is the same, but instead of using an 
integer index `i` to iterate through the data, continous mode provides
your strategy with the most up-to-date data at a given timestamp. 
In theory, if your code has no look-ahead, the same results will be 
achieved regardless of the run mode used. The code below shows the
differences in the `generate_signal` method of the 
[strategy](trading-strategy) class.


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