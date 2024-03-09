# AutoTrader API


```{toctree}
:maxdepth: 3
:hidden:
   
AutoTrader <AutoTrader>
AutoPlot <AutoPlot>
AutoBot <AutoBot>
Utilities <utilities>
```


This page provides a top-level overview of AutoTrader, and how 
everything is tied together.


## Module Overview
The table below provides a summary of the modules available.

| Module | Description | 
| :----: | ----------- |
| [AutoTrader](autotrader-docs) | The primary API, used for all trading purposes. |
| [AutoPlot](autoplot-docs) | The automated plotting tool, used by AutoTrader and for manual use. |
| [AutoBot](autobot-docs) | A trading bot, used to manage data and run strategies. |
| [Utilities](utilities-module) | A collection of tools and utilities to make everything work. |




## Code Workflow
AutoTrader follows a logical procedure when running a trading strategy
(or multiple strategies). This is summarised in the flowchart below.
Note that the flowchart below exemplifies running two trading strategies 
with six instrument-strategy pairs (hence six trading bots). However, it
is possible to run AutoTrader with as many or as few strategies and 
instruments as you would like.

```{image} ../assets/images/light-code-workflow.svg
:align: center
:class: only-light
```

```{image} ../assets/images/dark-code-workflow.svg
:align: center
:class: only-dark
```



### User Input Files
To run AutoTrader, a [strategy module](trading-strategy), containing the 
trading strategy, is required. Each strategy module requires it's own 
[strategy configuration](strategy-config) file, containing the strategy 
parameters and strategy
watchlist. There is a second configuration file, the [global configuration](global-config) file, which is used 
conditionally. If you are live trading, you will need to create a global configuration 
file to provide brokerage account details. You will also need to do this if you wish to use a broker to obtain price data. 
If you will are only backtesting, you do not need 
to provide a global configuration file.


### AutoTrader
AutoTrader provides the the skeleton to your trading framework - read the 
complete documentation for it [here](autotrader-docs). In brief, 
AutoTrader loads each strategy, deploys trading bots, and monitors them
for as long as they are trading.

The mechanism by which the bots are deployed depends on the selected 
[run mode](autotrader-run-modes) of AutoTrader. Bots can either be 
periodically updated with new data, or run continuously without stopping.
When running periodically, the bots will be deployed each time the data 
is updated, and terminated after executing the strategy. 

### Broker API Connection
Each bot will also be connected to one or more [broker APIs](broker-interface). 
When they recieve a signal from the trading strategy, they will place 
an order with the broker. This modular structure allows for a seamless 
transition from backtesting to livetrading. 


(shutdown-routines-overview)=
### Shutdown Routines
AutoTrader also supports the inclusion of strategy-specific shutdown 
routines. This includes any processes you would like to run *after* 
your strategy is finished trading. This may include writing data to 
file, pickling the strategy instance, or sending termination emails. 
Read more about this functionality [here](strategy-shutdown-routine).

