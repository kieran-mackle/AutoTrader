# Live Trading With AutoTrader

What use would backtesting be if you can't take the same strategy live? This is no concern when you use 
AutoTrader, which features a seamless transition from backtesting to livetrading.


## Supported Brokers
AutoTrader currently supports Oanda and Interactive Brokers for livetrading.


## Backtest Validation
Another important feature of AutoTrader is its backtest validation functionality. 

To ensure that the backtest framework is correctly modelling market dynamics, a validation study was performed. This 
study consisted of two phases: 

  1) Data collection: AutoTrader was run in live-trade mode for one month to build a real trade history dataset

  2) Backtest validation: AutoTrader was run in backtest mode over the live-trade period to see how the predicted performance 
     of the backtest algorithm.

Performing such a study is made easy with [AutoPlot](autoplot-docs).



```python
# Run backtest validation
at              = AutoTrader()
at.backtest     = True
at.verbosity    = 1
at.config_file  = 'simple_macd'
at.show_plot    = True
at.validation_file = r'path\to\trade-history.csv'
at.instruments  = 'EUR_USD'
at.run()
```


Running with parameters set during backtesting

<iframe data-src="../_static/charts/bt-validation1.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:900px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/bt-validation1.html"></iframe>


```
            Backtest Validation
-------------------------------------------
Difference between final portfolio balance between
live-trade account and backtest is $-48.97.
Number of live trades: 36 trades.
```



After refining the parameters

<iframe data-src="../_static/charts/bt-validation2.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:900px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/bt-validation2.html"></iframe>


```
            Backtest Validation
-------------------------------------------
Difference between final portfolio balance between
live-trade account and backtest is $-8.82.
Number of live trades: 36 trades.
```




If the trade history .csv file is from an account trading multiple instruments at the same time, the balance recorded will not
correspond to the instrument being examined exactly. This is because the balance will vary due to trades with other instruments 
on the account, which will not be accounted for. Therefore, there is no point comparing the portfolio balance for this validation.
When this is the case, simply set the `plot_validation_balance` flag to `False` to hide it.
```python
at.plot_validation_balance = False
```









