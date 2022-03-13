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
interfaces with a strategy using a set of common methods. This means that the same strategy can be run with the 
virtual broker or any other broker in live trading without changing a single line of code in your strategy. This 
page provides a general overview of the methods contained within each broker interface module. Of course, the mechanics
behind each method will change depending on the broker, however each method will behave in the same way.


## Module Structure
Each new broker API is contained within its own submodule of the `autotrader.brokers` module. This submodule must contain
two more submodules:
1. A core API module which communicates with the broker.
2. A utility module containing helper functions related to the core API module. This will usually inherit attributes from the `BrokerUtils` [class](broker-utils).

```
autotrader.brokers
├── broker_utils.py
└── broker_name
    ├── broker.py
    ├── __init__.py
    └── utils.py
```


## Methods
The shared methods of the brokers are described below.




|           Method          | Function                                                                                              |
| :-----------------------: | ----------------------------------------------------------------------------------------------------- |
|         `__init__`        | Initialises virtual broker with attributes.                                                           |
|        `get_price`        | Returns current price data                                                                            |
|       `place_order`       | Recieves order details and moves to `pending_positions` dictionary.                                   |
|       `open_position`     | Opens a position and moves it into `open_positions` dictionary.                                          |
|     `update_positions`    | Iterates through `pending_positions` and `open_positions` dictionaries and updates them based on order details and current price. |
|    `close_position`       | Closes a position and moves it into `closed_positions` dictionary.                                    |
|     `add_funds`           | Adds funds to account.                                                                                |
|    `calculate_margin`     | Calculates margin required to take a position.                                                        |
|        `update_MDD`       | Updates the maximum drawdown of the account.                                                          |



### Utility Functions

Refer to the [Broker Utility Functions](virtual-utils) for more information.






## Order Handling
An order can be created by providing the required information in a dictionary. This dictionary must be 
returned by a method named `generate_signal` in the [strategy module](strategies#signal-generation). This method is called 
from the `_update` method of the [AutoBot module](autobot#core-methods), and then processed by the 
`_process_signal` method. The contents of this dictionary will largely depend on the type of order, but at 
a minimum, it must contain the order type and trade direction. Possible keys for this dictionary are provided
in the table below. 


| Key | Description |  Specification  |
|-----|-------------|----|
| `order_type` | Order type | Required |
| `direction` | Trade direction (1 for long or -1 for short trades, 0 for no trade) | Required |
| `order_limit_price` | The limit entry price for the order | Required for `limit` order types |
| `order_stop_price` | The stop-limit entry price for the order | Required for `stop-limit` order types |
| `size` | Trade size, specified in trade units | Optional |
| `take_profit` | Take profit, specified as price | Optional |
| `take_distance` | Take profit, specified in pips from entry price | Optional |
| `stop_loss` | Stop loss, specified as price | Optional |
| `stop_distance` | Stop loss, specified in pips from entry price | Optional |
| `stop_type` | Type of stop loss order | Optional |
| `related_orders` | A dictionary of related order numbers | Optional |


Note that AutoTrader is intelligent when it comes to order handling. For example, if your strategy has no stop loss, you do not need 
to include it in the signal dictionary. The same goes for all other optional keys described above.



### Order Types

The following tables provides accepted values for the `order_type` specification of an order.

| Order Type | Description | Additional keys required |
|------------|-------------|--------------------------|
| `market`   | A [market order](https://www.investopedia.com/terms/m/marketorder.asp) type | None |
| `limit` | A [limit order](https://www.investopedia.com/terms/l/limitorder.asp) type | `order_limit_price` |
| `stop-limit` | A [stop-limit order](https://www.investopedia.com/terms/s/stop-limitorder.asp) type | `order_limit_price` and `order_stop_price` |
| `close` | An order to close a trade | Optionally trade ID in `related_orders` |
| `reduce` | An order to reduce a postion | None |


#### Market Order
`'order_type': 'market'`

A market order triggers a trade immediately at the best available price, provided there is enough liquidity 
to accomodate the order. Read more [here](https://www.investopedia.com/terms/m/marketorder.asp).


#### Limit Order
```py
'order_type': 'limit'
'order_limit_price': 'x.xxxx'
```

A limit order is allows a trader to buy or sell an instrument at a specified price (or better). Limit orders can
be used to avoid slippage. However, a limit order is not gauranteed to be filled. When using this order type, the 
limit price must be specified. Read more about limit orders [here](https://www.investopedia.com/terms/l/limitorder.asp).


#### Stop-Limit Order
```py
'order_type': 'stop-limit'
'order_limit_price': 'x.xxxx'
'order_stop_price': 'x.xxxx'
```

A stop-limit order type provides a means to place a conditional limit order. This order type can be used to place an order,
under the condition that price first moves to the stop price, at which point, a limit order is placed. In addition to a limit 
price, a stop price must also be specified. These prices are usually the same, although need not be. Read more about 
stop-limit orders [here](https://www.investopedia.com/terms/s/stop-limitorder.asp).



#### Close Order
```py
'order_type': 'close'
'related_orders': 224 # trade ID
```

A close order type allows you to close a specific trade or position of an instrument held. If you wish to close the entire position
held, no related order needs to be specified. In this case, all individual trades held for the relevant instrument will be closed. 
Alternatively, an trade ID can be provided to close a specific trade. 

Note: a dictionary containing all trade ID's can be obtained using the `get_open_trades` method. 


### Reduce Order
```py
'order_type': 'reduce'
'direction': -1
'size': 15
```

A reduce order type can be used to reduce the position held by the account. When using this order type, the `direction` key is used
to specify in which direction the reduction will take place. In the example above, the *long* units held will be reduced by 15 units,
since the direction specified implies *selling* to reduce the position. This is an important distinction to make, as both *long* and
*short* positions can be held simultaneously.

When reducing a position, the *first in, first out* method is applied. To avoid this, specific trades could be closed (or reduced) 
manually with the `close_trade` and/or `partial_trade_close` methods.




## Stop Loss Types
AutoTrader supports both limit stop loss orders, and trailing stop loss orders. The keys required to specify these stop loss 
types are provided in the table below. Note that `limit` stop losses are the default type, so if a `stop_price` (or 
`stop_distance`) is provided with no `stop_type`, a limit stop-loss will be placed.


| Stop Type | Description | Additional keys required |
|------------|-------------|--------|
| `limit` | A regular [stop loss](https://www.investopedia.com/terms/s/stop-lossorder.asp) order | None |
| `trailing` | A [trailing stop loss](https://www.investopedia.com/terms/t/trailingstop.asp) order | `stop_loss` or `stop_distance` |


A note about setting stop losses: the `stop_price` takes precedence over `stop_distance`. That is, if `stop_price` is 
provided along with a `stop_distance`, the stop loss will be set at the price defined by `stop_price`. To avoid ambiguity, 
only specify one.


### Limit Stop Loss
`'stop_type': 'limit'`

A `'limit'` stop loss type will place a limit order at the price specified by the `stop_loss` key. If the price crosses a stop loss
order, the trade associated with it will be closed. Read more about stop losses 
[here](https://www.investopedia.com/terms/s/stop-lossorder.asp).

### Trailing Stop Loss
`'stop_type': 'trailing'`

A trailing stop loss can be used to protect unrealised gains by moving with price in favour of the trade direction. When using the 
`trailing` stop loss type, the initial stop loss position can be set by the price provided to the `stop_loss` key, or by providing
the stop loss distance (in [pips](https://www.investopedia.com/ask/answers/06/pipexplained.asp)) to the `stop_distance` key.
Read more about trailing stop loss orders [here](https://www.investopedia.com/terms/t/trailingstop.asp).
