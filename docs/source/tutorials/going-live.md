# Going Live with AutoTrader


Live trading is the [default run mode](../docs/autotrader) of AutoTrader. As such, you are only 
required to specify the strategy configuration file along with any run 
[configuration](../docs/autotrader#configuration-methods) parameters. 


## Live Runfile
To take our MACD strategy live, we would modify our run file to the code shown below. 

```python
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(feed='oanda', account_id = 'xxx-xxx-xxxxxxxx-001')
at.add_strategy('macd')
at.run()
```

Using the `configure` method, we specify the feed as `oanda`, indicating we will be trading with the Oanda API.
This will automatically assign the Oanda API module as the broker, and use Oanda to retrieve price data. We also
provide our account ID here, which corresponds to our Oanda sub-account. 

This is a very minimal run file, however there are more options available in the `configure` method. For example, 
we can specify the level of email verbosity via the `notify` input, so that you get an email for specific trading 
activity. Read more about the configuration method [here](../docs/autotrader#configuration-methods). 


## Bot Deployment
If you have developed and backtested your strategy with AutoTrader, then it is likely that everything is set 
up already, and all you need to do differently to take your strategy live is modify the runfile as shown above.
Before doing this, double check the following requirements are met in each configuration file.

### Global Configuration
Specify all required account information in the [global configuration](../docs/configuration-global) file
corresponding to your brokerage account.

### Strategy Configuration
Ensure that the correct data period, data interval and trading instruments are specified in your 
[strategy configuration](../docs/configuration-strategy) file. 


## Automated Running
When you run AutoTrader in live-trade mode, it will analyse the current market conditions according to your
strategy and either do nothing, or submit an order to your broker. As such, you need a way to automatically run
AutoTrader at whatever interval your strategy demands (as per the `INTERVAL` key of your strategy configuration). 
In theory, if you are running a strategy on the daily timeframe, you could manually run AutoTrader at a certain 
time each day, such as when the daily candle closes. However, this will become tedious, especially when running 
a strategy on lower timeframes. To solve this, you will need some sort of job scheduler or automated run file.

If you are running on Linux, [cron](https://en.wikipedia.org/wiki/Cron) is a suitable option. Simply schedule 
the running of your run file at an appropriate interval, as dictated by your strategy. 

Alternatively, you could write a wrapper script in python to periodically run your strategy.

