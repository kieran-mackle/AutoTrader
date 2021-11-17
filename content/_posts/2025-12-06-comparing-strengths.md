---
title: Comparing Currency Strengths
cover: /assets/strength-blog/cover.png
tags: forex trading
---




# The Relative Strength Index







It is important to note that the results presented don't attempt to make any predictions,
rather, this is a tool to examine the strength of different currencies at any snapshot in
time. The way you use this information will depend on your trading style; a trend trader 
may look to go long on strong currencies and short on weak currencies, whereas a contrarian 
trader might do the opposite in the hopes of mean reversion. 






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



```py
quote_currencies['EUR'].tail(5)

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


<br>


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


<br>

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


Include charts from the times shown, to support strength metrics

Ie. show strong/weak currency pair to be trending up, etc.





