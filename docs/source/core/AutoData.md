(autodata-docs)=
# AutoData

AutoData is the unified data retrieval module of AutoTrader. It enables fetching historical and live 
price data from the feeds of the [supported brokers](supported-brokers). You can also use AutoData to load locally stored
data.

The `autodata.py` module contains the class `AutoData`. This class has three public methods:
1. `fetch`: to fetch historical OHLC data
2. `L1`: to get a snapshot of level 1 data
3. `L2`: to get a snapshot of level 2 data


## AutoData Class
The `AutoData` class is optionally initialised with a broker configuration dictionary (either manually 
constructed, or the output of the utility function [`get_config`](utils-get-config). This dictionary 
contains any authentication information related to the data feed being used.

### Fetch historical OHLC data

```{eval-rst}
.. automethod:: autotrader.autodata.AutoData.fetch
```


### Get level 1 data

```{eval-rst}
.. automethod:: autotrader.autodata.AutoData.L1
```

### Get level 2 data

```{eval-rst}
.. automethod:: autotrader.autodata.AutoData.L2
```


### Accessing exchange endpoints

api attribute to allow accessing the unique API endpoints directly.


Granularities for all brokers can now be entered using a single unified format, according 
to pandas timestamp formatting. More intuitive and easier.

Make sure to update strategy config docs, since the granularity format is now feed independent.






## Using Locally-Stored Data
When the [`add_data`](autotrader-add-data) method of AutoTrader is called, local data will be used in the 
active instance. In this case, the `local` method of `GetData` will be called.

When using a local data feed, the `instrument` argument must correspond to the data filepath.




## Usage
The AutoData module is automatically called when running AutoTrader. However, it may 
also be called to fetch price data manually. The code snippet below can be used to fetch 
price data for EUR/USD from Yahoo finance.

```python
from autotrader import AutoData

# Instantiate AutoData
data_config = {'data_source': 'yahoo'}
datafeed = AutoData(data_config)

# Get price data for EUR/USD
instrument = 'EURUSD=X'
data = datafeed.fetch(instrument, granularity='1h', 
                      start_time='2020-01-01', 
                      end_time='2020-08-01')
```