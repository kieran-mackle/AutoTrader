(trading-strategy)=
# Trading Strategy
`strategies/*.py`

Trading strategies are built as class objects, and must follow a few 
simple rules to function properly with AutoTrader. At a minimum, a 
strategy is required to have two methods. The first is the `__init__` method, 
which is used to instantiate the strategy. The second is the `generate_signal` 
method, which contains the strategy logic and ouputs any trading signals which 
may present themselves. Read more about these methods below and take a look at 
the sample strategies in the 
[demo repository](https://github.com/kieran-mackle/autotrader-demo). It might
also be helpful to review the tutorial, 
[*Building a Strategy*](strategy-tut).


(strategy-template)=
## Strategy Overview

```{tip}
A strategy template can be found in the templates folder of the 
<a href="https://github.com/kieran-mackle/AutoTrader/blob/main/templates/strategy.py" target="_blank">Github repository</a>.
You can also use the command line interface to download 
strategies from the repo.
```

The code block below provides some boilerplate for a strategy in
AutoTrader. The methods shown are the only things **required** 
of a strategy. Note the differences in the arguments to the 
`generate_signal` method between periodic and continuous update 
mode. Read about these modes in the 
[AutoTrader docs](autotrader-run-modes).


````{tab} Continuous Update Mode
```python
from autotrader import Order

class Strategy:
    def __init__(self, parameters, data, instrument, **kwargs):
        """Define all attributes of the strategy.
        """
        self.name = "Template Strategy"
        self.data = data
        self.params = params
        self.instrument = instrument
        
        # Define any indicators used in the strategy
        ...

        # Construct indicators dict for plotting
        self.indicators = {'Indicator Name': {'type': 'indicatortype',
                                              'data': 'indicatordata'},}
        
    def generate_signal(self, data):
        """Define strategy logic to determine entry signals.

        Parameters
        ----------
        data : pd.DataFrame|dict
            The strategy data.
        """
        # Example long market order
        order = Order(direction=1)
        return order
```
````
````{tab} Periodic Update Mode
```python
from autotrader import Order

class Strategy:
    def __init__(self, parameters, data, instrument, **kwargs):
        """Define all attributes of the strategy.
        """
        self.name = "Template Strategy"
        self.data = data
        self.params = params
        self.instrument = instrument
        
        # Define any indicators used in the strategy
        ...

        # Construct indicators dict for plotting
        self.indicators = {'Indicator Name': {'type': 'indicatortype',
                                              'data': 'indicatordata'},}
        
    def generate_signal(self, i):
        """Define strategy logic to determine entry signals.

        Parameters
        ----------
        i : int
            An integer index used to specify the location in the
            dataset. 
        """
        # Example long market order
        order = Order(direction=1)
        return order
```
````


(strategy-init)=
## Initialisation
The `__init__` method always initialises a strategy with the following named arguments:
  1. `parameters`: a dictionary containing the strategy parameters from your strategy configuration file.
  2. `data`: the strategy data, which may be a DataFrame, or a dictionary of different datasets.
  3. `instrument`: a string with the trading instrument's name (as it appears in the [watchlist](strategy-config-options)), or a list of instruments if the strategy has 
  `PORTFOLIO: True` in its configuration.



(strategy-broker-access)=
### Broker Access
In some cases, you may like to directly connect with the broker from your 
strategy module. In this case, you must include `INCLUDE_BROKER: True` in your 
[strategy configuration](strategy-config). This will tell AutoTrader to instantiate 
your strategy with the broker API and broker utilities. You will therefore need 
to include these as named arguments to your `__init__` method, as shown below. Now 
you can access the methods of the [broker](broker-interface) directly from your strategy!

```python
def __init__(self, parameters, data, instrument, broker, broker_utils, **kwargs):
    """Define all attributes of the strategy.
    """
    self.data = data
    self.parameters = parameters
    self.instrument = instrument
    self.broker = broker
    self.utils = broker_utils
```


(strategy-stream-access)=
### Data Stream Access
It may also be of interest to include the [data stream](utils-datastream) object 
when your strategy is instantiated, particularly if you are using a custom data 
stream. As above, this can be achieved by specifying `INCLUDE_STREAM: True` in 
your [strategy configuration](strategy-config). 

```python
def __init__(self, parameters, data, instrument, data_stream, **kwargs):
    """Define all attributes of the strategy.
    """
    self.data = data
    self.parameters = parameters
    self.instrument = instrument
    self.data_stream = data_stream
```


(strategy-indicator-dict)=
### Indicators Dictionary
If you wish to include any indicators your strategy uses when visualising 
backtest results, you must define an `indicators` attribute. This attribute
takes the form of a dictionary with the indicators which you would like to 
include. This dictionary then gets passed to [AutoPlot](autoplot-docs). 
The general form of this dictionary is shown below, but read more in the 
[docs](autoplot-indi-spec) for more information.

```python
self.indicators = {'indicator 1 name': {'type': 'indicator 1 type',
                                       'data': self.indicator1_data},
                   'indicator 2 name': {'type': 'indicator 2 type',
                                       'data': self.indicator2_data},
                    }
```


(strategy-signal-gen)=
## Signal Generation
Signals are generated using the `generate_signal` method. This method contains 
the logic behind your strategy and returns trading signals in the form of 
[`Order`s](order-object). This method must always return something, so either:
1. Return an `Order`,
2. Return multiple `Order`s grouped in a `list`,
3. Return a blank `Order` using `Order()`, or an empty list `[]`.

The details you provide in each order will depend on the 
[order type](order-types). The most basic (and default) order is a 
`market` order, which only requires you to specify the `direction`: 1 for a 
long trade, and -1 for a short trade. Note that you do not have to provide 
the `instrument` to the order; AutoTrader will do that for you based on the 
instruments defined in the `WATCHLIST` of the strategy's configuration. 
In some cases, however, you may want to provide it directly (when trading 
multiple instruments from the same strategy, for example). 

The input arguments to this method will depend on the 
[run mode](autotrader-run-modes) of AutoTrader. In 
[continuous update mode](autotrader-continuous-mode) (the default mode),
the most-recent strategy data is passed in. When backtesting, this dataset
will evolve over the backtest period. When livetrading, the latest data
available will be passed in. This mode is less prone to lookahead.
In [periodic update mode](autotrader-periodic-mode), the data indexing 
parameter `i` is passed in as the first argument. Since the entire dataset
is passed to the strategy in this mode, the indexing parameter `i` must be
used to act on the correct datapoints. 


(strategy-shutdown-routine)=
## Shutdown Routine
If you have a process you would like to exectue *after* your strategy 
has finished running, you may use the shutdown routine functionality 
to do so. This involves creating a method involving your shutdown routine 
and specifying it to AutoTrader via the 
[`add_strategy`](autotrader-add-strategy) method.

To explain this functionality, consider you are livetrading with a strategy 
which maintains many open trades at once. If you have this bot deployed in 
[continuous update mode](autotrader-continuous-mode) and would like 
to terminate it by deleting its [instance file](autotrader-instance-file), you 
likely would like it to safely close all open trades before terminating. 
Else, you may have unmanaged trades left open on your account. To prevent this, 
you may create a shutdown routine as shown below, which cancels any pending orders 
and closes all remaining open positions. Of course, this method should be more 
strategic than simply closing all positions and cancelling any orders.


```python
def safe_exit_strategy(self):
    # Cancel all pending orders
    pending_orders = self.broker.get_orders(self.instrument, 'pending')
    for order_id in pending_orders:
        self.broker.cancel_order(order_id)
    
    # Close all open trades
    close_order = Order(instrument=self.instrument, order_type='close')
    self.broker.place_order(close_order)
```

If you provide the name of your shutdown routine - in the example above this 
is 'safe_exit_strategy' - to AutoTrader via the `shutdown_method` argument 
of the [`add_strategy`](autotrader-add-strategy) method, it will be called 
when the bot is terminated.

