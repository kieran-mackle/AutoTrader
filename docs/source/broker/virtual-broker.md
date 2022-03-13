# Virtual Broker

`autotrader.brokers.virtual.virtual_broker`

The virtual broker immitates the functionality of a real broker during backtests. It is constructed as a class 
and instantiated before backtesting begins.


## Attributes
The attributes of the virtual broker are listed below, with default values shown in parenthesis.


|   Attribute   | Description (default)                                                                     |
| :-----------: | ----------------------------------------------------------------------------------------- |
| `leverage`      | The account leverage (1)                                                                  |
| `commission`    | The commission per trade (0)                                                              |
| `spread`        | The bid/ask price spread (0)                                                              |
| `home_currency` | The home currency of the account ('AUD')                                                  |
| `NAV`           | The net asset value of the account (0)                                                    |
| `portfolio_balance` | The current portfolio balance (0)                                                     |
| `margin_available`  | The margin available (0)                                                              |
| `pending_positions` | A dictionary containing pending orders ({})                                           |
| `open_positions`    | A dictionary containing open positions ({})                                           |
| `closed_positions`  | A dictionary containing closed positions ({})                                         |
| `cancelled_orders`  | A dictionary containing cancelled orders ({})                                         |
| `total_trades`      | A count of total trades taken (0)                                                     |
| `profitable_trades` | A count of profitable trades (0)                                                      |
| `peak_value`        | The peak value the account has taken (0)                                              |
| `low_value`         | The minimum value the account has taken (0)                                           |
| `max_drawdown`      | The maximum drawdown of the account (0)                                               | 



## Methods
The methods of the virtual broker are described in the table below.

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



## Utility Functions

Refer to the [Virtual Broker Utility Functions](virtual-utils) for more information.






## Order Handling

*This section is currently in development. Please check back soon!*

`stop_price` always takes precedence over `stop_distance`. That is, if `stop_price` is provided along with a `stop_distance`, 
the stop loss will be set at the price defined by `stop_price`. 

AutoTrader is intelligent when it comes to order types. If your strategy has no stop loss, you do not need to include it in the 
signal dictionary. If you prefer to set a stop loss in terms of distance in pips, you can do that instead. Same goes for take 
profit levels, specify price or distance in pips. The choice is yours.


## Order Types

- Market order
- Limit order
- Stop-limt order

### Stop loss order types

- limit
- trailing
