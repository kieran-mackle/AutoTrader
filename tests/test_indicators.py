import os
import pandas as pd
import autotrader.indicators as indicators

class TestIndicators:
    home_dir = os.path.abspath(os.path.dirname(__file__))
    
    def test_supertrend(self):
        data_dir = os.path.join(self.home_dir, 'data', 'EUR_USD_H4.csv')
        data = pd.read_csv(data_dir, index_col=0, 
                           parse_dates=True)
        testdata = data.iloc[-1000:]
        st = indicators.supertrend(testdata)
        
        assert st['trend'][-1] == 1
    
    