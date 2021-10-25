# AutoTrader Changelog

## Version 0.4.0
- Livetrade mode now supports bot detachment, so that bots will trade until
  a termination signal is received. This is achieved through the bot manager.
- Data time alginment can optionally be disabled
- Various plotting improvements

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
