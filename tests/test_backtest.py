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
    at.backtest(start = '1/1/2015',
                end = '1/3/2022',
                initial_balance=1000,
                leverage=30,
                spread=0.5,
                commission=0.005)
    at.run()
    bot = at.get_bots_deployed()
    bt_results = at.analyse_backtest(bot)
    
    # Test backtest results
    assert bt_results['no_trades'] == 236, "Incorrect number of trades"
    assert round(bt_results['all_trades']['ending_balance'], 3) == 748.946, "Incorrect ending balance"
    assert bt_results['long_trades']['no_trades'] == 99, "Incorrect number of long trades"
    assert bt_results['short_trades']['no_trades'] == 137, "Incorrect number of short trades"

test_macd_backtest()