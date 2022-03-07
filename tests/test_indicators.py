import os
import pandas as pd
import autotrader.indicators as indicators

class TestIndicators:
    
    def test_supertrend(self):
        testdata = self._get_test_data()
        st = indicators.supertrend(testdata)
        assert st['trend'][-1] == 1
    
    
    def test_range_filter(self):
        testdata = self._get_test_data()
        rfi = indicators.range_filter(testdata)
        assert round(rfi['upper'][-1], 6) == 1.12736
        assert round(rfi['lower'][-1], 6) == 1.119815
        assert round(rfi['rf'][-1], 6) == 1.123588
    
    
    @staticmethod
    def _get_test_data():
        home_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.join(home_dir, 'data', 'EUR_USD_H4.csv')
        data = pd.read_csv(data_dir, index_col=0, 
                           parse_dates=True)
        testdata = data.iloc[-1000:]
        return testdata