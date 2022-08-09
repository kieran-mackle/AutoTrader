(dydx-module-docs)=
# dYdX Exchange Interface

`broker=dydx`

[dYdX](https://dydx.exchange/) is a decentralised cryptocurrency 
derivatives exchange.



## Supported Features

| Feature | Supported? | Alternative | 
| ------- | ---------- | ----------- |
| Stop loss | No | Implement manually in strategy with limit orders |
| Take profit | No | Implement manually in strategy with stop-limit orders |



## API Reference
```{eval-rst}
.. autoclass:: autotrader.brokers.dydx.broker.Broker
   :members:
   :private-members:
```