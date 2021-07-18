---
layout: page
title: AutoTrader
permalink: /
---

# AutoTrader: the one stop solution for automated trading systems
AutoTrader is an event-driven platform intended to help in the development, optimisation and deployment of automated trading systems. 

A basic level of experience with Python is recommended for using AutoTrader, but the documentation aims to be clear enough that a beginner 
is able to pick up the key elements as they go. If you are new to Python, you may find the [tutorials](tutorials) especially useful.


## Features

AutoTrader has many features, so be sure to check out the [Documentation](docs) and the [Getting Started](docs/getting-started) guide for a 
complete summary. Some key features include:

 - [Validated backtesting](docs/validation) with a high-fidelity virtual broker: multiple order types supported, commissions, bid/ask 
   spread modelling, margin considerations for leveraged accounts
 - [Interactive visualisation](interactive-visualisation) of backtest results and live-trade performance
 - [Strategy optimisation](docs/auto-optimise)
 - [Streaming](docs/autostream) of price data (Oanda v20 API)
 - Access to historical price data (Yahoo finance, Oanda)
 - Market scanning with [email notifications](docs/emailing)


## MACD Strategy Example

Consider you want to develop and test a strategy using Moving Average Divergence Convergence (MACD), a popular trend-following momentum indicator. 
In your strategy, you go long (buy) when the MACD line crosses above the signal line, and go short when the oppposite happens. After doing some
research, you discover that MACD signals are strongest when cross-ups occur below the histogram-zero line (for long entries), or when cross-downs 
occur above the histogram-zero line. Furthermore, you follow the adage that 'the trend is your friend', so only go long when price is above the 
200 exponential moving average, and short when price is below it.

Coding this up in AutoTrader is easy; all you need is a [strategy](/docs/strategies) file and a [config](/docs/config-files) file. Then, with a
one line command, you can backtest your strategy over any time period and any time frame.

The command to do this is:

```
$ ./AutoTrader -c macd -b -p -v 1
```

As you can see, the executable here is *AutoTrader*, to which you passed four flags:
 - -c: this flag is used to specify the strategy [config](/docs/config-files) file
 - -b: this flag tells AutoTrader to run in backtest mode
 - -p: this flag tells AutoTrader to plot the results of the backtest onto an interactive chart
 - -v: this flag sets the verbosity of the code - a value of 1 requests moderate verbosity.

With a verbosity of 1, you will see an output similar to that shown below. As you can see, there is a detailed breakdown of traders taken during 
the backtest period. 


```
    _         _        ____             _    _            _   
   / \  _   _| |_ ___ | __ )  __ _  ___| | _| |_ ___  ___| |_ 
  / _ \| | | | __/ _ \|  _ \ / _` |/ __| |/ / __/ _ \/ __| __|
 / ___ \ |_| | || (_) | |_) | (_| | (__|   <| ||  __/\__ \ |_ 
/_/   \_\__,_|\__\___/|____/ \__,_|\___|_|\_\\__\___||___/\__|
                                                              

Analysing EUR/USD on H1 timeframe using Simple MACD Trend Strategy.
Time: Friday, July 16 2021, 11:25:59
From:  2020-01-01 00:00:00+00:00
To:    2021-02-01 00:00:00+00:00

-------------------------------------------
            Backtest Results
-------------------------------------------
Strategy: Simple MACD Trend Strategy
Timeframe:               H1
Risk to reward ratio:    1.5
Profitable win rate:     40.0%
Backtest win rate:       50.0%
Total no. trades:        134
Profit:                  $342.872 (34.3%)
Maximum drawdown:        -13.0%
Max win:                 $29.16
Average win:             $24.22
Max loss:                -$25.93
Average loss:            -$18.94
Longest win streak:      9 trades
Longest losing streak:   7 trades
Average trade duration   8:44:46
Cancelled orders:        2

         Summary of long trades
-------------------------------------------
Number of long trades:   61
Long win rate:           55.7%
Max win:                 $28.5
Average win:             $23.47
Max loss:                -$21.11
Average loss:            -$18.53

          Summary of short trades
-------------------------------------------
Number of short trades:  69
short win rate:          44.9%
Max win:                 $29.16
Average win:             $25.04
Max loss:                -$25.93
Average loss:            -$19.24
```

The plot will look something like the one shown below. Note that the one here is just a static image, but you will be given an interactive chart when running AutoTrader. 
Click [here](interactive-visualisation) to see the interactive version of the chart (which isn't quite ready to be viewed on mobile devices)! 

![backtest-demo-plot](../assets/img/backtest-example-plot.jpg)

Looks pretty good right? Well good news! Going from backtesting to live-trading is as easy as removing the '-b' flag from the command above!


For a more detailed guide on using AutoTrader, check out the [Getting Started](docs/getting-started) guide, or read the [documentation](docs). 


Would you like to request a feature or contribute?
[Open an issue]({{ site.repo }}/issues)
