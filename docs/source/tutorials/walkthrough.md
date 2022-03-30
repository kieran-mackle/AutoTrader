(detailed-walkthrough)=
# Detailed AutoTrader Walkthrough
The next few pages will walk you through building an algorithmic trading system in AutoTrader. There will also
be links to sections of relevant code documentation.

```{warning}
This walkthrough is intentionally very thorough and detailed. If you don't mind glossing over the finer details, 
the [condensed walkthrough](condensed-walkthrough) might be better suited for you.
```


(rec-dir-struc)=
## Directory Organisation
Before building a strategy in AutoTrader, it is important to understand the structure of a project. At a minimum, any 
strategy you run in AutoTrader requires two things: 
1. A strategy module, containing all the logic of your strategy, and
2. A configuration file, containing strategy configuration parameters.

If you plan to take your strategy [live](going-live), you will also need a [global configuration](global-config) 
file to connect to your broker, but we will get to that later. For now, the files above are enough to get started backtesting, so
this tutorial will go over setting them up.

Back to the recommended directory structure: you should have a `config/` directory - containing your configuration 
files - and a `strategies/` directory - containing your [trading strategies](../userfiles/strategy). When you 
run AutoTrader, it will look for the appropriate files under these directories. If you cloned the demo repository, 
you will see these directories set up already. Think of this directory structure as your 'bag' of algo-trading bots. 
Sticking to this will make path management super easy. Note, however, that you can also just directly provide the 
contents of each file to AutoTrader directly if preferred.

```
your_trading_project/
├── runfile.py                      # Run script to deploy trading bots
├── config 
│   ├── GLOBAL.yaml                 # Global configuration file
│   ├── strategy1_config.yaml       # Strategy 1 configuration file
│   └── strategy2_config.yaml       # Strategy 2 configuration file
└── strategies
    ├── strategy1.py                # Strategy 1 module, containing strategy 1 logic
    └── strategy2.py                # Strategy 2 module, containing strategy 2 logic
```

```{note}
AutoTrader has become even more flexible in version `0.6.0`. While the directory structure above is a good guide to 
keeping an organised system, it is no longer requied. You can now directly pass your strategy configuration as a `dict` object,
and your strategy logic as its class object.
```



```{toctree}
:maxdepth: 2
:hidden:

Building a Strategy <building-strategy>
Getting Price Data <getting-data>
Backtesting <backtesting>
Optimisation <optimisation>
Going Live <going-live>
```