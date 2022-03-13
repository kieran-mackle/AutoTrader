# Trading Objects

## Orders

```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Order
    :members:
    :special-members: __init__
    :private-members: _set_working_price, _calculate_exit_prices, _calculate_position_size, _from_dict
```



## Trades
```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Trade
    :show-inheritance:
    :private-members: _inheret_order, _split
```


## Positions
```{eval-rst}
.. autoclass:: autotrader.brokers.trading.Position
    :members:
```