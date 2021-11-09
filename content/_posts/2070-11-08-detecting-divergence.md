---
title: Detecting Divergence
cover: /assets/images/divergence_markedup.png
tags: features
---


![Name](/AutoTrader/assets/divergence-blog/.png "Name")

If you dont like reading, feel free to [skip to the good part](#detecting-divergence).


# Motivation

cAN i GET ANY SOURCES ON DIVERGENCE being effective? would be good to have some links.

define divergence, as per investopedia

Something different to using pivot points


# Building the Indicator
While building this indicator, I will be using [AutoPlot](../docs/autoplot) along the way to visualise what I am 
doing.

## Detecting price reversals

find_swings indicator

alternatively, pivot points. However, tradingview pivot points are very lagging, 
i want something quicker

![Price Swings](/AutoTrader/assets/divergence-blog/price-swings-trend.png "Price Swings")



## Support and Resistance

Detecting significant support and resistance levels using the price reversals

When an established reversal levels survives for more than 2 candles 
(ie. it is not broken)
2 is what was used, this is general

This filters regular fluctuations

![Support and Resistnace Levels](/AutoTrader/assets/divergence-blog/support-resistance.png "Support and Resistnace Levels")


## Filtering

Now we want to filter for strong high levels, and strong low levels

![Strong Levels](/AutoTrader/assets/divergence-blog/strong-levels.png "Strong Levels")


### First occurrence
Detect first occurance of strong high or low levels

![First Strong Levels](/AutoTrader/assets/divergence-blog/fsl.png "First Strong Levels")


## Finding Higher Highs and Lower Lows

![Lows change](/AutoTrader/assets/divergence-blog/lows-change.png "Lows change")



![Lower Lows](/AutoTrader/assets/divergence-blog/lower-low.png "Lower Lows")



# Testing on Indicators

On RSI with period of 14

![RSI](/AutoTrader/assets/divergence-blog/rsi-swings.png "RSI")



# Detecting Divergence

Combine the tools and indicators developed above on price and an indicator of choice, to detect 
divergence. 

Use RSI as an example, but other indicators can be used.

Maybe also show for MACD


Here is a cherry-picked example of the indicator at work:
(insert image of plot with price, RSI, and divergence detecting big reversal)

![Divergence Indicator](/AutoTrader/assets/images/divergence-markedup.png "Divergence Indicator")


# What Now?

The tools above have been combined into the indicators;
find_swings()
detect_divergence()

added to AutoTrader [indicator library]().


Next steps,
Implement into a strategy, backtest


