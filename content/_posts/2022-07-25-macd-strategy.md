---
title: Testing MACD Trend Strategy
cover: /assets/images/HA_chart.png
tags: Strategies MACD forex
---


Consider you want to develop and test a strategy using Moving Average Divergence Convergence (MACD), a popular trend-following momentum indicator. 
In your strategy, you go long (buy) when the MACD line crosses above the signal line, and go short when the oppposite happens. After doing some
research, you discover that MACD signals are strongest when cross-ups occur below the histogram-zero line (for long entries), or when cross-downs 
occur above the histogram-zero line. Furthermore, you follow the adage that 'the trend is your friend', so only go long when price is above the 
200 exponential moving average, and short when price is below it.

Coding this up in AutoTrader is easy; all you need is a [strategy](../docs/strategies) file and a [config](../docs/config-files) file. Then, with a
one line command, you can backtest your strategy over any time period and any time frame.

Looks pretty good right? Well good news! Going from backtesting to live-trading is as easy as removing 
the '-b' flag from the command above. But beware, backtesting performance alone is no strong indication of 
future performance! That's why [backtest validation](validation) is so important.

If you get an error message about your strategy not importing because it is in an 'unknown location', restart the console
and make sure you are in the correct working directory, as accoring to ... (where it shows the dir layout)

