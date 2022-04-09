(strategy-config)=
# Strategy Configuration


The strategy configuration contains information related specifically to a strategy. Each [strategy](trading-strategy) requires
its own configuration file to be able to run. It is written either as a 
[.yaml](https://www.redhat.com/en/topics/automation/what-is-yaml) file, or passed directly to AutoTrader as a dictionary via the
[`add_strategy`](autotrader-add-strategy) method. 
Note that spacing is important in .yaml files, with each level defined by two subsequent spaces.


(strategy-config-options)=
## Configuration Options
The keys of the strategy configuration file are described in the table below. Note that all parameters defined here will 
also be accessible in the [strategy](trading-strategy), via the `params` dictionary. Note that keys with no
default value are required to be specified.

| Key | Description | Default value |
|:---:|-------------| ------------- |
|`NAME`| A string defining the strategy name. | None |
|`MODULE`| A string containing the prefix name of the strategy module, without the *.py* suffix. | | 
|`CLASS`| A string containing the class name within the strategy module. | | 
|`INTERVAL`| The granularity of the strategy, in the [format required](autodata-docs) by the [data feed](autotrader-configure). | | 
|`PERIOD`| The number of candles to fetch when live trading (eg. a value of 300 will fetch the latest 300 candles). | | 
|`SIZING`| The method to use when calculating position size. Can be either 'risk' or an integer value corresponding to the number of units to trade. If using the 'risk' option, position size will be calculated based on trading account balance and the value assigned to `RISK_PC`.| | 
|`RISK_PC`| The percentage of the account balance to risk when determining position risk-based size.| |
|`PARAMETERS`| A dictionary containing custom strategy parameters (see below).| |
|`WATCHLIST`| A list of strings containing the instruments to be traded in the strategy, in the [format required](autodata-docs) by the [data feed](autotrader-configure). | | 
|`INCLUDE_POSITIONS`| A boolean flag to indicate if current possitions should be passed to the strategy's `generate_signal` method. Read more [here](generate-signal-boilerplate). | False | 
|`INCLUDE_BROKER`| A boolean flag to indicate if the broker interface and broker utilities should be passed to the strategy's `__init__` method. Read more [here](strategy-broker-access). | False |
|`INCLUDE_STREAM`| A boolean flag to indicate if the [data stream](utils-datastream) object should be passed to the strategy's `__init__` method. | False |

Some things to note:
- The `PERIOD` key is used to specify how many candles to retrieve when live trading. For example, if period takes the value of 300, the 
latest 300 candles will be downloaded. This number will depend on the strategy which you have implemented. If your strategy 
uses lagging indicators, the value of `PERIOD` should be *at least* as much as the slowest indicator period in your strategy.
- If you would like to build a strategy which uses multiple timeframes, simply specify the timeframes with comma separation in
the `INTERVAL` key. For example, to have access to 15-minute and 4-hour data, you would specify something like `INTERVAL: 'M15,H1'`.
In this case, the `data` object passed into the strategy will be a dictionary, with keys defined by each granularity specified
in `INTERVAL` and the associated data.


### Strategy Parameters
The parameters key contains any information you would like to be able to access from your [strategy](trading-strategy) module. 
Typically, this will include indicator configuration parameters, such as periods, and exit parameters, such as a risk-to-reward 
ratio.


## Example Configuration
An example strategy configuration is provided below. Each file will look very similar to this, with the exception of the 
parameters key, which will be tailored to your own strategy. Feel free to look at the configuration files for the example
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