(trading-strategy)=
# Trading Strategy

Trading strategies are built as class objects, and must follow a few simple guidelines to function properly with 
AutoTrader. At a minimum, a strategy is required to have two methods. The first is the `__init__` method, which
creates an active instance of the strategy. The second is the `generate_signal` method, which contains the 
strategy logic and ouputs any trading signals which may present themselves. Read more about these methods below 
and take a look at the sample strategies in the [demo repository](https://github.com/kieran-mackle/autotrader-demo).

Some other general guidelines are as follows:
- It is *recommended* that you keep your trading directory organised according to the suggested 
  [directory structure](rec-dir-struc). More specifically, that you have a 'strategies'
  directory, to keep your strategy modules. Note that as of AutoTrader `v0.6.0`, you can also directly pass your
  strategy classes to AutoTrader.
- If you wish to use [AutoPlot](autoplot-docs) to automatically generate charts for your strategy, you must include
  an `indicators` attribute in your strategy. This is explained further below.


```{important}
As of AutoTrader `v0.6.0`, there is a new run mode (continuous mode) which requires a different format to the strategy.
```

(strategy-template)=
## Strategy Template



(strategy-init)=
## Initialisation
The `__init__` method of a strategy initialises it with the following objects:
  1. `params`: a dictionary containing the strategy parameters from your strategy configuration file
  2. `data`: a dataframe of the instrument's price data 
  3. `instrument`: a string object with the instruments name

It is usually convenient to warm-start your strategy by pre-computing indicators and signals during the 
initialisation of the strategy.

```python
def __init__(self, params, data, pair):
    ''' Defines all indicators used in the strategy '''
    self.name   = "Strategy name"
    self.data   = data
    self.params = params

    # Calculate indicators here

    # Path variables
    strat_dir       = os.path.dirname(os.path.abspath(__file__))
    self.home_dir   = os.path.join(strat_dir, '..')
```

### Initialisation with access to the Broker
In some cases, you may like to directly connect with the broker from your strategy module. In this case, you would
include `INCLUDE_BROKER: True` in your [strategy configuration file](configuration-strategy). This will signal to 
AutoTrader to instantiate your strategy with the broker API and broker utilities. You will therefore need to include
these as inputs to your `__init__` method, as shown below. Now you can access the methods of the 
[broker API](brokers-interface) directly from your strategy!

```python
def __init__(self, params, data, pair, broker, broker_utilities):
    ''' Defines all indicators used in the strategy '''
    self.name   = "Strategy name"
    self.data   = data
    self.params = params
    self.broker = broker
    self.utils  = broker_utilities
```

(strategy-indicator-dict)=
### Indicators Dictionary
If you wish to visualise any of the results from your strategy, you must also include information about which
indicators you would like to plot. This information is stored in `self.indicators', a dictionary as defined 
below. This dictionary is passed to [AutoPlot](autoplot). 

```py
self.indicators = {'indicator name': {'type': 'indicator type',
                                      'data': self.indicator_data},
                   'indicator name': {'type': 'indicator type',
                                      'data': self.indicator_data},
		  ...
                  }

```

In this dictionary, the 'indicator name' is used to create a legend entry corresponding to the indicator. The sub-dictionary
assigned to each indicator contains the specific information and associated data. The `type` key should be a string corresponding
to the type of indicator, for example:
- `'type': 'MA'` for an exponential moving average (or any type of moving average)
- `'type': 'STOCH'` for stochastics
Finally, the data associated with the indicator must also be provided. For indicators with one set of data, such as a moving average,
simply provide the data with the `data` key. For indicators with multiple sets of data, such as MACD, provide a key for each set named
according to the [indicator specification](autoplot#indicator-specification).
See the example below for a strategy with MACD, two RSI's and two EMA's.

```py
self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                      'macd': self.MACD,
                                      'signal': self.MACDsignal,
                                      'histogram': self.MACDhist},
                   'EMA (200)': {'type': 'MA',
                                 'data': self.ema200},
                   'RSI (14)': {'type': 'RSI',
                                'data': self.rsi14},
                   'RSI (7)': {'type': 'RSI',
                               'data': self.rsi7},
                   'EMA (21)': {'type': 'MA',
                                'data': self.ema21}
                  }
```


(strategy-signal-gen)=
## Signal Generation
Signals are generated using the `generate_signal` method. This method contains the logic behind your strategy 
and returns a dictionary with details of the signal. The contents of the signal dictionary will largely depend 
on the order type, but at a minimum must contain the order type and trade direction. Read more about this
dictionary in the [*Broker API's* documentation](brokers-interface#order-handling).

Some boilerplate code for this method is provided below.

```python
def generate_signal(self, i, current_positions):
    ''' Define strategy to determine entry signals '''

    order_type  = 'market'
    signal_dict = {}

    # Put entry strategy here
    signal      = 0

    # Calculate exit targets
    exit_dict = self.generate_exit_levels(signal, i)

    # Construct signal dictionary
    signal_dict["order_type"]   = order_type
    signal_dict["direction"]    = signal
    signal_dict["stop_loss"]    = exit_dict["stop_loss"]
    signal_dict["stop_type"]    = exit_dict["stop_type"]
    signal_dict["take_profit"]  = exit_dict["take_profit"]

    return signal_dict
```

Note that a dict of the current positions held with the broker is passed into the `generate_signal` function.
This means that your strategy can take into account the positions you currently hold. The most obvious use of this
is when trading instruments which cannot be shorted. In this case, you would only place a sell order when you 
currently have an open position. 
You might also wan't to avoid entering a trade if it contradicts the position you currently hold.
Refer to the [AutoTrader docs](autotrader) for more information about this dict.


```{tip}
You can fire multiple orders at once from the `generate_signal` method! Simply return a list of the `Order`s 
you would like to place, and they will be submitted one by one!
```







## Order Types

*This section is currently in development. Please check back soon!*


AutoTrader is intelligent when it comes to order types. If your strategy has no stop loss, you do not need to include it in the 
signal dictionary. If you prefer to set a stop loss in terms of distance in pips, you can do that instead. Same goes for take 
profit levels, specify price or distance in pips. The choice is yours.


