(getting-price-data)=
# Data Management

AuotTrader is compatible with all kinds of price data, regardless of the 
nature of the instrument being traded. This means that it can be used for 
stocks, cryptocurrencies, foreign exchange, futures, options, commodities 
and even Mars bars - provided that you can get historical price data 
for them. 

Luckily for you, AutoTrader is ready to automatically fetch data for 
various instruments from all of the 
[supported brokers and exchanges](supported-brokers) using 
[AutoData](autodata-docs). 
All you have to do is provide a few details in your 
[configuration files](userfiles), and AutoTrader will take care of 
the rest. 

Of course, if you would prefer to provide your own data, you can do this 
too. The default search path for local data is the `price_data` 
[directory](rec-dir-struc).



## For the MACD Strategy
For our MACD strategy, we have already done everything we need to do 
to automatically download price data for EUR/USD. Recall the
`INTERVAL` and `WATCHLIST` keys of our [strategy configuration file](macd-strat-config):

```yaml
# macd.yaml
INTERVAL: '1h'
WATCHLIST: ['EURUSD=X']
```

That's all we need to specify to automatically get 1-hour bars of price data
from Yahoo Finance API. Just note that the way the instrument is 
written (eg. 'EURUSD=X') will depend on the data feed you are using. In this case 
we will be using the Yahoo Finance API. As such, we must specify EUR/USD exactly as it appears on the 
[Yahoo Finance website](https://finance.yahoo.com/quote/EURUSD=X/).

Now that we have a way to pass data to our strategy, we are ready to start 
backtesting!

