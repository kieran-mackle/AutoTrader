(virtual-broker-docs)=
# Virtual Broker

`broker='virtual'`

The virtual broker immitates the functionality of a real broker for 
the purpose of backtesting and live papertrading. 


## Virtual Account Configuration
Whenever the virtual broker is used (for example in backtesting or
papertrading), the virtual trading account must be configured using
the `virtual_account_config` method. If multiple brokers are being 
used simultaneously, this method must be called once for each 
broker.

When a real broker/exchange is specified in this method, the instance 
of AutoData created for data management will be connected to the broker
specified. 



## Internal Position Management

### Orders
Orders can take one of four statuses:
1. `pending` - a pending order is one which has been submitted, but is 
being held until new data arrives.
2. `open` - an open order is one which is valid to be filled. In the 
case of a market order, it will be filled as soon as new data is seen.
In the case of limit orders, the order will remain open until its limit
price has been triggered.
3. `filled` - after an order has been filled, its status is changed to 
'filled'.
4. `cancelled` - if an order is invalid, or gets cancelled by the user,
its status will be changed to 'cancelled'.


### Positions
Positions in an instrument are the result of orders being filled and trades 
being made.

In order to keep track of stop-losses and take-profits associated with individual
orders, a position is made up of multiple `IsolatedPositions`. These are positions
resulting from a single trade, and are treated in isolation of the entire position
in case there is a stop-loss or take-proft attached to them.



## Trade Execution
The virtual broker maintains its own orderbook. The details of this 
depend on whether AutoTrader is in backtest or livetrade mode.


### Backtest Mode
When backtesting, the top levels of the book are simulated to have 
infinite liquidity. The bid and ask prices are set using the OHLC 
data and the specified bid/ask spread model.


### Livetrade Mode 
When livetrading (including papertrading), the execution of orders 
can become more accurate by tapping into the real-time orderbook 
of your chosen exchange. To do so, the broker/exchange specified
in `AutoTrader.configure` and `AutoTrader.virtual_account_config`
is connected to when creating an instance of the virtual broker.
When orders are recieved, the real-time order book will be queried
and used to simulate execution.




## API Reference

```{eval-rst}
.. autoclass:: autotrader.brokers.virtual.Broker
   :members:
   :private-members:
```
