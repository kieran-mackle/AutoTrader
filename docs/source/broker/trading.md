# Trading Objects

(order-object)=
## Orders

```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Order
    :members:
    :special-members: __init__
    :private-members: _set_working_price, _calculate_exit_prices, _calculate_position_size, _from_dict
```


### Order types...

(empty-order)=
### Empty Order
Useful when no signal is present. AutoTrader will recognise this as an empty order and skip over it.

```python
empty_order = Order()
```




(trade-object)=
## Trades
```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Trade
    :show-inheritance:
    :private-members: _inheret_order, _split
```

(position-object)=
## Positions
```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Position
    :members:
```