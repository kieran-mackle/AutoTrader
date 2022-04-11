# Backtesting With AutoTrader

Thanks to the powerful [virtual broker](virtual-broker-docs), AutoTrader features a highly capable backtesting
environment. In addition to supporting mulitple [order types](order-types), AutoTrader supports backtesting
mutliple strategies with multiple instruments on multiple timeframes - all against the same broker at the 
same time. 


## Single-Bot Backtest
Shown below is the output for a backtest on EUR/USD using the MACD strategy developed in the 
[walkthrough](detailed-walkthrough).

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

This output is useful, but as the saying goes, a picture is worth a thousand words. Running a backtest is no 
exception, as when visualising backtest results in AutoTrader, you can see exactly where the stop loss and 
take profit levels are being placed for each and every trade. This is incredibly useful when assessing how 
effective your exit strategy is. By visualising the exit targets, you can see if you are being stopped out 
too early on otherwise good trades. The chart interactive chart below is automatically generated using the
automated plotting module, [AutoPlot](autoplot-docs), after running a backtest.

<iframe data-src="../_static/charts/macd_backtest_demo.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/macd_backtest_demo.html"></iframe>



## Multi-Bot Backtest

As mentioned above, AutoTrader supports running backtests on multiple products and strategies at the same 
time. This is referred to as a 'multi-bot backtest', since a [trading bot](autobot-docs) is deployed for
each unique strategy trading a unique product. 


### Specifying Multiple Products
To trade multiple products with a strategy, simply add them to the `WATCHLIST` in the 
[strategy configuration](strategy-config). In the example below, four FOREX pairs will
be traded by the strategy they are assigned to.

```yaml
WATCHLIST: ['EURUSD=X', 'EURJPY=X', 'EURAUD=X', 'AUDJPY=X']
```



### Specifying Multiple Strategies
Trading multiple strategies is equally as straightforward; simply use the [`add_strategy`](autotrader-add-strategy) 
method of the active [`AutoTrader`](autotrader-docs) instance to provide each strategy. This is
shown in the snippet below.

```python
at.add_strategy('macd_strategy')
at.add_strategy('ema_crossover_strategy')
```


### Output
Now let's look at the backtest results for two strategies, each trading two different products. The strategies
used here are a MACD trend strategy and an EMA crossover strategy - both of which can be found in the
AutoTrader [demo repository](https://github.com/kieran-mackle/autotrader-demo). As you can see in the output
below, four [trading bots](autobot-docs) are deployed:

1. to trade EUR/USD with the virtual broker using the MACD Trend Strategy;
2. to trade EUR/JPY with the virtual broker using the MACD Trend Strategy;
3. to trade AUD/JPY with the virtual broker using the EMA Crossover Strategy; and
4. to trade EUR/AUD with the virtual broker using the EMA Crossover Strategy.

Each of these bots is therefore responsible for trading a single product, with the knowledge of a single 
strategy. This is extremely useful, as you can see how different strategies will interact with each other
when trading them at the same time.

```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURUSD=X with virtual broker using MACD Trend Strategy.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURJPY=X with virtual broker using MACD Trend Strategy.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade AUDJPY=X with virtual broker using EMA Crossover.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURAUD=X with virtual broker using EMA Crossover.

Trading...

Warning: mismatched data lengths detected. Correcting via row reduction.
  Done.

Backtest complete (runtime 13.154 s).

----------------------------------------------
               Backtest Results
----------------------------------------------
Start date:              Aug 18 2021 14:00:00
End date:                Dec 31 2021 13:00:00
Starting balance:        $1000.0
Ending balance:          $1517.52
Ending NAV:              $1517.52
Total return:            $517.52 (51.8%)
Total no. trades:        120
Total fees:              $0.0
Backtest win rate:       42.5%
Maximum drawdown:        -13.97%
Max win:                 $57.45
Average win:             $37.77
Max loss:                -$29.58
Average loss:            -$20.41
Longest win streak:      4 trades
Longest losing streak:   7 trades
Average trade duration:  1 day, 3:59:00
Orders still open:       3
Cancelled orders:        10

            Summary of long trades
----------------------------------------------
Number of long trades:   53
Long win rate:           34.0%
Max win:                 $57.01
Average win:             $38.86
Max loss:                -$29.58
Average loss:            -$21.38

             Summary of short trades
----------------------------------------------
Number of short trades:  70
short win rate:          47.1%
Max win:                 $57.45
Average win:             $37.17
Max loss:                -$28.79
Average loss:            -$19.58
```

Now [AutoPlot](autoplot-docs) will create a dashboard-like output, showing the performance of each bot,
as well as account metrics such as net asset value and margin available for the duration of the backtest.

<iframe data-src="../_static/charts/multibot2.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/multibot2.html"></iframe>


```{tip}
You can also pull out individual trading bots using the [`get_bots_deployed`](autotrader-bots-deployed) 
method to analyse them (and the trades they took) individually. You can also plot them individually
using `at.plot_backtest(bot)`!
```





## Parameter Optimisation
AutoTrader also offers (a somewhat brute-force method of) parameter optimisation for backtested strategies.


```python
from autotrader.autotrader import AutoTrader

at = AutoTrader()
at.configure(show_plot=True, verbosity=1)
at.add_strategy('macd')
at.backtest(start = '1/1/2020',
            end = '1/1/2021',
            initial_balance=1000,
            leverage = 30)
at.add_data(data_dict={'EURUSD=X': 'EUdata.csv'})
at.optimise(opt_params=['MACD_fast', 'MACD_slow'],
            bounds=[(5, 20), (20, 40)])
at.run()
```

