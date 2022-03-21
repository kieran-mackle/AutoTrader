(autodata-docs)=
# AutoData

AutoData is the automated data retrieval module of AutoTrader. It enables fetching both historical and live 
price data from the [supported brokers](supported-brokers). You can also use AutoData to load locally stored
data. As with the [broker interface](broker-interface) of AutoTrader, the methods of AutoData are standardised
as much as possible, to make switching brokers a seamless process.

The AutoData module contains the class `GetData`. There are two public methods for each supported 
[data feed](autotrader-configure). The first is used to fetch historical price data, and so returns a Pandas
DataFrame of the Open, High, Low and Close prices. The second is used to fetch the live price of an instrument,
and returns the current bid and ask prices in a dictionary. If the feed supports it, the home conversion factors
will also be returned.


## GetData Class
AutoData's class `GetData` is optionally initialised with a broker configuration dictionary, the output of 
the utility function [`get_config`](utils-get-config). This dictionary contains all the essential information 
related to the API being used for data feeds and trading actions, and is automatically constructed from the 
[global configuration](global-config).




## Yahoo Finance API
`feed = 'yahoo'`

```{warning}
Data from Yahoo Finance is lagged. Decide if this is appropriate to use for your strategy.
```

```{eval-rst}
.. automethod:: autotrader.autodata.GetData.yahoo
```

```{eval-rst}
.. automethod:: autotrader.autodata.GetData.yahoo_liveprice
```


## Oanda v20 REST API
`feed = 'oanda'`

```{eval-rst}
.. automethod:: autotrader.autodata.GetData.oanda
```


```{eval-rst}
.. automethod:: autotrader.autodata.GetData.oanda_liveprice
```


## Interactive Brokers
`feed = 'ib'`

```{eval-rst}
.. automethod:: autotrader.autodata.GetData.ib
```


```{eval-rst}
.. automethod:: autotrader.autodata.GetData.ib_liveprice
```


## Using Locally-Stored Data
When the [`add_data`](autotrader-add-data) method of AutoTrader is called, local data will be used in the 
active instance. In this case, the `local` method of `GetData` will be called.

```{eval-rst}
.. automethod:: autotrader.autodata.GetData.local
```

Since there is no API to get the bid and ask price from when using local data, the private method 
`_pseudo_liveprice` is used. 




(autodata-candle-granularity)=
## Feed-Specific Parameter Formats
The format of the instrument and granularity strings provided to the methods of `GetData` are 
specific to the data feed being used. Refer to the websites of the feed being used for more
information.


| Feed | Example Instrument | Example granularity |
|------|--------------------|---------------------|
|yahoo | ['EURUSD=X'](https://finance.yahoo.com/quote/EURUSD=X/) | '30m' |
|oanda | ['EUR_USD'](https://developer.oanda.com/rest-live-v20/primitives-df/#InstrumentName) | ['M30'](https://developer.oanda.com/rest-live-v20/instrument-df/) |




## Usage
The AutoData module is automatically called when running AutoTrader. However, it may 
also be called to fetch price data manually. The code snippet below can be used to fetch 
price data for EUR/USD from Yahoo finance.

```python
from autotrader.lib.autodata import GetData

# Instantiate GetData class
get_data = GetData()

# Get price data for EUR/USD
instrument = 'EURUSD=X'
data = get_data.yahoo(instrument, '1h', 
                      start_time='2020-01-01', 
                      end_time='2020-08-01')
```