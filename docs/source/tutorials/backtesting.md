# Backtesting with AutoTrader
Now that you have a strategy, you can have some fun with backtesting. 



## Creating a Runfile
An easy and organised way to deploy a trading bot is to set up a 
run file. Here you import AutoTrader, configure the run settings and 
deploy your bot. This is all achieved in the example below.

```python
# runfile.py
from autotrader import AutoTrader

at = AutoTrader()
at.configure(show_plot=True, verbosity=1, feed='yahoo',
             mode='continuous', update_interval='1h') 
at.add_strategy('macd') 
at.backtest(start = '1/1/2021', end = '1/1/2022')
at.virtual_account_config(leverage=30)
at.run()
```

Let's dive into this a bit more:
- We begin by importing AutoTrader and creating an instance 
using `at = AutoTrader()`. 
- Next, we use the [`configure`](autotrader-configure) method to set 
the verbosity of the code and tell AutoTrader that you would like to see 
the backtest plot. We also define the [run mode](autotrader-run-modes)
and update interval to `1h`, meaning that we will step through the backtest
data by 1 hour at a time.
- Next, we add our strategy using the `add_strategy` method. Here we pass the 
file prefix of the strategy configuration file, located (by default) in the 
`config/` [directory](rec-dir-struc). Since our strategy configuration file
is named `macd.yaml`, we pass in 'macd'.
- We then use the [`backtest`](autotrader-backtest-config) method to define 
the backtest period. In this example, we set the start and end dates of the
backtest.
- Since we will be simulating trading (by backtesting), we also need to configure
the virtual trading account. We do this with the `virtual_account_config` method.
Here we set the account leverage to 30. You can also configure trading costs,
bid/ask spread, initial balance and other settings here.
- Finally, we run AutoTrader with the command `at.run()`.

Simply run this file, and AutoTrader will do its thing.


## Backtest Results
With a verbosity of 1, you will see an output similar to that shown below. 
As you can see, there is a breakdown of trades taken during the backtest period. 
Since we told AutoTrader to plot the results, you will also see the interactive 
chart shown [below](interactive-chart).


### Performance Breakdown
```
    ___         __      ______               __         
   /   | __  __/ /_____/_  __/________ _____/ /__  _____
  / /| |/ / / / __/ __ \/ / / ___/ __ `/ __  / _ \/ ___/
 / ___ / /_/ / /_/ /_/ / / / /  / /_/ / /_/ /  __/ /    
/_/  |_\__,_/\__/\____/_/ /_/   \__,_/\__,_/\___/_/     
                                                        

[*********************100%***********************]  1 of 1 completed
BACKTEST MODE

AutoTraderBot assigned to trade EURUSD=X with virtual broker using Simple Macd Strategy.

Trading...

31539600.0it [00:19, 1630112.41it/s]                                                                                                                                          
Backtest complete (runtime 19.348 s).

----------------------------------------------
               Trading Results
----------------------------------------------
Start date:              Jan 20 2021 04:00:00
End date:                Dec 31 2021 13:00:00
Duration:                345 days 09:00:00
Starting balance:        $1000.0
Ending balance:          $1140.75
Ending NAV:              $1170.16
Total return:            $140.75 (14.1%)
Maximum drawdown:        -18.97%
Total no. trades:        175
Total fees paid:         $0.0
Win rate:                21.7%
Max win:                 $36.51
Average win:             $25.26
Max loss:                -$21.57
Average loss:            -$16.38
Longest winning streak:  4 trades
Longest losing streak:   11 trades
Average trade duration:  1 day, 3:43:38
Positions still open:    1
Cancelled orders:        5

            Summary of long trades
----------------------------------------------
Number of long trades:   36
Win rate:                41.7%
Max win:                 $36.51
Average win:             $25.22
Max loss:                -$21.18
Average loss:            -$17.23

             Summary of short trades
----------------------------------------------
Number of short trades:  54
Win rate:                42.6%
Max win:                 $31.85
Average win:             $25.28
Max loss:                -$21.57
Average loss:            -$15.86
```

(interactive-chart)=
### Interactive Chart
The interactive chart will look something like the one shown below.

<iframe data-src="../_static/charts/macd_backtest_demo.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/macd_backtest_demo.html"></iframe>



### Accessing Backtest Data
We can also access even more details related to the backtest. Without getting 
into too many details, every time AutoTrader is run, it deploys one trading 
bot per instrument in the watchlist, per strategy. In our example, we only 
used one strategy (MACD) and one instrument (EUR/USD). Therefore, one trading 
bot was deployed. The details of this bot is stored in the AutoTrader instance 
we created. We can access the bots deployed by an instance of AutoTrader using 
the [`get_bots_deployed`](autotrader-bots-deployed) method, as shown below.

```py
bot = at.get_bots_deployed()
```

You will now have access to *bot*, an instance of [AutoBot](../core/AutoBot) 
which traded the MACD strategy on EUR/USD. Of interest now is the backtest 
summary of the bot, written to `bot.backtest_summary`. This is a dictionary 
containing a history of trades taken, orders cancelled, trades still open, 
and more. Exploring this is left as an exercise to the reader.

