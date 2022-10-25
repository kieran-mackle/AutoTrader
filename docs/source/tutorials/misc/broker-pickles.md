# Pickling Broker Instances

In order to make simulated paper trading persistant, AutoTrader offers 
the ability to [pickle](https://docs.python.org/3/library/pickle.html) 
the instance of the virtual broker being used. This basically means
the current state of the broker is saved to file, so that it can be
loaded and resumed later.



```python
from autotrader import AutoTrader

# Instantiate AutoTrader
at = AutoTrader()
at.configure(broker='ccxt:binanceusdm')
at.virtual_account_config(
    verbosity=1, 
    exchange='ccxt:binanceusdm', 
    leverage=10,
    picklefile="binancepickle")
broker = at.run()
```



