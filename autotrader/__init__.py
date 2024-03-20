from .autoplot import AutoPlot
from .autotrader import AutoTrader
from .utilities import TradeAnalysis, DataStream
from .brokers.trading import (
    Order,
    IsolatedPosition,
    Position,
    LimitOrder,
    MarketOrder,
    StopLimitOrder,
    Trade,
)

# Broker imports
# CCXT
try:
    from .brokers.ccxt import Broker as CCXT
except:
    pass

# Interactive Brokers
try:
    from .brokers.ib import Broker as IB
except:
    pass

# Oanda
try:
    from .brokers.oanda import Broker as Oanda
except:
    pass

# Virtual broker
from .brokers.virtual import Broker as VirtualBroker

# Define version number
__version__ = "1.0.1"
