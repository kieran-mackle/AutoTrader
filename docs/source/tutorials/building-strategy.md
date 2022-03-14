# Building a Strategy

A simple yet effective MACD crossover strategy will be developed in this section. An important note 
here is that this strategy assumes that the trading instrument is a *contract for difference*, and 
hence, can be shorted. 

```{tip}
The code for the MACD crossover strategy shown in this tutorial can be found in the
<a href="https://github.com/kieran-mackle/autotrader-demo" target="_blank">demo repository</a>.
```


## Strategy Rules
Lets start by defining the rules for this strategy.

1. Trade in the direction of the trend, as determined by the 200EMA.
2. Enter a long position when the MACD line crosses *up* over the signal line, and enter a short when the MACD line crosses *down* below 
the signal line.
3. To ensure only the strongest MACD signals, the crossover must occur below the histogram zero line for long positions, and above the histogram 
zero line for short positions.
3. Stop losses are set at recent price swings/significant price levels.
4. Take profit levels are set at 1:1.5 risk-to-reward.

From these rules, the following strategy parameters can be extracted:

| Parameter | Nominal value |
|-----------|---------------|
| ema_period | 200 |
| MACD_fast | 12  |
| MACD_slow | 26  |
| MACD_smoothing | 9 |
| RR | 1.5 |

An example of a long entry signal from this strategy is shown in the image below (generated using 
[AutoTrader IndiView](../features/visualisation)).

![MACD crossover strategy](../assets/images/long_macd_signal.png "Long trade example for the MACD Crossover Strategy")



## Strategy Construction
Strategies in AutoTrader are built as class objects. They contain the logic required to map a set of 
data into a trading signal, which then gets passed on to your broker. To make this possible, the strategy
is instantiated with its parameters, price data for the instrument being traded, and the name of the 
instrument being traded - but don't worry, this is all taken care of behind the scenes by 
[AutoTrader](autotrader-docs). 



### Strategy Configuration
```{admonition} Follow Along
Follow along in the demo repository: 
config/<a href="https://github.com/kieran-mackle/autotrader-demo/blob/main/config/macd.yaml" target="_blank">macd.yaml</a>
```

Now, lets write the [strategy configuration](strategy-config) `.yaml` file. This file is a 
convenient place to define your strategy parameters (using the `PARAMETERS` key) and which instruments to 
trade using this strategy (using the `WATCHLIST` key). It is also used to tell AutoTrader where to find 
your strategy - the `MODULE` key defines the prefix of the file where your strategy is written, and the
`CLASS` key defines the actual class name of your strategy. By separating the strategy parameters from the 
strategy iteself, you are able to easily tweak the strategy to your liking, or perform hyperparameter
optimisation (something we will get to shortly).

```{attention}
YAML cares about whitespace; each nested key must be indented by two spaces more than its parent.
```

We will put our strategy parameters from the table above under the `PARAMETERS` key. You can call these parameters
whatever you want, and that is how they will appear in your strategy. As you can see below, we define the EMA 
period by the `ema_period` key, the MACD settings by the `MACD_fast`, `MACD_slow` and `MACD_smoothing` keys, 
and the risk-to-reward ratio is by the `RR` key. 


```yaml
NAME: 'Simple_macd_strategy'
MODULE: 'macd'
CLASS: 'SimpleMACD'
INTERVAL: '1h'
SIZING: 'risk'
RISK_PC: 1.5
PARAMETERS:
  ema_period: 200
  MACD_fast: 12
  MACD_slow: 26
  MACD_smoothing: 9
  
  # Exit level parameters
  RR: 1.5

WATCHLIST: ['EURUSD=X']
```

This file is read by AutoTrader and passed into your strategy when it is instantiated. We will start by 
backtesting on the EUR/USD currency pair alone, as specified by the `WATCHLIST` key. Note that the format
of the instruments provided here must match your data feed (in this case, Yahoo Finance).

```{note}
As of AutoTrader version `0.6.0`, you can now directly pass your strategy configuration to AutoTrader as a dictionary.
```

It is worth noting that we are taking advantage of AutoTrader's automatic position size calculation, by defining the 
`SIZING: 'risk'` and `RISK_PC: 1.5` keys. These keys tell AutoTrader to use a risk-based approach to position sizing. As such,
when an order is submitted from the strategy, AutoTrader will use the current price and stop-loss price to calculate the appropriate
position size, capping the maximium loss to the percentage defined by `RISK_PC`. In this case, any single trade will only ever
lose 1.5% of the account. 

We also define the `INTERVAL: '1h'` key, meaning that our strategy will run the 1-hour timeframe. This value is used when 
retrieving price data through [AutoData](autodata-docs), so make sure it matches the format required by your data feed. This
is discussed more in the next section.


### Building the Strategy Module

```{admonition} Follow Along
Follow along in the demo repository: 
strategies/<a href="https://github.com/kieran-mackle/autotrader-demo/blob/main/strategies/macd.py" target="_blank">macd.py</a>
```


Now we can write the [strategy class](trading-strategy) `SimpleMACD` in a module called `macd.py`
 (hence `MODULE: 'macd'` and `CLASS: 'SimpleMACD'` in our strategy configuration).
Although strategy construction is extremely flexible, the class must contain at a minimum an `__init__` method, and a 
method named `generate_signal`. The first of these methods is called whenever the strategy is instantiated. By default,
strategies in AutoTrader are instantiated with three things:

1. The strategy parameters (`PARAMETERS`)
2. The trading instruments data
3. The name of the instrument being traded in this specific instance.

By providing the data to the strategy upfront, strategies have a warm-up period before running, calculating all indicators 
when instantiated. The name of the instrument being traded is also passed in to allow for more complex, 
<a href="https://github.com/kieran-mackle/autotrader-demo/blob/main/strategies/portfolio_rebalance.py" target="_blank">portfolio-based</a>
trading systems - or any strategy where you need to know the specific instrument being traded in the logic. 

```{caution}
Be careful when defining indicators not to use methods which can lead to look-ahead. For example, backwards-filling values. 
```

We will start by filling out the 
<a href="https://github.com/kieran-mackle/autotrader-demo/blob/main/strategies/template.py" target="_blank">template strategy module</a>
shown below, and finish with the strategy configuration file.

```py
# Import packages

class SimpleMACD:
    def __init__(self, params, data, instrument):
        ''' Initialise the strategy here '''
        ...

    def generate_signal(self, i, current_position):
        ''' Define the trading strategy to determine entry signals '''
        ...
        return signal_dict
    
    def generate_exit_levels(self, signal, i):
        ''' Function to determine stop loss and take profit levels '''
        ...
        return exit_dict
```



#### Instantiation

For the MACD crossover strategy, instantiation will look as shown below. Note the following:
- the <a href="https://github.com/peerchemist/finta" target="_blank">finta</a> technical analysis package is used to calculate the 200-period EMA and the MACD
- the custom indicator `crossover` is used from the [built-in indicators](../indicators)
- an `indicators` dict is defined to tell [AutoPlot](../core/AutoPlot) which indicators to plot, and what to title them
- the custom indicator `find_swings` is used to detect swings in the price, which will be used in the exit strategy

```python
# Import packages
from finta import TA
import autotrader.indicators as indicators
from autotrader.brokers.trading import Order

class SimpleMACD:

    def __init__(self, params, data, pair):
        """Define all indicators used in the strategy.
        """
        self.name   = "Simple MACD Trend Strategy"
        self.data   = data
        self.params = params
        
        # 200EMA
        self.ema = TA.EMA(data, params['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, self.params['MACD_fast'], 
                            self.params['MACD_slow'], self.params['MACD_smoothing'])
        self.MACD_CO = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
        self.MACD_CO_vals = indicators.cross_values(self.MACD.MACD, 
                                                      self.MACD.SIGNAL,
                                                      self.MACD_CO)
        # Construct indicators dict for plotting
        self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                              'macd': self.MACD.MACD,
                                              'signal': self.MACD.SIGNAL},
                           'EMA (200)': {'type': 'MA',
                                         'data': self.ema}}
        
        # Price swings
        self.swings = indicators.find_swings(data)
```

Now with the inidicators calculated, we have everything we need to define the logic of the strategy.













#### Strategy Signals

The next step is to define the signal generation function, `generate_signal`. Make sure to use this name for all your strategies, as
AutoTrader will call it when you run it. This method is where the logic of the strategy sits. The inputs to this function are `i`, 
an indexing variable, and `current_positions`, a dictionary containing current positions held. We will not need the `current_positions`
dictionary in this strategy, but it is useful in others (such as [portfolio rebalancing](https://github.com/kieran-mackle/autotrader-demo/blob/main/strategies/portfolio_rebalance.py)).

Since price data and all of your indicators are pre-loaded when your strategy is instantiated, the indexing
variable `i` is required to generate a signal at the correct timestamp. When backtesting with AutoTrader, the value 
of `i` will vary from `0` to `len(data)`, as AutoTrader steps through each bar in your data. If you are running
AutoTrader in live-trade mode, `i` will simply index the last candle in the data, corresponding to the most recent 
market conditions. Read more about the indexing system [here](autotrader-data-indexing).

The output of this function is a dictionary, `signal_dict`, containing the details of your signal/order. AutoTrader's virtual 
broker supports multiple [order types](order-handling), multiple 
[stop loss types](broker-stop-loss-types) and anything else you might encounter with a real broker. 
For this strategy, we will only be placing market orders when we get the entry signal. A long trade is triggered by setting 
the 'direction' key of the `signal_dict` to `1`, and a short trade is triggered by setting the it to `-1`. If there is no signal, 
set this key to `0`, and nothing will happen. We also define our exit targets by the `stop_loss` and `take_profit` keys of 
`signal_dict`. These price targets come from our exit strategy, defined in the next section. 


```{attention}
AutoTrader v`0.6.0` introduced the `Order`, `Trade` and `Position` objects. Orders can now be created from 
strategies (as in the example below), rather than through dictionaries as was previously the case. Legacy
functionality is still supported, so you don't need to modify existing strategies using `signal_dict`'s.
```


TODO - show the change in code using code tabs



```python
    def generate_signal(self, i, current_position):
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



#### Exit Signals
As with any good strategy, we must define an exit strategy to manage risk. In this strategy, stop losses are set at recent swings 
in price. Since this is a trend following strategy, market structure tells us that price is unlikely to break past a recent swing 
level, unless of course the trend is reversing. The `find_swings` indicator built into AutoTrader's 
[indicator library](swing-detection) makes this an easy task. Finally, take profits are set at 1:1.5
risk-to-reward (as defined by the `RR` key in our strategy parameters). This is all completed with the code below.

```py
    def generate_exit_levels(self, signal, i):
        """Function to determine stop loss and take profit levels.
        """
        stop_type = 'limit'
        RR = self.params['RR']
        
        if signal == 0:
            stop = None
            take = None
        else:
            if signal == 1:
                stop = self.swings.Lows[i]
                take = self.data.Close[i] + RR*(self.data.Close[i] - stop)
            else:
                stop = self.swings.Highs[i]
                take = self.data.Close[i] - RR*(stop - self.data.Close[i])
                
        
        exit_dict = {'stop_loss': stop, 
                     'stop_type': stop_type,
                     'take_profit': take}
        
        return exit_dict
```


## Onwards and Upwards
That's it! You now have your very own algorithmic trading strategy ready to unleash on the world. In the next 
few pages, you will learn how to backtest, optimise and deploy your strategies. But first, a quick lesson on 
getting data.


