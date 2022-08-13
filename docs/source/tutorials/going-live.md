# Live Trading with AutoTrader
If you have a strategy and have been able to run a backtest on it,
you are able to take it live with no extra effort. Live trading is
also known as 'forward testing', since you are running the strategy
in real-time. You can do this in two different environments:

1. A simulated environment, where trades are simulated in real-time 
("paper trading")
2. The live environment, where trades are submitted to real brokers
and exchanges for execution with real money.

If you want to do the latter, you will need to make sure you have your
API keys defined in your [`keys.yaml` file](global-config). This isn't 
necessary for paper trading, since the environment is completely 
simulated.


## Live Runfile
To take our MACD strategy live, we can modify the run file to that 
shown below. 

### Paper Trade with Virtual Broker

```python
from autotrader import AutoTrader

at = AutoTrader()
at.configure(verbosity=1, feed='yahoo',
             mode='continuous', update_interval='1h') 
at.add_strategy('macd') 
at.virtual_account_config(leverage=30)
at.run()
```

This will launch AutoTrader into live papertrade mode. Every 1 hour,
AutoTrader will refresh your strategy to get the latest signals. If
an order is recieved, it will be executed in the virtual broker. 

When you run AutoTrader in livetrade mode, it will create a new directory
named `active_bots`, and store a text file for each actively running 
AutoTrader instance. To kill an instance, simply delete the instance
file, or do a keyboard interrupt. You can open these files to remind 
yourself which strategy they are running. In the example above, a file 
named something like "autotrader_instance_1" will be created, and contain 
the following text.

```
This instance of AutoTrader contains the following bots:
Simple Macd Strategy (EURUSD=X)
```

What if you want to get a bit more accurate with your paper trading? 


### Paper Trade with Real Broker
Sometime brokers/exchanges offer a paper trading API endpoint, such as
Oanda. In this case, you can use their papertrading API to test your 
strategies in livetrade mode. What if the broker doesn't offer this?
In this case, AutoTrader can mirror the real-time orderbook of the 
exchange you would like to simulate, executing trades in an instance
of AutoTrader's virtual broker.

The runfile below is an example of papertrading on the crypto exchange
[dYdX](https://dydx.exchange/). The first difference is that we specify
the broker/exchange to trade on in the `configure` method using the 
`broker` argument. Since we would like to papertrade, we need to configure
the virtual account as before. Now, however, you should specify that the 
account you are configuring is for the 'dydx' exchange, as specified in 
the `configure` method. This is especially important when trading with 
multiple brokers at once. When setting up AutoTrader like this, the 
virtual broker will retrieve the real-time orderbook from 'dydx' 
in order to simulate trade execution.

```python
from autotrader import AutoTrader

at = AutoTrader()
at.configure(verbosity=1, broker='dydx',
             mode='continuous', update_interval='1h') 
at.add_strategy('macd') 
at.virtual_account_config(leverage=30, exchange='dydx')
at.run()
```



### Live Trade with Real Broker

If you are ready to trade directly on a real exchange, make sure you
have defined your API keys in the `keys.yaml` file. Then, set up your
run file like the one shown below. It is that easy.

```python
from autotrader import AutoTrader

at = AutoTrader()
at.configure(verbosity=1, broker='dydx',
             mode='continuous', update_interval='1h') 
at.add_strategy('macd')
at.run()
```

```{note}
If the broker you are trading on supports native paper trading (such as 
Oanda), you can use the same runfile shown above, but pass in 'paper'
as the `environment` argument to the `configure` method.
```




## Automated Running

If you are running on a server, you might want to use 
[`nohup`](https://www.maketecheasier.com/nohup-and-uses/) (short for 'no 
hangup') to prevent your system from stopping Python when you log out.

