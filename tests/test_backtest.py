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
    bt_results = at.analyse_backtest()
    
    # Test backtest results
    assert bt_results['no_trades'] == 36, "Incorrect number of trades"
    assert round(bt_results['all_trades']['ending_balance'], 3) == 923.056, "Incorrect ending balance"
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
    at.configure(verbosity=2, show_plot=True)
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
    bt_results = at.multibot_backtest_results
    
    assert round(bt_results['win_rate'][0],5) == 34.28571
    assert round(bt_results['win_rate'][1],5) == 36.36364
    assert bt_results['no_long'][0] == 10, "Incorrect number of long trades"
    assert bt_results['no_long'][1] == 8, "Incorrect number of long trades"
    assert bt_results['no_short'][0] == 25, "Incorrect number of short trades"
    assert bt_results['no_short'][1] == 25, "Incorrect number of short trades"
    assert round(EU1bot.backtest_results.account_history['equity'][-1], 5) == 839.43366, "Incorrect ending balance"

