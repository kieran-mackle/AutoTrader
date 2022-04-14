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


## Latest Changes
AutoTrader `v0.6.0` has been released! This release has too many new features to list here, so 
check out the [changelog](changelog) for more details. Major changes include:
- Support for Interactive Brokers
- Introduction of `Order`, `Trade` and `Position` objects
- Continuous update mode
- Greater flexibility in deploying trading bots (ability to add strategy class object, add DataStream object
  for custom data pipelines)
- Tests and templates added


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
