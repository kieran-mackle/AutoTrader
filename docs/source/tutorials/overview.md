# AutoTrader Overview 
This page provides a high level overview of using AutoTrader.

## User Inputs
At a minimum, AutoTrader requires you to provide a trading 
[strategy](trading-strategy). Given
some data, your strategy is expected to output trading signals in the form
of [`Order`](order-object)s. This is normally enough for you to run a 
backtest on your strategy, but if you would like to trade live, you will 
also need to provide your trading account API keys in a 
[`keys.yaml`](global-config) file. It is also recommended that you bring 
your own data, but this isn't essential.

```{note}
With AutoTrader `v0.7`, you can also click trade. This means you can connect
to your broker without providing a strategy. See the tutorial 
[here](misc/click-trading.md) for more information.
```


## General Deployment Process
To make things go as smoothly as possible, you should generally set up
your instance of AutoTrader by calling the methods in the following order.


1. Create the AutoTrader instance

```python
at = AutoTrader()
```

2. Configure the AutoTrader instance

```python
at.configure()
```

3. (Optional) Add a trading strategy (or strategies)

```python
at.add_strategy()
```

4. (Optional) Add data

```python
at.add_data()
```

4. (Optional) Configure virtual account (for backtesting and paper trading)

```python
at.virtual_account_config()
```

5. (Optional) Configure backtest (for backtesting)

```python
at.backtest()
```

6. Run AutoTrader

```python
at.run()
```



(rec-dir-struc)=
## Recommended Directory Organisation
If you are just getting started with AutoTrader, it is recommended that you
use the directory structure shown below when developing your strategies. This
structure includes a `config/` directory (containing your configuration 
files) and a `strategies/` directory (containing your 
[trading strategies](../userfiles/strategy)). When you run AutoTrader, it will 
look for the appropriate files under these directories. If you cloned the demo 
repository, you will see these directories set up already. 

```{tip}
You can use the AutoTrader Command Line Interface to initialise your trading 
directory to this structure using `autotrader init`.
```

```
your_trading_project/
├── runfile.py                      # Run script to deploy trading bots
├── config 
│   ├── GLOBAL.yaml                 # Global configuration file
│   ├── strategy1_config.yaml       # Strategy 1 configuration file
│   └── strategy2_config.yaml       # Strategy 2 configuration file
├── price_data
|   ├── dataset1.csv                # Local OHLC dataset
│   └── dataset2.csv                # Another dataset
└── strategies
    ├── strategy1.py                # Strategy 1 module, containing strategy 1 logic
    └── strategy2.py                # Strategy 2 module, containing strategy 2 logic
```


(trading-environments)=
## Trading Environments
There are two trading environments: `paper` and `live`. The environment 
being used can be specified in the [`configure`](autotrader-configure) 
method, but it will be overwritten to `paper` any time you call the
[virtual account configuration](autotrader-virtual-account-config) method.

### Paper Trading
`environment="paper"`

Paper trading can fall into one of two categories:
- fully simulated trading via the [virtual broker](virtual-broker-docs), or;
- demo trading via an exchange/broker's dedicated demo API.

If the exchange you wish to use offers a "demo" trading API (or testnet
on crypto-specific exchanges), this can be a good way to test that all
the required functionality of your strategy is supported by the exchange. It
should always be an intermediate step before deploying your strategy live. 
Simply make sure that you have provided the appropriate API keys in your
[account configuration file](global-config).

In some instances, the liquidity available on testnet API's is not reflective
of that on the live exchange. In this case, you will not get a good indication
of your strategy's performance. For this purpose, using the capabilities of the
[virtual broker](virtual-broker-docs) to simulate trading is the way to go. To
activate this functionality, simply configure a virtual trading account via the
[virtual account configuration](autotrader-virtual-account-config) method. 


### Live Trading
When you are ready to deploy your strategy with real money, set the `environment`
argument in the [`configure`](autotrader-configure) method to `live`. This will
switch all of the API pointers to the live endpoints, and fire your orders to
the live platforms. When Autotrader is running in livetrade mode, you will
see this indicated as shown below.


```{image} ../assets/images/livetrade-banner.png
:align: center
```
