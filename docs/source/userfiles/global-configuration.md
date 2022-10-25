(global-config)=
# Account Configuration
`config/keys.yaml`


In order to connect with your broker/exchange of choice, you must provide
the API keys. Keys can be kept in a `keys.yaml` file in your `config` directory, 
or passed directly to AutoTrader as a dictionary. To do the latter, use the 
[configure](autotrader-configure) method of AutoTrader. If you are keeping 
your keys in the `keys.yaml` file, AutoTrader will automatically find them.


## Example
Example account configuration structures are shown below. For exchange-specific
configuration keys, refer to the appropriate [docs](broker-interface).

```{tip}
A template `keys.yaml` file can be generated using the command
line interface! Simply run `autotrader init` in your home directory, 
and the template file will be created in the `config/` directory.
You can also find this template in the 
<a href="https://github.com/kieran-mackle/AutoTrader/blob/main/autotrader/data/keys.yaml" target="_blank">Github repository</a>.
```

````{tab} YAML File
```yaml
OANDA:
  LIVE_API: "api-fxtrade.oanda.com"
  LIVE_ACCESS_TOKEN: "12345678900987654321-abc34135acde13f13530"
  PRACTICE_API: "api-fxpractice.oanda.com"
  PRACTICE_ACCESS_TOKEN: "12345678900987654321-abc34135acde13f13530"
  DEFAULT_ACCOUNT_ID: "xxx-xxx-xxxxxxxx-001"
  PORT: 443

CCXT:EXCHANGE:
  api_key: "xxxx"
  secret: "xxxx"
  base_currency: "USDT"
```
````
````{tab} Dictionary Form
```python
keys_config = {
    "OANDA": {
        "LIVE_API": "api-fxtrade.oanda.com",
        "LIVE_ACCESS_TOKEN": "12345678900987654321-abc34135acde13f13530",
        "PRACTICE_API": "api-fxpractice.oanda.com",
        "PRACTICE_ACCESS_TOKEN": "12345678900987654321-abc34135acde13f13530",
        "DEFAULT_ACCOUNT_ID": "xxx-xxx-xxxxxxxx-001",
        "PORT": 443,
    },
    "CCXT:EXCHANGE": {"api_key": "xxxx", "secret": "xxxx", "base_currency": "USDT"},
}
```

To pass the keys dictionary to AutoTrader, use 
`at.configure(global_config=keys_config)`.

````

