---
hide-toc: true
---

# Welcome to AutoTrader's Documentation

AutoTrader is a cross-exchange trading platform designed to help in the development, optimisation and live 
deployment of automated trading systems. Here you will find everything you need to start 
algotrading with AutoTrader.

A basic level of experience with Python is recommended, but the documentation here 
aims to be clear enough that a beginner is able to pick up the key components as they go. If you are 
new to Python, you may find the tutorials especially useful. There is even a 
[complete walkthrough](tutorials/walkthrough), where a popular MACD trading strategy is built and tested.

If you are still deciding if AutoTrader is for you, check out the [features](features-landing) to 
see what is on offer. Otherwise, head on over to the [Getting Started](getting-started) guide.


## Supported Exchanges
With AutoTrader `v0.7.0`, you can access over 100 cryptocurrency exchanges thanks to the integration
with [CCXT](https://github.com/ccxt/ccxt).

| Exchange | Asset classes | Integration status | Docs page |
| -------- | ------------- | ------------------ | --------- |
| [Oanda](https://www.oanda.com/)    | Forex CFDs    | Complete | [link](oanda-module-docs)|
| [Interactive Brokers](https://www.interactivebrokers.com/en/home.php) | Many | In progress | [link](ib-module-docs) |
| [dYdX](https://dydx.exchange/) | Cryptocurrencies | Complete | [link](dydx-module-docs) |
| [CCXT](https://github.com/ccxt/ccxt) | Cryptocurrencies | In progress | [link](ccxt-module-docs) |



## Latest Changes
AutoTrader `v0.7.0` has been released! Make sure to check out the [changelog](changelog) when upgrading details on the breaking changes. 


## Contact
If you have any other queries or suggestions, please [raise an issue](https://github.com/kieran-mackle/AutoTrader/issues)
on GitHub or send me an [email](mailto:kemackle98@gmail.com).


## Index
Looking for something specific? Try the search bar on the left, or take a look through the 
{ref}`index <genindex>`.



```{toctree}
:hidden:

Getting Started <getting-started>
Features <features/features>
```

```{toctree}
:maxdepth: 2
:caption: Tutorials
:hidden:

Detailed Walkthrough <tutorials/walkthrough>
Condensed Walkthrough <tutorials/condensed-walkthrough>
Miscellaneous <tutorials/misc/misc-tuts>
```

```{toctree}
:maxdepth: 2
:caption: API Documentation
:hidden:
   
User Input Files <userfiles/userfiles>
Core Modules <core/core-modules>
Broker Interface <broker/broker-interface>
Indicator Library <indicators>
Communications <comms>
Utilities <utilities>
```

```{toctree}
:maxdepth: 2
:caption: Package Information
:hidden:

Change Log <changelog>
License <license>
```
