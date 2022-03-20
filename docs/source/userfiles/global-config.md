(global-config)=
# Account Configuration

Account configuration is achieved through the global configuration. This can be kept in a yaml file in your `config` 
directory, or passed directly to AutoTrader as a dictionary. To do the latter, use the [configure](autotrader-configure)
method of AutoTrader.


## Example
The contents of the global configuration are provided in the templates below. As more [brokers](broker-interface)
are integrated into AutoTrader, account details will be added in this file.

````{tab} YAML File
```yaml
OANDA:
  LIVE_API: "api-fxtrade.oanda.com"
  PRACTICE_API: "api-fxpractice.oanda.com"
  ACCESS_TOKEN: "12345678900987654321-abc34135acde13f13530"
  DEFAULT_ACCOUNT_ID: "xxx-xxx-xxxxxxxx-001"
  PORT: 443

EMAILING:
  HOST_ACCOUNT:
    email: "host_email@domain.com"
    password: "host_email_password"
  MAILING_LIST:
    FIRST_LASTNAME:
      title: "Mr/Mrs"
      email: "your_email@domain.com"
```
````
````{tab} Dictionary Form
```python
global_config = {'OANDA': {'LIVE_API': 'api-fxtrade.oanda.com',
                           'PRACTICE_API': 'api-fxpractice.oanda.com',
                           'ACCESS_TOKEN': '12345678900987654321-abc34135acde13f13530',
                           'DEFAULT_ACCOUNT_ID': 'xxx-xxx-xxxxxxxx-001',
                           'PORT': 443},
                 'EMAILING': {'HOST_ACCOUNT': {'email': 'host_email@domain.com',
                                               'password': 'host_email_password'},
                              'MAILING_LIST': {'FIRST_LASTNAME': {'title': 'Mr/Mrs',
                                                                  'email': 'your_email@domain.com'}}
                              }
                 }
```
````

### Brokerage Account Details
Brokerage account details are added to the global configuration under a key corresponding to the brokerage. The example shown
above is for [Oanda](https://developer.oanda.com/rest-live-v20/introduction/), but as more brokers are integrated into AutoTrader,
they will be added in a similar manner. No configuration is required to use the Yahoo Finance API.


### EMAILING
If you would like to recieve [email notifactions](emailing-utils), you will need to set up a host email account 
for AutoTrader to send emails from. The details of this host account are stored in the global config file under the `HOST_ACCOUNT` 
field, as shown below. Next, you can provide a mailing list of people to send emails to. You can also provide a mailing list in the
strategy config file, in case you would like a different mailing list for different strategies.

