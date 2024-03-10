(strategy-tut)=
# Building a Strategy
So you have an idea for a trading strategy. How do you code this up to 
use with AutoTrader? Read on to find out, where we code the MACD strategy
described [here](walkthrough).

```{tip}
The code for the MACD crossover strategy shown in this tutorial can be found in the
<a href="https://github.com/kieran-mackle/autotrader-demo" target="_blank">demo repository</a>.
```


## Strategy Construction
Strategies in AutoTrader are built as class objects. They contain the logic 
required to transform data into a trading signals. Generally speaking, a 
strategy class will be instantiated with the name of the instrument being 
traded and the strategy parameters, but you can customise what gets passed
in using the [strategy configuration](strategy-config).

(macd-strat-config)=
### Strategy Configuration
```{admonition} Follow Along
Follow along in the demo repository: 
<a href="https://github.com/kieran-mackle/autotrader-demo/blob/main/config/macd.yaml" target="_blank">config/macd.yaml</a>
```

Lets start by writing the [strategy configuration](strategy-config) `.yaml` file.
Call this `macd.yaml`, refering to our MACD strategy. 
This file is a convenient place to define your strategy parameters (using the 
`PARAMETERS` key) and which instruments to trade using this strategy (using the 
`WATCHLIST` key). It is also used to tell AutoTrader where to find your strategy -
the `MODULE` key defines the prefix of the file where your strategy is written, 
and the `CLASS` key defines the actual class name of your strategy. 
You can also define the strategy configuration using a dictionary instead of a 
yaml file, and pass that in when [adding your strategy](autotrader-add-strategy).

By separating the strategy parameters from the strategy iteself, you are able 
to easily tweak the strategy to your liking, or perform hyperparameter 
optimisation.

```{attention}
YAML cares about whitespace; each nested key must be indented by 
two spaces more than its parent.
```

We will put our [strategy parameters](walkthrough-strategy-parameters) under 
the `PARAMETERS` key. You can call these parameters whatever you want, and that 
is how they will appear in your strategy. As you can see below, we define the 
EMA period by the `ema_period` key, the MACD settings by the `MACD_fast`, 
`MACD_slow` and `MACD_smoothing` keys, and the risk-to-reward ratio is by 
the `RR` key. 


```yaml
# macd.yaml
NAME: 'Simple Macd Strategy'    # strategy name
MODULE: 'macd'                  # strategy module
CLASS: 'SimpleMACD'             # strategy class
INTERVAL: '1h'                  # stategy timeframe
PARAMETERS:                     # strategy parameters
  ema_period: 200
  MACD_fast: 12
  MACD_slow: 26
  MACD_smoothing: 9
  
  # Exit level parameters
  RR: 1.5

WATCHLIST: ['EURUSD=X']         # strategy watchlist
```

This file is read by AutoTrader and passed into your strategy when it is 
instantiated. We will start by backtesting on the EUR/USD currency pair 
alone, as specified by the `WATCHLIST` key. Note that the format
of the instruments provided here must match your data feed (in this case, 
Yahoo Finance, which denotes FX with '=X').

We also define the `INTERVAL: '1h'` key, meaning that our strategy will run 
on the 1-hour timeframe. This value is used when retrieving price data.
This is discussed more in the next section.

```{tip}
You can find a template strategy configuration file in the 
<a href="https://github.com/kieran-mackle/AutoTrader/blob/main/templates/strategy_config.yaml" target="_blank">Github repository</a>.
```

### Strategy Class

```{admonition} Follow Along
Follow along in the demo repository: 
strategies/<a href="https://github.com/kieran-mackle/autotrader-demo/blob/main/strategies/macd.py" target="_blank">macd.py</a>
```

Now we can write the [strategy class](trading-strategy) `SimpleMACD`, and
place it in a module (Python file) called `macd.py` (hence `MODULE: 'macd'` 
and `CLASS: 'SimpleMACD'` in our strategy configuration). Although strategy 
construction is extremely flexible, the class **must** contain an `__init__` 
method, and a method named `generate_signal`. The first of these methods is 
called whenever the strategy is instantiated.

By default, strategies in AutoTrader are instantiated with three named 
arguments:

1. The name of the instrument being traded in this specific instance (`instrument`).
2. The strategy parameters (`parameters`)
3. The trading instruments data (`data`)

When backtesting, the `data` provided is for the entire backtest period. This
is partly from older versions of AutoTrader, but it remains this way to allow
you to calculate all indicators for plotting purposes (as you will see below).
You shouldn't use this data in your strategy, however, since you risk introducing
look-ahead. 

#### Template Strategy
We will start by filling out the 
<a href="https://github.com/kieran-mackle/AutoTrader/blob/main/templates/strategy.py" target="_blank">template strategy</a>
shown below.

```py
from autotrader.brokers.trading import Order


class Strategy:
    def __init__(self, instrument, parameters, **kwargs):
        """Initialise the strategy."""
        self.name = "Template Strategy"
        self.instrument = instrument
        self.params = parameters

        # Construct indicators dict for plotting
        self.indicators = {
            "Indicator Name": {"type": "indicatortype", "data": "indicatordata"},
        }

    def generate_signal(self, data):
        """Define strategy logic to transform data into trading signals."""

        # Initialise empty order list
        orders = []

        # The data passed into this method is the most up-to-date data.

        # Example long market order:
        long_market_order = Order(direction=1)
        orders.append(long_market_order)

        # Example short limit order:
        short_limit = Order(direction=-1, order_type="limit", order_limit_price=1.0221)
        orders.append(short_limit)

        # Return any orders generated
        # If no orders are generated, return an empty list [], an empty dict {},
        # or a blank order Order().
        return orders
```



#### Instantiation

For the MACD crossover strategy, instantiation will look as shown below. 
Note the following:
- we save the instrument and strategy parameters to the class attributes
(using the `self` variable).
- the <a href="https://github.com/peerchemist/finta" target="_blank">finta</a> 
technical analysis package is used to calculate the 200-period EMA and the MACD.
This calculation happens in a method called `generate_features`, defined later.
- the custom indicator `crossover` is used from the 
[built-in indicators](../indicators).
- an `indicators` dictionary is defined to tell [AutoPlot](../core/AutoPlot) 
which indicators to plot, and what to name them.


```python
from finta import TA
from autotrader import Order, indicators


class SimpleMACD:
    """Simple MACD Strategy
    
    Rules
    ------
    1. Trade in direction of trend, as per 200EMA.
    2. Entry signal on MACD cross below/above zero line.
    3. Set stop loss at recent price swing.
    4. Target 1.5 take profit.
    """
    
    def __init__(self, parameters, data, instrument):
        """Define all indicators used in the strategy.
        """
        self.name = "Simple MACD Trend Strategy"
        self.params = parameters
        self.instrument = instrument
        
        # Initial feature generation (for plotting only)
        self.generate_features(data)

        # Construct indicators dict for plotting
        self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                              'macd': self.MACD.MACD,
                                              'signal': self.MACD.SIGNAL},
                           'EMA (200)': {'type': 'MA',
                                         'data': self.ema}
                        }
```



#### Strategy Signals

The next step is to define the signal generation function, `generate_signal`. 
Make sure to use this name for all your strategies, as AutoTrader will call 
it when you run it. This method is where the logic of the strategy sits. It 
gets passed some data using the `data` argument, which you can use to generate
any trading signals. This data will always be the most up-to-date data, so you
should only create trading signals for the latest information it provides. In 
most cases, this data will be 
[OHLC](https://www.investopedia.com/terms/o/ohlcchart.asp) data, in the form of
a [Pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).


```{important}
Strategies must contain a `generate_signal` method! AutoTrader calls this method
to get trading signals from your strategy.
```

For the MACD strategy, this method translates the 
[strategy rule](walthrough-strat-rules) into code.


AutoTrader supports multiple [order types](order-types), multiple 
[stop loss types](broker-stop-loss-types) and anything else you might 
encounter with your live-trade broker. To create a new order, we can use the 
[`Order`](order-object) object, imported from the 
[`autotrader.trading`](../broker/trading) module. For this strategy, we will only 
be placing market orders when we get the entry signal, which are the default 
order type. 

A long order can be created by specifying `direction=1` when creating the 
`Order`, whereas a short order can be created by specifying `direction=-1`. 
If there is no trading signal this update, you can create an 
[empty order](empty-order) with just `Order()`. We also define our exit targets 
by the `stop_loss` and `take_profit` arguments. These price targets 
come from our exit strategy, defined in the next section. 


```python
def generate_features(self, data):
    """Updates MACD indicators and saves them to the class attributes."""
    # Save data for other functions
    self.data = data
    
    # 200EMA
    self.ema = TA.EMA(self.data, self.params['ema_period'])
    
    # MACD
    self.MACD = TA.MACD(self.data, self.params['MACD_fast'], 
                        self.params['MACD_slow'], self.params['MACD_smoothing'])
    self.MACD_CO = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
    self.MACD_CO_vals = indicators.cross_values(self.MACD.MACD, 
                                                self.MACD.SIGNAL,
                                                self.MACD_CO)
    
    # Price swings
    self.swings = indicators.find_swings(self.data)
    
    
def generate_signal(self, data):
    """Define strategy to determine entry signals."""
    # Feature calculation
    self.generate_features(data)
    
    # Look for entry signals (index -1 for the latest data)
    if self.data.Close.values[-1] > self.ema[-1] and \
        self.MACD_CO[-1] == 1 and \
        self.MACD_CO_vals[-1] < 0:
            # Long entry signal detected! Calculate SL and TP prices
            stop, take = self.generate_exit_levels(signal=1)
            new_order = Order(direction=1, stop_loss=stop, take_profit=take)
            
    elif self.data.Close.values[-1] < self.ema[-1] and \
        self.MACD_CO[-1] == -1 and \
        self.MACD_CO_vals[-1] > 0:
            # Short entry signal detected! Calculate SL and TP prices
            stop, take = self.generate_exit_levels(signal=-1)
            new_order = Order(direction=-1, stop_loss=stop, take_profit=take)

    else:
        # No trading signal, return a blank Order
        new_order = Order()
    
    return new_order
```


#### Exit Signals
As with any good strategy, we must define an exit strategy to manage our risk. 
In this strategy, stop losses are set at recent swings in price. Since this is a 
trend following strategy, market structure tells us that price is unlikely to 
break past a recent swing level, unless of course the trend is reversing. The 
`find_swings` indicator built into AutoTrader's 
[indicator library](swing-detection) makes this an easy task. As per our rules, 
take profits are set at 1:1.5 risk-to-reward ratio. This is all completed with 
the code below, which returns our target exit prices, used by our 
signal generation method in the section above.

```py
def generate_exit_levels(self, signal):
    """Function to determine stop loss and take profit prices."""
    RR = self.params['RR']
    if signal == 1:
        # Long signal
        stop = self.swings.Lows[-1]
        take = self.data.Close[-1] + RR*(self.data.Close[-1] - stop)
    else:
        # Short signal
        stop = self.swings.Highs[-1]
        take = self.data.Close[-1] - RR*(stop - self.data.Close[-1])
    return stop, take
```


## Time to Trade
You now have your very own algorithmic trading strategy ready to unleash 
on the world. In the next few pages, you will learn how to backtest, 
optimise and deploy your strategies. But first, a quick aside on data
management.

