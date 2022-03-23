# Backtesting With AutoTrader

Thanks to the powerful [virtual broker](virtual-broker), AutoTrader features a highly capable backtesting
environment. In addition to supporting mulitple [order types](order-types), AutoTrader supports backtesting
mutliple strategies with multiple instruments on multiple timeframes - all against the same broker at the 
same time. 



## Single Strategy Backtest


### Single Instrument
Single strategy, single instrument

```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade AUDJPY=X with virtual broker using EMA Crossover.

Trading...

Backtest complete (runtime 0.706 s).

----------------------------------------------
               Backtest Results
----------------------------------------------
Start date:              Aug 18 2021 14:00:00
End date:                Dec 31 2021 13:00:00
Starting balance:        $1000.0
Ending balance:          $1476.42
Ending NAV:              $1476.42
Total return:            $476.42 (47.6%)
Total no. trades:        25
Total fees:              $0.0
Backtest win rate:       60.0%
Maximum drawdown:        -6.11%
Max win:                 $57.21
Average win:             $47.92
Max loss:                -$28.26
Average loss:            -$24.25
Longest win streak:      3 trades
Longest losing streak:   2 trades
Average trade duration:  1 day, 16:50:24

            Summary of long trades
----------------------------------------------
Number of long trades:   13
Long win rate:           61.5%
Max win:                 $57.21
Average win:             $48.3
Max loss:                -$28.26
Average loss:            -$24.24

             Summary of short trades
----------------------------------------------
Number of short trades:  12
short win rate:          58.3%
Max win:                 $54.52
Average win:             $47.49
Max loss:                -$26.19
Average loss:            -$24.25
```

Chart is AUDJPY=x backtest

Note the run backtest time - periodic update mode

<iframe data-src="../_static/charts/AUDJPY=X-backtest-chart.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:900px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/AUDJPY=X-backtest-chart.html"></iframe>





### Multiple Instruments
```yaml
WATCHLIST: ['EURUSD=X', 'EURJPY=X', 'EURAUD=X', 'AUDJPY=X']
```





## Multiple Strategy Backtest


```python
at.add_strategy('macd_continuous')
at.add_strategy('ema_crossover_continuous')
```


### Single Instrument

```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Beginning new backtest.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade EURJPY=X with virtual broker using MACD Trend Strategy.
[*********************100%***********************]  1 of 1 completed

AutoTraderBot assigned to trade AUDJPY=X with virtual broker using EMA Crossover Strategy.

Trading...

Backtest complete (runtime 34.839 s).

---------------------------------------------------
            MultiBot Backtest Results
---------------------------------------------------
Start date:              2021-08-01 00:00:00+00:00
End date:                2022-01-01 00:00:00+00:00
Starting balance:        $1000.0
Ending balance:          $1700.85
Ending NAV:              $1700.85
Total return:            $700.85 (70.1%)
Instruments traded:  ['EURJPY=X' 'AUDJPY=X']
Total no. trades:    53
Short trades:        30 (56.6%)
Long trades:         24 (45.28%)

Instrument win rates (%):
           win_rate  no_trades
EURJPY=X  53.571429         28
AUDJPY=X  60.000000         25

Maximum/Average Win/Loss breakdown ($):
            max_win   max_loss    avg_win   avg_loss
EURJPY=X  40.111049  25.404342  30.114452  21.611662
AUDJPY=X  65.967451  32.074735  53.327594  26.983047

Average Reward to Risk Ratio:
EURJPY=X    1.4
AUDJPY=X    2.0
dtype: float64

Results for multiple-instrument backtests have been
written to AutoTrader.multibot_backtest_results.
```

Chart is multibot 1

<iframe data-src="../_static/charts/multibot1.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:900px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/multibot1.html"></iframe>




### Multiple Instruments

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


Chart is multibot 2

<iframe data-src="../_static/charts/multibot2.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:900px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/multibot2.html"></iframe>











## Running a Backtest

When visualising backtest results in AutoTrader, you can actually see where the stop loss and take profit
levels are being placed for each and every trade. This is incredibly useful when assessing how effective your exit strategy is. Too many
people focus on the entry, but exit is so important. By visualising the exit target, you can see if you are being stopped out 
too early on otherwise good trades.


```python
from autotrader.autotrader import AutoTrader

# Instantiate AutoTrader
at = AutoTrader()

# Run backtest
at.backtest     = True
at.verbosity    = 1
at.config_file  = 'simple_macd'
at.show_plot    = True
at.run()
```




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



<iframe data-src="../_static/charts/simple-macd-bt.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/simple-macd-bt.html"></iframe>






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

