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

To do this, I will be using the swing detection unitilty indicator of AutoTrader. Check out the docs for that 
in the [indicators library](../docs/indicators#price-swing-detection).

![Price Swings](/AutoTrader/assets/divergence-blog/price-swings-trend.png "Price Swings")

Note that as part of the version `0.5.5` release of AutoTrader, this indicator has been generalised to accept 
indicators as well as price data. This will come in handy later on - as you will see below.


## Support and Resistance

Detecting significant support and resistance levels using the price reversals

When an established reversal levels survives for more than 2 candles 
(ie. it is not broken)
2 is what was used, this is general

This filters regular fluctuations


```py
new_level = np.where(swing_df.Last != swing_df.Last.shift(), 1, 0)

candles_since_last = candles_between_crosses(new_level)

# Add column 'candles since last swing' CSLS
swing_df['CSLS'] = candles_since_last

# Find strong Support and Resistance zones
swing_df['Support'] = (swing_df.CSLS > 0) & (swing_df.Trend == 1)
swing_df['Resistance'] = (swing_df.CSLS > 0) & (swing_df.Trend == -1)
```

![Support and Resistnace Levels](/AutoTrader/assets/divergence-blog/support-resistance.png "Support and Resistnace Levels")


## Filtering

Now we want to filter for strong high levels, and strong low levels

```py
# Find higher highs and lower lows
swing_df['Strong_lows'] = swing_df['Support'] * swing_df['Lows'] # Returns high values when there is a strong support
swing_df['Strong_highs'] = swing_df['Resistance'] * swing_df['Highs'] # Returns high values when there is a strong support
```

![Strong Levels](/AutoTrader/assets/divergence-blog/strong-levels.png "Strong Levels")


### First occurrence
Detect first occurance of strong high or low levels



```py
# Remove duplicates to preserve indexes of new levels
swing_df['FSL'] = unroll_signal_list(swing_df['Strong_lows']) # First of new strong lows
swing_df['FSH'] = unroll_signal_list(swing_df['Strong_highs']) # First of new strong highs
```

![First Strong Levels](/AutoTrader/assets/divergence-blog/fsl.png "First Strong Levels")


## Finding Higher Highs and Lower Lows




```py
# Now compare each non-zero value to the previous non-zero value.
low_change = np.sign(swing_df.FSL) * (swing_df.FSL - swing_df.Strong_lows.replace(to_replace=0, method='ffill').shift())
high_change = np.sign(swing_df.FSH) * (swing_df.FSH - swing_df.Strong_highs.replace(to_replace=0, method='ffill').shift())
```



![Lows change](/AutoTrader/assets/divergence-blog/lows-change.png "Lows change")



```py
swing_df['LL'] = np.where(low_change < 0, True, False)
swing_df['HL'] = np.where(low_change > 0, True, False)
swing_df['HH'] = np.where(high_change > 0, True, False)
swing_df['LH'] = np.where(high_change < 0, True, False)
```

![Lower Lows](/AutoTrader/assets/divergence-blog/lower-low.png "Lower Lows")



# Testing on Indicators

On RSI with period of 14

![RSI](/AutoTrader/assets/divergence-blog/rsi-swings.png "RSI")



# Detecting Divergence


Combine the tools and indicators developed above on price and an indicator of choice, to detect 
divergence. 


```py
regular_bullish = []
for i in range(len(classified_price_swings)):
    # Look backwards in each
    
    if sum(classified_price_swings['LL'][i-tol:i]) + sum(classified_indicator_swings['HL'][i-tol:i]) > 1:
        regular_bullish.append(True)
    else:
        regular_bullish.append(False)
```


Use RSI as an example, but other indicators can be used.

Maybe also show for MACD


Here is a cherry-picked example of the indicator at work:
(insert image of plot with price, RSI, and divergence detecting big reversal)

![Divergence Indicator](/AutoTrader/assets/images/divergence_markedup.png "Divergence Indicator")


# What Now?

The tools above have been combined into the indicators;
find_swings()
detect_divergence()

added to AutoTrader [indicator library](../docs/indicators).


Next steps,
Implement into a strategy, backtest


