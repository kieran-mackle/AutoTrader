# Click Trading with AutoTrader

Although AutoTrader is a platform for automated trading systems, it can
sometimes be useful to 'click trade' - a term used to describe manually 
trading. 




## Imports
All you need to get started is `AutoTrader` and the `Order` object.

```python
from autotrader import AutoTrader, Order
```


## Paper Click Trading

As a first example, lets look at papertrading, where we will use the virtual
broker to simulate trading on our exchange of choice. As usual, you must
configure the virtual trading account with the `virtual_account_config` method.
In the example below, we are simulating trading on 
[Binance](https://www.binance.com/en) throught the [CCXT](ccxt-module-docs)
integration. After creating a new instance of AutoTrader, configure it to
use `ccxt:binance` as the broker, then configure the virtual Binance account.
Here we are using 10x leverage.


### Start-Up

AutoTrader will go into manual mode whenever you call the `run` method without 
having added a strategy.

```python
at = AutoTrader()
at.configure(broker='ccxt:binance')
at.virtual_account_config(verbosity=1, exchange='ccxt:binance', leverage=10)
broker = at.run()
```

Notice that we now ask `at.run()` to return the broker instance created, and that
is exaclty what we get. 


[ what does it look like? What can we do? ]


```{tip}
While you are at it, why not spin up a [dashboard](dashboarding) to get a 
nice overview of your trading?
```


### Realtime Updates
To make this all possible, the virtual broker needs to have a constant data feed
from the exchange it is mirroring. When launching AutoTrader in manual papertrade
mode, a new thread is spawned to do this. This means that the broker instance(s)
created will constantly be updating in the background to see if any of your
orders should be filled, and to update the value of your positions.



### Shut-Down
When you are finished click trading, you should use the `shutdown` method to kill
the update threads and run the shutdown routine. After doing this, you will be 
shown a summary of your trades taken during the trading period.

```python
at.shutdown()
```

[ show trade results ]




## Live Click Trading

Now that we are live trading, we will also need to specify our API keys in a
`keys.yaml` file. 

```{tip}
You can use the [command line interface](cli) to initialise the `keys.yaml` file.
```

In this case, to make things a bit more interesting, lets connect to two exchanges
at once: Binance and dYdX.

```python
at = AutoTrader()
at.configure(verbosity=1, broker='ccxt:bitmex, dydx')
brokers = at.run()
```

Now, the object returned by `at.run()` is a dictionary with each broker instance.