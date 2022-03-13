# Building a Strategy


The next few pages will provide a detailed walkthrough building and running a strategy with AutoTrader. 

*Note: the code for the MACD crossover strategy shown in this tutorial can be found in the*
*[demo repository](https://github.com/kieran-mackle/autotrader-demo).*


## Directory Organisation
Before building a strategy in AutoTrader, it is important to understand the structure of a project. At a minimum, any 
strategy you run in AutoTrader requires two things: 
1. A strategy module, containing all the logic of your strategy, and
2. A configuration file, containing strategy configuration parameters.

If you plan to take your strategy [live](going-live), you will also need a [global configuration](global-config) 
file to connect to your broker, but we will get to that later. For now, the files above are enough to get started backtesting, so
this tutorial will go over setting them up.

Back to your directory structure: you must have a `config/` directory - containing your configuration files - and a 
`strategies/` directory - containing (you guessed it) your [trading strategies](../userfiles/strategy). When you 
run AutoTrader, it will look for the appropriate files under these directories. If you cloned the demo repository, you will
see these directories set up already. Think of this directory structure as your 'bag' of algo-trading bots. 

```
your_trading_project/
  |- run_script.py                      # Run script to deploy trading bots
  |- config/
  |    |- GLOBAL.yaml                   # Global configuration file
  |    |- your_strategy1_config.yaml    # Strategy-specific configuration file
  |    |- your_strategy2_config.yaml    # Strategy-specific configuration file
  |- strategies/
  |    |- your_strategy1.py             # Strategy 1 module, containing strategy logic
  |    |- your_strategy2.py             # Strategy 1 module, containing strategy logic
```


## Strategy Construction
*Follow along in the [demo repository](https://github.com/kieran-mackle/autotrader-demo/blob/main/strategies/macd.py): strategies/macd.py*

Now we can get onto building the strategy - the simple yet effective MACD crossover. An important note here is that this strategy assumes
that the underlying asset is a *contract for difference*, and hence, can be shorted. 

### MACD Strategy Rules
The rules for this strategy are as follows.

1. Trade in the direction of the trend, as determined by the 200EMA.
2. Enter a long position when the MACD line crosses *up* over the signal line, and enter a short when the MACD line crosses *down* below 
the signal line.
3. To ensure only the strongest MACD signals, the crossover must occur below the histogram zero line for long positions, and above the histogram 
zero line for short positions.
3. Stop losses are set at recent price swings/significant price levels.
4. Take profit levels are set at 1:1.5 risk-to-reward.

An example of a long entry signal from this strategy is shown in the image below (generated using 
[AutoTrader IndiView](../features/0.3-visualisation)).

![MACD crossover strategy](../assets/images/long_macd_signal.png "Long trade example for the MACD Crossover Strategy")


### Building the Strategy Module
Strategies in AutoTrader are built as classes, instantiated with parameters from the configuration file, price data and 
the name of the instrument being traded - but don't worry, this is all taken care of behind the scenes. The `params` dict is 
read in from the strategy configuration file and contains all strategy-specific parameters. By providing the data to the 
strategy upfront, strategies have a warm-up period before running, calculating all indicators when instantiated. The name of 
the instrument being traded is also passed in to allow for more complex, portfolio-based trading systems. More on this later.

Although strategy construction is extremely flexible, the class must contain the `__init__` function and a method named 
`generate_signal`, as shown below. Often, it is also convenient to define an exit strategy. In the example below, this is 
contained within the `generate_exit_levels` method. The details of these methods follow.

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

We will start by filling the skeleton of the strategy module above, and finish with the strategy configuration file.


#### Instantiation

The only 'rule' about strategy instantiation is the number of inputs which `__init__` accepts.
In *[most cases](strategy-init)*, this method must accept the following three inputs:
  1. `params`: a dictionary containing the strategy parameters from your strategy configuration file
  2. `data`: a dataframe of the instrument's price data 
  3. `instrument`: a string object with the instruments name

Of course, you do not *need* to do anything with these inputs, but AutoTrader will always try instantiate your strategy with them.
Nonetheless, it is usually convenient to calculate all indicators used in the strategy when it is instantiated. For the MACD 
crossover strategy, this will look as shown below. Note the following:
- the `finta` technical analysis package is used to calculate the 200 EMA and the MACD
- the custom indicator `crossover` is used from the [built-in indicators](../indicators)
- the fast, slow and smoothing periods of the MACD are defined in the `params` dictionary by the names of 'MACD_fast', 'MACD_slow' and 'MACD_smoothing`. These parameters come straight from our configuration file (defined below).
- an `indicators` dict is defined to tell [AutoPlot](../core/AutoPlot) which indicators to plot, and what to call them.
- the custom indicator `find_swings` is used to detect swings in the price, which will be used in the exit strategy.

```python
# Import packages
from finta import TA
from autotrader.lib import indicators

class SimpleMACD:

    def __init__(self, params, data, pair):
        ''' Define all indicators used in the strategy '''
        self.name   = "Simple MACD Trend Strategy"
        self.data   = data
        self.params = params
        
        # 200EMA
        self.ema    = TA.EMA(data, params['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, self.params['MACD_fast'], 
                            self.params['MACD_slow'], self.params['MACD_smoothing'])
        self.MACD_CO        = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
        self.MACD_CO_vals   = indicators.cross_values(self.MACD.MACD, 
                                                      self.MACD.SIGNAL,
                                                      self.MACD_CO)
        # Construct indicators dict for plotting
        self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                              'macd': self.MACD.MACD,
                                              'signal': self.MACD.SIGNAL},
                           'EMA (200)': {'type': 'MA',
                                         'data': self.ema}}
        
        # Price swings
        self.swings     = indicators.find_swings(data)
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

```python
    def generate_signal(self, i, current_position):
        ''' Define strategy to determine entry signals '''
        
        order_type  = 'market'
        signal_dict = {}
        related_orders  = None
        
        if self.data.Close.values[i] > self.ema[i] and \    # Price is above 200 EMA
            self.MACD_CO[i] == 1 and \                      # MACD cross above signal line
            self.MACD_CO_vals[i] < 0:                       # MACD cross occured below zero
                # Long entry signal
                signal = 1
                
        elif self.data.Close.values[i] < self.ema[i] and \  # Price is below 200 EMA
            self.MACD_CO[i] == -1 and \                     # MACD cross below signal line
            self.MACD_CO_vals[i] > 0:                       # MACD cross occured above zero 
                # short entry signal
                signal = -1

        else:
            # No signal
            signal = 0
        
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




#### Exit Signals
As with any good strategy, we must define an exit strategy to manage risk. In this strategy, stop losses are set at recent swings 
in price. Since this is a trend following strategy, market structure tells us that price is unlikely to break past a recent swing 
level, unless of course the trend is reversing. The `find_swings` indicator built into AutoTrader's 
[indicator library](swing-detection) makes this an easy task. Finally, take profits are set at 1:1.5
risk-to-reward (as defined by the `RR` key in our strategy parameters). This is all completed with the code below.

```py
    def generate_exit_levels(self, signal, i):
        ''' Function to determine stop loss and take profit levels '''
        
        stop_type   = 'limit'
        RR          = self.params['RR']
        
        if signal == 0:
            stop    = None
            take    = None
        else:
            if signal == 1:
                stop    = self.swings.Lows[i]
                take    = self.data.Close[i] + RR*(self.data.Close[i] - stop)
            else:
                stop    = self.swings.Highs[i]
                take    = self.data.Close[i] - RR*(stop - self.data.Close[i])
                
        
        exit_dict   = {'stop_loss'    : stop, 
                       'stop_type'    : stop_type,
                       'take_profit'  : take}
        
        return exit_dict
```



### Strategy Configuration
*Follow along in the [demo repository](https://github.com/kieran-mackle/autotrader-demo/blob/main/config/macd.yaml): config/macd.yaml*

The next step is to write the [strategy configuration](strategy-config) yaml file. This file is a convenient place to
define your strategy parameters (using `PARAMETERS`) and which instruments to trade with using this strategy (using `WATCHLIST`). As
you can see below, the default MACD settings of 12/26/9 are used. The risk-to-reward ratio is also defined by the `RR` key. As mentioned
previously, this file is read by AutoTrader and passed into your strategy when it is instantiated. We will start by backtesting with the
EUR/USD currency pair. However, to make things interesting, AutoTrader supports multi-instrument (and multi-timeframe) backtesting. This
will be showcased later on.

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

It is worth noting that we are taking advantage of AutoTrader's automatic position size calculation, by defining the 
`SIZING: 'risk'` and `RISK_PC: 1.5` keys. These keys tell AutoTrader to use a risk-based approach to position sizing. As such,
when an order is submitted from the strategy, AutoTrader will use the current price and stop-loss price to calculate the appropriate
position size, capping the maximium loss to the percentage defined by `RISK_PC`. In this case, any single trade will only ever
lose 1.5% of the account. 

We also define the `INTERVAL: '1h'` key, signifying that our strategy will run the 1-hour timeframe. 

Read on to learn about getting price data to perform a backtest on.
