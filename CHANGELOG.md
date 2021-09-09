# AutoTrader Changelog

## Version 0.4.0
- Livetrade mode now supports bot detachment, so that bots will trade until
  a termination signal is received. This is achieved through the bot manager.
- Data time alginment can optionally be disabled
- Various plotting improvements

### 0.4.10
- Major improvements to AutoStream
- Livetrade with data updates directly from stream
- If running in detached bot mode, must include initialise_strategy(data)
method in strategy module so that it can recieve data updates from the bot
- Must also have exit_strategy(i) method in strategy module, to allow safe
strategy termination from bot manager