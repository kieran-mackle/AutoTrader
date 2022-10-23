<p align="center">
  <a href="https://kieran-mackle.github.io/AutoTrader/">
    <img src="https://user-images.githubusercontent.com/60687606/132320916-23445f43-dfdc-4949-9881-e18f622605d2.png" alt="AutoTrader Logo" width="15%" >
  </a>
</p>

<h1 align="center">AutoTrader</h1>

<p align="center">
  <a href="https://pypi.org/project/autotrader">
    <img src="https://img.shields.io/pypi/v/autotrader.svg?color=blue&style=plastic" alt="Latest version" width=95 height=20>
  </a>
  
  <a href="https://pepy.tech/project/autotrader">
    <img src="https://pepy.tech/badge/autotrader/month" alt="Monthly downloads" >
  </a>
  
  <a>
    <img src="https://github.com/kieran-mackle/AutoTrader/actions/workflows/tests.yml/badge.svg" alt="Build Status" >
  </a>
  
  <a href='https://autotrader.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/autotrader/badge/?version=latest' alt='Documentation Status' />
  </a>
  
  <a href="https://github.com/psf/black">
    <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
  </a>
  
</p>



AutoTrader is Python-based platform intended to help in the development, optimisation and deployment of automated trading systems. 
A basic level of experience with Python is recommended for using AutoTrader, but the [docs](https://autotrader.readthedocs.io/en/latest/) 
aim to make using it as easy as possible with detailed tutorials and documentation.

## Latest News
- Version 0.7 has been released, adding integrations with [CCXT](https://github.com/ccxt/ccxt) and [dYdX](https://dydx.exchange/) crypto exchanges. Many more powerful upgrades too.
- AutoTrader has been featured in GitClone's recent article, [*Top Crypto Trader Open-Source Projects on Github*](https://gitclone.dev/top-crypto-trader-open-source-projects-on-github/).

## Features
- A feature-rich trading simulator, supporting [backtesting](https://autotrader.readthedocs.io/en/latest/features/backtesting.html) and 
papertrading. The 'virtual broker' allows you to test your strategies in a risk-free, simulated environment before going live. Capable 
of simulating multiple order types, stop-losses and take-profits, cross-exchange arbitrage and portfolio strategies, AutoTrader has 
more than enough to build a profitable trading system.
- [Integrated data feeds](https://kieran-mackle.github.io/AutoTrader/tutorials/price-data), making OHLC data retrieval as easy as possible.
- [Automated interactive visualisation](https://autotrader.readthedocs.io/en/latest/features/visualisation.html) using [Bokeh](https://bokeh.org/)
- [Library of custom indicators](https://autotrader.readthedocs.io/en/latest/indicators.html).
- [Live trading](https://autotrader.readthedocs.io/en/latest/features/live-trading.html) supported for multiple venues.
- [Detailed documenation and tutorials](https://autotrader.readthedocs.io/en/latest/index.html)
- [Repository](https://github.com/kieran-mackle/autotrader-demo) of example strategies

## Supported Brokers and Exchanges

| Broker | Asset classes | Integration status |
| -------- | ------------- | ------------------ |
| [Oanda](https://www.oanda.com/)    | Forex CFDs    | Complete |
| [Interactive Brokers](https://www.interactivebrokers.com/en/home.php) | Many | In progress |
| [dYdX](https://dydx.exchange/) | Cryptocurrencies | Complete |
| [CCXT](https://github.com/ccxt/ccxt) | Cryptocurrencies | In progress |


## Installation
AutoTrader can be installed using pip:
```
pip install autotrader
```
### Updating
AutoTrader can be updated by appending the `--upgrade` flag to the install command:
```
pip install autotrader --upgrade
```

## Documentation
AutoTrader is very well documented in-code and on [Read the Docs](https://autotrader.readthedocs.io/en/latest/). There is also a [detailed walthrough](https://autotrader.readthedocs.io/en/latest/tutorials/walkthrough.html), covering everything from strategy concept to livetrading.

### Example Strategies
Example strategies can be found in the [demo repository](https://github.com/kieran-mackle/autotrader-demo).


## Backtest Demo
The chart below is produced by a backtest of the MACD trend strategy documented in the 
[tutorials](https://autotrader.readthedocs.io/en/latest/tutorials/building-strategy.html) (and available in the 
[demo repository](https://github.com/kieran-mackle/autotrader-demo)). Entry signals are defined by MACD crossovers, with exit targets defined
by a 1.5 risk-to-reward ratio. Stop-losses are automatically placed using the custom
[swing detection](https://autotrader.readthedocs.io/en/latest/indicators.html#swing-detection) indicator, and position sizes are dynamically calculated based 
on risk percentages defined in the strategy configuration.

Running this strategy with AutoTrader in backtest mode will produce the following interactive chart. 

[![MACD-backtest-demo](https://user-images.githubusercontent.com/60687606/128127659-bf81fdd2-c246-4cd1-b86d-ef624cac50a7.png)](https://autotrader.readthedocs.io/en/latest/tutorials/backtesting.html#interactive-chart)

Note that stop loss and take profit levels are shown for each trade taken. This allows you to see how effective your exit strategy is - are you being stopped out too 
early by placing your stop losses too tight? Are you missing out on otherwise profitable trades becuase your take profits are too far away? AutoTrader helps you 
visualise your strategy and answer these questions.

## Legal 
### License
AutoTrader is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

### Disclaimer
This platform is currently under heavy development and should not be considered stable for livetrading until version 1.0.0 is released.

Never risk money you cannot afford to lose. Always test your strategies on a paper trading account before taking it live.
