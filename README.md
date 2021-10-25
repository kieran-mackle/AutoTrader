<p align="center">
  <a href="https://kieran-mackle.github.io/AutoTrader/">
    <img src="https://user-images.githubusercontent.com/60687606/132320916-23445f43-dfdc-4949-9881-e18f622605d2.png" alt="AutoTrader Logo" width="15%" >
  </a>
</p>

<h1 align="center">AutoTrader</h1>

<p align="center">
  <a href="https://pypi.org/project/autotrader">
    <img src="https://img.shields.io/pypi/v/autotrader.svg?color=skyblue&style=for-the-badge" alt="AutoTrader version" width="120" height="30" >
  </a>
  
  <a href="https://pypi.org/project/autotrader">
    <img src="https://img.shields.io/pypi/dd/autotrader.svg?color=skyblue&style=for-the-badge" alt="PyPI downloads" width="160" height="30" >
  </a>
</p>


AutoTrader is Python-based platform intended to help in the development, optimisation and deployment of automated trading systems. 
From simple indicator-based strategies, to complex non-directional hedging strategies, AutoTrader can do it all. If you prefer a more hands-on 
approach to trading, AutoTrader can also assist you by notifying you of price behaviour, ensuring you never miss a signal again.
A basic level of experience with Python is recommended for using AutoTrader, but the [website](https://kieran-mackle.github.io/AutoTrader) 
aims to make using it as easy as possible with detailed tutorials.

## Features
- [Backtesting](https://kieran-mackle.github.io/AutoTrader/tutorials/backtesting), featuring multiple order types (market, limit, stop-limit, trailing stops, etc.) and the ability to **trade multiple instruments, multiple timeframes, and multiple strategies in the same backtest, against the same broker**
- [Integrated data feeds](https://kieran-mackle.github.io/AutoTrader/tutorials/price-data), such as Yahoo Finance (via [yfinance](https://pypi.org/project/yfinance/)) and Oanda v20 REST API
- [Automated interactive visualisation](https://kieran-mackle.github.io/AutoTrader/interactive-visualisation) using [Bokeh](https://bokeh.org/)
- [Built-in parameter optimisation](https://kieran-mackle.github.io/AutoTrader/tutorials/optimisation) using [scipy](https://docs.scipy.org/doc/scipy/reference/optimize.html)
- [Library of custom indicators](https://kieran-mackle.github.io/AutoTrader/docs/indicators)
- [Price streaming](https://kieran-mackle.github.io/AutoTrader/docs/autostream) through [Oanda v20 REST API](https://developer.oanda.com/rest-live-v20/introduction/)
- [Live trading](https://kieran-mackle.github.io/AutoTrader/supported-api) through [Oanda v20 REST API](https://developer.oanda.com/rest-live-v20/introduction/) (with support for more brokers coming soon!)
- [Email notification system](https://kieran-mackle.github.io/AutoTrader/docs/emailing)
- [Detailed documenation and tutorials](https://kieran-mackle.github.io/AutoTrader/tutorials/getting-autotrader)
- [Repository](https://github.com/kieran-mackle/autotrader-demo) of example strategies

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
AutoTrader is well documented on the [project website](https://kieran-mackle.github.io/AutoTrader/docs).

There is also a detailed [Quick Start Guide](https://kieran-mackle.github.io/AutoTrader/tutorials/getting-autotrader).

Examples can be found in the [demo repository](https://github.com/kieran-mackle/autotrader-demo).


## Demo Chart
The chart below is produced by a backtest of a MACD strategy (which can be found in the 
[demo repository](https://github.com/kieran-mackle/autotrader-demo)). Note that stop loss and take profit levels are shown for each trade taken. 
This allows you to see how effective your exit strategy is - are you being stopped out too early by placing your stop losses too tight? 
Are you missing out on otherwise profitable trades becuase your take profits are too far away? AutoTrader helps you visualise your strategy
and answer these questions.

[![MACD-backtest-demo](https://user-images.githubusercontent.com/60687606/128127659-bf81fdd2-c246-4cd1-b86d-ef624cac50a7.png)](https://kieran-mackle.github.io/AutoTrader/interactive-visualisation)

## License
AutoTrader is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

## Disclaimer
Never risk money you cannot afford to lose. Always test your strategies on a paper trading account before taking it live.
