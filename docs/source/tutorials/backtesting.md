# Backtesting in AutoTrader
Now that you have defined a strategy and written the strategy configuration file, you can have some fun with backtesting. 

## Creating a Runfile
An easy way and organised way to deploy a trading bot is to set up a run file. Here you import AutoTrader, configure the 
run settings and deploy your bot. This is all achieved in the example below.

```python
from autotrader import AutoTrader

at = AutoTrader()                           # Create a new instance of AutoTrader
at.configure(show_plot=True, verbosity=1)   # Configure the instance
at.add_strategy('macd')                     # Add the strategy by its configuration file prefix
at.backtest(start = '1/1/2021',             # Define the backtest settings
            end = '1/1/2022',
            initial_balance=1000,
            leverage = 30)
at.run()                                    # Run AutoTrader!
```

To run a backtest in AutoTrader, begin by importing AutoTrader and creating 
an instance using `at = AutoTrader()`. Next, use the [`configure`](autotrader-configure) method to set 
the verbosity of the code and tell AutoTrader that you would like to see the plot. Next, we add our 
strategy using the `add_strategy` method. Here we pass the file prefix of the strategy configuration file, 
located in the `config/` [directory](rec-dir-struc). Then, we use the [`backtest`](autotrader-backtest-config) 
method to define your backtest settings. In this example, we set the start and end dates of the backtest, 
the initial account balance and the leverage of the account. You can also define a commission here, as 
well as an average bid/ask price spread. Finally, we run AutoTrader with the command `at.run()`, and that's it! 


## Backtest Results
With a verbosity of 1, you will see an output similar to that shown below. As you can see, there is a detailed breakdown of 
trades taken during the backtest period. Since we told AutoTrader to plot the results, you will also see the interactive chart
shown [below](interactive-chart).


### Performance Breakdown
```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURUSD=X with virtual broker using MACD Trend Strategy.

Trading...

Backtest complete (runtime 4.642 s).

----------------------------------------------
               Backtest Results
----------------------------------------------
Start date:              Jan 20 2021 05:00:00
End date:                Dec 31 2021 13:00:00
Starting balance:        $1000.0
Ending balance:          $1255.11
Ending NAV:              $1270.05
Total return:            $255.11 (25.5%)
Total no. trades:        96
Total fees:              $0.0
Backtest win rate:       46.9%
Maximum drawdown:        -18.1%
Max win:                 $40.5
Average win:             $26.53
Max loss:                -$43.81
Average loss:            -$18.41
Longest win streak:      6 trades
Longest losing streak:   6 trades
Average trade duration:  1 day, 2:37:30
Orders still open:       1
Cancelled orders:        3

            Summary of long trades
----------------------------------------------
Number of long trades:   40
Long win rate:           50.0%
Max win:                 $40.5
Average win:             $26.99
Max loss:                -$21.91
Average loss:            -$17.96

             Summary of short trades
----------------------------------------------
Number of short trades:  59
short win rate:          42.4%
Max win:                 $35.06
Average win:             $26.17
Max loss:                -$43.81
Average loss:            -$18.65
```

(interactive-chart)=
### Interactive Chart
The interactive chart will look something like the one shown below.


<iframe data-src="../_static/charts/macd_backtest_demo.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/macd_backtest_demo.html"></iframe>




### Accessing Backtest Data
We can also access even more details related to the backtest. Without getting into too many details, every time AutoTrader is run, it
deploys one trading bot per instrument in the watchlist, per strategy. In our example, we only used one strategy (MACD) and one 
instrument (EUR/USD). Therefore, one trading bot was deployed. The details of this bot is stored in the AutoTrader instance we created. 
We can access the bots deployed by an instance of AutoTrader using the [`get_bots_deployed`](autotrader-bots-deployed) method, as 
shown below.

```py
bot = at.get_bots_deployed()
```

You will now have access to *bot*, an instance of [AutoBot](../core/AutoBot) which traded the MACD strategy on EUR/USD. Of interest 
now is the backtest summary of the bot, written to `bot.backtest_summary`. This is a dictionary containing a history of trades taken,
orders cancelled, trades still open, and more. Exploring this is left as an exercise to the reader.

```{tip}
With AutoTrader `v0.6.2`, you can also access backtest data from `at.backtest_results`. This attribute is an instance of 
the [BacktestResults](utils-backtest-results) class.
```
