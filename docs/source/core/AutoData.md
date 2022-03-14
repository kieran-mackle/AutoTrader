(autodata-docs)=
# AutoData


AutoData is the automated data retrieval module of AutoTrader.



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


```{warning}
Data from Yahoo Finance is lagged. Decide if this is appropriate to use for your strategy.
```


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











AutoData is used to fetch price data of a requested instrument. It currently supports data retrieval
from Oanda and Yahoo Finance. Note that an account is required to fetch data from Oanda. Read more 
about AutoTrader's [supported brokers](brokers).


(supported-data-feeds)=
## Supported Data Feeds


## Module
The attributes and methods of the AutoData module are detailed below. Note that the module contains a
class named `GetData`.

### Initialisation

```py
def __init__(self, broker_config=None, allow_dancing_bears=False)
```

AutoData's class `GetData` is optionally initialised with a broker configuration dictionary, the output of the 
[environment manager](environment-manager). This dictionary contains all the essential information 
related to the API being used for data feeds and trading actions. Note that if the Yahoo finance 
API is to be used, no broker configuration is required.

The broker configuration dictionary must contain the following.

```py
broker_config = {'data_source'    : data_source,
                 'API'            : api, 
                 'ACCESS_TOKEN'   : access_token, 
                 'ACCOUNT_ID'     : account_id, 
                 'PORT'           : port}
```



### Attributes
The attributes of `GetData` are presented in the table below.

| Attribute | Description |
| :-------: | ----------- |
|   `self.api` | The API context being used. |
| `self.allow_dancing_bears` | A boolean flag to allow incomplete candlesticks. |
| `self.home_currency` | The home currency of the account. |

Note that AutoData considers the home currency of the account being traded. This is so that backtest 
results can be displayed in terms of local currency units, rather than absolute units, which is 
especially useful for trading currencies. As a result of this, each data feed has an associated 
method to retrieve 'quote data', the price conversion data to convert from the currency being traded 
back to the home currency. 


### Oanda v20 REST API

When using the Oanda v20 API, instruments must be provided in the format of `XXX_YYY`, 
as specified in the [Oanda API documentation](https://developer.oanda.com/rest-live-v20/primitives-df/#InstrumentName). 
For example, to trade EUR/USD, specify as `EUR_USD`.




```{eval-rst}
.. automethod:: autotrader.autodata.GetData.oanda
```


To overcome the 5000 candle download limit when backtesting on extended time periods, a helper function `_get_extended_oanda_data` has
been defined. This function wraps around the main data retrieval function and incrementally builds upon the data to retrieve the
full time range requested.




#### Quote Data
Price conversion data is retrieved using the `oanda_quote_data` function. This function uses the `home_currency` attribute to 
determine whether or not conversion data is required.

```py
def oanda_quote_data(self, data, pair, granularity, start_time, end_time)
```

(autodata-candle-granularity)
#### Candlestick Granularity Format

Candlestick granularity must be passed as a string according to the format outlined in the  
[Oanda API documentation](https://developer.oanda.com/rest-live-v20/instrument-df/). Some
example formats are listed below.

> S5, S30, M1, M15, H1, H4, D, W, M






### Yahoo Finance API
The Yahoo Finance [API](https://pypi.org/project/yfinance/) is accessed from the function shown below.

```python
def yahoo(ticker, start_string, end_string, granularity=None)
```


#### Quote Data
```py
def yahoo_quote_data(self, data, pair, interval, from_date, to_date)
```


#### Candlestick Granularity Format

Candlestick granularity must be passed as a string according to the format outlined in the  
[Oanda API documentation](https://developer.oanda.com/rest-live-v20/instrument-df/).

> 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo.





### Utilities

#### JSON Response to DataFrame
Function to convert api response into a pandas dataframe.

```py
def response_to_df(self, response)
```





## Usage
The AutoData module is automatically called when running AutoTrader. However, it may 
also be called to fetch price data manually.

### Minimum Working Example
The code snippet below can be used to fetch price data for EUR/USD from Yahoo finance.

```py
from autotrader.lib.autodata import GetData

# Instantiate GetData class
get_data = GetData()

# Get price data for EUR/USD
instrument = 'EURUSD=X'
data = get_data.yahoo(instrument, '1h', 
                      start_time='2020-01-01', 
                      end_time='2020-08-01')
```