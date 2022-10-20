(autotrader-docs)=
# AutoTrader
`from autotrader import AutoTrader`

The `AutoTrader` class is the orchestrator of your trading system. It will
sort out all the boring stuff so that you can spend more time where it 
matters - researching good trading strategies.



(autotrader-config-methods)=
## Configuration Methods
The following methods are used to configure the active instance of AutoTrader.


(autotrader-configure)=
### Run Configuration

To configure the settings of AutoTrader, use the `configure` method. Here 
you can specifiy the verbosity of AutoTrader, set your data feed, set
which broker to trade with and more. If you are going to provide
local data, you should always call the `configure` method prior to specifying 
the local data via the `add_data` [method](autotrader-add-data), to ensure 
that the working directory is correctly configured. In general, it is always
good to call `configure` first up.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.configure
```

(autotrader-backtest-config)=
### Backtest Configuration
To configure a backtest, use the `backtest` method.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.backtest
```

(autotrader-virtual-account-config)=
### Virtual Account Configuration
Any time you are simulating trading, either in backtest or papertrading, you
should configure the simulated trading account. This is done using the
`virtual_account_config` method. Here, you can set your initial balance,
the bid/ask spread, the trading fees and more. If you do not call this method
when simulating trading, the default settings will be used.

If you plan on simultaneously trading across multiple venues, you will 
need to configure a virtual account for each exchange being simulated. When
doing so, use the `exchange` argument to specify which account it is that
you are configuring. This should align with the brokers/exchanges
specified to the `broker` argument in 
[`AutoTrader.configure`](autotrader-configure).


```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.virtual_account_config
```


### Configure AutoPlot Settings
To configure the settings used by [AutoPlot](autoplot-docs) when creating
charts, use the `plot_settings` method.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.plot_settings
```



## Other Methods
Below are the methods used to add your own components to AutoTrader.


(autotrader-add-strategy)=
### Add New Strategy
Trading strategies can be added using the `add_strategy` method of 
AutoTrader. If you would like to add multiple strategies to the same
instance of AutoTrader, simply call this method for each strategy 
being added. Note that this method accepts both `strategy_filename` and `strategy_dict` arguments. The first of these is used to provide the 
prefix of a [strategy configuration](strategy-config) file, while
the second can be used to directly pass in a strategy configuration 
dictionary.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.add_strategy
```


(autotrader-add-data)=
### Add Data
To trade using a local data source, use the `add_data` method to tell 
AutoTrader where to look for the data. You can use this method for 
both backtesting and livetrading. Of course, if you are livetrading,
you will need to make sure that the locally stored data is being
updated at an appropriate interval.

Note that you do not have to call this method if you are directly 
connecting to one of the supported exchanges for a data 
[feed](autotrader-configure). In this case, AutoTrader will automatically
download data using the information provided in your 
[strategy configuration](strategy-config) and supply it to your 
strategy.


```{important}
The `configure` [method](autotrader-configure) should be called 
before calling `add_data`, as it will set the `home_dir` of your project. 
```

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.add_data
```



(autotrader-bots-deployed)=
### Get Bots Deployed
After running AutoTrader, it may be of interest to access the 
[trading bots](autobot-docs) that were deployed. To do so,
use the `get_bots_deployed` method.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.get_bots_deployed
```


(autotrader-plot-backtest)=
### Plot Backtest
After running a backtest, you can call `plot_backtest` to create
a chart of the trade results. You can also pass in a specific
[trading bot](autobot-docs) to view the trades taken by that 
specific bot.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.plot_backtest
```



### Print Trade Results

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.print_trade_results
```


## Run AutoTrader
After [configuring](autotrader-configure) AutoTrader, 
[adding a strategy](autotrader-add-strategy) and specifying
how you would like to trade, you are ready to run AutoTrader. To 
do so, simply call the `run` method.

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
from autotrader import AutoTrader

at = AutoTrader()
at.configure(feed='oanda', broker='oanda', verbosity=1)
at.add_strategy('macd_crossover')
at.backtest(start='1/1/2015', end='1/3/2022')
at.virtual_account_config(leverage=30, exchange='oanda')
at.run()
```
````
````{tab} Papertrade Mode
```
from autotrader import AutoTrader

at = AutoTrader()
at.configure(feed='oanda', broker='oanda', verbosity=1)
at.add_strategy('macd_crossover')
at.virtual_account_config(leverage=30, exchange='oanda')
at.run()
```
````
````{tab} Livetrade Mode
```
from autotrader import AutoTrader

at = AutoTrader()
at.configure(feed='oanda', broker='oanda', verbosity=1)
at.add_strategy('macd_crossover')
at.run()
```
````
