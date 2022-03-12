# Account Configuration

`./config/GLOBAL.yaml`

The global configuration file is read by AutoTrader when runnning the code. Depending on your 
[strategy config](configuration-strategy) file, some of the contents in the global configuration may be ignored. For example,
mailing lists or trading sub-accounts. Nonetheless, you may specify all your account details in this file once when getting started, 
and easily switch between brokers when required by specifying them in the strategy configuration file.


## Contents
The contents of the global configuration file are provided in the template below. As more [brokers](/AutoTrader/supported-api)
are integrated into AutoTrader, account details will be added in this file.

```
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


### Brokerage Account Details
Brokerage account details are added to the global configuration file under a key corresponding to the brokerage. The example shown
above is for [Oanda](https://developer.oanda.com/rest-live-v20/introduction/), but as more brokers are integrated into AutoTrader,
they will be added in a similar manner. No configuration is required to use the Yahoo Finance API.

Note that the `DEFAULT_ACCOUNT_ID` will be used to trade when `ACCOUNT_ID` is not provided in the [strategy configuration](configuration-strategy#account_id) file. 



### EMAILING
If you would like to recieve [email notifactions](emailing), you will need to [set up](../tutorials/host-email) a host email account 
for AutoTrader to send emails from. The details of this host account are stored in the global config file under the 'HOST_ACCOUNT' 
field, as shown below. Next, you can provide a mailing list of people to send emails to. You can also provide a mailing list in the
strategy config file, in case you would like a different mailing list for different strategies.

```
EMAILING:
  HOST_ACCOUNT:
    email: “ ”
    password: “ ”
  MAILING_LIST:
    Full_name
      title
      email: “ ”
```
