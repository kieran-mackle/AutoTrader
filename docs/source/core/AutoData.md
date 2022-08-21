(autodata-docs)=
# AutoData
`from autotrader import AutoData`

AutoData is the unified data retrieval module of AutoTrader. 
It enables fetching historical and live price data from the 
feeds of the [supported brokers](supported-brokers) (where 
available). You can also use `AutoData` to load locally stored
data. To configure AutoData, you must provide a `data_config` 
dictionary, specifying at least the data source. If you do
not provide this dictionary, AutoData will assume you will
be using local data.

AutoData has three main public methods:
1. `fetch`: to fetch historical OHLC data
2. `L1`: to get a snapshot of level 1 data
3. `L2`: to get a snapshot of level 2 data



## AutoData Class
The `AutoData` class is optionally initialised with a configuration 
dictionary (either manually constructed, or the output of the utility
function [`get_data_config`](utils-get-data-config). This dictionary 
contains any authentication information related to the data feed being 
used. Some samples are provided below.


````{tab} CCXT Exchange
```python
data_config = {
    'data_source': 'ccxt',
    'exchange': 'binance'
}
ad = AutoData(data_config)
```
````
````{tab} dYdX
```python
data_config = {
    'data_source': 'dydx',
}
ad = AutoData(data_config)
```
````
````{tab} Oanda
```python
data_config = {
    'data_source': "oanda",
    'API': "api-fxtrade.oanda.com",
    'ACCESS_TOKEN': "xxx-yyy",
    'PORT': 443,
    'ACCOUNT_ID': "xxx-xxx-xxxxxxxx-xxx",
}
ad = AutoData(data_config)
```
````


### Fetch historical OHLC data
To fetch OHLC price data, use the `fetch` method. 

```{eval-rst}
.. automethod:: autotrader.autodata.AutoData.fetch
```


### Get level 1 data
To retrieve a snapshot of the current level 1 data, use the 
`L1` method.

```{eval-rst}
.. automethod:: autotrader.autodata.AutoData.L1
```

### Get level 2 data
To retrieve a snapshot of the current level 2 data, use the 
`L2` method.

```{eval-rst}
.. automethod:: autotrader.autodata.AutoData.L2
```


### Accessing exchange endpoints
If you wish to access an endpoint of the feed-specific API, you can
do so through the `AutoData.api` attribute. This attribute gets created
when you instantiate AutoData with the `data_config` dictionary.

