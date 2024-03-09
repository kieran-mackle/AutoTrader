# Building a Strategy to Run From a Single File

If you would like to have everything relating to your strategy in a single file, then this page is
for you. The example strategy below is for the MACD strategy developed in the 
[walkthrough](detailed-walkthrough). However, instead of keeping the strategy, strategy configuration
and runfile in separate files, we put it all in one. 

The strategy class `SimpleMACD` is the same as before, but now we include `if __name__ == "__main__":`
at the bottom of the file. This conditional will be `True` whenever we run the entire script. So
this is where our new runfile will sit. Here we create an instance of AutoTrader just as before, 
and set it up for a backtest. The difference is, however, the arguments we provide to the 
[`add_strategy`](autotrader-add-strategy) method. Instead of providing the file prefix of the 
strategy configuration yaml file, we provide the strategy configuration dictionary directly with
`config_dict=config`, and provide the strategy class directly with `strategy=SimpleMACD`. Now
when we run this module, the strategy will run!


```python
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


if __name__ == "__main__":
    from autotrader import AutoTrader

    config = {
        "NAME": "MACD Strategy",
        "MODULE": "macd_strategy",
        "CLASS": "SimpleMACD",
        "INTERVAL": "H4",
        "PARAMETERS": {
            "ema_period": 200,
            "MACD_fast": 5,
            "MACD_slow": 19,
            "MACD_smoothing": 9,
            "RR": 1.5,
        },
        "WATCHLIST": ["EUR_USD"],
    }

    at = AutoTrader()
    at.configure(verbosity=1, show_plot=False)
    at.add_strategy(config_dict=config, strategy=SimpleMACD)
    at.plot_settings(show_cancelled=False)
    at.backtest(
        start="1/1/2015",
        end="1/3/2022",
        initial_balance=1000,
        leverage=30,
        spread=0.5,
        commission=0.005,
    )
    at.run()
```