import os
from macd_strategy import SimpleMACD
from limit_strategy import LimitStrategy
from autotrader.autotrader import AutoTrader


def test_macd_backtest():
    config = {
        "NAME": "MACD Strategy",
        "MODULE": "macd_strategy",
        "CLASS": "SimpleMACD",
        "INTERVAL": "4h",
        "PERIOD": 300,
        "RISK_PC": 1.5,
        "SIZING": "risk",
        "PARAMETERS": {
            "ema_period": 200,
            "MACD_fast": 5,
            "MACD_slow": 19,
            "MACD_smoothing": 9,
            "RR": 1.5,
        },
        "WATCHLIST": ["EUR_USD"],
    }
    home_dir = os.path.abspath(os.path.dirname(__file__))

    at = AutoTrader()
    at.configure(verbosity=1, show_plot=False, mode="periodic")
    at.add_strategy(config_dict=config, strategy=SimpleMACD)
    at.plot_settings(show_cancelled=True)
    at.add_data(
        {"EUR_USD": "EUR_USD_H4.csv"}, data_directory=os.path.join(home_dir, "data")
    )
    at.backtest(start="1/1/2021", end="1/1/2022")
    at.virtual_account_config(
        initial_balance=1000,
        leverage=30,
        spread=0.5 * 1e-4,
        commission=0.005,
        hedging=True,
    )
    at.run()
    bot = at.get_bots_deployed()
    bt_results = at.trade_results.summary()

    # Test backtest results
    assert bt_results["no_trades"] == 70, (
        "Incorrect number of trades " + "(single instrument backtest)"
    )
    assert round(bt_results["ending_balance"], 3) == 903.857, (
        "Incorrect " + "ending balance (single instrument backtest)"
    )


def test_multibot_macd_backtest():
    config = {
        "NAME": "MACD Strategy",
        "MODULE": "macd_strategy",
        "CLASS": "SimpleMACD",
        "INTERVAL": "4h",
        "PERIOD": 300,
        "RISK_PC": 1.5,
        "SIZING": "risk",
        "PARAMETERS": {
            "ema_period": 200,
            "MACD_fast": 5,
            "MACD_slow": 19,
            "MACD_smoothing": 9,
            "RR": 1.5,
        },
        "WATCHLIST": ["EUR_USD", "EUR_USD2"],
    }
    home_dir = os.path.abspath(os.path.dirname(__file__))

    at = AutoTrader()
    at.configure(verbosity=0, show_plot=False, mode="periodic")
    at.add_strategy(config_dict=config, strategy=SimpleMACD)
    at.plot_settings(show_cancelled=False)
    at.add_data(
        {"EUR_USD": "EUR_USD_H4.csv", "EUR_USD2": "EUR_USD_H4.csv"},
        data_directory=os.path.join(home_dir, "data"),
    )
    at.backtest(start="1/1/2021", end="1/1/2022")
    at.virtual_account_config(
        initial_balance=1000,
        leverage=30,
        spread=0.5 * 1e-4,
        commission=0.005,
        hedging=True,
    )
    at.run()
    bt_results = at.trade_results.summary()

    assert bt_results["no_trades"] == 134, (
        "Incorrect number of trades" + " (multi-instrument backtest)"
    )
    assert round(bt_results["ending_balance"], 3) == 838.037, (
        "Incorrect " + "ending balance (multi-instrument backtest)"
    )


def test_limit_backtest():
    config = {
        "NAME": "Limit Order Strategy",
        "CLASS": "LimitStrategy",
        "INTERVAL": "4h",
        "PERIOD": 50,
        "PARAMETERS": {},
        "SIZING": 100,
        "WATCHLIST": ["EUR_USD"],
    }
    home_dir = os.path.abspath(os.path.dirname(__file__))

    at = AutoTrader()
    at.configure(verbosity=1, show_plot=False, mode="continuous", update_interval="4h")
    at.add_strategy(config_dict=config, strategy=LimitStrategy)
    at.plot_settings(show_cancelled=True)
    at.add_data(
        {"EUR_USD": "EUR_USD_H4.csv"}, data_directory=os.path.join(home_dir, "data")
    )
    at.backtest(start="1/1/2021", end="1/3/2021")
    at.virtual_account_config(
        initial_balance=1000, leverage=30, spread=0.5 * 1e-4, commission=0.005
    )
    at.run()

    bt_results = at.trade_results.summary()

    # Test backtest results
    assert bt_results["no_trades"] == 2, (
        "Incorrect number of trades " + "(limit order backtest)"
    )
    assert round(bt_results["ending_balance"], 3) == 1000.988, (
        "Incorrect " + "ending balance (limit order backtest)"
    )


def test_margin_call_backtest():
    config = {
        "NAME": "Limit Order Strategy",
        "CLASS": "LimitStrategy",
        "INTERVAL": "4h",
        "PERIOD": 50,
        "PARAMETERS": {},
        "SIZING": 10000,
        "WATCHLIST": ["EUR_USD"],
    }
    home_dir = os.path.abspath(os.path.dirname(__file__))

    at = AutoTrader()
    at.configure(verbosity=1, show_plot=False, mode="continuous", update_interval="4h")
    at.add_strategy(config_dict=config, strategy=LimitStrategy)
    at.plot_settings(show_cancelled=True)
    at.add_data(
        {"EUR_USD": "EUR_USD_H4.csv"}, data_directory=os.path.join(home_dir, "data")
    )
    at.backtest(start="1/1/2021", end="1/3/2021")
    at.virtual_account_config(
        initial_balance=1000,
        leverage=30,
        margin_call_fraction=0.6,
        spread=0.5 * 1e-4,
        commission=0.005,
    )
    at.run()

    bt_results = at.trade_results.summary()

    # Test backtest results
    assert bt_results["no_trades"] == 4, (
        "Incorrect number of trades " + "(margin call backtest)"
    )
    assert round(bt_results["ending_balance"], 3) == 970.769, (
        "Incorrect " + "ending balance (margin call backtest)"
    )
