# Oanda Broker API


`autotrader.brokers.oanda.Oanda`


AutoTrader currently supports interaction with the [OANDA REST-v20 API](https://developer.oanda.com/rest-live-v20/introduction/).
This is currently the preffered API for trading foreign exchange currencies. To use this API with AutoTrader, add your Oanda API
account details to the [global configuration](configuration-global) and specifiy 'Oanda' as the `FEED` in your 
[strategy configuration](configuration-strategy) file.


## Configuration
Include the following yaml in your [global configuration](configuration-global) file.

```yaml
OANDA:
  LIVE_API: "api-fxtrade.oanda.com"
  PRACTICE_API: "api-fxpractice.oanda.com"
  ACCESS_TOKEN: "12345678900987654321-abc34135acde13f13530"
  DEFAULT_ACCOUNT_ID: "xxx-xxx-xxxxxxxx-001"
  PORT: 443
```


## Attributes

|   Attribute   | Description (default)                                                                     |
| :-----------: | ----------------------------------------------------------------------------------------- |
| `ACCOUNT_ID`  | The Oanda account ID.                                                                     |
| `api`         | The v20 API context.                                                                      |



## Methods


|           Method          | Function                                                                                              |
| :-----------------------: | ----------------------------------------------------------------------------------------------------- |
|         `__init__`        | Creates Oanda v20 context and connects to API.                                                        |
|        `get_price`        | Fetches current price data for currency pair (bid, ask, and home conversion factors).                 |
|       `place_order`       | Places trade order through API and verifies API response.                                             |
|        `get_data`         | Retrieves and returns candlestick price data for specified granularity and time range.                |
|      `get_balance`        | Returns account balance.                                                                              |
|     `get_positions`       | Returns positions currently held by the account.                                                      |
|      `get_summary`        | Returns account summary.                                                                              |
|    `close_position`       | Closes a position held by the account.                                                                |
|     `get_precision`       | Returns the allowable price precision for a specified currency pair.                                  |
|    `check_precision`      | Checks and modifies stop and take target to meet required ordering precision.                         |
|      `check_response`     | Checks API response and returns message.                                                              |
|      `update_data`        | Attempts to manually update candlestick data by fetching data on a reduced timeframe.                 |
|  `get_historical_data`    | Retrieves and returns data from a historical time range.                                              |
| `deconstruct_granularity` | Deconstructs granularity string and converts to time in seconds.                                      |
| `get_reduced_granularity` | Returns a candlestick granularity as a fraction of a specified granularity.                           |


## Utility Functions

Refer to the [Oanda Utility Functions](oanda-utils) for more information.
