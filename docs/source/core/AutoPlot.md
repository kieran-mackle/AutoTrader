(autoplot-docs)=
# AutoPlot
`from autotrader import AutoPlot`

AutoPlot is the automated plotting module of AutoTrader. It is 
automatically used when visualising backtest results, but can
also be interacted with to create charts and visualise 
indicators. Refer to this 
[blog post](https://kieran-mackle.github.io/AutoTrader/2021/09/17/using-indiview.html) for an example.


```{eval-rst}
.. autoclass:: autotrader.autoplot.AutoPlot
   :noindex: configure
```


## Methods

### Configure

```{eval-rst}
.. automethod:: autotrader.autoplot.AutoPlot.configure
```

```{seealso}
Refer to the [Bokeh documentation](https://docs.bokeh.org/en/latest/docs/first_steps/first_steps_4.html#using-themes) 
for more details of the different themes.
```


### Add Plot Tools
To customise the tools of the figures produced with AutoPlot, the `add_tool`
should be used. This method simply appends the `tool_name` to the `fig_tools`
attribute of the class instance. Refer to the 
[Bokeh documentation](https://docs.bokeh.org/en/latest/docs/user_guide/tools.html) for details on the tools available.

```{eval-rst}
.. automethod:: autotrader.autoplot.AutoPlot.add_tool
```


### Create Plot

The `plot` method is used to generate a chart. It is used in both backtest plotting and indicator viewing. 

```{eval-rst}
.. automethod:: autotrader.autoplot.AutoPlot.plot
```






## Usage

(autoplot-indi-spec)=
### Indicator Specification
To plot indicators with AutoPlot, you must provide a dictionary containing each indicator. This dictionary must be 
structured according to the example provided below. 

```python
self.indicators = {'indicator 1 name': {'type': 'indicator 2 type',
                                        'data': self.indicator_data},
                   'indicator 2 name': {'type': 'indicator 1 type',
                                        'data': self.indicator_data},
		  ...
                  }
```

In this dictionary, each key 'indicator name' is used to create the 
legend entry corresponding to the indicator. The sub-dictionary 
assigned to each indicator contains the specific information and 
associated data. The `type` key should be a string corresponding to 
the type of indicator, as defined in the table below. It is used to 
determine whether the indicator should be plotted overlayed on the 
OHLC chart, or below it on a separate plot. Finally, the data 
associated with the indicator must also be provided. For indicators 
with one set of data, such as a moving average, simply provide the 
data with the `data` key. For indicators with multiple sets of data,
such as MACD, provide a key for each set named according to the keys
specified in the table below.


| Indicator     | Type   | Keys                                  |
| :-----------: |:------:| :-----------------------------------: |
| Generic overlay indicator | `over` | `data` |
| Generic below-figure indicator | `below` | `data` |
| MACD          |`MACD`  | `macd`, `signal`, `histogram`         |
| EMA           | `MA`   | `data`                                |
| SMA           | `MA`   | `data`|
| RSI | `RSI`| `data`|
| Stochastics |`STOCHASTIC`|`K`, `D`|
| Heikin-Ashi |`Heikin-Ashi`| `data`|
|Supertrend|`Supertrend`|`data`|
|HalfTrend|`HalfTrend`|`data`|
|Swings|`Swings`|`data`|
|Engulfing|`Engulfing`|`data`|
|Crossover|`Crossover`|`data`|
|Pivot Points| `Pivot` | `data`, optionally `levels` | 
|Multiple line plot |`multi`| See below |
|Shaded bands|`bands`| See below |
|Shaded threshold| `threshold`| See below |
|Trade signals|`signals`| `data` |



#### Example Indicator Dictionary
In this dictionary, each key is used to create a legend entry corresponding to the indicator. The sub-dictionary
assigned to each key contains the specific information and associated data. The `type` key is a string corresponding
to the type of indicator, for example:
- `'type': 'MA'` for an exponential moving average (or any type of moving average)
- `'type': 'STOCH'` for stochastics
Finally, the data associated with the indicator must also be provided. For indicators with one set of data, such as a moving average,
simply provide the data with the `data` key. For indicators with multiple sets of data, such as MACD, provide a key for each set named
according to the [indicator specification](autoplot-indi-spec).
See the example below for a strategy with MACD, two RSI's and two EMA's.

```python
self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                      'macd': self.MACD,
                                      'signal': self.MACDsignal,
                                      'histogram': self.MACDhist},
                   'EMA (200)': {'type': 'MA',
                                 'data': self.ema200},
                   'RSI (14)': {'type': 'RSI',
                                'data': self.rsi14},
                   'RSI (7)': {'type': 'RSI',
                               'data': self.rsi7},
                   'EMA (21)': {'type': 'MA',
                                'data': self.ema21}
                  }
```



#### Multiple line plot
To plot multiple lines on the same figure, the `multi` indicator type can be used. In the example below, a figure with
title 'Figure title' will be created below the OHLC chart. On this figure, two lines will be plotted, with legend names
of 'Line 1 name' and 'Line 2 name'. Line 1 will be blue and line 2 will be red, as set using the 'color' key specifier.

```python
indicator_dict = {'Figure title': {'type': 'multi',
                                   'Line 1 name': {'data': line1_data,
                                                   'color': 'blue'},
                                   'Line 2 name': {'data': line2_data,
                                                   'color': 'red'},
                                   }
                  }
```

#### Shaded bands plot
To plot shaded bands, such as Bollinger Bands&reg;, the `bands` indicator type can be used. An example of using this indicator
type is provided below. 

```python
indicator_dict = {'Bollinger Bands': {'type': 'bands',
                                      'lower': bb.lower,
                                      'upper': bb.upper,
                                      'mid': bb.mid,
                                      'mid_name': 'Bollinger Mid Line'},
                  }
```

The full list of keys which can be provided with the indicator type is shown in the table below.

| Key          | Required/Optional  | Description                  | Default value    |
| ------------ | ------------------ | ---------------------------- | ---------------- |
| `band_name`  | Optional           | legend name for bands       | String provided for indicator (eg. 'Bollinger Bands') |
| `fill_color` | Optional           | color filling upper and lower bands | 'blue'  |
| `fill_alpha` | Optional           | transparency of fill (0 - 1) |    0.6      |
| `mid`        | Optional           |  data for a mid line        |    None |
| `mid_name`   | Optional           | legend name for mid line    |     'Band Mid Line' |
| `line_color` | Optional           | line color for mid line     |  'black' |


#### Shaded threshold plot
The `threshold` plot indicator type is the standalone-figure version of the `bands` indicator type. That is, instead of 
overlaying shaded bands on the OHLC chart, a new figure is created below. The same keys apply to this method as the  
keys of the `bands` indicator type, as documented in the table above. An example of using this indicator is provided
below.

```python
'RSI threshold': {'type': 'threshold',
                  'lower': 30,
                  'upper': 70,
                  'mid': rsi,
                  'mid_name': 'RSI'},
```

#### Trade signals plot
The `signals` plot indicator type can be used to overlay buy and sell signals onto the OHLC chart. To do so,
pass a DataFrame with columns named "buy" and "sell" with the `data` key. Note that the values in these coloumns 
are the prices at which the signal occurs. This means that if you have a DataFrame with Booleans corresponding to 
the buy and sell points, you will need to multiply them by the price data to shift them.



#### Unrecognised indicator type

If an indicator type isn't recognised, AutoPlot will attempt to plot it as a line plot on a new chart below the OHLC 
chart using the `data` key of the indicator. A warning message stating that the indicator is not recognised will 
also be printed. Also note that a `type` key can be used for an indicator that isn't specified above if it has 
similar plotting behaviour. See the [indicators](autoplot-indi-spec) for details on the indicators listed above.


### Minimum Working Example
As a plotting class, each instance of AutoPlot must be provided with price data in the form of OHLC data. A minimal 
working example is provided below to visualise the price data of Apple from the Yahoo finance feed of 
[AutoData](autodata-docs). 

```py
from autotrader import AutoPlot, AutoData

instrument = 'AAPL'
get_data = AutoData({'data_source': 'yahoo'})
data = get_data.fetch(instrument, '1d', 
                      start_time='2020-01-01', 
                      end_time='2021-01-01')

ap = AutoPlot(data)
ap.plot(instrument=instrument)
```