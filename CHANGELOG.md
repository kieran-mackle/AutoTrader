# AutoTrader Changelog

## v1.0.1 (2024-03-12)

### Fix

- **ccxt**: add exception handling for place_order
- **AutoTrader**: only try instantiate notifier if notify > 0
- **Notifier**: reimplement telegram notifier

## v1.0.0 (2024-03-10)

### Feat

- option to instantiate ccxt broker as read only
- **Strategy**: add method for including indicators to plot
- **utilities.py**: added ccxt-download data stream object
- using logging throughout
- **utilities.py**: added logger function
- **Broker**: ccxt broker will translate native TP/SL to ccxt params
- **Broker**: added broker base class
- added ability for bots to kill instance
- **Strategy**: added strategy base class

### Fix

- **utilities.py**: ccxt global config indexing case
- pass logging config to brokers
- **AutoTrader**: handling of logger kwargs
- **AutoTrader**: logging arguments
- log handling and ccxt instrument precisions
- **Broker**: use _safe_add method to update ccxt_params
- **AutoPlot**: fixed plotting nav timezone bug
- **DataStream**: use generalised data fetch methods of AutoData

### Refactor

- simplified broker module strucutre
- major refactor of entire project
- **data**: renamed data to package_data for clarity

## v0.12.1 (2023-09-26)

### Fix

- **autoplot.py**: fix plot_data error for indicator scaling

## v0.12.0 (2022-11-17)

### Feat

- **indicators**: added signal column to chandelier indicator
- **indicators**: added chandelier exit indicator
- **cli**: added option to initialise directory from demo repository

### Fix

- **indicators.py**: fill na values in indicator data for finding swings
- **autoplot.py**: skip autoscaling when there is no data variation
- **indicators.py**: fixed outdated argument for autodecting divergence

## v0.11.2 (2022-10-27)

### Fix

- **AutoData**: do not truncate yahoo data if start and end arguments are not None

## v0.11.1 (2022-10-27)

### Refactor

- **AutoData**: optionally provide workers as kwarg to fetch

## v0.11.0 (2022-10-27)

### Feat

- **AutoData**: batch fetch instruments

## v0.10.1 (2022-10-26)

### Perf

- data fetch of yahoo finance with count extends range to account for business days

## v0.10.0 (2022-10-25)

### Feat

- improved monitor and added dashboard template
- **cli.py**: added backtest demo function to cli

### Fix

- **autotrader.py**: write broker hist when click paper trading
- **autodata.py**: raise exception when invalid granularity is provided to yahoo finance

### Refactor

- added exception handling for click papertrade
- **autodata.py**: added exception handling for ccxt orderbook method
- moved print_banner function to utilities
- **cli.py**: init method more robust
- **macd_strategy.py**: load data from yahoo finance
- **macd_strategy.py**: changed data directory path to cwd
- deprecated support for email notifications

## v0.9.1 (2022-10-23)

### Fix

- **indicators.py**: fixed handling of different data types in find_swings indicator

## v0.9.0 (2022-10-21)

### Feat

- reimplemented scan mode
- integrated Telegram for trade notifications (#12)
- **tg.py**: telegram bot can write chat id to keys.yaml
- **telegram.py**: telegram bot returns chat id for initialisation
- added initialisation method

### Fix

- fixed circular import errors
- **tg.py**: order side determination logic

### Refactor

- **tg.py**: renamed telegram.py to tg.py to avoid name conflict
- **notifier.py**: added abstract communications class Notifier

## v0.8.2 (2022-10-19)

### Refactor

- **Broker**: all broker class inherit from AbstractBroker
- **brokers.broker.py**: renamed Broker to AbstractBroker
- **broker.py**: implemented initial broker abstraction

## v0.8.1 (2022-10-19)

### Refactor

- **ccxt.broker.py**: added network exception handling with single retries

## v0.8.0 (2022-10-17)

### Feat

- **autoplot.py**: portfolio plot includes equity and nav hovertool

## v0.7.11 (2022-10-17)

### Fix

- email_manager import (#46)
- datetime.timezone import
- CCXT get_trades uses kwargs in fetchMyTrades call

## Version 0.7.10
### Changes
- Improved verbosity for exception handling.
- Improved verbosity in `autotrader.py` for bot updates.
- Added utility to CCXT interface (`get_min_notional` and 
  `get_ticksize` methods).
- Improved CCXT `get_orders` capability.

### Fixes
- CCXT interface `get_trades` method updated for `Trade` object 
  arguments.

## Version 0.7.9
### Fixes
- Plotting bug when option to show cancelled orders is True.

## Version 0.7.8
### Features
- Upgraded virtual broker: backtest speedup for large portfolio's 
- Ability to specify `deploy_time` in `AutoTrader.configure()`, a datetime 
  object for when to release trading bots.
- Improved verbosity from main module when running.

## Version 0.7.7
### Fixes
- Decimal error when placing market orders with `dydx` module.

## Version 0.7.6
### Fixes
- Import error of `AutoData` in `dydx` module.

## Version 0.7.5
### Features
- AutoBot submits orders using `ThreadPoolExecutor` to speedup
  submission of multiple orders.
- Ability to provide custom execution methods via 
  `AutoTrader.configure(execution_method=)`. 
- Improved verbosity from `autobot`s.

### Fixes
- Handling of testnet/mainnet keys when paper/virtual/live trading.
- Inclusion of `__init__.py` file in `autotrader/brokers/ccxt/`.
- Timezone handling.
- Virtual broker does not use lambda functions to allow pickling.
- Unified `broker._utils` attribute naming.


## Version 0.7.4
### Features
- Better exception handling in CCXT broker interface.
- Ability to specify `mainnet` and `testnet` API keys in your
  `keys.yaml` file.
- Ability to provide slippage models for backtests (via 
  `at.configure()`).

### Fixes
- Inifite `while` loop bug in virtual broker `_reduce_position`
  method due to machine precision.
- Backtest portfolio plotting of more than 18 instruments is 
  possible now due to an increased color pallete.

## Version 0.7.3
### Fixes
- Unification of `get_orderbook` in supporting `broker` modules.
- Expected behaviour of `get_positions` method in CCXT broker module.

### Features
- Trading object `Position` includes attribute `ccxt` to include the 
  output from `CCXT` methods.
- Improved configuration options for CCXT exchanges in `keys.yaml` file.

## Version 0.7.2
### Fixes
- Oanda live trade functionality restored (after `keys.yaml` rename).

### Features
- `AutoData` is more intelligent when creating a new instance; `kwargs` can
  be used in place of `data_config` dictionary, simplifying instantiation.
- Utility methods `get_broker_config` and `get_data_config` have been 
  simplified, allowing calling without `global_config` argument (`keys.yaml`
  will be read in from `config/` directory).

## Version 0.7.1
### Changes
- Oanda configuration keys in `keys.yaml` have changed for clarification

### Fixes
- Oanda `data_config` includes account id, restoring automated data retrieval

### Features 
- Improved portfolio plot type
- Improved printouts


## Version 0.7.0
AUGUST 2022

### Breaking Changes
- Backtest `spread` is now specified in absolute price units (rather than 
  pips as previously)
- Environment specification: paper trading can be activated by setting 
  `environment` to `paper` (default) and live trading can be activated
  by setting `environment` to `live`
- To further remove the distinction between backtesting and livetrading,
  various methods and attributes have been renamed to reflect their 
  generality and indifference to mode of trading. Important changes include
  `AutoTrader.backtest_results` to `AutoTrader.trade_results` (and similar for 
  `AutoBot`), `AutoTrader.print_backtest_results` to `AutoTrader.print_trade_results` 
  and `BacktestResults` class to `TradeAnalysis`.
  Renaming generally followed the pattern of renaming `*backtest*` to 
  `*trade*`.
- For consistency in naming conventions, `GetData` class of `autodata.py` has 
  been renamed to `AutoData`.
- Broker interface method `get_positions` will directly 
- Rename `virtual_livetrade_config` to `virtual_account_config`.
- Strategy configuration key `INCLUDE_POSITIONS` has been deprecated in favour
  of using `INCLUDE_BROKER`, then directly fetching positions from broker using
  `get_positions` method.
- Renamed `GLOBAL.yaml` to `keys.yaml` for clarification.
- Run mode 'continuous' has become the default run mode. To continue running strategies
in periodic update mode, you will now need to specify `mode='periodic'` in `configure`.
- The behaviour of broker method `get_trades` has changed: now returns a list of fills 
(executed trades based on the `Trade` object), rather than a dictionary of 
`IsolatedPositions` objects as before. This falls in line with the more common 
definition of a trade, but diverges from Oanda. As such, a new method 
`get_isolated_positions` has been added to the virtual broker and Oanda API interface
to maintain the previous functionality of `get_trades`.


### Features
- Major backtest speed improvements: over 50% reduction in backtest time for 
  large, multi-asset backtests
- Live paper-trading via the virtual broker: use `AutoTrader.virtual_livetrade_config`
  to configure virtual broker.
- To check-in on paper trading status, there is a new convenience method 
  `papertrade_snapshot`, which will print up-to-date trade results from 
  the virtual broker pickled instance.
- Support for decentralised crypto exchange dYdX
- Support for many more crypto exchanges via CCXT
- Introduction of 'portfolio' strategies: passing data of multiple assets to 
  a single strategy. Simply include `PORTFOLIO: True` in your strategy 
  configuration.
- Data feeds have been unified to make data retrieval simpler than ever. Now there
  are methods `fetch` and `quote`, which can be used to fetch OHLC price data 
  from various feeds, depending on the `data_source` specified in the 
  data configuration dictionary. Retrieval of level 1 and level 2 data is also
  available (where possible), accessible via the `L1` and `L2` methods.
- Improved backtest accuracy, with orderbook simulation and order type dependent
  commissions.
- Additional commission schemes for backtesting.
- Option to specify bid/ask spread as a percentage value.
- Manual trading (paper and live) via command line. Simply configure an instance 
  of AutoTrader without adding a strategy, and the broker specified will be 
  instantiated ready for trading. Papertrading via the virtual broker supported.
- Ability to trade across multiple venues from a single strategy. Simply
  provide the broker names with comma separation via the `configure` method,
- Exchange-specific precision checking for Orders. Even in backtest mode, AutoTrader
  will communicate with your chosen exchange to precision-check your orders.
- Code is now formatted using [Black](https://github.com/psf/black).
- Ability to specify a time range for `PERIOD` in strategy configuration. This value
will be converted to an integer using the `INTERVAL` key.


### Deprecation Notices
- Broker method `get_trade_details` has been deprecated in favour of `get_trades`
  method.
- Strategy configuration key `INCLUDE_POSITIONS` has been deprecated in favour
  of using `INCLUDE_BROKER`, then directly fetching positions from broker using
  `get_positions` method.

### Fixes
- Minor improvements to margin requirement calculations in backtest



## Version 0.6.6
### Features 
- Support of local data with portfolio strategies
- Backtest spread is now specified in price units for disambiguation
- Skip data warmup period to speed up backtests (specify `warmup_period` in
  autotrader.backtest) in continuous update mode
- Improved backtest printout
- All instruments will be passed to a portfolio strategy as a list using the 
  `instrument` argument
- Instrument specific pip values can be provided when creating an order 
- Improved Trade and Position `__repr__` methods

### Fixes
- Bug with floating pnl calculation when running multi-instrument backtests
- Pagination of Oanda data retrieval



## Version 0.6.5
### Features 
- General exception handling of bot updates in continuous mode

### Fixes
- Link to documentation and website


## Version 0.6.4
### Fixes
- Autodetect divergence order of operations, timeseries indexing
- Specification and handling of 'home_currency' (provided through `configure`)
- Calculation of home conversion factors, and handling of oanda quote data


## Version 0.6.3
### Features 
- Portfolio strategies: include `"PORTFOLIO": True` in your strategy 
  configuration to signal that the strategy is a portfolio-based strategy.
  Doing so, data for each instrument in the watchlist will be passed to the
  strategy, allowing a single strategy to control multiple instruments at 
  once, as in a portfolio. Currently supported for continuous mode only.
- Strategy configuration key `PARAMETERS` now optional.
- Autodetection of multiple instrument backtests for plotting.
- Option to select chart type (standard or portfolio) for single instrument
  backtests, via `AutoTrader.plot_settings()`.
- Option to specify `base_size` when creating an `Order`. This refers to the 
  trade size calculated using the base currency, pre-conversion using the 
  account's home currency (particularly useful for Forex traders).
- `modify` order types are now supported by the Oanda broker API, allowing
  a trader to change the take profit or stop loss attached to an open trade.

### Fixes
- generalised `get_size` method of broker utilities to give correct results
  for non-FX instruments (in this case, SL price must be provided rather than
  SL distance).


## Version 0.6.2
### Features
- Named arguments for strategy initialisation: strategies must be constructed
  from named arguments "parameters", "data" and "instrument". Additionally,
  "broker" and "broker_utils", when including broker access, and "data_stream"
  when including data stream access. This change was made for disambiguation of
  input arguments.
- Improvements to `AutoPlot`, including autoscaling of indicator figures
  and backtest account history
- Addition of `BacktestResults` class, improving readability and accessibility 
  of backtest results.



## Version 0.6.1
### Features
- Simpler imports: for example, `AutoTrader` can be imported 
  using `from autotrader import AutoTrader`, instead of
  `from autotrader.autotrader import AutoTrader`. Likewise for `AutoPlot`,
  `GetData`, and trade objects (`Order`, `Trade`, `Position`).
  

### Fixes
- Handling of close and reduce order types in `autobot`
- Assign UTC timezone to data after downloading from yfinance
- Fetch current positions from virtual broker after updating with latest
  data.
- Duplicate bar checking method in `autobot`


## Version 0.6.0
- Interactive Brokers is now supported.
- Improvements to public broker methods for clarity.
- Comprehensive docstrings and type hints added.
- Distinction of broker and feed, allowing specification of broker and feed 
  separately.
- New broker template directory added.
- All AutoTrader attributes have been made private to avoid confusion - the 
  configuration methods should be used exclusively to set the attributes.
  This also clarifies and promotes visibility of public methods.
- New method `get_bots_deployed` added to AutoTrader.
- Project heirarchy: note changes in location of `autodata`, `indicators` and
  other modules previously in the `lib/` directory.
- Deprecated `help` and `usage` methods of AutoTrader (replaced by in-code
  docstrings).
- AutoTrader method `add_strategy` now accepts strategy classes as input 
  argument, to directly provide strategy class objects.
- Broker public method name changes: `cancel_pending_order` to `cancel_order`,
  `get_pending_orders` to `get_orders`, `get_open_trades` to `get_trades`,
  `get_open_positions` to `get_positions`.
- Broker public method deleted: `get_cancelled_orders` - functionality 
  available using `get_orders` method with `order_status = 'cancelled'`.
- To facilitate strategies built with prior autotrader versions, the previous 
  format of signal dictionaries from strategy modules is still supported. 
  Support for this format will be phased out in favour of the new `Order` and
  `Trade` objects (found in `autotrader.brokers.trading` module). 
- For new Order, Trade and Position objects, support for legacy code is 
  included via `as_dict` methods, to convert class objects to dictionaries.
- AutoTrader demo repository has been updated to reflect the changes above.
- Option to include/exclude positions from broker when updating strategy.
- Distinction of order/trade size and direction; size is now an absolute value
  representing the number of units to be traded, while direction specifies
  if the trade is long or short.
- Strategy module: method `generate_signal` is passed named arguments 
  `i` and `current_position`.
- Continuous mode: single instantiation, iteration by timestamp
- AutoStream deprecated: if using streamed data, local data file paths should
  be provided using the `add_data` method.
- Abstracted data update method into `DataStream` class 
  (within `autotrader.utilities` module) to allow custom data pipelines
- Ability to trade multiple contracts on an underlying asset (continuous 
  mode only)
- Ability to use virtual broker in livetrade mode


## Older Versions
For a changelog of versions prior to `v0.6.0`, please refer to the 
[older versions](old-changelog) changelog.