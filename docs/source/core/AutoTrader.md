(autotrader-docs)=
# AutoTrader

AutoTrader is the main module you will interact with. It is a class object, so you begin by creating an 
instance of AutoTrader. You can then configure the settings, add a strategy, add data, and finally, run it to 
begin trading.


(autotrader-mediums)=
## Trading Mediums
Although the strategies and trading bots are not aware of it, AutoTrader has three trading mediums:
1. Livetrading: real-time trading (paper and real)
2. Backtesting: virtual trading on historical data
3. Scanning: real-time monitoring of market conditions with alerts (no order submission)

With minimal configuration, AutoTrader will run livetrading. To run a backtest, the [`backtest`](autotrader-backtest-config) 
method must be called to set the backtest parameters. Likewise, to run AutoTrader as a market scanner, the 
[`scan`](autotrader-scan-config) method must be called.




(autotrader-run-modes)=
## Run Modes
AutoTrader has two run modes, which control how data is handled and how frequently strategies are instantiated. The 
active run mode is controlled using [`configure`](autotrader-configure) method. A summary of these modes is provided 
in the table below, but the following sections discuss them in more detail.


|           | Periodic Mode | Continuous Mode |
| --------- | ------------- | --------------- |
| Strategy instantiation | Every update | Once during deployment |
| Data indexing | Index based | Time based |
| Lookahead risk | High | Low |
| Backtest time | Very fast | Slow |

```{important}
The input arguments to your strategy's `generate_signal` method change slightly depending on the run mode you are using. 
Check out the [boilerplate code](generate-signal-boilerplate) to see these differences.
```


(autotrader-periodic-mode)=
### Periodic Update Mode
In periodic update mode, an integer index `i` is used to iterate through the data set to provide trading signals at different
points in time. When backtesting, this index will vary from `0` to `len(data)`. Upon each iteration, the method 
`generate_signal` from the strategy module is called to obtain a signal corresponding to the current timestep. When livetrading 
or scanning, this index will be `-1`, corresponding to the most recent data, as required for livetrading. This is adequate for
most strategies, but carries the risk of accidental data leakage when backtesting, since the strategy is instantiated with 
the entire dataset. 

After the trading bots are updated with the latest data in periodic update mode, they will self-terminate and the AutoTrader 
instance will become inactive. For this reason, AutoTrader must be run periodically to repeatedly deploy trading bots and act 
on the latest signal - hence the name 'periodic update mode'. For example, a strategy running on the 4-hour timeframe, AutoTrader 
should be scheduled to run every 4 hours. Each time it runs, the trading bots will be provided with data of the latest 4-hour 
candles to run the strategy on.This task is easily automated using [cron](https://en.wikipedia.org/wiki/Cron), or even in a 
`while True` loop. A single bot update in this mode is illustrated in the chart below.


```{image} ../assets/images/light-periodic-update-run.svg
:align: center
:class: only-light
```

```{image} ../assets/images/dark-periodic-update-run.svg
:align: center
:class: only-dark
```

Noting this should bring to attention a point of difference between backtesting and livetrading using periodic update mode: 
strategies are instantiated once in backtests, but multiple times when livetrading. For some strategies this does not matter,
but for others where you would like to maintain the strategies attributes it does. In such cases, continuous update mode may 
be better suited. 



(autotrader-continuous-mode)=
### Continuous Update Mode

In continuous update mode, a time marching algorithm is used in place of the integer indexing method used in periodic update 
mode. That is, time is slowly incremented forwards, and data is slowly revealed to the trading bots. More importantly, there 
is practically no difference between backtesting and livetrading from the perspective of the trading bots; strategies are 
instantiated once in both mediums. This means that strategies will maintain attributes from the time it is deployed until the 
time it is terminated. Data is automatically checked for lookahead bias in this mode, ensuring that the strategy will not
see any future data. This comes at the cost of extra processing, meaning that backtesting in this mode is significantly slower.

The charts below illustrate this mode.

```{image} ../assets/images/light-detached-bot.svg
:align: center
:class: only-light
```

```{image} ../assets/images/dark-detached-bot.svg
:align: center
:class: only-dark
```

(autotrader-instance-file)=
#### Livetrading Bot Management
When bots are deployed for livetrading in continuous mode, a directory named 'active_bots' will be created in the working 
directory. In this directory, an 'instance file' will be created for each active instance of AutoTrader. The contents of 
the instance file includes the trading bots deployed in that instance, and the instruments they are trading. This provides
a reference as to which AutoTrader instance contains which trading bots. To kill an active instance of AutoTrader, simply
delete (or rename) the instance file. This will safely terminate the active bots, and proceed with the 
[shutdown routines](strategy-shutdown-routine).

```{seealso}
The name of the instance file can be customised using the `instance_str` argument of the 
[configure](autotrader-configure) method.
```







(autotrader-config-methods)=
## Configuration Methods
The following methods are used to configure the active instance of AutoTrader.


(autotrader-configure)=
### Run Configuration

To configure the run settings of AutoTrader, the `configure` method should be used. This is mostly optional,
and if not used, AutoTrader will run with the defualt settings. If you are livetrading, however, you will need to
set the feed to match your broker and provide your trading account number. Additionally, if you are going to provide
local data file(s), you should always call the `configure` method prior to specifying the local data via the 
`add_data` [method](autotrader-add-data), to ensure that file paths are correctly configured. 

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.configure
```

(autotrader-backtest-config)=
### Backtest Configuration

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.backtest
```

(autotrader-virtual-livetrade-config)=
### Virtual Livetrade Configuration

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.virtual_livetrade_config
```


(autotrader-optimise-config)=
### Optimisation Configuration
The optimisation capability of AutoTrader is a sub-function of the backtest mode, since a backtest must be run each iteration
of the optimisation. To configure the optimisation settings, use the `optimise` method.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.optimise
```

```py
optimise(opt_params, bounds, Ns=4)
```


(autotrader-scan-config)=
### Scan Configuration


```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.scan
```



### Configure AutoPlot Settings

[AutoPlot](autoplot-docs)

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.plot_settings
```




## Other Methods

(autotrader-add-strategy)=
### Add New Strategy
Trading strategies can be added using the `add_strategy` method of AutoTrader. This method can be used multiple times
to add multiple strategies to the same run. Note that this method accepts both `strategy_filename` and `strategy_dict`. 
The first of these is used to provide the prefix of a [strategy configuration](strategy-config) file, while
the second can be used to directly pass in a strategy configuration dictionary.


```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.add_strategy
```


(autotrader-add-data)=
### Add Data
To backtest a strategy using locally stored price data, the `add_data` method should be used to tell AutoTrader where the data
is. Note that the `configure` [method](autotrader-configure) should be called before calling `add_data`, as it will set the 
`home_dir` parameter for your project. This method can be used to provide data for both single-timeframe strategies and 
multiplie-timeframe strategies.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.add_data
```





(autotrader-bots-deployed)=
### Get Bots Deployed

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.get_bots_deployed
```


(autotrader-plot-backtest)=
### Plot Backtest

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.plot_backtest
```



### Print Backtest Results

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.print_backtest_results
```


## Run AutoTrader
```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.run
```





## Example Runfiles
Shown below are example scripts for running AutoTrader. 

```{seealso}
More examples can be found in the [demo repository](https://github.com/kieran-mackle/autotrader-demo).
```

````{tab} Backtest Mode
```
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(feed = 'oanda', broker='oanda', verbosity = 1,
             home_dir = '/home/ubuntu/trading/')
at.add_strategy('macd_crossover')
at.backtest(start = '1/1/2015',
            end = '1/3/2022',
            initial_balance=1000,
            leverage=30)
at.run()
```
````
````{tab} Livetrade Mode
```
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(feed = 'oanda', broker='oanda', verbosity = 1,
             home_dir = '/home/ubuntu/trading/')
at.add_strategy('macd_crossover')
at.run()
```
````