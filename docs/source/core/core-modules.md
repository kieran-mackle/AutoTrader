# AutoTrader Core Modules



```{toctree}
:maxdepth: 3
:hidden:
   
AutoTrader <AutoTrader>
AutoData <AutoData>
AutoPlot <AutoPlot>
AutoBot <AutoBot>
```



Welcome to the AutoTrader Documentation. Everything you need to know about the code is documented here.
This page provides a top-level overview of the software, with links to documentation of each module.


## Code Workflow
AutoTrader follows a logical procedure when running a trading strategy. This is summarised in the flowchart below.
Note that the flowchart below exemplifies running two trading strategies with six instrument-strategy pairs (hence
six trading bots). However, it is possible to run AutoTrader with as many or as few strategies and instruments as 
you would like.

```{image} ../assets/images/light-code-workflow.svg
:align: center
:class: only-light
```

```{image} ../assets/images/dark-code-workflow.svg
:align: center
:class: only-dark
```



### User Input Files
To run AutoTrader, a [strategy module](trading-strategy), containing the trading strategy, is required. Each strategy module
requires it's own [strategy configuration](strategy-config) file, containing the strategy parameters and strategy
watchlist. There is a second configuration file, the [global configuration](global-config) file, which is used 
conditionally. If you are [live-trading](autotrader-livetrade-mode), you will need to create a global configuration 
file to provide brokerage account details. You will also need to do this if you wish to use a broker to obtain price data. 
If you will only be [backtesting](autotrader-backtest-mode) or [scanning](autotrader-scan-mode), you do not need 
to provide a global configuration file. In this case, [AutoData](autodata-docs) will revert to using the Yahoo Finance 
API for price data.

The global configuration file is also used to store email account details for [email notifications](emailing-utils).

### AutoTrader
AutoTrader is the brains behind the software - read the complete documentation for it [here](autotrader-docs). In brief,
it compiles each strategy and assigns a trading bot for each instrument in the strategy's watchlist (as defined in the 
[strategy configuration](strategy-config) file). Each of these bots will then monitor a single instrument
to trade it according to the strategy it has been assigned. 

The mechanism by which the bots are deployed depends on the update mode of AutoTrader. Bots can either be periodically
updated with new data, or connected to a data stream to run continuously. When running periodically, the bots will be 
deployed each time the data is updated, and terminated after executing the strategy. When connected to a price stream,
the bots will be deployed in detached-bot mode once only, trading continuously until a termination signal is received.
In most strategies, periodic update mode is adequate. 

### Broker API Connection
Each bot will also be connected to a [broker API](broker-interface). When they recieve a signal from the trading strategy,
they will place an order with the broker. This modular structure allows for a seamless transition from backtesting to 
livetrading. 

### Post-Processing
When [AutoTrader](autotrader-docs) has finished running its core processes, the relevant data will be passed on for 
post-processing. This includes, but is not limited to, visualisation of results, emailing order details, and logging
information where appropriate.


## Project Directory Structure
To ensure that AutoTrader finds your strategy and configuration files, your project's working 
directory must be structured according to the layout shown below. See the 
[demo repository](https://github.com/kieran-mackle/autotrader-demo/) for an example of this structure.

```
home_dir/
  |- config/
  |    |- GLOBAL.yaml
  |    |- your_strategy_config.yaml
  |- strategies/
  |    |- your_strategy.py
  |- run_script.py
```


## Useful Links
You can navigate the documentation using the sidebar, or start by following one of the links below.

[AutoTrader](autotrader-docs): Details of the main code.

[User Input Files](userfiles): Details of the user-provided files used to run AutoTrader.

[Broker Interface](broker-interface): Details of the brokers used in AutoTrader.

[Utilities](utilities-module): Details of the utility functions used in AutoTrader.