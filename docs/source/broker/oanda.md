(oanda-module-docs)=
# Oanda Broker API

`broker='oanda'`


## Supported Features

| Feature | Supported? | Alternative | 
| ------- | ---------- | ----------- |
| Stop loss | Yes | N/A |
| Take profit | Yes | N/A |


## Configuration

Trading through dYdX requires the following configuration details.

````{tab} keys.yaml configuration
```yaml
OANDA:
  LIVE_API: "api-fxtrade.oanda.com"
  PRACTICE_API: "api-fxpractice.oanda.com"
  ACCESS_TOKEN: "12345678900987654321-abc34135acde13f13530"
  DEFAULT_ACCOUNT_ID: "xxx-xxx-xxxxxxxx-001"
  PORT: 443
```
````
````{tab} Dictionary configuration
```python
{"OANDA":
   {
      "LIVE_API": "api-fxtrade.oanda.com",
      "PRACTICE_API": "api-fxpractice.oanda.com",
      "ACCESS_TOKEN": "12345678900987654321-abc34135acde13f13530",
      "DEFAULT_ACCOUNT_ID": "xxx-xxx-xxxxxxxx-001",
      "PORT": 443
   }
}
```
````


## API Reference

```{eval-rst}
.. autoclass:: autotrader.brokers.oanda.Broker
   :members:
   :private-members:
```

