---
title: Comparing Currency Strengths
cover: /assets/strength-blog/cover.png
tags: forex trading
---


This post provides a 'technical' approach to determining the strength of a single currency (or any other instrument
for that matter).

This offers a more holistic approach to determining currency strength, rather than using the RSI of the traded pair
alone.

It is an attempt to isolate the driving forces behind a market.

Risk management by portfolio exposure


![GBP/NZD Downtrend](/AutoTrader/assets/strength-blog/NC.png "GBP/NZD Downtrend")


Sure we 

Looking at the chart, there are a number of explanations that could explain the movement in that time period.
GBP getting weaker, NZD getting stronger, or even some combination of both.


Looking at the RSI of a single currency pair alone is not enough to conclude what the underlying driving forces are
for price movement.



Describe which currencies will be looked at


You could take a look at the indices, but this gives a single metric to strength.



# Relative Strength Index
The Relative Strenght Index (RSI) is an oscillator used to reflect the strength of an instrument, relative to 
its own recent price levels. Bound by 0 and 100, a higher value indicators greater strength, meaning that price 
is stronger relative to its recent history. There are many ways to use the RSI as a trading indicator:

1. To indicate overbought (RSI > 70) and oversold (RSI < 30) regions;
2. To detect bullish or bearish divergence (see my [previous post](../../11/08/detecting-divergence.html) about this);
3. To determine the direction of the trend (downtrend when RSI < 50, uptrend when RSI > 50).



It is important to note that the results presented don't attempt to make any predictions,
rather, this is a tool to examine the strength of different currencies at any snapshot in
time. The way you use this information will depend on your trading style; a trend trader 
may look to go long on strong currencies and short on weak currencies, whereas a contrarian 
trader might do the opposite in the hopes of mean reversion. 

One way I invisage using this tool is to validate the directional biases of positions my 
algoritms may form. Not only could this tool be used to confirm trending markets, but it could
be used to deploy algorithms which thrive in ranging markets. While trends are most easily
tackled by using a 200 period moving average, numerically detecting a ranging market is not 
so easy. However, the tool presented offers one way to do this. 



A currency pair consists of (unsurpisingly) two currencies - take for example EUR/USD. The top currency in 
this pair (the Euro), is known as the 'quote currency', while the bottom currency (the US dollar) is known
as the base currency. We make this distinction because 

trading the EUR/USD pair actually involves to transactions 



Compare this to simply using a 200EMA.



Consider using the tool on multiple timeframes



## Calculating RSI


```py
quote_currencies = {}
base_currencies = {}

for instrument in instruments:
    # Determine base and quote currency
    base_currency = instrument[-3:]
    quote_currency = instrument[:3]
    
    # Get data for currency pair
    data = get_data.oanda(instrument, 'D', count=candle_duration)
    
    # Calculate RSI
    rsi = TA.RSI(data, rsi_period)
    
    # Add to dictionaries
    if quote_currency in quote_currencies:
        # Currency already in dict
        rsi_df = quote_currencies[quote_currency]
        rsi_df[base_currency] = rsi
    else:
        # Currency not yet in dict, create new entry
        rsi_df = rsi.to_frame(base_currency)
    quote_currencies[quote_currency] = rsi_df
    
    if base_currency in base_currencies:
        # Currency already in dict
        inv_rsi_df = base_currencies[base_currency]
        inv_rsi_df[quote_currency] = 100-rsi
    else:
        # Currency not yet in dict, create new entry
        inv_rsi_df = (100-rsi).to_frame(quote_currency)
    base_currencies[base_currency] = inv_rsi_df
```


Now we have two dictionaries (one for the quote currencies and one for the base currencies) containing
the RSI.

Strength of EUR, in relation to each of the other currencies. 

```py
>>> quote_currencies['EUR'].tail(5)

                                 USD        GBP  ...        JPY        NZD
2021-11-10 22:00:00+00:00  31.744920  62.941167  ...  37.534505  50.870087
2021-11-11 22:00:00+00:00  31.204319  54.018673  ...  35.018237  45.798325
2021-11-14 22:00:00+00:00  25.190594  41.648786  ...  29.264566  37.070776
2021-11-15 22:00:00+00:00  22.223418  34.511404  ...  33.950544  43.147900
2021-11-16 22:00:00+00:00  20.995073  33.347071  ...  31.897378  40.293189
```






Sometimes a currency is the base currency, sometimes it is the quote currency. So,
we want to combine the data of the `quote_currencies` dictionary with the data of the 
`base_currencies` dictionary.


## Combining RSI History

```py
# Combine base and quote currency lists
currencies = quote_currencies.keys() | base_currencies.keys()
combined = {}
for currency in currencies:
    if currency in base_currencies and currency in quote_currencies:
        combined[currency] = pd.merge(base_currencies[currency],
                                      quote_currencies[currency], 
                                      left_index=True, 
                                      right_index=True)
    elif currency in base_currencies:
        combined[currency] = base_currencies[currency]
    else:
        combined[currency] = quote_currencies[currency]
```


Now we have all the RSI data in a single dictionary. 



## Averaging the Results

We can perform some rudimentary statistics on the data. In the code snippet below, I take the 
row-wise mean and standard deviation of the RSI data for each currency in the `combined` 
dictionary.


```py
for instrument in combined:
    combined[instrument]['mean'] = combined[instrument].mean(axis=1)
    combined[instrument]['stdev'] = combined[instrument].std(axis=1)
    combined[instrument]['lower'] = combined[instrument]['mean']-combined[instrument]['stdev']
    combined[instrument]['upper'] = combined[instrument]['mean']+combined[instrument]['stdev']
```



# Visualising Strength
There are three useful ways in which the information calculated above may be visualised. The first presents 
the trends of currency strengths over time.

The second and third methods represent a snapshot of the currency strengths at some point in time. 

These visualisations are provided below.



## Strength Trends
The figure below illustrates how the strengths of the selected currencies have varied over time. The plots
also include Bollinger-style bands representing the standard deviation of the currency strength at each 
point in time.


<iframe 
	src="/AutoTrader/assets/strength-blog/strength-trends.html"
	data-src="/AutoTrader/assets/strength-blog/strength-trends.html" 
	id="iframe" 
	loading="lazy" 
	style="width:100%; margin-top:1em; height:830px; overflow:hidden;" 
	data-ga-on="wheel" data-ga-event-category="iframe" 
	data-ga-event-action="wheel"
>
</iframe>


When the bands squeeze, there is increased confidence in the strength metric.


## Strength Snapshot
Rather than looking at the strength over time, it may be convenient to look at all currency strengths at 
a single time. The figure below does exaclty this - it is simply a slice of the trends in the previous 
figure. Again, the standard deviation of the strength metric is represented, this time with error bars.
Consequently, the smaller the error bars, the greater confidence you may have in the strength of the 
currency.


<iframe 
	src="/AutoTrader/assets/strength-blog/strength-slice.html"
	data-src="/AutoTrader/assets/strength-blog/strength-slice.html" 
	id="iframe" 
	loading="lazy" 
	style="width:75%; margin:auto; display:block; height:640px; overflow:hidden;" 
	data-ga-on="wheel" data-ga-event-category="iframe" 
	data-ga-event-action="wheel"
>
</iframe>


## Strength Heatmap
An alternative representation of the slice shown above is a heatmap. In this case, the ratios of currency strengths
are visualised. 

This provides a quick insight into currency pairs which have been strongly trending, and those which are ranging. 

This information can of course be gleaned from the previous figures presented, but it is nonetheless a convenient
visualisation.

<iframe 
	src="/AutoTrader/assets/strength-blog/strength-heatmap.html"
	data-src="/AutoTrader/assets/strength-blog/strength-heatmap.html" 
	id="iframe" 
	loading="lazy" 
	style="width:61%; margin:auto; display:block; height:530px; overflow:hidden;" 
	data-ga-on="wheel" data-ga-event-category="iframe" 
	data-ga-event-action="wheel"
>
</iframe>





## Comparing to Price



Let us now revisit the GBP/NZD chart




<iframe 
	src="/AutoTrader/assets/strength-blog/nov13-strength-slice.html"
	data-src="/AutoTrader/assets/strength-blog/nov13-strength-slice.html" 
	id="iframe" 
	loading="lazy" 
	style="width:75%; margin:auto; display:block; height:640px; overflow:hidden;" 
	data-ga-on="wheel" data-ga-event-category="iframe" 
	data-ga-event-action="wheel"
>
</iframe>


From this chart we can now see that the strong downtrend in GBP/NZD seen in November of 2018 was actually the 
coalescence of GBP weakening and NZD strengthening. Sure, if you were reading the news every day, you might be 
able to speculate the reasons for GBP being weak or NZD being strong, but this is an algo trading blog.

The method presented here is a relatively easy way to examing currency strengths from the interaction across many 
markets.








Include charts from the times shown, to support strength metrics

Ie. show strong/weak currency pair to be trending up, etc.

Also mention the timestamp of the charts provided 




![EUR/USD Daily Candles](/AutoTrader/assets/strength-blog/EU.png "EUR/USD Daily Candles")



![NZD/CHF Daily Candles](/AutoTrader/assets/strength-blog/NC.png "NZD/CHF Daily Candles")






# Applications
How can this information be used



## Confirmation
Confirmation of trends or of ranging market conditions



## Risk Management
Portfolio risk management / asset allocation


## Forecasting

Feature engineering for ML?


## Benchmarking
Assessing the performance of trades against the currency strength



## Entry and Exit Conditions
Lower timeframes to generate entry and exit signals along with larger trend















# Full Code

The complete code used to prepare this post is available on my GitHub [here]().

The code provided is dependent on AutoTrader. Specifically, the following sub-modules:
- `autotrader.lib.instrument_list`: required to retrieve currency pair names from method `get_watchlist`
- `autotrader.lib.autodata`: required to retrieve price data from `GetData`
- `autotrader.lib.environment_manager`: to read the global configuration file


Note that you will need an account with Oanda, and will need to have set up your API key in the
global configuration file. If you do not want to make an account with Oanda, you would have to
modify the code below to work with the symbol codes of wherever you get your data from. The 
changes would then just be to how you extract the base and quote currency of each pair.



