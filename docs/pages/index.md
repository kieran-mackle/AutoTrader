---
layout: page
title: AutoTrader
permalink: /
---

# AutoTrader
AutoTrader is an event-driven platform indended to help in the development, optimisation and deployment of automated trading systems. 

A basic level of experience with Python is recommended for using AutoTrader, but the documentation aims to be clear enough that a beginner 
is able to pick up the key elements as they go. If you are new to Python, you may find the [tutorials](tutorials) especially useful.


## Features

What are these features? You should see the {% include doc.html name="Getting Started" path="getting-started" %}
guide for a complete summary. Briefly:

 - *Visualisation*
 - *Simple, elegant code*
 - *Backtesting* 
 - *Live-trading*
 - *Optimisation*
 - *Validation*
 - *Event-driven*
 - *Variety of order types* available in backtesting, such as market orders, limit orders, and trailing stop orders.
 - *Data streaming*
 - *Historical data*
 - *Live market scanning with email notification*
 - *Complex strategy implementation*: the limit is your imagination!
 - *file-controlled strategies*: the configuration of each strategy is contained within config files, allowing for easy 
    manipulation of strategy parameters. This also means that you can run the same strategy with different parameters,
    in parallel! 


## Simple Example

The key components required to run a strategy using AutoTrader are:

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

{% include backtest-plot.html %}


For a more detailed guide on getting started with AutoTrader, check out the Getting Started guide, or read the [documentation](docs). 


For features, getting started with development, see the {% include doc.html name="Getting Started" path="getting-started" %} page. Would you like to request a feature or contribute?
[Open an issue]({{ site.repo }}/issues)
