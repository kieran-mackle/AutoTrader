# Trading Objects


(order-object)=
## Orders
Orders can be created using the `Order` object, shown below. The 
different order types and requirements are documented following.

```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Order
    :members:
    :special-members: __init__
    :private-members: _set_working_price, _calculate_exit_prices, _calculate_position_size, _from_dict
```


(order-types)=
### Summary of Order Types

AutoTrader is intelligent when it comes to order types. If your strategy 
has no stop loss, you do not need to include it in the signal dictionary. 
If you prefer to set a stop loss in terms of distance in pips, you can do 
that instead. Same goes for take profit levels, specify price or distance 
in pips - whatever is more convenient. The following tables provides 
accepted values for the `order_type` of an order.

| Order Type | Description | Additional keys required |
|------------|-------------|--------------------------|
| `market`   | A [market order](https://www.investopedia.com/terms/m/marketorder.asp) type | None |
| `limit` | A [limit order](https://www.investopedia.com/terms/l/limitorder.asp) type | `order_limit_price` |
| `stop-limit` | A [stop-limit order](https://www.investopedia.com/terms/s/stop-limitorder.asp) type | `order_limit_price` and `order_stop_price` |


(empty-order)=
### Empty Order
Useful when no signal is present. AutoTrader will recognise this as 
an empty order and skip over it.

```python
empty_order = Order()
```

### Market Order

A market order triggers a trade immediately at the best available price, 
provided there is enough liquidity 
to accomodate the order. Read more 
[here](https://www.investopedia.com/terms/m/marketorder.asp). Note that
this is the default order type, so `order_type` does not need to be specified.

```python
long_market_order = Order(direction=1)
short_market_order = Order(direction=-1)
```

### Limit Order
A limit order is allows a trader to buy or sell an instrument at a 
specified price (or better). Limit orders can be used to avoid 
slippage. However, a limit order is not gauranteed to be filled. 
When using this order type, the limit price must be specified. 
Read more about limit orders 
[here](https://www.investopedia.com/terms/l/limitorder.asp).

```python
limit_order = Order(direction=1, order_type='limit', order_limit_price=1.2312)
```

### Stop-Limit Order
A stop-limit order type provides a means to place a conditional limit 
order. This order type can be used to place an order, under the 
condition that price first moves to the stop price, at which point, 
a limit order is placed. In addition to a limit price, a stop price 
must also be specified. These prices are usually the same, although 
need not be. Read more about stop-limit orders 
[here](https://www.investopedia.com/terms/s/stop-limitorder.asp).

```python
stop_limit_order = Order(
    direction=1, 
    order_type='stop-limit', 
    order_limit_price=1.2312, 
    order_stop_price=1.2300
)
```


(broker-stop-loss-types)=
### Stop Loss Types
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


Note that for the purpose of calculating trading fees, stop loss orders are treated as `limit` order type (liquidity providing).

#### Limit Stop Loss
`stop_type='limit'`

A `'limit'` stop loss type will place a limit order at the price specified by the `stop_loss` key. If the price crosses a stop loss
order, the trade associated with it will be closed. Read more about stop losses 
[here](https://www.investopedia.com/terms/s/stop-lossorder.asp).

#### Trailing Stop Loss
`stop_type='trailing'`

A trailing stop loss can be used to protect unrealised gains by moving with price in favour of the trade direction. When using the 
`trailing` stop loss type, the initial stop loss position can be set by the price provided to the `stop_loss` key, or by providing
the stop loss distance (in [pips](https://www.investopedia.com/ask/answers/06/pipexplained.asp)) to the `stop_distance` key.
Read more about trailing stop loss orders [here](https://www.investopedia.com/terms/t/trailingstop.asp).


### Take Profit Orders
Take-profit orders can be attached to an order using the `take_profit` or `take_price` attribute. Note that take profit orders
are treated as `market` order type (liquidity consuming) when calculating trading costs.



(trade-object)=
## Trades
```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Trade
    :show-inheritance:
    :special-members: __init__
    :private-members: _inheret_order, _split
```


(isolated-position-object)=
## Isolated Positions
```{eval-rst}
.. autoclass:: autotrader.brokers.trading.IsolatedPosition
    :members:
```


(position-object)=
## Positions
```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Position
    :members:
```
