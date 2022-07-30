(userfiles)=
# User Inputs

To use AutoTrader, you must provide three things:
1. A trading strategy,
2. The strategy configuration settings,
3. The account configuration parameters (trading account keys, etc.).

The first of these, the trading strategy, is written as a Python class, and contains 
the logic of your strategy - given a dataset, what trading signals can be extracted?

The strategy configuration tells AutoTrader the required information about how your 
strategy should be run. This included things like the minimum number of data points 
required to run your strategy, and which assets to trade with. It also contains 
strategy parameters which get passed to your strategy, which can be tuned to improve 
the performance of your strategy. 

Finally, the account configuration is required to connect to your broker and place 
orders. This is only required when live trading.


```{toctree}
:maxdepth: 3
:hidden:

Trading Strategy <strategy>
Strategy Configuration <strategy-configuration>
Account Configuration <global-configuration>
```