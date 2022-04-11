# Condensed AutoTrader Walkthrough
This page is a condensed version of the [detailed walkthrough](walkthrough), which goes through the
process of building and running a strategy in AutoTrader. If you are familiar with Python, it should 
be sufficient to get you up and running.

```{tip}
The code for the MACD crossover strategy shown in this tutorial can be found in the
<a href="https://github.com/kieran-mackle/autotrader-demo" target="_blank">demo repository</a>.
```

## Strategy Rules
The rules for the MACD crossover strategy are as follows.

1. Trade in the direction of the trend, as determined by the 200EMA.
2. Enter a long position when the MACD line crosses *up* over the signal line, and enter a short 
when the MACD line crosses *down* below the signal line.
3. To ensure only the strongest MACD signals, the crossover must occur below the histogram zero line for 
long positions, and above the histogram zero line for short positions.
3. Stop losses are set at recent price swings/significant price levels.
4. Take profit levels are set at 1:1.5 risk-to-reward.

An example of a long entry signal from this strategy is shown in the image below (generated using 
[AutoTrader IndiView](../features/visualisation)).

![MACD crossover strategy](../assets/images/long_macd_signal.png "Long trade example for the MACD Crossover Strategy")





## Strategy Construction
A strategy in AutoTrader is defined by a class. The `__init__` and `generate_signal` methods are the only
required methods, and must accept the following inputs.


### Configuration
```{admonition} Follow Along
Follow along in the demo repository: 
config/[macd.yaml](https://github.com/kieran-mackle/autotrader-demo/blob/main/config/macd.yaml)
```

The [strategy configuration](strategy-config) file defines all strategy parameters and instruments 
to trade with the strategy. The `PARAMETERS` of this file will be passed into your strategy for you 
to use there. 

```yaml
NAME: 'Simple Macd Strategy'    # strategy name
MODULE: 'macd'                  # strategy module
CLASS: 'SimpleMACD'             # strategy class
INTERVAL: '1h'                  # stategy timeframe
PERIOD: 300                     # candles required by strategy
SIZING: 'risk'                  # sizing method
RISK_PC: 1.5                    # risk per trade (%)
PARAMETERS:                     # strategy parameters
  ema_period: 200
  MACD_fast: 12
  MACD_slow: 26
  MACD_smoothing: 9
  
  # Exit level parameters
  RR: 1.5

WATCHLIST: ['EURUSD=X']         # strategy watchlist
```

```{note}
As of AutoTrader version `0.6.0`, you can now directly pass your strategy configuration to AutoTrader as a dictionary.
```


### Code
Although strategy construction is extremely flexible, the class must contain at a minimum an `__init__` method, and a 
method named `generate_signal`. The first of these methods is called whenever the strategy is instantiated. By default,
strategies in AutoTrader are instantiated with three named arguments:

1. The strategy parameters (`parameters`)
2. The trading instruments data (`data`)
3. The name of the instrument being traded in this specific instance (`instrument`).

The signal generation function, `generate_signal`, is where the logic of the strategy sits. The inputs to this function 
are `i`, an indexing variable which is used when iterating over the data. When livetrading, `i` will simply index the
last candle in the data, corresponding to the most recent market conditions. Read more about the indexing system for 
periodic update mode [here](autotrader-run-modes).


```py
# Import packages
from finta import TA
from autotrader import indicators 
from autotrader import Order

class SimpleMACD:

    def __init__(self, parameters, data, instrument):
        """Define all indicators used in the strategy.
        """
        self.name   = "Simple MACD Trend Strategy"
        self.data   = data
        self.parameters = parameters
        
        # 200EMA
        self.ema = TA.EMA(data, parameters['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, self.parameters['MACD_fast'], 
                            self.parameters['MACD_slow'], self.parameters['MACD_smoothing'])
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
    
    
    def generate_exit_levels(self, signal, i):
        """Function to determine stop loss and take profit levels.
        """
        stop_type = 'limit'
        RR = self.parameters['RR']
        
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




## Backtesting
To run a backtest in AutoTrader, begin by importing AutoTrader and creating 
an instance using `at = AutoTrader()`. Next, use the [`configure`](autotrader-configure) method to set 
the verbosity of the code and tell AutoTrader that you would like to see the plot. Next, we add our 
strategy using the `add_strategy` method. Then, we use the [`backtest`](autotrader-backtest-config) 
method to define your backtest settings. Finally, we run AutoTrader with the command `at.run()`, and 
that's it! 


```python
from autotrader import AutoTrader

at = AutoTrader()                           # Create a new instance of AutoTrader
at.configure(show_plot=True, verbosity=1)   # Configure the instance
at.add_strategy('macd')                     # Add the strategy by its configuration file prefix
at.backtest(start = '1/1/2021',             # Define the backtest settings
            end = '1/1/2022',
            initial_balance=1000,
            leverage = 30)
at.run()                                    # Run AutoTrader!
```


### Backtest Results
With a verbosity of 1, you will see an output similar to that shown below. As you can see, there is a detailed breakdown of 
trades taken during the backtest period. Since we told AutoTrader to plot the results, you will also see the interactive chart
shown below.

```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURUSD=X with virtual broker using MACD Trend Strategy.

Trading...

Backtest complete (runtime 4.642 s).

----------------------------------------------
               Backtest Results
----------------------------------------------
Start date:              Jan 20 2021 05:00:00
End date:                Dec 31 2021 13:00:00
Starting balance:        $1000.0
Ending balance:          $1255.11
Ending NAV:              $1270.05
Total return:            $255.11 (25.5%)
Total no. trades:        96
Total fees:              $0.0
Backtest win rate:       46.9%
Maximum drawdown:        -18.1%
Max win:                 $40.5
Average win:             $26.53
Max loss:                -$43.81
Average loss:            -$18.41
Longest win streak:      6 trades
Longest losing streak:   6 trades
Average trade duration:  1 day, 2:37:30
Orders still open:       1
Cancelled orders:        3

            Summary of long trades
----------------------------------------------
Number of long trades:   40
Long win rate:           50.0%
Max win:                 $40.5
Average win:             $26.99
Max loss:                -$21.91
Average loss:            -$17.96

             Summary of short trades
----------------------------------------------
Number of short trades:  59
short win rate:          42.4%
Max win:                 $35.06
Average win:             $26.17
Max loss:                -$43.81
Average loss:            -$18.65
```


<iframe data-src="../_static/charts/macd_backtest_demo.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/macd_backtest_demo.html"></iframe>




## Parameter Optimisation
We will modify our runfile to optimise the `MACD_fast` and `MACD_slow` parameters of our MACD strategy by using
the [`optimise`](autotrader-optimise-config) method of AutoTrader. This method requires two inputs: 
- `opt_params`: the names of the parameters we wish to optimise, as they appear in the `PARAMETERS` section of our 
strategy configuration.
- `bounds`: the upper and lower bounds on the optimisation parameters, specified as tuples.

Before we run the optimiser, lets download the price data used in our backtest, so that we do not have to download it 
for each iteration of the optimisation. This can be acheived with the code snippet below. 

```python
bot = at.get_bots_deployed()
bot.data.to_csv('price_data/EUdata.csv')
```

Now we can use this data in our optimiser by providing it via the [`add_data`](autotrader-add-data) method, as shown below.

```python
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(show_plot=True, verbosity=1)
at.add_strategy('macd')
at.backtest(start = '1/1/2020',
            end = '1/1/2021',
            initial_balance=1000,
            leverage = 30)
at.add_data(data_dict={'EURUSD=X': 'EUdata.csv'})
at.optimise(opt_params=['MACD_fast', 'MACD_slow'],
            bounds=[(5, 20), (20, 40)])
at.run()
```

The objective of the optimiser is to maximise profit. 


### Optimisation Results
Running the file above will result in the following output. After a few minutes on a mid-range laptop, the 
parameters of our MACD strategy have been optimised to maximise profit over the one-year backtest period. As you can 
see from the output, the optimal parameter values for the strategy configuration parameters specified are approximately 
10 and 33. This means that the fast MACD period should be 10, and the slow MACD period should be 33.

```
Parameters/objective: [ 5. 20.] / -966.904
                    .
                    .
                    .
Parameters/objective: [ 9.79685545 33.30738306] / -1246.284

Optimisation complete.
Time to run: 555.793s
Optimal parameters:
[ 9.796875   33.30729167]
Objective:
-1246.2841641533123
```


### Comparison to Baseline Strategy
Now let's compare the performance of the strategy before and after optimisation. Simply run the backtest again with 
the optimised parameters (you will need to update the strategy configuration file) and observe the results shown below. 

```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURUSD=X with virtual broker using MACD Trend Strategy.

Trading...

Backtest complete (runtime 2.884 s).

----------------------------------------------
               Backtest Results
----------------------------------------------
Start date:              Jan 20 2021 05:00:00
End date:                Dec 31 2021 13:00:00
Starting balance:        $1000.0
Ending balance:          $1261.72
Ending NAV:              $1276.52
Total return:            $261.72 (26.2%)
Total no. trades:        92
Total fees:              $0.0
Backtest win rate:       46.7%
Maximum drawdown:        -13.53%
Max win:                 $37.47
Average win:             $25.65
Max loss:                -$22.3
Average loss:            -$17.16
Longest win streak:      4 trades
Longest losing streak:   6 trades
Average trade duration:  1 day, 0:52:49
Orders still open:       1
Cancelled orders:        1

            Summary of long trades
----------------------------------------------
Number of long trades:   37
Long win rate:           43.2%
Max win:                 $37.47
Average win:             $26.37
Max loss:                -$22.27
Average loss:            -$17.11

             Summary of short trades
----------------------------------------------
Number of short trades:  58
short win rate:          46.6%
Max win:                 $32.44
Average win:             $25.22
Max loss:                -$22.3
Average loss:            -$17.2
```

Let's take a look at the profit [before](backtesting) and after:
>
>Profit before optimisation:
>$255.11 (25.5%)
>
>Profit after optimisation:
>$261.72 (26.2%)



## Going Live

Live trading is the [default trading medium](autotrader-mediums) of AutoTrader. As such, you are only 
required to specify the strategy configuration file along with any run [configuration](autotrader-config-methods) 
parameters to take a strategy live. 


```python
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(broker='oanda', feed='oanda')
at.add_strategy('macd')
at.run()
```

Using the [`configure`](autotrader-configure) method, we specify the broker and feed as `oanda`, indicating we will 
be trading with the Oanda API. This will automatically assign the Oanda API module as the broker, and use Oanda to 
retrieve price data. This is a very minimal run file, however there are more options available in the `configure` 
method. For example, we can specify the level of email verbosity via the `notify` input, so that you get an email 
for specific trading activity. Read more about the configuration method [here](autotrader-configure). 


### Automated Running
Putting a strategy live will vary depending on if you are running AutoTrader in periodic or continuous mode.
In this tutorial, we developed the strategy to run in periodic mode, which was the original mode of AutoTrader.
Read about these modes [here](autotrader-run-modes).

#### Periodic Mode
When running in periodic mode, you need a way to automatically run AutoTrader at whatever interval your strategy 
demands (as per the `INTERVAL` key of your strategy configuration). In theory, if you are running a strategy 
on the daily timeframe, you could manually run AutoTrader at a certain time each day, such as when the daily 
candle closes. To automate this, you will need some sort of job scheduler or automated run file.

If you are running on Linux, [cron](https://en.wikipedia.org/wiki/Cron) is a suitable option. Simply schedule 
the running of your run file at an appropriate interval, as dictated by your strategy. Alternatively, you could 
write the runfile above into a `while True:` loop to periodically run your strategy, using `time.sleep()` to 
pause between the periodic updates.


#### Continuous Mode
Going live in continous mode is tremendously effortless. Specify how frequently you would like AutoTrader to 
refresh the data feed using the `update_interval` in the [`configure`](autotrader-configure) method, and 
run the file. Thats it! When you do this, you'll notice that AutoTrader will create an `active_bots/` directory,
and create an empty file each time you run an instance of AutoTrader live in continuous. To kill the trading 
bots associated with that instance, simply delete this file, and AutoTrader will stop running.

If you are running on a server, you might want to use [`nohup`](https://www.maketecheasier.com/nohup-and-uses/)
(short for 'no hangup') to prevent your system from stopping Python when you log out.
