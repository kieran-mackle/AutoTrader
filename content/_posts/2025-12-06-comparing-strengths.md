---
title: Comparing Currency Strengths
cover: /assets/strength-blog/cover.png
tags: forex trading
---




A currency pair consists of (unsurpisingly) two currencies - take for example EUR/USD. The top currency in 
this pair (the Euro), is known as the 'quote currency', while the bottom currency (the US dollar) is known
as the base currency. We make this distinction because 

trading the EUR/USD pair actually involves to transactions 



# The Relative Strength Index
The Relative Strenght Index (RSI) is an oscillator used to reflect the strength of an instrument, relative to 
its own recent price levels. Bound by 0 and 100, a higher value indicators greater strength, meaning that price 
is stronger relative to its recent history. There are many ways to use the RSI as a trading indicator;
1) To indicate overbought (RSI > 70) and oversold (RSI <30) regions
2) To detect bullish or bearish divergence (see my [previous post]() about this)
3) To determine the direction of the trend (downtrend when RSI < 50, uptrend when RSI > 50)






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




Compare this to simply using a 200EMA.



Consider using the tool on multiple timeframes




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

Also mention the timestamp of the charts provided 




![EUR/USD Daily Candles](/AutoTrader/assets/strength-blog/EU.png "EUR/USD Daily Candles")



![NZD/CHF Daily Candles](/AutoTrader/assets/strength-blog/NC.png "NZD/CHF Daily Candles")



# Full Code

Note that you will need an account with Oanda, and will need to have set up your API key in the
global configuration file. If you do not want to make an account with Oanda, you would have to
modify the code below to work with the symbol codes of wherever you get your data from. The 
changes would then just be to how you extract the base and quote currency of each pair.


```py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Currency Strength Comparator
----------------------------
"""

from autotrader.lib.instrument_list import get_watchlist
from autotrader.lib.autodata import GetData
from autotrader.lib import environment_manager, read_yaml
from finta import TA
from bokeh.plotting import figure, show, output_file
from bokeh.models import (
    ColorBar, 
    LinearColorMapper, 
    LinearAxis, 
    Range1d, 
    ColumnDataSource)
from bokeh.palettes import Greens, OrRd
from bokeh.layouts import gridplot
import numpy as np
import pandas as pd
from time import sleep
from datetime import datetime

# Analysis parameters
rsi_period = 10
candle_duration = 365
rsi_tol = 50
std_tol = 12

# Specify slice index - the index of the data to plot in heatmap and slice
slice_index = -1

global_config = read_yaml.read_yaml('./config' + '/GLOBAL.yaml')
broker_config = environment_manager.get_config('demo', global_config, 'Oanda')
get_data = GetData(broker_config, allow_dancing_bears=True)
instruments = get_watchlist('all', 'oanda')

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


"                        Combine Currency Dictionaries                      "
"                        =============================                      "
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



"                     Calculate Mean and Standard Deviation                 "
"                     =====================================                 "
for instrument in combined:
    combined[instrument]['mean'] = combined[instrument].mean(axis=1)
    combined[instrument]['stdev'] = combined[instrument].std(axis=1)
    combined[instrument]['lower'] = combined[instrument]['mean']-combined[instrument]['stdev']
    combined[instrument]['upper'] = combined[instrument]['mean']+combined[instrument]['stdev']
    

"                        Plot Currency Strength Trends                      "
"                        =============================                      "
strength_figs = []
for instrument in combined:
    if len(strength_figs)==0:
        fig = figure(title = f'Strength of {instrument}',
                      height = 200,
                      width = 400,
                      x_axis_type = 'datetime',
                      tools          = "pan,xwheel_zoom,box_zoom,undo,redo,reset,save",
                      active_drag    = 'pan',
                      active_scroll  = 'xwheel_zoom')
    else:
        fig = figure(title = f'Strength of {instrument}',
                      height = 200,
                      width = 400,
                      x_axis_type = 'datetime',
                      x_range = strength_figs[-1].x_range,
                      tools          = "pan,xwheel_zoom,box_zoom,undo,redo,reset,save",
                      active_drag    = 'pan',
                      active_scroll  = 'xwheel_zoom')
                  
    fig.varea(combined[instrument].index, 
              combined[instrument]['lower'], 
              combined[instrument]['upper'],
              fill_alpha=0.6)
    fig.line(combined[instrument].index, combined[instrument]['mean'])
    
    fig.line(combined[instrument].index, 100, line_color='black')
    fig.line(combined[instrument].index, 50, line_dash='dashed', line_color='black')
    fig.line(combined[instrument].index, 0, line_color='black')
    
    # Create secondary y-axis
    fig.extra_y_ranges = {"stdev": Range1d(start=0, end=np.max(combined[instrument]['stdev']))}
    fig.add_layout(LinearAxis(y_range_name="stdev"), 'right')
    fig.line(combined[instrument].index, 
              combined[instrument]['stdev'], 
              y_range_name="stdev", 
              color='black')
    
    strength_figs.append(fig)
    
output_file('strength-trends.html')
fig = gridplot(strength_figs, 
               ncols = 2, 
               toolbar_location = 'right',
               toolbar_options = dict(logo = None), 
               merge_tools = True
               )
show(fig)
sleep(0.2)


time_string = datetime.strftime(data.index[slice_index], "%H:%M %b %d, %Y")
print(f"Slices shown for {time_string}.")


"                        Plot Slice of Currency Strengths                   "
"                        ================================                   "
cats = [curr for curr in combined]
lower = [combined[curr]['lower'][slice_index] for curr in combined]
upper = [combined[curr]['upper'][slice_index] for curr in combined]
mid = [combined[curr]['mean'][slice_index] for curr in combined]
std = [combined[curr]['stdev'][slice_index] for curr in combined]

source = ColumnDataSource({'cats': cats, 
                           'lower': lower, 
                           'mid': mid,
                           'upper': upper,
                           'std': std})

output_file('strength-slice.html')
p = figure(title = 'Snapshot of Currency Strengths',
           tools = "", 
           background_fill_color = "#efefef", 
           x_range = cats, 
           toolbar_location = None,
           tooltips = [('Currency', '@cats'), 
                       ('Strength', '@mid'),
                       ('STD', '@std')]
           )
p.segment('cats', 'lower', 'cats', 'upper', line_color="black", source=source)
p.rect('cats', 'lower', 0.2, 0.01, line_color="black", source=source)
p.circle('cats', 'mid', size=10, line_color="black", source=source)
p.rect('cats', 'upper', 0.2, 0.01, line_color="black", source=source)
show(p)
sleep(0.2)


"                        Plot Heatmap of Currency Strengths                 "
"                        ==================================                 "
# Calculate currency strength ratios
currency_1 = list(np.concatenate([[i]*len(currencies) for i in list(currencies)], axis=0))
currency_2 = list(currencies)*len(currencies)
ratio_df = pd.DataFrame({'base': currency_1, 'quote': currency_2})
ratios = []
for i in range(len(ratio_df)):
    ratios.append(combined[ratio_df.base[i]]['mean'][slice_index]/combined[ratio_df.quote[i]]['mean'][slice_index])
    
ratio_df['ratio'] = ratios

# Define colour mapping
n = 6
green = Greens[n][::-1]
red = OrRd[n]
mapper = LinearColorMapper(palette = red+green, 
                           low = ratio_df.ratio.min(), 
                           high = ratio_df.ratio.max())

# Create heatmap
output_file('strength-heatmap.html')
hm = figure(width = 500, 
            height = 500, 
            title = "Currency Strength Heat Map",
            y_range = list(currencies),
            x_range = list(reversed(list(currencies))),
            toolbar_location = None, 
            tools = "", 
            x_axis_location = "above",
            tooltips = [('Pair', '@base/@quote'), ('ratio', '@ratio')])

hm.rect(x='base',y='quote', width=1, height=1, source=ratio_df,
        line_color=None, fill_color={'field': 'ratio','transform': mapper})

color_bar = ColorBar(color_mapper=mapper, 
                     major_label_text_font_size="7px",
                     label_standoff=6, 
                     border_line_color=None)
hm.add_layout(color_bar, 
              'right')
show(hm)
```




