(broker-interface)=
# AutoTrader Broker Interface

```{toctree}
:maxdepth: 3
:hidden:

Orders, Trades and Positions <trading>
Virtual Broker <virtual-broker>
Oanda <oanda>
Interactive Brokers <ib>
CCXT <ccxt>
```

To make the transition from backtesting to live-trading seamless, 
each broker integrated into AutoTrader interfaces using a set of 
common methods. This means that the same strategy can be run with 
the virtual broker or any other broker without changing a single 
line of code in your strategy. This page provides a general 
overview of the methods contained within each broker interface 
module. Of course, the mechanics behind each method will change 
depending on the broker, however each method will behave in the 
same way, accepting the same input arguments and outputting the 
same objects.


```{seealso}
A great way to learn the broker interface is to do some 
[click trading](click-trading).
```


(broker-methods)=
## Methods
The shared methods of the broker interfaces are described below.
Note that each broker may have their own additional methods
to extend their functionality based on the brokers API 
capabilities.

```{tip}
A template for integrating new brokers into AutoTrader is included 
in the 'templates/' directory of the 
[GitHub repository](https://github.com/kieran-mackle/AutoTrader).
```

|           Method          | Function                                |
| :-----------------------: | --------------------------------------- |
| `get_NAV` | Returns Net Asset Value of account. |
| `get_balance`| Returns balance of account. |
| `place_order` | Place order with broker. |
| `get_orders` | Returns orders. |
| `cancel_order` | Cancels an order by ID. |
| `get_trades` | Returns open trades for the specified instrument. |
| `get_positions` | Returns the open positions in the account. |


### Accessing Exchange API Methods
When trading with a real exchange/broker, you are also able to communicate
directly with their API endpoints via the `api` attribute of the broker
instance. This allows you to access all methods offered by an exchange,
outside of the unified methods listed in the table above.


## Module Structure
Each new broker API is contained within its own submodule of the 
`autotrader.brokers` module. This submodule must contain two more 
submodules:
1. A core API module which communicates with the broker.
2. A utility module containing helper functions related to the core API 
module. 

```
autotrader.brokers
├── broker_utils.py
└── broker_name
    ├── broker.py
    ├── __init__.py
    └── utils.py
```


(supported-brokers)=
## Supported Brokers and Exchanges

### Virtual Broker

`broker='virtual'`

At the heart of AutoTrader's backtesting algorithm is the virtual broker, a 
Python class intended to replicate the functionality of a real broker. See 
the documentation of the [Virtual Broker](virtual-broker-docs) for more 
information about how this functions.


### Oanda v20 REST API

`broker='oanda'`

AutoTrader supports Oanda's v20 REST API. See the documentation of the 
[Oanda Broker](oanda-module-docs) module for more information.


### Interactive Brokers

`broker='ib'`

As of AutoTrader `v0.6.0`, [Interactive Brokers](ib-module-docs) is also 
supported.


### CCXT

`broker='ccxt:<exchange name>'`

The CryptoCurrency eXchange Trading (CCXT) library is an open-source 
[Python library](https://github.com/ccxt/ccxt) supporting over 100 
cryptocurrency exchange markets and trading APIs.



## API Reference

```{eval-rst}
.. autoclass:: autotrader.brokers.broker.AbstractBroker
   :members:
   :private-members:
```
