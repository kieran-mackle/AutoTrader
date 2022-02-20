from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import 
from ibapi.order_condition import Create, OrderCondition
from ibapi.order import Order

import threading
import time
import pandas


class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = [] #Initialize variable to store candle
        
    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 2 and reqId == 1: 
            print('The current ask price is: ', price)
    
    def historical_data(self, reqID, bar):
        print(f'Time: {bar.date} Close: {bar.close}')
        self.data.append([bar.date, bar.close])
        
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        print('The next valid order id is: ', self.nextorderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)
	
    def openOrder(self, orderId, contract, order, orderState):
        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action, order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)
    

def show_ticktypes():
    for i in range(91):
        print(TickTypeEnum.to_str(i), i)

def FX_order(symbol):
    "Creates FX order contract"
    contract = Contract()
    contract.symbol = symbol[:3]
    contract.secType = 'CASH'
    contract.exchange = 'IDEALPRO'
    contract.currency = symbol[3:]
    return contract


# Test connection
# app = IBapi()
# app.connect('127.0.0.1', 7497, 123)
# app.run()
# app.disconnect()

# Get current price of AAPL
def run_loop():
    app.run()




app = IBapi()
app.connect('127.0.0.1', 7497, 123)

#Start the socket in a thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

time.sleep(1) #Sleep interval to allow time for connection to server

# Create contract object
apple_contract = Contract()
apple_contract.symbol = 'AAPL'
apple_contract.secType = 'STK'
apple_contract.exchange = 'SMART'
apple_contract.currency = 'USD'

# Request Market Data
app.reqMktData(1, apple_contract, '', False, False, [])
# Arguments :  ID, contract, tick type, unsubscribed snapshot, subscribed snapshot, internal use 

time.sleep(10) #Sleep interval to allow time for incoming price data
app.disconnect()

# GET EUR/USD data - below creates contract object
eurusd_contract = Contract()
eurusd_contract.symbol = 'EUR'
eurusd_contract.secType = 'CASH' # 'FUT' for futures
eurusd_contract.exchange = 'IDEALPRO'
eurusd_contract.currency = 'USD'


# Retrieve last 10 1h bars
# Note that incomplete candles will be sent
app.reqHistoricalData(1, eurusd_contract, '', '2 D', '1 hour', 'BID', 0, 2, False, [])
# Args: ID, contract, end date, interval,  granularity, data type, RTH, time format, streaming, internal
# Can have BID ASK or MIDPOINT
time.sleep(5) #sleep to allow enough time for data to be returned
# app.disconnect()


# Save bars
df = pandas.DataFrame(app.data, columns=['DateTime', 'Close'])
df['DateTime'] = pandas.to_datetime(df['DateTime'],unit='s') 
# df.to_csv('EURUSD_Hourly.csv')  
print(df)

app.disconnect()


# Fire order
app.nextorderId = None
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Check if API is connected
while True:
	if isinstance(app.nextorderId, int):
		print('connected')
		break
	else:
		print('waiting for connection')
		time.sleep(1)

#Create order object
order = Order()
order.action = 'BUY'
order.totalQuantity = 100000
order.orderType = 'LMT' # 'MKT'
order.lmtPrice = '1.10'

#Place order
app.placeOrder(app.nextorderId, FX_order('EURUSD'), order)
#app.nextorderId += 1   # Increment when placing multiple

time.sleep(3)

#Cancel order 
print('cancelling order')
app.cancelOrder(app.nextorderId)

time.sleep(3)
app.disconnect()



# SL / TP
# First create main order
order = Order()
order.action = 'BUY'
order.totalQuantity = 100000
order.orderType = 'LMT'
order.lmtPrice = '1.10'
order.orderId = app.nextorderId
app.nextorderId += 1
order.transmit = False  # Do not process until SL order has been submitted

# Then create stop loss order object
stop_order = Order()
stop_order.action = 'SELL'
stop_order.totalQuantity = 100000
stop_order.orderType = 'STP'
stop_order.auxPrice = '1.09'
stop_order.orderId = app.nextorderId
app.nextorderId += 1
stop_order.parentId = order.orderId
order.transmit = True

#Place orders
app.placeOrder(order.orderId, FX_order('EURUSD'), order)
app.placeOrder(stop_order.orderId, FX_order('EURUSD'), stop_order)

app.disconnect()


# Set order to fire at a set price




