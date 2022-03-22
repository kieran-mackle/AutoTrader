# Optimising a Strategy with AutoTrader

If you have successfully [set up a strategy](building-strategy) and run a [backtest](backtesting) on it, 
then you can optimise the strategy paramaters with ease. All you need to do is specify which parameters 
to optimise and what bounds should be placed on them and that's it!

## MACD Optimisation
We will modify our runfile to optimise the `MACD_fast` and `MACD_slow` parameters of our MACD strategy by using
the [`optimise`](autotrader-optimise-config) method of AutoTrader. This method requires two inputs: 
- `opt_params`: the names of the parameters we wish to optimise, as they appear in the `PARAMETERS` section of our 
strategy configuration.
- `bounds`: the upper and lower bounds on the optimisation parameters, specified as tuples.

We must also include the `backtest` method, which is used to specify the backtest parameters to be used in the optimisation.
In the code snippet below, we will optimise the strategy over the time period specified by the start and end dates provided.
Note that the objective of the optimiser is to maximise profit. 

Before we run the optimiser, lets download the price data used in our backtest, so that we do not have to download it 
for each iteration of the optimisation. This can be acheived with the code snippet below. Note that since we only
ran the backtest on a single isntrument, we do not have to provide any arguments to the 
[`get_bots_deployed`](autotrader-bots-deployed) method. Note that we save the data to a the `price_data` directory,
as that is where AutoTrader will look for price data by default.

```python
bot = at.get_bots_deployed()
bot.data.to_csv('price_data/EUdata.csv')
```
Now we can use this data in our optimiser by providing it via the [`add_data`](autotrader-add-data) method, as shown below.

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


### Optimised Parameters
Running the file above will result in the following output. After a few minutes on a mid-range laptop, the 
parameters of our MACD strategy have been optimised to maximise profit over the one-year backtest period. As you can 
see from the output, the optimal parameter values for the strategy configuration parameters specified are approximately 
10 and 33. This means that the fast MACD period should be 10, and the slow MACD period should be 33.

```
Parameters/objective: [ 5. 20.] / -966.904
                    .
                    .
                    .
Parameters/objective: [ 9.79685545 33.30738306] / -1246.284

Optimisation complete.
Time to run: 555.793s
Optimal parameters:
[ 9.796875   33.30729167]
Objective:
-1246.2841641533123
```

### Comparison to Baseline Strategy
Now let's compare the performance of the strategy before and after optimisation. Simply run the backtest again with 
the optimised parameters (you will need to update the strategy configuration file) and observe the results shown below. 

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

Backtest complete (runtime 2.884 s).

----------------------------------------------
               Backtest Results
----------------------------------------------
Start date:              Jan 20 2021 05:00:00
End date:                Dec 31 2021 13:00:00
Starting balance:        $1000.0
Ending balance:          $1261.72
Ending NAV:              $1276.52
Total return:            $261.72 (26.2%)
Total no. trades:        92
Total fees:              $0.0
Backtest win rate:       46.7%
Maximum drawdown:        -13.53%
Max win:                 $37.47
Average win:             $25.65
Max loss:                -$22.3
Average loss:            -$17.16
Longest win streak:      4 trades
Longest losing streak:   6 trades
Average trade duration:  1 day, 0:52:49
Orders still open:       1
Cancelled orders:        1

            Summary of long trades
----------------------------------------------
Number of long trades:   37
Long win rate:           43.2%
Max win:                 $37.47
Average win:             $26.37
Max loss:                -$22.27
Average loss:            -$17.11

             Summary of short trades
----------------------------------------------
Number of short trades:  58
short win rate:          46.6%
Max win:                 $32.44
Average win:             $25.22
Max loss:                -$22.3
Average loss:            -$17.2
```

Let's take a look at the profit [before](backtesting) and after:
>
>Profit before optimisation:
>$255.11 (25.5%)
>
>Profit after optimisation:
>$261.72 (26.2%)



## A Word of Caution
This tutorial was intended to illustrate how to use AutoTrader's parameter optimisation functionality. In the example above,
the strategy is now likely highly overfit to the backtest dataset. You will have to use your discretion when chosing parameters 
to optimise.