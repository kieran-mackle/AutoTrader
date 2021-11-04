---
title: AutoTrader Live Trade Performance
# cover: None
tags: live-trading
aside:
    toc: false
---

(Turn off right sidebar)

This post marks the first in a series documenting the performance of my 



Although AutoTrader is a completely free-to-use software package, I feel that this series of posts is important to validate the functionality of the framework.


# Strategy
In the interest of maintaining an edge, I will not be revealing the details of my strategy. However, I will provide the following generalities:
- the characteristics of the algorithm change depending on market conditions (ie. ranging or trending)
- The strategy is portfolio-based.
- I will be trading FX currencies and indices 
- all trades and orders are placed through AutoTrader, but trades will be supervised daily to ensure expected behaviour.
- all trades have clearly defined entries and exits. Outside of the price range defined by these points, the bot trading the strategy will be terminated.
- position sizes are calculated based on risk management principles.
- the trading account has 30:1 leverage 

Hopefully, many of these points are not very surprising or insightful - they are simply good practices of trading. 

A final comment about the strategy is that it is possibly the most simple strategy I have tested to date. Despite spending countless hours trawling through YouTube and reading through trading forums, 

So why do I believe in this strategy? Because it is built upon risk management... etc



# Performance Logging
To keep track of my algo's performance, I will be using the logging script shown below. Every 5 minutes, this code
will ping the broker and take a snapshot of my account details at that time. These details will then be written to the 
csv file, *equity_history.csv*. For now, keeping track of my account balance, net asset value, margin usage, number of 
open trades, and number of positions is enough information to work with when analysing performance.  

```py
from autotrader.brokers.oanda.Oanda import Oanda
from datetime import datetime
import time

oanda_config = {"API": "api-fxtrade.oanda.com",
                "ACCESS_TOKEN":"XXXX-YYYY", 
                "PORT": 443, 
                "ACCOUNT_ID": "XXX-XXX-XXXXXXXX-XXX"}

while True:
    try:
        broker = Oanda(oanda_config, None)
        summary = broker.get_summary()
        time_now = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        NAV = broker.get_NAV()
        balance = broker.get_balance()
        margin_pc = summary.body['account'].marginCloseoutPercent
        open_trades = summary.body['account'].openTradeCount
        open_positions = summary.body['account'].openPositionCount
        
        with open('equity_history.csv', 'a+') as f:
            f.write(f"{time_now},{NAV},{balance},{margin_pc},{open_trades},{open_positions}\n")

        # Everything is good, sleep for 5 minutes
        time.sleep(5*60)
        
    except:
        # Some error occured, sleep for 10 seconds then try again
        time.sleep(10)
```

## Performance Visualisation
The script below was prepared to visualise the results written to the csv file by the logger script.

```py
import pandas as pd
from bokeh.plotting import figure, show, output_file
from bokeh.models import (
    ColumnDataSource,
    HoverTool
)
from bokeh.layouts import gridplot

eqh = pd.read_csv('equity_history.csv')
eqh.time = pd.to_datetime(eqh.time)
eqh = eqh.set_index('time')
source = ColumnDataSource(eqh)
output_file('ROE.html', title='Return on equity')

' ~~~~~~~~~~ ROI ~~~~~~~~~~ '
initial_balance = eqh.NAV[0]
eqh['roi'] = 100*(eqh.NAV - initial_balance)/initial_balance
eqh['date'] = eqh.index
eqh['zeroes'] = 0
eqh['margin'] = 100*eqh.margin_pc
eqh['int_index'] = eqh.reset_index(drop=True).index
eqh['profit'] = eqh.NAV.diff()
eqh['cumulative'] = eqh.profit.cumsum().round(2)
eqh['highValue'] = eqh['cumulative'].cummax()
eqh['drawdown'] = eqh['cumulative'] - eqh['highValue']
eqh['ddpc'] = -100*eqh['drawdown']/(eqh.NAV + eqh['highValue'])
source = ColumnDataSource(eqh)

hovertool = HoverTool(tooltips=[('Date', '@date{%d-%m-%Y}'),
                                ("ROE", "@roi %")],
                      formatters = {'@date': 'datetime'},
                      mode='vline')

nav = figure(plot_width     = 1000,
             plot_height    = 200,
             title          = 'Return on Equity (%)',
             tools          = "xpan,xwheel_zoom,undo,redo,reset,save,crosshair",
             active_drag    = 'xpan',
             active_scroll  = 'xwheel_zoom',
             x_axis_type    = 'datetime'
             )

nav.line(x="int_index", 
            y="roi",
          source=source)
nav.add_tools(hovertool)


' ~~~~~~~~~~ OPEN TRADERS ~~~~~~~~~~ '
tdshover = HoverTool(tooltips=[('Date', '@date{%d-%m-%Y}'),
                               ("trades", "@trades")],
                      formatters = {'@date': 'datetime'},
                      mode='vline')
tds = figure(plot_width     = 1000,
             plot_height    = 200,
             title          = 'Number of open trades',
             tools          = "xpan,xwheel_zoom,undo,redo,reset,save,crosshair",
             active_drag    = 'xpan',
             active_scroll  = 'xwheel_zoom',
             x_axis_type    = 'datetime',
             x_range        = nav.x_range)
tds.line('int_index', 
         'trades', 
         line_color = 'black',
         source = source)
tds.add_tools(tdshover)

' ~~~~~~~~~~ OPEN POSITIONS ~~~~~~~~~~ '
poshover = HoverTool(tooltips=[('Date', '@date{%d-%m-%Y}'),
                               ("positions", "@positions")],
                      formatters = {'@date': 'datetime'},
                      mode='vline')
pos = figure(plot_width     = 1000,
             plot_height    = 200,
             title          = 'Number of positions',
             tools          = "xpan,xwheel_zoom,undo,redo,reset,save,crosshair",
             active_drag    = 'xpan',
             active_scroll  = 'xwheel_zoom',
             x_axis_type    = 'datetime',
             x_range        = nav.x_range)
pos.line('int_index', 
         'positions', 
         line_color = 'black',
         source = source)
pos.add_tools(poshover)

' ~~~~~~~~~~ MARGIN PERCENTAGE ~~~~~~~~~~ '
mpchover = HoverTool(tooltips=[('Date', '@date{%d-%m-%Y}'),
                               ("margin", "@margin%")],
                      formatters = {'@date': 'datetime'},
                      mode='vline')
mpc = figure(plot_width     = 1000,
             plot_height    = 200,
             title          = 'Margin %',
             tools          = "xpan,xwheel_zoom,undo,redo,reset,save,crosshair",
             active_drag    = 'xpan',
             active_scroll  = 'xwheel_zoom',
             x_axis_type    = 'datetime',
             x_range        = nav.x_range)
mpc.line(x="int_index", 
         y="margin", 
         line_color = 'black',
         source = source)
mpc.add_tools(mpchover)


' ~~~~~~~~~~ CONSTRUCT FINAL FIGURE ~~~~~~~~~~ '
plots = [nav, tds, pos, mpc]

for plot in plots:
    plot.xaxis.major_label_overrides = {
                    i: date.strftime('%b %d') for i, date in enumerate(pd.to_datetime(eqh["date"]))
                }
fig = gridplot(plots, 
               ncols = 1, 
               toolbar_location = 'right',
               toolbar_options = dict(logo = None), 
               merge_tools = True
               )

show(fig)
```


# Performance to Date

