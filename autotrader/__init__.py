from .autoplot import AutoPlot
from .autodata import AutoData
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
    from .brokers.ccxt.broker import Broker as CCXTBroker
except:
    pass

# dYdX
try:
    from .brokers.dydx.broker import Broker as dYdXBroker
except:
    pass

# Interactive Brokers
try:
    from .brokers.ib.broker import Broker as IBroker
except:
    pass

# Oanda
try:
    from .brokers.oanda.broker import Broker as OandaBroker
except:
    pass

# Virtual broker
from .brokers.virtual.broker import Broker as VirtualBroker

# Define version number
__version__ = "0.11.2"
