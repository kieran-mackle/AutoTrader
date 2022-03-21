(autobot-docs)=
# AutoBot

Every time you run a strategy in AutoTrader, a trading bot (from the class `AutoTraderBot`), will be deployed for each 
instrument in your strategy's watchlist. Each trading bot is therefore responsible for trading a single instrument 
using the rules of a single strategy, until it is terminated. All methods of the `AutoTraderBot` class are private,
as it is unlikely you will ever need to call them as a user. However, you may want to use the bot instance for other
things, such as [backtest plotting](autotrader-plot-backtest). For this purpose, you can use the 
[`get_bots_deployed`](autotrader-bots-deployed) method of AutoTrader.



```{eval-rst}
.. autoclass:: autotrader.autobot.AutoTraderBot
   :members:
   :private-members:
```
