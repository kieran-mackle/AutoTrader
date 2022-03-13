# Broker Utilities

*This page is currently in development. Check back soon!*

`autotrader.brokers.broker_utils`

The *broker_utils.py* module contains the `BrokerUtils` class, containing general utility methods 
for the broker API's.


## Methods

A summary of the methods contained with the `BrokerUtils` class is provided in the table below.

| Method | Description |
|:------:|-------------|
|`response_to_df`|Convert JSON Response to Pandas DataFrame.|
|`get_pip_ratio`|Function to return pip value ($/pip) of a given pair.|
|`get_size`|Calculate position size based on account balance and risk profile.|
|`truncate`|Truncates a float f to n decimal places without rounding.|
|`interval_to_seconds`|Converts the interval to time in seconds.|
|`trade_summary`|Compiles all trades into Pandas DataFrame.|
|`reconstruct_portfolio`|Reconstructs portfolio balance from trades taken.|
|`get_streaks`|Calculates longest winning and losing streaks.|


### Position Sizing
The position sizing utility `get_size` is automatically used whenever the 'risk' option is used for the 
`SIZING` method in the [strategy configuration](configuration-strategy#overview-of-options). This method
is a position size calculator similar to the one at [babypips](https://www.babypips.com/tools/position-size-calculator).

```
def get_size(self, pair, amount_risked, price, stop_price, HCF, stop_distance = None):
    ''' Calculate position size based on account balance and risk profile. '''
```
