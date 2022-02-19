from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum

import threading
import time


class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self) 
        
    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 2 and reqId == 1: 
            print('The current ask price is: ', price)

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
eurusd_contract.secType = 'CASH'
eurusd_contract.exchange = 'IDEALPRO'
eurusd_contract.currency = 'USD'


