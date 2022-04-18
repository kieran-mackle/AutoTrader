import os
from macd_strategy import SimpleMACD
from autotrader.autotrader import AutoTrader

def test_macd_backtest():
    config = {'NAME': 'MACD Strategy',
              'MODULE': 'macd_strategy',
              'CLASS': 'SimpleMACD',
              'INTERVAL': 'H4',
              'PERIOD': 300,
              'RISK_PC': 1.5,
              'SIZING': 'risk',
              'PARAMETERS': {'ema_period': 200,
                             'MACD_fast': 5,
                             'MACD_slow': 19,
                             'MACD_smoothing': 9,
                             'RR': 1.5},
              'WATCHLIST': ['EUR_USD'],}
    home_dir = os.path.abspath(os.path.dirname(__file__))
    
    at = AutoTrader()
    at.configure(verbosity=2, show_plot=True)
    at.add_strategy(config_dict=config, strategy=SimpleMACD)
    at.plot_settings(show_cancelled=False)
    at.add_data({'EUR_USD': 'EUR_USD_H4.csv'}, 
                data_directory=os.path.join(home_dir, 'data'))
    at.backtest(start = '1/1/2021', end = '1/1/2022',
                initial_balance=1000, leverage=30,
                spread=0.5, commission=0.005, hedging=True)
    at.run()
    bot = at.get_bots_deployed()
    bt_results = at.backtest_results.summary()
    
    # Test backtest results
    assert bt_results['no_trades'] == 36, "Incorrect number of trades"
    assert round(bt_results['ending_balance'], 3) == 923.056, "Incorrect ending balance"
    assert bt_results['long_trades']['no_trades'] == 10, "Incorrect number of long trades"
    assert bt_results['short_trades']['no_trades'] == 26, "Incorrect number of short trades"


def test_multibot_macd_backtest():
    config = {'NAME': 'MACD Strategy',
              'MODULE': 'macd_strategy',
              'CLASS': 'SimpleMACD',
              'INTERVAL': 'H4',
              'PERIOD': 300,
              'RISK_PC': 1.5,
              'SIZING': 'risk',
              'PARAMETERS': {'ema_period': 200,
                              'MACD_fast': 5,
                              'MACD_slow': 19,
                              'MACD_smoothing': 9,
                              'RR': 1.5},
              'WATCHLIST': ['EUR_USD', 'EUR_USD2'],}
    home_dir = os.path.abspath(os.path.dirname(__file__))
    
    at = AutoTrader()
    at.configure(verbosity=0, show_plot=False)
    at.add_strategy(config_dict=config, strategy=SimpleMACD)
    at.plot_settings(show_cancelled=False)
    at.add_data({'EUR_USD': 'EUR_USD_H4.csv',
                  'EUR_USD2': 'EUR_USD_H4.csv'}, 
                data_directory=os.path.join(home_dir, 'data'))
    at.backtest(start = '1/1/2021', end = '1/1/2022',
                initial_balance=1000, leverage=30,
                spread=0.5, commission=0.005, hedging=True)
    at.run()
    bots = at.get_bots_deployed()
    EU1bot = bots['EUR_USD']
    bt_results = at.backtest_results.summary()
    
    assert bt_results['no_trades'] == 68, "Incorrect number of trades"
    assert round(bt_results['ending_balance'], 3) == 839.434, "Incorrect ending balance"
    assert bt_results['long_trades']['no_trades'] == 18, "Incorrect number of long trades"
    assert bt_results['short_trades']['no_trades'] == 50, "Incorrect number of short trades"
    
