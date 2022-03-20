(autobot-docs)=
# AutoBot


`autotrader.autobot`

When you run a strategy in AutoTrader, a trading bot, or `AutoBot`, will be deployed for each instrument in your strategies 
watchlist. From that point on, each trading bot will continue to monitor its designated instrument with the rules of your 
strategy until it is terminated. A user of AutoTrader will not often need to interact with the trading bots, but if required,
they can be accessed from the `bots_deployed` attribute of the AutoTrader instance used to deploy them. 



## Order Processing

show methods to check orders