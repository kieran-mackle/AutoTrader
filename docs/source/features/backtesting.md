# Backtesting With AutoTrader

Thanks to the powerful [virtual broker](virtual-broker), AutoTrader features a highly capable backtesting
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
                                                              

Analysing EUR/USD on M15 timeframe using Simple MACD Trend Strategy.
Time: Saturday, August 07 2021, 10:32:36
From:  2020-07-01 00:00:00+00:00
To:    2021-01-01 00:00:00+00:00

-------------------------------------------
            Backtest Results
-------------------------------------------
Strategy: Simple MACD Trend Strategy
Timeframe:               M15
Risk to reward ratio:    1.5
Profitable win rate:     40.0%
Backtest win rate:       52.3%
Total no. trades:        247
Profit:                  $685.987 (68.6%)
Maximum drawdown:        -18.1%
Max win:                 $36.02
Average win:             $27.59
Max loss:                -$30.58
Average loss:            -$22.88
Longest win streak:      7 trades
Longest losing streak:   12 trades
Average trade duration   9:59:55
Cancelled orders:        52

         Summary of long trades
-------------------------------------------
Number of long trades:   116
Long win rate:           53.4%
Max win:                 $35.71
Average win:             $26.68
Max loss:                -$30.19
Average loss:            -$22.51

          Summary of short trades
-------------------------------------------
Number of short trades:  79
short win rate:          50.6%
Max win:                 $36.02
Average win:             $29.0
Max loss:                -$30.58
Average loss:            -$23.4
```

This output is useful, but as the saying goes, a picture is worth a thousand words. Running a backtest is no 
exception, as when visualising backtest results in AutoTrader, you can see exactly where the stop loss and 
take profit levels are being placed for each and every trade. This is incredibly useful when assessing how 
effective your exit strategy is. By visualising the exit targets, you can see if you are being stopped out 
too early on otherwise good trades. The chart interactive chart below is automatically generated using the
automated plotting module, [AutoPlot](autoplot-docs), after running a backtest.

<iframe data-src="../_static/charts/simple-macd-bt.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/simple-macd-bt.html"></iframe>



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

AutoTraderBot assigned to trade AUDJPY=X with virtual broker using EMA Crossover Strategy.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURAUD=X with virtual broker using EMA Crossover Strategy.

Trading...

Backtest complete (runtime 69.541 s).

---------------------------------------------------
            MultiBot Backtest Results
---------------------------------------------------
Start date:              2021-08-01 00:00:00+00:00
End date:                2022-01-01 00:00:00+00:00
Starting balance:        $1000.0
Ending balance:          $1456.54
Ending NAV:              $1456.54
Total return:            $456.54 (45.7%)
Instruments traded:  ['EURUSD=X' 'EURJPY=X' 'AUDJPY=X' 'EURAUD=X']
Total no. trades:    116
Short trades:        66 (56.9%)
Long trades:         54 (46.55%)

Instrument win rates (%):
           win_rate  no_trades
EURUSD=X  38.709677         31
EURJPY=X  50.000000         26
AUDJPY=X  60.000000         25
EURAUD=X  29.411765         34

Maximum/Average Win/Loss breakdown ($):
            max_win   max_loss    avg_win   avg_loss
EURUSD=X  34.036303  23.568356  28.984046  19.756270
EURJPY=X  34.971404  21.449399  28.871176  19.957594
AUDJPY=X  56.713913  28.449948  50.929921  26.115462
EURAUD=X  55.921397  29.655745  49.439287  26.207001

Average Reward to Risk Ratio:
EURUSD=X    1.5
EURJPY=X    1.4
AUDJPY=X    2.0
EURAUD=X    1.9
dtype: float64

Results for multiple-instrument backtests have been
written to AutoTrader.multibot_backtest_results.
Individual bot results can be found in the
'bots_deployed' attribute of the AutoTrader instance.
```

Now [AutoPlot](autoplot-docs) will create a dashboard-like output, showing the performance of each bot,
as well as account metrics such as net asset value and margin available for the duration of the backtest.
You can also pull out individual trading bots using the [`get_bots_deployed`](autotrader-bots-deployed) 
method to analyse them (and the trades they took) individually.

<iframe data-src="../_static/charts/multibot2.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/multibot2.html"></iframe>








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

