(broker-interface)=
# AutoTrader Broker Interface

```{toctree}
:maxdepth: 3
:hidden:

Orders, Trades and Positions <trading>
Virtual Broker <virtual-broker>
Oanda <oanda>
Interactive Brokers <ib>
Broker Utilities <utils>
```

To make the transition from backtesting to live-trading seamless, each broker integrated into AutoTrader 
interfaces using a set of common methods. This means that the same strategy can be run with the 
virtual broker or any other broker without changing a single line of code in your strategy. This 
page provides a general overview of the methods contained within each broker interface module. Of course, the mechanics
behind each method will change depending on the broker, however each method will behave in the same way.



## Methods
The shared methods of the brokers are described below.

```{tip}
A template for integrating new brokers into AutoTrader is included in the 'templates/' directory of the
[GitHub repository](https://github.com/kieran-mackle/AutoTrader).
```


|           Method          | Function                                                                                              |
| :-----------------------: | ----------------------------------------------------------------------------------------------------- |
|         `__init__`        | Initialises broker with broker configuration dictionary and broker utilities class instance. |
| `get_NAV` | Returns Net Asset Value of account. |
|`get_balance`| Returns balance of account. |
| `place_order` | Place order with broker. |
| `get_orders` | Returns orders. |
| `cancel_order` | Cancels the order. |
| `get_trades` | Returns open trades for the specified instrument. |
| `get_trade_details` | Returns the trade specified by trade_ID. |
| `get_positions` | Returns the open positions (including all open trades) in the account. |



## Module Structure
Each new broker API is contained within its own submodule of the `autotrader.brokers` module. This submodule must contain
two more submodules:
1. A core API module which communicates with the broker.
2. A utility module containing helper functions related to the core API module. This will usually inherit attributes from 
the [`BrokerUtils`](broker-utils) class.

```
autotrader.brokers
├── broker_utils.py
└── broker_name
    ├── broker.py
    ├── __init__.py
    └── utils.py
```



(supported-brokers)=
## Integrated Brokers

### Virtual Broker
At the heart of AutoTrader's backtesting algorithm is the virtual broker, a Python class intended to replicate the 
functionality of a real broker. See the documentation of the [Virtual Broker](virtual-broker-docs) for more information.


### Oanda v20 REST API
AutoTrader supports Oanda's v20 REST API. See the documentation of the [Oanda Broker](oanda-module-docs) module 
for more information.


### Interactive Brokers
As of AutoTrader `v0.6.0`, [Interactive Brokers](ib-module-docs) is also supported.

