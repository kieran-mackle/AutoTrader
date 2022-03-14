# Condensed AutoTrader Walkthrough
This page is a condensed version of the [detailed walkthrough](walkthrough). If you are 
familiar with Python, it should be sufficient to get you up and running with AutoTrader.

```{tip}
The code for the MACD crossover strategy shown in this tutorial can be found in the
<a href="https://github.com/kieran-mackle/autotrader-demo" target="_blank">demo repository</a>.
```

## Strategy Rules
The rules for the MACD crossover strategy are as follows.

1. Trade in the direction of the trend, as determined by the 200EMA.
2. Enter a long position when the MACD line crosses *up* over the signal line, and enter a short when the MACD line crosses *down* below 
the signal line.
3. To ensure only the strongest MACD signals, the crossover must occur below the histogram zero line for long positions, and above the histogram 
zero line for short positions.
3. Stop losses are set at recent price swings/significant price levels.
4. Take profit levels are set at 1:1.5 risk-to-reward.

An example of a long entry signal from this strategy is shown in the image below (generated using 
[AutoTrader IndiView](../features/visualisation)).

![MACD crossover strategy](../assets/images/long_macd_signal.png "Long trade example for the MACD Crossover Strategy")


## Strategy Structure
A strategy in AutoTrader is defined by a class. The `__init__` and `generate_signal` methods are the only
required methods, and must accept the following inputs.

### Initialisation
In *[most cases](../docs/strategies#initialisation)*, the `__init__` method must accept the following three inputs:
  1. `params`: a dictionary containing the strategy parameters from your strategy configuration file
  2. `data`: a dataframe of the instrument's price data 
  3. `instrument`: a string object with the instruments name

### Signal Generation
The `generate_signal` method is where the logic of the strategy sits. The inputs to this function are `i`, 
an indexing variable, and `current_positions`, a dictionary containing current positions held.


## Code
The strategy class defining this strategy is shown below. 

```py
# Import packages
import talib
from autotrader.lib import indicators

class SimpleMACD:

    def __init__(self, params, data, pair):
        ''' Define all indicators used in the strategy '''
        self.name   = "Simple MACD Trend Strategy"
        self.data   = data
        self.params = params
        
        # 200EMA
        self.ema    = talib.EMA(data.Close.values, params['ema_period'])
        
        # MACD
        self.MACD, self.MACDsignal, self.MACDhist = talib.MACD(data['Close'].values, 
                                                  self.params['MACD_fast'], 
                                                  self.params['MACD_slow'], 
                                                  self.params['MACD_smoothing']
                                                  )
        self.MACD_CO        = indicators.crossover(self.MACD, self.MACDsignal)
        self.MACD_CO_vals   = indicators.cross_values(self.MACD, 
                                                      self.MACDsignal,
                                                      self.MACD_CO)
        # Construct indicators dict for plotting
        self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                              'macd': self.MACD,
                                              'signal': self.MACDsignal,
                                              'histogram': self.MACDhist},
                           'EMA (200)': {'type': 'MA',
                                         'data': self.ema}}
        
        # Price swings
        self.swings     = indicators.find_swings(data)
        
    def generate_signal(self, i, current_position):
        ''' Define strategy to determine entry signals '''
        
        order_type  = 'market'
        signal_dict = {}
        related_orders  = None
        
        if self.data.Close.values[i] > self.ema[i] and \
            self.MACD_CO[i] == 1 and \
            self.MACD_CO_vals[i] < 0:
                signal = 1
                
        elif self.data.Close.values[i] < self.ema[i] and \
            self.MACD_CO[i] == -1 and \
            self.MACD_CO_vals[i] > 0:
                signal = -1

        else:
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


## Strategy Configuration
```{admonition} Follow Along
Follow along in the demo repository: 
config/[macd.yaml](https://github.com/kieran-mackle/autotrader-demo/blob/main/config/macd.yaml)
```

The [strategy configuration](strategy-config) file defines all strategy parameters and instruments to trade with the strategy.

```yaml
NAME: 'Simple_macd_strategy'
MODULE: 'macd'
CLASS: 'SimpleMACD'
INTERVAL: '1h'
PERIOD: 300
RISK_PC: 1.5
SIZING: 'risk'
PARAMETERS:
  ema_period: 200
  MACD_fast: 12
  MACD_slow: 26
  MACD_smoothing: 9
  
  # Exit level parameters
  RR: 1.5

WATCHLIST: ['EURUSD=X']
```

## Backtesting
Backtesting in AutoTrader can be achieved with the python runfile below.

```python
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(show_plot = True)
at.add_strategy('macd')
at.backtest(start = '1/1/2020',
            end = '1/1/2021',
            initial_balance = 1000,
            leverage = 30)
at.run()
```


## Backtest Results
With a verbosity of 1, you will see an output similar to that shown below. As you can see, there is a detailed breakdown of 
trades taken during the backtest period. Since we told AutoTrader to plot the results, you will also see the interactive chart
shown [below](#interactive-chart).

## Performance Breakdown
```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
  From:  01/01/2020 00:00
  To:    01/01/2021 00:00
[*********************100%***********************]  1 of 1 completed
AutoTraderBot assigned to analyse EURUSD=X on 1h timeframe using Simple MACD Trend Strategy.

Trading...

Backtest complete.

-------------------------------------------
            Backtest Results
-------------------------------------------
Backtest win rate:       44.3%
Total no. trades:        82
Profit:                  $118.352 (11.8%)
Maximum drawdown:        -11.6%
Max win:                 $30.29
Average win:             $23.23
Max loss:                -$18.92
Average loss:            -$15.79
Longest win streak:      8 trades
Longest losing streak:   5 trades
Average trade duration   1 day, 9:22:47
Orders still open:       1
Cancelled orders:        2

         Summary of long trades
-------------------------------------------
Number of long trades:   42
Long win rate:           50.0%
Max win:                 $27.8
Average win:             $23.44
Max loss:                -$18.92
Average loss:            -$15.76

          Summary of short trades
-------------------------------------------
Number of short trades:  37
short win rate:          37.8%
Max win:                 $30.29
Average win:             $22.91
Max loss:                -$18.15
Average loss:            -$15.81
```


### Interactive Chart
The interactive chart will look something like the one shown below.

<iframe data-src="/AutoTrader/assets/charts/macd_backtest_demo.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="/AutoTrader/assets/charts/macd_backtest_demo.html"></iframe>


## Strategy Optimisation
Optimising a strategy is as easy as specifying which paramaters you would like to optimise, and what bounds to place on them.

```python
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.verbosity = 1
at.add_strategy('macd')
at.backtest(start = '1/1/2020',
            end = '1/1/2021',
            leverage = 30)
at.optimise(opt_params=['MACD_fast', 'MACD_slow'],
            bounds=[(5, 20), (20, 40)])
at.show_plot = True
at.run()
```

The objective of the optimiser is to maximise profit. 


## Optimisation Output
Running the commands above will result in the following output. From the output, the optimal parameter values for the strategy 
configuration parameters specified are approximately 5 and 19. This means that the fast MACD period should be 5, and the slow 
MACD period should be 19.

```

[*********************100%***********************]  1 of 1 completed
Parameters/objective: [ 5. 20.] / -437.4069911837578
                    .
                    .
                    .
Parameters/objective: [ 5.24997711 19.00006104] / -449.7053394317683

Optimisation complete.
Time to run: 108.632s
Optimal parameters:
[ 5.25 19.  ]
Objective:
-449.7053394317683
```

## Comparison to Baseline Strategy
Now let's compare the performance of the strategy before and after optimisation. Simply run the backtest again with 
the optimised parameters (you will need to update the strategy configuration file) and observe the results shown below. 

```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
  From:  01/01/2020 00:00
  To:    01/01/2021 00:00
[*********************100%***********************]  1 of 1 completed
AutoTraderBot assigned to analyse EURUSD=X on 1h timeframe using Simple 
MACD Trend Strategy.

Trading...

Backtest complete.

-------------------------------------------
            Backtest Results
-------------------------------------------
Backtest win rate:       47.8%
Total no. trades:        147
Profit:                  $449.705 (45.0%)
Maximum drawdown:        -11.4%
Max win:                 $34.55
Average win:             $25.6
Max loss:                -$28.66
Average loss:            -$17.1
Longest win streak:      6 trades
Longest losing streak:   6 trades
Average trade duration   22:34:24
Cancelled orders:        11

         Summary of long trades
-------------------------------------------
Number of long trades:   79
Long win rate:           57.0%
Max win:                 $34.55
Average win:             $26.46
Max loss:                -$28.66
Average loss:            -$17.78

          Summary of short trades
-------------------------------------------
Number of short trades:  57
short win rate:          35.1%
Max win:                 $30.89
Average win:             $23.66
Max loss:                -$23.14
Average loss:            -$16.47
```

Let's take a look at the profit before and after optimisation:
>
>Profit before optimisation:
>$118.352 (11.8%)
>
>Profit after optimisation:
>$449.705 (45.0%)
 

### Optimised Backtest Performance
<iframe data-src="../_static/charts/optimised_macd.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/optimised_macd.html"></iframe>







