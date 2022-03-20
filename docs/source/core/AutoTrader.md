(autotrader-docs)=
# AutoTrader

AutoTrader is the main module where you will run things from. It is a class object, so you begin by creating an 
instance of AutoTrader. You can then configure the settings, add a strategy, add data, and finally, run it to 
begin trading.


(autotrader-modes-of-operation)=
## Modes of Operation
Although the strategies and trading bots are not aware of it, AutoTrader has three modes of operation:
  1. Livetrade mode
  2. Backtest mode
  3. Scan mode

By default, AutoTrader will run in livetrade mode. The run modes can be controlled by using the appropriate 
[configuration methods](autotrader-config-methods). Each of these methods allow the user to modify the default
attributes of AutoTrader.


(autotrader-livetrade-mode)=
### Livetrade Mode
If both `backtest_mode` and `scan_mode` attributes are set to `False`, AutoTrader will run in livetrade mode. 

In livetrade mode, the data indexing is similar to that described [above](autotrader-data-indexing) in backtest mode, however, only the last 
candle is indexed. This candle corresponds to latest market conditions, so long as the data retrieval was called upon runnning 
AutoTrader, to retrieve the last `N` candles. This parameter is specified as the `period` in the 
[strategy configuration](strategy-config) file.


#### Email Notifications

The verbosity of email notifications can be controlled using the `notify` attribute of AutoTrader. 

|  `notify` value | Behaviour                                                   |
| :-------------: | ----------------------------------------------------------- |
|        0        | No emails will be sent.                                     |
|        1        | Minimal emails will be sent (summaries only).               |
|        2        | All possible emails will be sent (every order and summary). |

Note that if daily email summaries are desired, `email_manager.py` must be employed in a scheduled job to send the summary.
This is to allow for flexibility in when the daily summaries will be sent. Setting the `notify` flag to `1` or greater will
therefore write to a text file containing all orders placed since the last email summary. See more information [here](emailing-utils).

(autotrader-backtest-mode)=
### Backtest Mode
AutoTrader will run in backtest mode is the attribute `backtest_mode` is `True`. This will occur any time the 
[backtest configuration](autotrader-backtest-config) method is used. Useful flags and notes for backtest mode are provided below.

#### Verbosity
The verbosity of the code is set by the `verbosity` attribute. In backtest mode, the values given to `verbosity` result in the 
following behaviour.

|  `verbosity` value | Behaviour                                                   |
| :----------------: | ----------------------------------------------------------- |
|         0          | All outputs are suppressed.                                 |
|         1          | Minimal output is displayed (test period, trade statistics) |
|         2          | All possible output are displayed.                          |


#### Show Plot
When the `show_plot` attribute is set to `True`, AutoTrader will pass a trade summary dictionary to `autoplot.py`. This dictionary
will then be used to plot the trade history on a price chart, along with key indicators used in the strategy. Read more about 
AutoPlot [here](autoplot-docs).


(autotrader-data-indexing)=
#### Data Indexing
Although data and strategy indicators are pre-loaded when a strategy is instantiated, the platform is event-driven thanks to the 
indexing system employed. This system involves iterating through the entire dataset, candlestick by candlestick. Upon each iteration,
the method `generate_signal` from the strategy module is called to obtain a signal corresponding to the current timestep. 


(autotrader-scan-mode)=
### Scan mode
The third mode of AutoTrader is scan mode, activated by setting the `scan` attribute to `True`. When activated, AutoTrader will run
as in livetrade mode, but instead of submitting an order to the broker when a signal is received, it will notify you that the scan 
criteria has been met. If email notifications are not activated (using the `notify` flag), the scan results will be printed to the 
console. 


#### Market Scan Notifications
Email notifications require a host email account and a mailing list specified in the [global](global-config) and 
[strategy](strategy-config) files as appropriate. The extent of these notifications is controlled by the `notify`
attribute of AutoTrader in a similar way to the verbosity of the code.

|  `notify` value | Behaviour                                                   |
| :-------------: | ----------------------------------------------------------- |
|        0        | No emails will be sent.                                     |
|        1        | Emails will be sent each time the scanner gets a hit.       |
|        2        | Emails will be sent every time the scanner runs, regardless of whether or not a hit was detected. |



(autotrader-config-methods)=
## Configuration Methods
The following methods are used to configure the behaviour of AutoTrader.

(autotrader-run-config)=
### Run Configuration
To configure the run settings of AutoTrader, the `configure` method should be used. This is mostly optional,
and if not used, AutoTrader will run with the defualt settings. If you are livetrading, however, you will need to
set the feed to match your broker and provide your trading account number. Additionally, if you are going to provide
local data file(s), you should always call the `configure` method prior to specifying the local data via the 
`add_data` [method](autotrader-local-data), to ensure that file paths are correctly configured. 



```py
def configure(feed='yahoo', verbosity=1, notify=0, home_dir=None,
              include_broker=False, use_stream=False, detach_bot=False,
              check_data_alignment=True, allow_dancing_bears=False,
              account_id=None, environment='demo', show_plot=False,
              MTF_initialisation=False)
```

#### Parameters
The `configure` method has the following parameters. Note that many of these parameters are assigned as attributes to 
[AutoTrader bots](AutoBot). 

| Parameter | Description |
| ------- | ----------- |
| feed (str) | The data feed to be used (eg. Yahoo, Oanda)|
| verbosity (int)| the verbosity of AutoTrader (0, 1 or 2)|
| notify (int)| the level of email notification (0, 1 or 2) |
| home_dir (str)| the project home directory |
| include_broker (bool)| set to True to assign broker to strategy attributes |
| use_stream (bool)| set to True to use price stream as data feed |
| detach_bot (bool)| set to True to spawn new thread for each bot deployed |
| check_data_alignment (bool)| verify time of latest candle in data recieved against current time |
| allow_dancing_bears (bool)| allow incomplete candles to be passed to strategy |
| account_id (str)| the brokerage account ID to use in this instance |
| environment (str) | the trading environment of this instance: 'demo' for live paper-trading, 'real' for live trading with real money. |
| show_plot (bool) | automatically display plot of results |
| MTF_initialisation (bool) | Only download mutliple time frame data when initialising the strategy, rather than every update |


### Providing Strategies
Trading strategies can be added using the `add_strategy` method of AutoTrader. This method can be used multiple times
to add multiple strategies to the same run. Note that this method accepts both `strategy_filename` and `strategy_dict`. 
The first of these is used to provide the prefix of a [strategy configuration](strategy-config) file, while
the second can be used to directly pass in a strategy configuration dictionary.


```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.add_strategy
```

```py
def add_strategy(strategy_filename=None, 
                 strategy_dict=None)
```

(autotrader-local-data)=
### Providing Local Data
To backtest a strategy using locally stored price data, the `add_data` method should be used to tell AutoTrader where the data
is. Note that the `configure` [method](autotrader-run-config) should be called before calling `add_data`, as it will set the 
`home_dir` parameter for your project. This method can be used to provide data for both single-timeframe strategies and 
multiplie-timeframe strategies. 

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.add_data
```

```py
def add_data(self, data_dict, data_directory='price_data', abs_dir_path=None):
```

#### Parameters
The `add_data` method has the following parameters. If price data is stored in any directory other than the default
suggested sub-directory, "./price_data", the path must be provided by the `data_directory` or `abs_dir_path` parameters.

| Parameter | Description |
| ------- | ----------- |
| `data_dict` (dict)| A dictionary containing the filenames of the price data, with keys corresponding to the instruments provided in the [strategy configurations](strategy-config) `WATCHLIST`. |
| `data_directory` (str)| The name of the sub-directory containing the price data. This sub-directory must be within the projects `home_dir`. Default value is `price_data`. |
| `abs_dir_path` (str)| The absolute path to the data directory, which can be located anywhere on your computer. |


#### Examples
Example `data_dict`'s are provided below.

##### Single-Timeframe Data Specification
The example below illustrates how to provide data for a single-timeframe strategy, trading EUR/USD and EUR/JPY. This 
example assumes that the price data `.csv` files are stored in the default `./price_data` sub-directory of the project.

```py
at.add_data(data_dict={'EURUSD=X': 'EU_data.csv',
                       'EURJPY=X': 'EJ_data.csv'})
```

##### Multiple-Timeframe Data Specification
The example below builds upon the example above, but now the strategy employs multiple timeframes (`1h` and `1d`). Additionally,
in this example, the price data `.csv` files are stored in the directory with the path of '/home/algotrading/historical_data'.

```py
at.add_data(data_dict={'EURUSD=X': {'1h': 'my_hourly_data.csv', 
                                    '1d': 'my_daily_data.csv'},
                       'EURJPY=X': {'1h': 'EJ_hourly_data.csv', 
                                    '1d': 'EJ_daily_data.csv'},},
            abs_dir_path='/home/algotrading/historical_data')
```



(autotrader-backtest-config)=
### Backtest Configuration
To configure the backtest settings, use the `backtest` method. 

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.backtest
```

```py
def backtest(start=None, end=None, initial_balance=1000, spread=0, 
             commission=0, leverage=1, base_currency='AUD', start_dt=None, 
             end_dt=None)
```

#### Parameters
The `backtest` method has the following parameters.

| Parameter | Description |
| ------- | ----------- |
| start (str)| start date for backtesting, in format d/m/yyyy |
| end (str)| end date for backtesting, in format d/m/yyyy |
| initial_balance (float)| initial account balance in base currency units |
| spread (float)| bid/ask spread of instrument, specified in pips |
| commission (float)| trading commission as percentage per trade |
| leverage (int)| account leverage |
| base_currency (str)| base currency of account |
| start_dt (datetime)| datetime object corresponding to start time |
| end_dt (datetime)| datetime object corresponding to end time |


Note that start and end times must be specified as the same type. For example, both start
and end arguments must be provided together, or alternatively, start_dt and end_dt must 
both be provided.



##### Parameters

| Parameter | Description |
| ------- | ----------- |
| opt_params (list) | the parameters to be optimised, as they are named in the strategy configuration file |
| bounds (list of tuples) | the bounds on each of the parameters to be optimised, specified as a tuple of the form (lower, upper) for each parameter |
| Ns (int) | the number of points along each dimension of the optimisation grid |


(autotrader-scan-config)=
### Scan Configuration

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.scan
```

```py
def scan(strategy_filename=None, scan_index=None)
```

#### Parameters

| Parameter | Description |
| ------- | ----------- |
| strategy_filename (str) | prefix of yaml strategy configuration file, located in `home_dir/config` |
| scan_index (str) | index to scan |





## Private Methods
The following methods are used internally by autotrader to coordinate the workflow.

| Method | Description |
| ------ | ----------- |
| `_main` | Executes the core workflow of AutoTrader. |
| `_clear_strategies` | Removes all strategies saved in autotrader instance. |
| `_clear_bots` | Removes all deployed bots in autotrader instance. |
| `_instantiate_autoplot` | Creates instance of [AutoPlot](autoplot-docs). |
| `_update_strategy_watchlist` | Updates the watchlist of each strategy with the scan watchlist. |
| `_assign_broker` | Configures and assigns appropriate broker for trading. |
| `_configure_emailing` | Configure email settings. |
|`_run_optimise`| Runs optimisation of strategy parameters. |
| `_optimisation_helper_function` | Helper function for optimising strategy parameters in AutoTrader. This function will parse the ordered params into the config dict. |




## Example Runfiles
Shown below are example runfiles for running AutoTrader in livetrade, backtest and scan mode. Run-able examples can also 
be found in the [demo repository](https://github.com/kieran-mackle/autotrader-demo).

### LIvetrade Mode
```
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(feed = 'Oanda', verbosity = 1, notify = 1,
             home_dir = '/home/ubuntu/algotrade/', 
             account_id = '101-000-12345678-999')
at.add_strategy('macd_crossover')
at.run()
```






## Configuration Methods
The following methods are used to configure the active instance of AutoTrader.


(autotrader-configure)=
### Run Configuration

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.configure
```

### Backtest Configuration

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.backtest
```

### Optimisation Configuration
The optimisation capability of AutoTrader is a sub-function of the backtest mode, since a backtest must be run each iteration
of the optimisation. To configure the optimisation settings, use the `optimise` method.

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.optimise
```

```py
optimise(opt_params, bounds, Ns=4)
```


(autotrader-add-strategy)=
### Add New Strategy

```{eval-rst}
.. automethod:: autotrader.autotrader.AutoTrader.add_strategy
```



(autotrader-bots-deployed)=
### Get Bots Deployed


(autotrader-run-modes)=
## Run Modes


(autotrader-periodic-mode)=
### Periodic Update Mode


(autotrader-continuous-mode)=
### Continuous Update Mode

