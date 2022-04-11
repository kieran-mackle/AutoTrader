# Going Live with AutoTrader

Live trading is the [default trading medium](autotrader-mediums) of AutoTrader. As such, you are only 
required to specify the strategy configuration file along with any run 
[configuration](autotrader-config-methods) parameters to take a strategy live. 


## Live Runfile
To take our MACD strategy live, we would simply modify our run file by removing the `backtest` and
`optimise` calls, as shown below. 

```python
from autotrader import AutoTrader

at = AutoTrader()
at.configure(broker='oanda', feed='oanda')
at.add_strategy('macd')
at.run()
```

Using the [`configure`](autotrader-configure) method, we specify the broker and feed as `oanda`, indicating we will 
be trading with the Oanda API. This will automatically assign the Oanda API module as the broker, and use Oanda to 
retrieve price data. This is a very minimal run file, however there are more options available in the `configure` 
method. For example, we can specify the level of email verbosity via the `notify` input, so that you get an email 
for specific trading activity. Read more about the configuration method [here](autotrader-configure). 

If you have developed and backtested your strategy with AutoTrader, then it is likely that everything is set 
up already, and all you need to do differently to take your strategy live is modify the runfile as shown above.
Before doing this, double check the following requirements are met in each configuration file.
- Global Configuration: Specify all required account information in the 
[global configuration](global-config) corresponding to your 
brokerage account.
- Strategy Configuration: Ensure that the correct data period, data interval and trading instruments are
specified in your [strategy configuration](strategy-config). 


## Automated Running
Putting a strategy live will vary depending on if you are running AutoTrader in periodic or continuous mode.
In this tutorial, we developed the strategy to run in periodic mode, which was the original mode of AutoTrader.
Read about these modes [here](autotrader-run-modes).

### Periodic Mode
When running in periodic mode, you need a way to automatically run AutoTrader at whatever interval your strategy 
demands (as per the `INTERVAL` key of your strategy configuration). In theory, if you are running a strategy 
on the daily timeframe, you could manually run AutoTrader at a certain time each day, such as when the daily 
candle closes. To automate this, you will need some sort of job scheduler or automated run file.

If you are running on Linux, [cron](https://en.wikipedia.org/wiki/Cron) is a suitable option. Simply schedule 
the running of your run file at an appropriate interval, as dictated by your strategy. Alternatively, you could 
write the runfile above into a `while True:` loop to periodically run your strategy, using `time.sleep()` to 
pause between the periodic updates.


### Continuous Mode
Going live in continous mode is tremendously effortless. Specify how frequently you would like AutoTrader to 
refresh the data feed using the `update_interval` in the [`configure`](autotrader-configure) method, and 
run the file. Thats it! When you do this, you'll notice that AutoTrader will create an `active_bots/` directory,
and create an empty file each time you run an instance of AutoTrader live in continuous. To kill the trading 
bots associated with that instance, simply delete this file, and AutoTrader will stop running.

If you are running on a server, you might want to use [`nohup`](https://www.maketecheasier.com/nohup-and-uses/)
(short for 'no hangup') to prevent your system from stopping Python when you log out.

