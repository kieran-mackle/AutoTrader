# AutoTrader Changelog


## Version 0.5.0
Breaking change:
- virtual broker method 'get_open_positions' will now behave more as expected,
  returning the culmination of open trades for the specified instrument(s).
  Instead of returning a dictionary of open trades, a nested dictionary will
  be returned, containing the total position size held (long and short units),
  associated trade ID's and other information. 

Fixes:
- margin calculations for multi-instrument backtests
- fix: MTF None type handling when optimising
- fix: MTF assignment error when providing custom data file
- fix: Heikin Ashi overwriting inputted price data
- fix: trailing stop behaviour in virtual broker, when specifying stop loss as
  a price.
- fix: added v20 dependency
- fix: stop loss filter will only be applied when there is a stop loss
- fix: overwrite of keys in strategy parameters

Features:
- Multi-instrument backtest data checking: datasets with mis-matched lengths
  are automatically corrected to improve backtest reliability.
- improved docstrings
- feat: added pivot point plot method to AutoPlot
- feat: added resampling method to AutoPlot to allow for MTF plotting
- feat: MTF support for local files
- feat: new indicators: divergence detection
- feat: improved divergence indicators
- feat: new indicator: halftrend
- feat: improved robustness of generic indicator line plotting
- feat: added capability to plot multiple indicator lines on same figure

### 0.5.14
- fix: overwrite of keys in strategy parameters: risk_pc, granularity, sizing  
    and period. If these keys exist already, they will no longer be overwritten

### 0.5.13
- fix: data alignment verification method when using MTF data

### 0.5.12
- feat: added signal plotting method to IndiView ('type': 'signals')
- feat: improved multibot backtest axis labelling
- docs: changed virtual broker update order in backtest to improve order 
      executions

### 0.5.11
- fix: stop loss filter will only be applied when there is a stop loss

### 0.5.10
- feat: improved robustness of generic indicator line plotting
- feat: added capability to plot multiple indicator lines on same figure

### 0.5.9
- fix: added v20 dependency

### 0.5.8
- fix: trailing stop behaviour in virtual broker, when specifying stop loss as
  a price.
- feat: new indicator: halftrend

### 0.5.7
- fix: Heikin Ashi overwriting inputted price data

### 0.5.6
- feat: improved divergence indicators

### 0.5.5
- feat: new indicators: divergence detection

### 0.5.4
- feat: MTF support for local files

### 0.5.3
- fix: MTF assignment error when providing custom data file
- feat: added pivot point plot method to AutoPlot
- feat: added resampling method to AutoPlot to allow for MTF plotting

### 0.5.2
- fix: MTF None type handling when optimising

### 0.5.1
- fix: margin available will update upon initial deposit
- improved docstrings


## Version 0.4.0
- Livetrade mode now supports bot detachment, so that bots will trade until
  a termination signal is received. This is achieved through the bot manager.
- Data time alginment can optionally be disabled
- Various plotting improvements


### 0.4.27
- Feature: added trade unit precision method to oanda

### 0.4.26
- Changed links on pypi

### 0.4.25
- Added website/github link on pypi

### 0.4.24
- Added pip location method to Oanda API module

### 0.4.23
- Fix: rounding of position sizing in broker utils

### 0.4.22
- Fix: added small pause between opening new plot from scan results to 

### 0.4.21
- Added generic emailing method 'send_message' to easily send custom emails

### 0.4.20
- Added position retrieval from Oanda

### 0.4.19
- Plotting enhancements
- Improvements to scan mode

### 0.4.18
- various stream fixes

### 0.4.17
- Stream will check instrument of tick data to attempt to fix price bug

### 0.4.16
- Stream will run indefinitely until manually stopped, to ensure bots using 
stream will not be prematurely terminated

### 0.4.15
- Improved exception handling

### 0.4.14
- Ability to suspend bots and stream when livetrading. This is useful for 
  weekends / closed trading period, where trading is not possible, but you
  do not wish to kill an active bot.
- Various stream connection improvements
- Docstring improvements

### 0.4.13
- Added 3 second sleep when reconnecting to Oanda API

### 0.4.12
- fix typo in connection check

### 0.4.11
- Added connection check to Oanda module

### 0.4.10
- Major improvements to AutoStream
- Livetrade with data updates directly from stream
- If running in detached bot mode, must include initialise_strategy(data)
method in strategy module so that it can recieve data updates from the bot
- Must also have exit_strategy(i) method in strategy module, to allow safe
strategy termination from bot manager
