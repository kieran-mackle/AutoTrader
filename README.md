# AutoTrader
AutoTrader is an event-driven platform intended to help in the development, optimisation and live deployment of automated trading systems. 
A basic level of experience with Python is recommended for using AutoTrader, but the [website](https://kieran-mackle.github.io/AutoTrader) 
aims to make using it as easy as possible with detailed tutorials.

## Features
- [Backtesting](https://kieran-mackle.github.io/AutoTrader/tutorials/backtesting), with multiple order types supported (market order, limit orders, stop-limit orders, trailing stops, etc.)
- [Integrated data feeds](https://kieran-mackle.github.io/AutoTrader/tutorials/price-data), such as Yahoo Finance (via [yfinance](https://pypi.org/project/yfinance/)) and Oanda v20 REST API
- [Interactive visualisation](https://kieran-mackle.github.io/AutoTrader/interactive-visualisation) using [Bokeh](https://bokeh.org/)
- [Built-in parameter optimisation](https://kieran-mackle.github.io/AutoTrader/tutorials/optimisation) using [scipy](https://docs.scipy.org/doc/scipy/reference/optimize.html)
- [Library of custom indicators](https://kieran-mackle.github.io/AutoTrader/docs/indicators)
- [Price streaming](https://kieran-mackle.github.io/AutoTrader/docs/autostream)
- [Live trading](https://kieran-mackle.github.io/AutoTrader/supported-api) through [Oanda v20 REST API](https://developer.oanda.com/rest-live-v20/introduction/)
- [Email notification system](https://kieran-mackle.github.io/AutoTrader/docs/emailing)

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

## Demo Chart
The chart below is produced by a backtest of a MACD strategy. Note that stop loss and take profit levels are shown for each trade taken. 
This allows you to see how effective your exit strategy is - are you being stopped out too early by placing your stop losses too tight? 
Are you missing out on otherwise profitable trades becuase your take profits are too far away? AutoTrader helps you visualise your strategy
and answer these questions.

[![MACD-backtest-demo](https://user-images.githubusercontent.com/60687606/128127659-bf81fdd2-c246-4cd1-b86d-ef624cac50a7.png)](https://kieran-mackle.github.io/AutoTrader/interactive-visualisation)

## License
AutoTrader is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).
