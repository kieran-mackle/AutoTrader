import os
import pandas as pd
import autotrader.indicators as indicators

class TestIndicators:
    
    def test_supertrend(self):
        testdata = self._get_test_data()
        st = indicators.supertrend(testdata)
        assert st['trend'][-1] == 1, "Supertrend indicator failed"
    
    
    def test_halftrend(self):
        testdata = self._get_test_data()
        ht = indicators.halftrend(testdata)
        assert round(ht['halftrend'][-1], 5) == 1.12344, "Halftrend indicator failed"
        assert round(ht['atrHigh'][-1], 5) == 1.12593, "Halftrend indicator failed"
        assert round(ht['atrLow'][-1], 5) == 1.12095, "Halftrend indicator failed"
    
    
    def test_range_filter(self):
        testdata = self._get_test_data()
        rfi = indicators.range_filter(testdata)
        assert round(rfi['upper'][-1], 6) == 1.12736, "Range filter indicator failed"
        assert round(rfi['lower'][-1], 6) == 1.119815, "Range filter indicator failed"
        assert round(rfi['rf'][-1], 6) == 1.123588, "Range filter indicator failed"
    
    
    @staticmethod
    def test_rolling_signal_list():
        signals = [0,1,0,0,0,-1,0,0,1,0,0]
        rolled_signals = indicators.rolling_signal_list(signals)
        assert rolled_signals == [0, 1, 1, 1, 1, -1, -1, -1, 1, 1, 1], "Rolling signal list indicator failed"
    
    
    @staticmethod
    def test_unroll_signal_list():
        signals = [0, 1, 1, 1, 1, -1, -1, -1, 1, 1, 1]
        unrolled_signals = indicators.unroll_signal_list(signals)
        assert list(unrolled_signals) == [0,1,0,0,0,-1,0,0,1,0,0], "Unroll signal list indicator failed"
    
    
    @staticmethod
    def _get_test_data():
        home_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.join(home_dir, 'data', 'EUR_USD_H4.csv')
        data = pd.read_csv(data_dir, index_col=0, 
                           parse_dates=True)
        testdata = data.iloc[-1000:]
        return testdata