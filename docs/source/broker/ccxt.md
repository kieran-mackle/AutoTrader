(ccxt-module-docs)=
# CCXT Exchange Interface
`broker=ccxt:exchange_name`

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



## API Reference
```{eval-rst}
.. autoclass:: autotrader.brokers.ccxt.broker.Broker
   :members:
   :private-members:
```
