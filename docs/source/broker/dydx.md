(dydx-module-docs)=
# dYdX Exchange Interface

`broker='dydx'`

[dYdX](https://dydx.exchange/) is a decentralised cryptocurrency 
derivatives exchange.



## Supported Features

| Feature | Supported? | Alternative | 
| ------- | ---------- | ----------- |
| Stop loss | No | Implement manually in strategy with limit orders |
| Take profit | No | Implement manually in strategy with stop-limit orders |


## Configuration

Trading through dYdX requires the following configuration details.

````{tab} keys.yaml configuration
```yaml
dYdX:
  ETH_ADDRESS: "0xxxxx"
  ETH_PRIV_KEY: "xxxxx"
```
````
````{tab} Dictionary configuration
```python
{"dYdX":
   {
      "ETH_ADDRESS": "0xxxxx",
      "ETH_PRIV_KEY": "xxxxx",
   }
}
```
````


## API Reference
```{eval-rst}
.. autoclass:: autotrader.brokers.dydx.broker.Broker
   :members:
   :private-members:
```