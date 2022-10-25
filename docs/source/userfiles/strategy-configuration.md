(strategy-config)=
# Strategy Configuration
`config/*.yaml`

The strategy configuration contains information related specifically 
to a strategy. Each [strategy](trading-strategy) requires its own 
configuration to be able to run. It is written either as a 
[.yaml](https://www.redhat.com/en/topics/automation/what-is-yaml) file, 
or passed directly to AutoTrader as a dictionary via the
[`add_strategy`](autotrader-add-strategy) method (`.yaml` files are
read into Python as dictionaries). Note that spacing is important in 
`.yaml` files, with each level defined by two subsequent spaces.

```{tip}
A template strategy configuration file can be generated using the command
line interface! Simply run `autotrader init -s config` in your home
directory, and a template file will be created in the `config/` directory.
You can also find this template in the
<a href="https://github.com/kieran-mackle/AutoTrader/blob/main/templates/strategy_config.yaml" target="_blank">Github repository</a>.
```

(strategy-config-options)=
## Configuration Options
The keys of the strategy configuration file are described in the table 
below. Note that all `PARAMETERS` defined will be accessible in 
the [strategy](trading-strategy), via the `parameters` argument. 

| Key | Description | Required | Default value |
|:---:|-------------|----------|---------------|
|`NAME`| A string defining the strategy name. |Yes|  |
|`MODULE`| A string containing the prefix name of the strategy module, without the *.py* suffix. |Yes, unless the strategy is passed directly via `add_strategy`| | 
|`CLASS`| A string containing the class name within the strategy module. |Yes| | 
|`INTERVAL`| The granularity of the data used by the strategy.|Yes | | 
|`PERIOD`| The number of candles to fetch when live trading (eg. a value of 300 will fetch the latest 300 candles), or a timedelta string (eg. '30d').|Yes | | 
|`PARAMETERS`| A dictionary containing custom strategy parameters (see below).|Yes| |
|`WATCHLIST`| A list containing the instruments to be traded in the strategy, in the [format required](autodata-docs) by the [data feed](autotrader-configure). |Yes| | 
|`SIZING`| The method to use when calculating position size. Can be either 'risk' or an integer value corresponding to the number of units to trade. If using the 'risk' option, position size will be calculated based on trading account balance and the value assigned to `RISK_PC`.|No| None | 
|`RISK_PC`| The percentage of the account balance to risk when determining position risk-based size.|No| None |
| `PORTFOLIO` | A boolean flag for if the strategy is a portfolio-based strategy, requiring fata for all instrumenets in the watchlists to run. |No| False |
|`INCLUDE_BROKER`| A boolean flag to indicate if the broker interface and broker utilities should be passed to the strategy's `__init__` method. Read more [here](strategy-broker-access). |No| False |
|`INCLUDE_STREAM`| A boolean flag to indicate if the [data stream](utils-datastream) object should be passed to the strategy's `__init__` method. |No| False |


### Data Interval
The `INTERVAL` key is a string used to define the granularity of the data used by 
your strategy. For example, '1m' for minutely data, or '4h' for 4-hourly data.
This is used to infer the timestep to take when backtesting (and livetrading), but
also to convert the `PERIOD` to an integer value if necessary.

If you would like to build a strategy which uses multiple timeframes, simply 
specify the timeframes with comma separation in the `INTERVAL` key. For example, 
to have access to 15-minute and 4-hour data, you would specify something 
like `INTERVAL: 'M15,H1'`. In this case, the `data` object passed into the 
strategy will be a dictionary, with keys defined by each granularity specified
in `INTERVAL` and the associated data.


### Data Period
The `PERIOD` key is used to determine how many rows of data (OHLC) is
required by your strategy. This could refer to the lookback period, either
as an integer value of the number of rows, or as a string such as '30d', 
indicating 30 days worth of data is required. If an integer value is provided,
for example 300, then the latest 300 rows of data will be passed to your 
strategy.


### Strategy Parameters
The parameters key contains any information you would like to be able to 
access from your [strategy](trading-strategy) module. This might include 
things like indicator configuration parameters, such as periods, and exit 
parameters, such as a risk-to-reward ratio.


## Example Configuration
An example strategy configuration is provided below. Each file will look very 
similar to this, with the exception of the parameters key, which will be tailored 
to your own strategy. Feel free to look at the configuration files for the example
strategies provided in the AutoTrader [demo repository](https://github.com/kieran-mackle/autotrader-demo/tree/main/config).


````{tab} YAML File
```yaml
NAME: 'Strategy Name'
MODULE: 'modulename'
CLASS: 'StrategyClassName'
INTERVAL: 'M15'
PERIOD: 300
RISK_PC: 1      # 1%
SIZING: 'risk'
PARAMETERS:
  ema_period: 200
  rsi_period: 14
  
  # Exit level parameters
  RR: 2
  stop_buffer: 10 # pips

# Define instruments to monitor
WATCHLIST: ['EUR_USD']
```
````
````{tab} Dictionary Form
```python
strategy_config = {'NAME': 'Strategy Name',
                   'MODULE': 'modulename',
                   'CLASS': 'StrategyClassName',
                   'INTERVAL': 'M15',
                   'PERIOD': 300,
                   'RISK_PC': 1,
                   'SIZING': 'risk',
                   'PARAMETERS': {'ema_period': 200,
                                  'rsi_period': 14,
                                  'RR': 2,
                                  'stop_buffer': 10},
                    'WATCHLIST': ['EUR_USD',]}
```
````