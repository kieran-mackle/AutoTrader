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

Trading through CCXT requires the following configuration details. Note that
the heading key given for each exchange must match both the format specified
above (eg. `ccxt:binance`), and the exchange name format required by 
[CCXT](https://github.com/ccxt/ccxt).

````{tab} keys.yaml configuration
```yaml
CCXT:EXCHANGE:
  api_key: "xxxx"
  secret: "xxxx"
  password: "abcDEF"
  base_currency: "USDT"
  options:
    defaultType: "swap"
```
````
````{tab} Dictionary configuration
```python
{"CCXT:EXCHANGE":
   {
      "api_key": "xxxx",
      "secret": "xxxx",
      "password": "abcDEF"
      "base_currency": "USDT",
      "options": {
         "defaultType": "swap",
      }
   }
}
```
````

### Mainnet and Testnet Configurations
If you have api keys for an exchanges mainnet and testnet, you 
can include both in your `keys.yaml` file using the format shown
below. The `mainnet` configuration is used when the 
[`environment`](autotrader-configure) is set to `"live"`, while 
the `testnet` configuration is used when it is set to `"paper"`.

```yaml
CCXT:EXCHANGE:
  mainnet:
    api_key: "xxxx"
    secret: "xxxx"
    password: "abcDEF"
    base_currency: "USDT"
    options:
      defaultType: "swap"
  testnet:
    api_key: "yyyy"
    secret: "yyyy"
    password: "ABC123"
    base_currency: "USDT"
    options:
      defaultType: "swap"
```


## API Reference
```{eval-rst}
.. autoclass:: autotrader.brokers.ccxt.Broker
   :members:
   :private-members:
```
