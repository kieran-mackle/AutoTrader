(userfiles)=
# User Input Files

To use AutoTrader, users must define three things:
1. A trading strategy
2. The strategy configuration settings
3. The account configuration parameters

The first of these, the trading strategy, is written as a Python class, and contains the logic of your strategy.
The strategy configuration tells AutoTrader the required information about how your strategy should be run. It
also contains any strategy parameters, which can be tuned to improve the performance of your strategy. Finally,
the account configuration is required to connect to your broker and to configure anything else requiring log in
details.


```{toctree}
:maxdepth: 3
:hidden:

Trading Strategy <strategy>
Strategy Configuration <strategy-configuration>
Account Configuration <global-configuration>
```