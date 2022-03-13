(autobot-docs)=
# AutoBot


`autotrader.autobot`

When you run a strategy in AutoTrader, a trading bot, or `AutoBot`, will be deployed for each instrument in your strategies 
watchlist. From that point on, each trading bot will continue to monitor its designated instrument with the rules of your 
strategy until it is terminated. A user of AutoTrader will not often need to interact with the trading bots, but if required,
they can be accessed from the `bots_deployed` attribute of the AutoTrader instance used to deploy them. 


## Run Modes
AutoTrader trading bots have two modes: periodic update mode and detached mode. The active mode is controlled using the `detach_bot`
attribute, which can be set from the [configuration method](autotrader#run-configuration) of AutoTrader. When set to `False` (which
is the default), the bots will run in periodic update mode.

### Periodic Update Mode
Periodic update mode is the default bot deployment mode, and is adequate for most strategies. When using this mode, bots will 
analyse price data according to the strategy to determine the signal on the most recent candle. After acting on this signal, the 
bot will self-terminate. For this reason, AutoTrader must be run periodically to repeatedly deploy trading bots and act on the 
latest signal. This task is easily automated using [cron](https://en.wikipedia.org/wiki/Cron), or a similar job scheduler. A 
single bot update in this mode is illustrated in the chart below.


```{image} ../assets/images/light-periodic-update-run.svg
:align: center
:class: only-light
```

```{image} ../assets/images/dark-periodic-update-run.svg
:align: center
:class: only-dark
```


The reasoning behind this run mode is that many strategies act on the *close* of a candle, meaning that running the technical 
analysis at each candle close is adequate to execute the strategy. For example, for a strategy running on the 4-hour timeframe,
AutoTrader would be scheduled to run every 4 hours. Each time it runs, the trading bots will be provided with the latest 4-hour
candles to perform the strategy on.




### Detached Bot Mode

In detached bot mode, a new thread is spawned for each bot deployed, allowing it to run semi-independently. When a bot is deployed
in this mode, it will be passed to the [bot manager](bot-manager). The main purpose of this run mode is to allow a trading bot to 
maintain attributes from the time it is deployed until the time it is terminated. This is because it will only be deployed once, 
meaning that the strategy it is assigned will only be instantiated once upon deployment. This mode is also more appropriate when
using [AutoStream](autostream) for live trading on tick data. 

```{image} ../assets/images/light-detached-bot.svg
:align: center
:class: only-light
```

```{image} ../assets/images/dark-detached-bot.svg
:align: center
:class: only-dark
```


In this mode, the bot will continue to trade indefinitely until a termination signal is received. This signal can either come from
the strategy module or from the user via manual intervention. In the latter case, the user can send a termination signal to the 
[bot manager](bot-manager), which will then safely terminate the bot from further trading. 



