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
|`PARAMETERS`| A dictionary containing custom strategy parameters (see below).|Yes| |
|`WATCHLIST`| A list containing the instruments to be traded in the strategy, in the [format required](autodata-docs) by the [data feed](autotrader-configure). |Yes| | 
| `PORTFOLIO` | A boolean flag for if the strategy is a portfolio-based strategy, requiring fata for all instrumenets in the watchlists to run. |No| False |


### Data Interval
The `INTERVAL` key is a string used to define the granularity of the data used by 
your strategy. For example, '1m' for minutely data, or '4h' for 4-hourly data.
This is used to infer the timestep to take when backtesting (and livetrading).



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
strategy_config = {
  'NAME': 'Strategy Name',
  'MODULE': 'modulename',
  'CLASS': 'StrategyClassName',
  'INTERVAL': 'M15',
  'PERIOD': 300,
  'PARAMETERS': {
    'ema_period': 200,
    'rsi_period': 14,
    'RR': 2,
    'stop_buffer': 10
  },
  'WATCHLIST': ['EUR_USD',]
}
```
````