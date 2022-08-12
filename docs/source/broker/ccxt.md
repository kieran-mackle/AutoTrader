(ccxt-module-docs)=
# CCXT Exchange Interface
`broker='ccxt:<exchange name>'`

The CryptoCurrency eXchange Trading (CCXT) library is an open-source 
[Python library](https://github.com/ccxt/ccxt) supporting over 100 
cryptocurrency exchange markets and trading APIs.



## Specifying the Exchange
CCXT serves as a unified API for many different cryptocurrency exchanges.
To trade with one of the supported exchanges, you must specify the name
of the exchange after providing the `ccxt` key. For example, to trade 
with Binance, you would specify:


```python
broker=ccxt:binance
```


## Supported Features

| Feature | Supported? | Alternative | 
| ------- | ---------- | ----------- |
| Stop loss | No | Implement manually in strategy with limit orders |
| Take profit | No | Implement manually in strategy with stop-limit orders |


## Configuration

Trading through CCXT requires the following configuration details.

````{tab} keys.yaml configuration
```yaml
CCXT:EXCHANGE:
  api_key: "xxxx"
  secret: "xxxx"
  base_currency: "USDT"
```
````
````{tab} Dictionary configuration
```python
{"CCXT:EXCHANGE":
   {
      "api_key": "xxxx",
      "secret": "xxxx",
      "base_currency": "USDT",
   }
}
```
````



## API Reference
```{eval-rst}
.. autoclass:: autotrader.brokers.ccxt.broker.Broker
   :members:
   :private-members:
```
