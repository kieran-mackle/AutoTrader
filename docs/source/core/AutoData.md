(autodata-docs)=
# AutoData



`autotrader.lib.autodata`

AutoData is used to fetch price data of a requested instrument. It currently supports data retrieval
from Oanda and Yahoo Finance. Note that an account is required to fetch data from Oanda. Read more 
about AutoTrader's [supported brokers](brokers).

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