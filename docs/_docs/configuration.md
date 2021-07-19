---
title: AutoTrader Configuration Files
---

# AutoTrader Configuration Files

Configuration files tell AutoTrader key information required to run.

There are two types of configuration files. The first is the global configuration file, used to specify information used 
throughout AutoTrader, such as mailing lists, account details and other personal information. The second is the strategy
configuration file, which provides all the parameters relating to your strategy. 
Each of these files are written in yaml.

Read more about these files below.


## Global Config 


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
      title: "Mr"
      email: "your_email@domain.com"
```


## Strategy config 


```
ENVIRONMENT: 'demo'

STRATEGY:
  MODULE: 'modulename'
  NAME: 'StrategyClassName'
  INTERVAL: 'M15'
  PERIOD: 300
  RISK_PC: 1
  SIZING: 'risk'
  PARAMETERS:
    ema_period: 200
    rsi_period: 14
    
    # Exit level parameters
    RR: 2
    stop_buffer: 10 # pips

# Define instruments to monitor
WATCHLIST: ['EUR_USD']

BACKTESTING:
  base_currency: 'AUD'
  initial_balance: 1000
  spread: 0.5
  commission: 0.005
  leverage: 30
  FROM: 1/1/2021
  TO: 1/7/2021
```



