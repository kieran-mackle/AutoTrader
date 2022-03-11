# Backtesting in AutoTrader


Now that you have [defined a strategy](strategy) and written the strategy [configuration file](../docs/configuration), you can
have some fun with backtesting. 

## Creating a Runfile
An easy way to quickly deploy a trading bot is to set up a run file. This file will import AutoTrader, configure the run settings
and finally deploy your bot. This is all achieved in the example below.

```py
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(show_plot=True, verbosity=1)
at.add_strategy('macd')
at.backtest(start = '1/1/2020',
            end = '1/1/2021',
            initial_balance=1000,
            leverage = 30)
at.run()
```

To run AutoTrader in [backtest mode](../docs/autotrader#backtest-mode), begin by 

First, we import AutoTrader and creating an instance using `at = AutoTrader()`. Next, we use the `configure` method to set the 
verbosity of the code and tell AutoTrader that we would like to see a plot. Next, we add our strategy using the `add_strategy` method. 
Then, we use the `backtest` method to define your backtest settings. In this example, we set the start and end dates of the backtest, the initial account balance and the leverage of the account. You can also define a commission here, as well as an average bid/ask price spread. Finally, we run AutoTrader with the command `at.run()`, and that's it.



## Backtest Results
With a verbosity of 1, you will see an output similar to that shown below. As you can see, there is a detailed breakdown of 
trades taken during the backtest period. Since we told AutoTrader to plot the results, you will also see the interactive chart
shown [below](#interactive-chart).

### Performance Breakdown
```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
  From:  01/01/2020 00:00
  To:    01/01/2021 00:00
[*********************100%***********************]  1 of 1 completed
AutoTraderBot assigned to analyse EURUSD=X on 1h timeframe using Simple MACD Trend Strategy.

Trading...

Backtest complete.

-------------------------------------------
            Backtest Results
-------------------------------------------
Backtest win rate:       44.3%
Total no. trades:        82
Profit:                  $118.352 (11.8%)
Maximum drawdown:        -11.6%
Max win:                 $30.29
Average win:             $23.23
Max loss:                -$18.92
Average loss:            -$15.79
Longest win streak:      8 trades
Longest losing streak:   5 trades
Average trade duration   1 day, 9:22:47
Orders still open:       1
Cancelled orders:        2

         Summary of long trades
-------------------------------------------
Number of long trades:   42
Long win rate:           50.0%
Max win:                 $27.8
Average win:             $23.44
Max loss:                -$18.92
Average loss:            -$15.76

          Summary of short trades
-------------------------------------------
Number of short trades:  37
short win rate:          37.8%
Max win:                 $30.29
Average win:             $22.91
Max loss:                -$18.15
Average loss:            -$15.81
```


### Interactive Chart
The interactive chart will look something like the one shown below.


<iframe data-src="../_static/charts/macd_backtest_demo.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/macd_backtest_demo.html"></iframe>




### Accessing Backtest Data
We can also access even more details related to the backtest. Without getting into too many details, every time AutoTrader is run, it
deploys one trading bot per instrument in the watchlist, per strategy. In our example, we only used one strategy (MACD) and one 
instrument (EUR/USD). Therefore, one trading bot was deployed. The details of this bot is stored in the `bots_deployed` attribute of 
AutoTrader. Therefore, we can access every trade this bot took during the backtest by examining:

```py
bot = at.bots_deployed[0]
```

You will now have access to *bot*, an instance of [AutoBot](../docs/autobot). Of interest now is the backtest summary of the bot,
written to `bot.backtest_summary`. This is a dictionary containing a history of trades taken, orders cancelled, trades still open, and
more. Exploring this is left as an exercise to the reader.


