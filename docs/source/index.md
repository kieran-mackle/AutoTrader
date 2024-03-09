---
hide-toc: true
---

# AutoTrader Documentation

```{image} assets/images/logo1.svg
:align: center
:class: only-light
```
```{image} assets/images/logo2.svg
:align: center
:class: only-dark
```

AutoTrader is a Python-based trading framework for the development, 
optimisation and deployment of automated trading systems. Here you 
will find everything you need to start algotrading with AutoTrader.

If you are new to Python, you may find the tutorials especially 
useful. For those who like no details spared, refer to the 
[complete strategy walkthrough](tutorials/walkthrough), where a 
popular MACD trading strategy is built and tested. The 
[condensed walkthrough](tutorials/condensed-walkthrough) offers a 
more concise version of this tutorial.

If you are still deciding if AutoTrader is for you, check out the 
[feature showcase](features-landing) to see what on AutoTrader has 
to offer. Otherwise, head on over to the 
[Getting Started](getting-started) guide.


## Supported Brokers and Exchanges
AutoTrader supports integrations with the following brokers.

| Broker | Asset classes | Integration status | Docs page |
| -------- | ------------- | ------------------ | --------- |
| [Oanda](https://www.oanda.com/)    | Forex CFDs    | Complete | [link](oanda-module-docs)|
| [CCXT](https://github.com/ccxt/ccxt) | Cryptocurrencies | Complete | [link](ccxt-module-docs) |
| [Interactive Brokers](https://www.interactivebrokers.com/en/home.php) | Many | In progress | [link](ib-module-docs) |
<!-- | [dYdX](https://dydx.exchange/) | Cryptocurrencies | Complete | [link](dydx-module-docs) | -->


## Latest Changes
AutoTrader has gone through a full refactor to simplify the way things run.
Make sure to check out the [changelog](changelog) when upgrading
for details on the breaking changes and latest features.

## Index
Looking for something specific? Try the search bar on the left, or take a look through the 
{ref}`index <genindex>`.



```{toctree}
:hidden:

Getting Started <getting-started>
Feature Showcase <features/features>
```

```{toctree}
:maxdepth: 1
:caption: Using AutoTrader
:hidden:

Overview <tutorials/overview>
Condensed Walkthrough <tutorials/condensed-walkthrough>
Detailed Walkthrough <tutorials/walkthrough>
Miscellaneous <tutorials/misc/misc-tuts>
```

```{toctree}
:maxdepth: 2
:caption: Documentation
:hidden:
   
User Inputs <userfiles/userfiles>
AutoTrader API <core/core-modules>
Broker Interface <broker/broker-interface>
Communications Module <core/communications>
Indicator Library <indicators>
Command Line Interface <core/cli>
```


```{toctree}
:maxdepth: 2
:caption: Package Information
:hidden:

Change Log <changelog>
License <license>
```
