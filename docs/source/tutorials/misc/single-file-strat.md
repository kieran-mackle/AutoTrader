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
import os
from finta import TA
from autotrader import indicators
from autotrader import Order


class SimpleMACD:
    """Simple MACD Strategy
    
    Rules
    ------
    1. Trade in direction of trend, as per 200EMA.
    2. Entry signal on MACD cross below/above zero line.
    3. Set stop loss at recent price swing.
    4. Target 1.5 take profit.
    """
    
    def __init__(self, params, data, instrument):
        """Define all indicators used in the strategy.
        """
        self.name = "MACD Trend Strategy"
        self.data = data
        self.params = params
        self.instrument = instrument
        
        # 200EMA
        self.ema = TA.EMA(data, params['ema_period'])
        
        # MACD
        self.MACD = TA.MACD(data, self.params['MACD_fast'], 
                            self.params['MACD_slow'], self.params['MACD_smoothing'])
        self.MACD_CO = indicators.crossover(self.MACD.MACD, self.MACD.SIGNAL)
        self.MACD_CO_vals = indicators.cross_values(self.MACD.MACD, 
                                                    self.MACD.SIGNAL,
                                                    self.MACD_CO)
        
        # Price swings
        self.swings = indicators.find_swings(data)

        # Construct indicators dict for plotting
        self.indicators = {'MACD (12/26/9)': {'type': 'MACD',
                                              'macd': self.MACD.MACD,
                                              'signal': self.MACD.SIGNAL},
                           'EMA (200)': {'type': 'MA',
                                         'data': self.ema}}
        
        
    def generate_signal(self, i, **kwargs):
        """Define strategy to determine entry signals.
        """
        
        if self.data.Close.values[i] > self.ema[i] and \
            self.MACD_CO[i] == 1 and \
            self.MACD_CO_vals[i] < 0:
                exit_dict = self.generate_exit_levels(signal=1, i=i)
                new_order = Order(direction=1,
                                  stop_loss=exit_dict['stop_loss'],
                                  take_profit=exit_dict['take_profit'])
                
        elif self.data.Close.values[i] < self.ema[i] and \
            self.MACD_CO[i] == -1 and \
            self.MACD_CO_vals[i] > 0:
                exit_dict = self.generate_exit_levels(signal=-1, i=i)
                new_order = Order(direction=-1,
                                  stop_loss=exit_dict['stop_loss'],
                                  take_profit=exit_dict['take_profit'])

        else:
            new_order = Order()
        
        return new_order
    
    
    def generate_exit_levels(self, signal, i):
        """Function to determine stop loss and take profit levels.
        """
        stop_type = 'limit'
        RR = self.params['RR']
        
        if signal == 0:
            stop = None
            take = None
        else:
            if signal == 1:
                stop = self.swings.Lows[i]
                take = self.data.Close[i] + RR*(self.data.Close[i] - stop)
            else:
                stop = self.swings.Highs[i]
                take = self.data.Close[i] - RR*(stop - self.data.Close[i])
        
        exit_dict = {'stop_loss': stop, 
                     'stop_type': stop_type,
                     'take_profit': take}
        
        return exit_dict
    
    
if __name__ == "__main__":
    from autotrader import AutoTrader
    
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
    
    at = AutoTrader()
    at.configure(verbosity=1, show_plot=False)
    at.add_strategy(config_dict=config, strategy=SimpleMACD)
    at.plot_settings(show_cancelled=False)
    at.add_data({'EUR_USD': 'EUR_USD_H4.csv'}, 
                data_directory=os.path.join(os.getcwd(), 'data'))
    at.backtest(start = '1/1/2015',
                end = '1/3/2022',
                initial_balance=1000,
                leverage=30,
                spread=0.5,
                commission=0.005)
    at.run()
```