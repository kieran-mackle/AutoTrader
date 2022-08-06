# Click Trading with AutoTrader


## Imports

```python
from autotrader import AutoTrader, Order
```

## Paper Click Trading
```python
at = AutoTrader()
at.configure(broker='ccxt:binance', home_dir=home_dir)
at.virtual_account_config(verbosity=1, exchange='ccxt:binance', leverage=10)
broker = at.run()
at.shutdown()
```


## Live Click Trading
```python
at = AutoTrader()
at.configure(verbosity=1, broker='ccxt:bitmex, dydx')
brokers = at.run()
```

