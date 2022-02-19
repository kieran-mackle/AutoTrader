from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum

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

def show_ticktypes():
    for i in range(91):
        print(TickTypeEnum.to_str(i), i)


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

