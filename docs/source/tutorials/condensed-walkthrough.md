# Condensed AutoTrader Walkthrough
This page is a condensed version of the [detailed walkthrough](walkthrough), 
which goes through the process of building and running a strategy in 
AutoTrader. If you are familiar with Python, it should be sufficient to get 
you up and running.

```{tip}
The code for the MACD crossover strategy shown in this tutorial can be found in the
<a href="https://github.com/kieran-mackle/autotrader-demo" target="_blank">demo repository</a>.
```

## Strategy Rules
The rules for the MACD crossover strategy are as follows.

1. Trade in the direction of the trend, as determined by the 200EMA.
2. Enter a long position when the MACD line crosses *up* over the signal 
line, and enter a short when the MACD line crosses *down* below the 
signal line.
3. To ensure only the strongest MACD signals, the crossover must occur 
below the histogram zero line for long positions, and above the histogram 
zero line for short positions.
3. Stop losses are set at recent price swings/significant price levels.
4. Take profit levels are set at 1:1.5 risk-to-reward.

An example of a long entry signal from this strategy is shown in the 
image below (generated using [AutoTrader IndiView](../features/visualisation)).

![MACD crossover strategy](../assets/images/long_macd_signal.png "Long trade example for the MACD Crossover Strategy")



## Strategy Construction
Strategies in AutoTrader are built as class objects. They contain the logic 
required to transform data into a trading signals. Generally speaking, a 
strategy class will be instantiated with the name of the instrument being 
traded and the strategy parameters, but you can customise what gets passed
in using the [strategy configuration](strategy-config).


### Configuration
```{admonition} Follow Along
Follow along in the demo repository: 
config/[macd.yaml](https://github.com/kieran-mackle/autotrader-demo/blob/main/config/macd.yaml)
```

The [strategy configuration](strategy-config) file defines all strategy 
parameters and instruments to trade with the strategy. The `PARAMETERS` 
of this file will be passed into your strategy for you to use there. 


```yaml
# macd.yaml
NAME: 'Simple Macd Strategy'    # strategy name
MODULE: 'macd'                  # strategy module
CLASS: 'SimpleMACD'             # strategy class
INTERVAL: '1h'                  # stategy timeframe
PARAMETERS:                     # strategy parameters
  ema_period: 200
  MACD_fast: 12
  MACD_slow: 26
  MACD_smoothing: 9
  
  # Exit level parameters
  RR: 1.5

WATCHLIST: ['EURUSD=X']         # strategy watchlist
```


### Class Object
Although strategy construction is extremely flexible, the class **must** 
contain an `__init__` method, and a method named `generate_signal`. The 
first of these methods is called whenever the strategy is instantiated.

By default, strategies in AutoTrader are instantiated with three named 
arguments:

1. The name of the instrument being traded in this specific instance (`instrument`).
2. The strategy parameters (`parameters`)
3. The trading instruments data (`data`)

When backtesting, the `data` provided to `__init__` is for the entire 
backtest period. This allows you to calculate all indicators for 
plotting purposes down the line, but it shouldn't be used in the 
`generate_signal` method, as this could introduce look-ahead.

Aside from the `__init__` method, your strategy must have a method named 
`generate_signal`. This method gets called by AutoTrader everytime new
data becomes available, and expects a trading [Order](order-object) in 
return.

A long order can be created by specifying `direction=1` when creating the 
`Order`, whereas a short order can be created by specifying `direction=-1`. 
If there is no trading signal this update, you can just return `None`. 
We also define our exit targets 
by the `stop_loss` and `take_profit` arguments. The strategy below uses
the `generate_exit_levels` helper method to calculate these prices.



```{tip}
Take a look at the 
<a href="https://github.com/kieran-mackle/AutoTrader/blob/main/templates/strategy.py" target="_blank">template strategy</a>
provided in the Github repository.
```


```py
import pandas as pd
from finta import TA
from datetime import datetime
from autotrader.strategy import Strategy
import autotrader.indicators as indicators
from autotrader.brokers.trading import Order
from autotrader.brokers.broker import Broker


class SimpleMACD(Strategy):
    """Simple MACD Strategy

    Rules
    ------
    1. Trade in direction of trend, as per 200EMA.
    2. Entry signal on MACD cross below/above zero line.
    3. Set stop loss at recent price swing.
    4. Target 1.5 take profit.
    """

    def __init__(
        self, parameters: dict, instrument: str, broker: Broker, *args, **kwargs
    ) -> None:
        """Define all indicators used in the strategy."""
        self.name = "MACD Trend Strategy"
        self.params = parameters
        self.broker = broker
        self.instrument = instrument

    def create_plotting_indicators(self, data: pd.DataFrame):
        # Construct indicators dict for plotting
        ema, MACD, MACD_CO, MACD_CO_vals, swings = self.generate_features(data)
        self.indicators = {
            "MACD (12/26/9)": {
                "type": "MACD",
                "macd": MACD.MACD,
                "signal": MACD.SIGNAL,
                "histogram": MACD.MACD - MACD.SIGNAL,
            },
            "EMA (200)": {"type": "MA", "data": ema},
        }

    def generate_features(self, data: pd.DataFrame):
        # 200EMA
        ema = TA.EMA(data, self.params["ema_period"])

        # MACD
        MACD = TA.MACD(
            data,
            self.params["MACD_fast"],
            self.params["MACD_slow"],
            self.params["MACD_smoothing"],
        )
        MACD_CO = indicators.crossover(MACD.MACD, MACD.SIGNAL)
        MACD_CO_vals = indicators.cross_values(MACD.MACD, MACD.SIGNAL, MACD_CO)

        # Price swings
        swings = indicators.find_swings(data)

        return ema, MACD, MACD_CO, MACD_CO_vals, swings

    def generate_signal(self, dt: datetime):
        """Define strategy to determine entry signals."""
        # Get OHLCV data
        data = self.broker.get_candles(self.instrument, granularity="1h", count=300)
        if len(data) < 300:
            # This was previously a check in AT
            return None

        # Generate indicators
        ema, MACD, MACD_CO, MACD_CO_vals, swings = self.generate_features(data)

        # Create orders
        if (
            data["Close"].values[-1] > ema.iloc[-1]
            and MACD_CO.iloc[-1] == 1
            and MACD_CO_vals.iloc[-1] < 0
        ):
            exit_dict = self.generate_exit_levels(signal=1, data=data, swings=swings)
            new_order = Order(
                direction=1,
                size=1,
                stop_loss=exit_dict["stop_loss"],
                take_profit=exit_dict["take_profit"],
            )

        elif (
            data["Close"].values[-1] < ema.iloc[-1]
            and MACD_CO.iloc[-1] == -1
            and MACD_CO_vals.iloc[-1] > 0
        ):
            exit_dict = self.generate_exit_levels(signal=-1, data=data, swings=swings)
            new_order = Order(
                direction=-1,
                size=1,
                stop_loss=exit_dict["stop_loss"],
                take_profit=exit_dict["take_profit"],
            )

        else:
            new_order = None

        return new_order

    def generate_exit_levels(
        self, signal: int, data: pd.DataFrame, swings: pd.DataFrame
    ):
        """Function to determine stop loss and take profit levels."""
        stop_type = "limit"
        RR = self.params["RR"]

        if signal == 0:
            stop = None
            take = None
        else:
            if signal == 1:
                stop = swings["Lows"].iloc[-1]
                take = data["Close"].iloc[-1] + RR * (data["Close"].iloc[-1] - stop)
            else:
                stop = swings["Highs"].iloc[-1]
                take = data["Close"].iloc[-1] - RR * (stop - data["Close"].iloc[-1])

        exit_dict = {"stop_loss": stop, "stop_type": stop_type, "take_profit": take}

        return exit_dict
```



## Backtesting

An easy and organised way to deploy a trading bot is to set up a 
run file. Here you import AutoTrader, configure the run settings and 
deploy your bot. This is all achieved in the example below.


```python
# run.py
from autotrader import AutoTrader

# Create AutoTrader instance, configure it, and run backtest
at = AutoTrader()
at.configure(verbosity=1, show_plot=True, feed="yahoo")
at.add_strategy("macd")
at.backtest(start="1/6/2023", end="1/2/2024", localize_to_utc=True)
at.virtual_account_config(initial_balance=1000, leverage=30)
at.run()

```

Let's dive into this a bit more:
- We begin by importing AutoTrader and creating an instance 
using `at = AutoTrader()`. 
- Next, we use the [`configure`](autotrader-configure) method to set 
the verbosity of the code and tell AutoTrader that you would like to see 
the backtest plot. We also define the [run mode](autotrader-run-modes)
and update interval to `1h`, meaning that we will step through the backtest
data by 1 hour at a time.
- Next, we add our strategy using the `add_strategy` method. Here we pass the 
file prefix of the strategy configuration file, located (by default) in the 
`config/` [directory](rec-dir-struc). Since our strategy configuration file
is named `macd.yaml`, we pass in 'macd'.
- We then use the [`backtest`](autotrader-backtest-config) method to define 
the backtest period. In this example, we set the start and end dates of the
backtest.
- Since we will be simulating trading (by backtesting), we also need to configure
the virtual trading account. We do this with the `virtual_account_config` method.
Here we set the account leverage to 30. You can also configure trading costs,
bid/ask spread, initial balance and other settings here.
- Finally, we run AutoTrader with the command `at.run()`.

Simply run this file, and AutoTrader will do its thing.




### Backtest Results
With a verbosity of 1, you will see an output similar to that shown below. 
As you can see, there is a detailed breakdown of trades taken during the
backtest period. Since we told AutoTrader to plot the results, you will also 
see the interactive chart shown below.

```
    ___         __      ______               __         
   /   | __  __/ /_____/_  __/________ _____/ /__  _____
  / /| |/ / / / __/ __ \/ / / ___/ __ `/ __  / _ \/ ___/
 / ___ / /_/ / /_/ /_/ / / / /  / /_/ / /_/ /  __/ /    
/_/  |_\__,_/\__/\____/_/ /_/   \__,_/\__,_/\___/_/     
                                                        

[*********************100%***********************]  1 of 1 completed
BACKTEST MODE

AutoTraderBot assigned to trade EURUSD=X with virtual broker using Simple Macd Strategy.

Trading...

31539600.0it [00:19, 1630112.41it/s]                                                                                                                                          
Backtest complete (runtime 19.348 s).

----------------------------------------------
               Trading Results
----------------------------------------------
Start date:              Jan 20 2021 04:00:00
End date:                Dec 31 2021 13:00:00
Duration:                345 days 09:00:00
Starting balance:        $1000.0
Ending balance:          $1140.75
Ending NAV:              $1170.16
Total return:            $140.75 (14.1%)
Maximum drawdown:        -18.97%
Total no. trades:        175
Total fees paid:         $0.0
Win rate:                21.7%
Max win:                 $36.51
Average win:             $25.26
Max loss:                -$21.57
Average loss:            -$16.38
Longest winning streak:  4 trades
Longest losing streak:   11 trades
Average trade duration:  1 day, 3:43:38
Positions still open:    1
Cancelled orders:        5

            Summary of long trades
----------------------------------------------
Number of long trades:   36
Win rate:                41.7%
Max win:                 $36.51
Average win:             $25.22
Max loss:                -$21.18
Average loss:            -$17.23

             Summary of short trades
----------------------------------------------
Number of short trades:  54
Win rate:                42.6%
Max win:                 $31.85
Average win:             $25.28
Max loss:                -$21.57
Average loss:            -$15.86
```


<iframe data-src="../_static/charts/macd_backtest_demo.html" id="iframe" loading="lazy" style="width:100%; margin-top:1em; height:720px; overflow:hidden;" data-ga-on="wheel" data-ga-event-category="iframe" data-ga-event-action="wheel" src="../_static/charts/macd_backtest_demo.html"></iframe>





## Going Live
Taking a strategy live is as easy as changing a few lines in your runfile.
Say you would like to trade your strategy on the cryptocurrency exchange 
[Bybit](https://www.bybit.com/invite?ref=7NDOBW). 
Then, all you need to do is specify this 
as the `broker` in the `configure` method, as shown below. You will
just need to make sure you have provided the relevant API keys in your 
`keys.yaml` file to connect to your exchange.

```python
from autotrader import AutoTrader

at = AutoTrader()
at.configure(verbosity=1, broker='ccxt:bybit') 
at.add_strategy('macd')
at.run()
```


What if you wanted to paper trade your strategy before putting real money into
it? Simply configure a virtual trading account and specify the exchange as 
`ccxt:bybit` (or whatever `broker` you specify in `configure`) and then you will
be paper trading! Doing this, AutoTrader's virtual broker mirrors the real-time
orderbook of the exchange specified, making execution of orders as accurate as 
possible.

```python
from autotrader import AutoTrader

at = AutoTrader()
at.configure(verbosity=1, broker='ccxt:bybit') 
at.add_strategy('macd') 
at.virtual_account_config(leverage=30, exchange='ccxt:bybit')
at.run()
```
