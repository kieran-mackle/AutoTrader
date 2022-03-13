(getting-price-data)=
# Getting Price Data


AuotTrader is compatible with all kinds of price data, regardless of the nature of the security being traded. This means that
it can be used for stocks, cryptocurrencies, foreign exchange, futures, options, commodities and even Mars bars - provided that 
you can get historical price data for them. Luckily for you, AutoTrader is capable of retrieving price data for 
[supported instruments](../supported-api) automatically using the utility function [AutoData](autodata-docs). All you have 
to do is provide a few details in the [user configuration files](userfiles) and runfile, and AutoTrader will take care of 
the rest. If you would prefer to provide your own price data, you can also pass a `.csv` file with your data to AutoTrader.

## For the MACD Strategy
For our MACD strategy, we have already done everything we need to do to automatically download price data for EUR/USD. Recall the
`INTERVAL` and `WATCHLIST` keys of our [strategy configuration file](strategy#strategy-configuration):

```yaml
INTERVAL: '1h'
WATCHLIST: ['EURUSD=X']
```

That's all we need to specify to automatically get 1-hour price data! Just note that the way the instrument is written (eg. 'EURUSD=X') 
will depend on the data feed you are using. In this case - and by default - we are using the Yahoo Finance API. As such,
we must specify EUR/USD exactly as it appears on the [Yahoo Finance website](https://finance.yahoo.com/quote/EURUSD=X/). The format
of the `INTERVAL` key is also feed-specific. Read more about that [here](../docs/autodata#candlestick-granularity-format-1).

While that is all you need to know for this section of the tutorial, feel free to read on about AutoData below. Otherwise,
continue with the tutorial [here](backtesting).


## AutoData
AutoData is the automated data retrieval module of AutoTrader. It currently supports the Yahoo Finance and Oanda data feeds. 
Which feed you use depends on the type of instruments you wish to trade, and/or the broker you are using. For detailed documenation
of *AutoData*, refer to the [docs](autodata-docs).


### Yahoo Finance API
For preliminary strategy development, the Yahoo Finance API ([yfinance](https://pypi.org/project/yfinance/)) is most convenient. This
is because it does not require any broker accounts or sign-ups. It supports:
- Stocks
- Indices
- Commodities
- Foreign Exchange Currencies
- Cryptocurrencies

An obvious limitation of this API is that is does not support live trading, only data retrieval. To access the Yahoo Finance API,
use the `feed` 'yahoo'. Note, however, that this is the default feed of AutoTrader, so it does not need to be explicitly requested.

An important requirement of using the Yahoo Finance API is the correct specification of instruments in the `WATCHLIST` 
field of the strategy file. Instrument tickers must be specified exactly as they appear on 
[Yahoo Finance](https://finance.yahoo.com/). For example, 
[BTC/USD](https://au.finance.yahoo.com/quote/BTC-USD?p=BTC-USD&.tsrc=fin-srch) must be specified as `'BTC-USD'`, and stocks in 
[Woolworths on the ASX](https://au.finance.yahoo.com/quote/WOW.AX?p=WOW.AX&.tsrc=fin-srch) must be specified as `'WOW.AX'`.


### Oanda v20 REST API
For those interested in trading in the foreign exchange, the 
[OANDA REST-v20 API](https://developer.oanda.com/rest-live-v20/introduction/) will be of more interest. This API supports:
- Foreign Exchange Currencies
- Indices
- Bitcoin
- Commodities
- Bonds
- Metals


This data feed can be accessed by specifying the feed as 'oanda'. Note that to use the this API, you must also 
[make an account](https://www.oanda.com/au-en/trading/), obtain your API credentials, and specify them in the 
[global configuration](global-configuration) file. These details will look somthing like those shown below.

```yaml
OANDA:
  LIVE_API: "api-fxtrade.oanda.com"
  PRACTICE_API: "api-fxpractice.oanda.com"
  ACCESS_TOKEN: "12345678900987654321-abc34135acde13f13530"
  DEFAULT_ACCOUNT_ID: "xxx-xxx-xxxxxxxx-001"
  PORT: 443
```


### Providing your own data
If you have your own price data you would like to use, all you need to do is define the `data_file` attribute of AutoTrader. 
You must also place your data in a directory named 'price_data', within your strategy directory.

```python
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.data_file = 'price_data.csv' # Just the name of the file, not the full path
```

When using your own data, your directory structure will have to look something like this.

```
your_trading_project/
  |- config/
  |    |- GLOBAL.yaml
  |    |- your_strategy_config.yaml
  |- strategies/
  |    |- your_strategy.py
  |- price_data/
  |    |- AAPL.csv
  |    |- GOOG.csv
  |- run_script.py
```

### Multiple Timeframes
If you would like to provide your own data in multiple timeframes, use the `MTF_data_files` attribute of AutoTrader instead. In this case, you
will need to specify the data file names and granularity associated with them in a dictionary. For example, if you have 15-minute, hourly and 
daily data files, you would do something like shown below.

```python
at = AutoTrader()
at.MTF_data_files = {'15m': 'my_15min_data.csv', 
                     '1h', 'my_hourly_data.csv', 
                     '1d': 'my_daily_data.csv'}
```

Note, the keys you define in this dictionary will appear in the `data` dictionary provided to your strategy. Read more about using MTF data in 
the strategy configuration docs
[here](https://kieran-mackle.github.io/AutoTrader/docs/configuration-strategy#overview-of-options).

