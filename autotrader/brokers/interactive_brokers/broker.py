#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from autotrader.brokers.interactive_brokers.utils import Utils
import datetime
import pandas as pd
import numpy as np
import ib_insync


class InteractiveBroker:
    def __init__(self, config: dict, utils: Utils) -> None:
        """InteractiveBroker Class constructor.
        """
        # self.ib = ib_insync.IB()
        # self.ib.connect()
        
    
    def __str__(self):
        return 'AutoTrader-InteractiveBrokers interface'
    
    
    def get_summary(self):
        """Returns account summary.
        """
        
        self.check_connection()
        
        # response = self.api.account.get(accountID=self.ACCOUNT_ID)
        response = self.api.account.summary(accountID=self.ACCOUNT_ID)
        # print(response.body['account'])
        
        return response
    
    
    def get_NAV(self):
        """Returns the net asset/liquidation value of the account.
        """
        # nav = (float([i.value for i in self.ib.accountSummary() if i.tag == 'NetLiquidation'][0]))
        
        return
    
    
    def get_balance(self):
        """Returns account balance.
        """
        return
        
    
    def get_position(self, symbol: str):
        """Returns details of the current position in the requested symbol. 
        """
        return
    
    
    def get_trade_details(self, trade_ID: str):
        """Returns the details of the trade specified by trade_ID.
        """
        
        response = self.api.trade.list(accountID=self.ACCOUNT_ID, ids=int(trade_ID))
        trade = response.body['trades'][0]
        
        details = {'direction': int(np.sign(trade.currentUnits)), 
                   'stop_loss': 82.62346473606581, 
                   'order_time': datetime.datetime.strptime(trade.openTime[:-4], '%Y-%m-%dT%H:%M:%S.%f'), 
                   'instrument': trade.instrument, 
                   'size': trade.currentUnits,
                 'order_price': trade.price, 
                 'order_ID': trade.id, 
                 'time_filled': trade.openTime, 
                 'entry_price': trade.price, 
                 'unrealised_PL': trade.unrealizedPL, 
                 'margin_required': trade.marginUsed}
        
        # Get associated trades
        related = []
        try:
            details['take_profit'] = trade.takeProfitOrder.price
            related.append(trade.takeProfitOrder.id)
        except:
            pass
        
        try:
            details['stop_loss'] = trade.stopLossOrder.price
            related.append(trade.stopLossOrder.id)
        except:
            pass
        details['related_orders'] = related
        
        return details
    
    
    def get_price(self, symbol: str, snapshot: bool = True, **kwargs):
        """Returns current price (bid+ask) and home conversion factors.
        """
        # TODO - calculate conversion factors
        
        contract = self._build_contract(symbol)
        data = self.ib.reqMktData(contract, snapshot=snapshot)
        
        price = {"ask": data.ask,
                 "bid": data.bid,
                 "negativeHCF": None,
                 "positiveHCF": None,
                 }
    
        return price
    
    
    def get_pending_orders(self, instrument=None):
        """Returns all pending orders in the account.
        """
        
        response = {}
        
        oanda_pending_orders = response.body['orders']
        pending_orders = {}
        
        for order in oanda_pending_orders:
            if order.type != 'TAKE_PROFIT' and order.type != 'STOP_LOSS':
                new_order = {}
                new_order['order_ID']           = order.id
                new_order['order_type']         = order.type
                new_order['order_stop_price']   = order.price
                new_order['order_limit_price']  = order.price
                new_order['direction']          = np.sign(order.units)
                new_order['order_time']         = order.createTime
                new_order['strategy']           = None
                new_order['instrument']         = order.instrument
                new_order['size']               = order.units
                new_order['order_price']        = order.price
                new_order['granularity']        = None
                new_order['take_profit']        = order.takeProfitOnFill.price if order.takeProfitOnFill is not None else None
                new_order['take_distance']      = None
                new_order['stop_type']          = None
                new_order['stop_distance']      = None
                new_order['stop_loss']          = None
                new_order['related_orders']     = None
                
                if instrument is not None and order.instrument == instrument:
                    pending_orders[order.id] = new_order
                elif instrument is None:
                    pending_orders[order.id] = new_order
            
        return pending_orders
    
    
    def cancel_pending_order(self, order_id):
        """Cancels pending order by order ID.
        """
        pass
    
    
    def get_open_trades(self, instruments=None):
        """Returns the open trades held by the account. 
        """
        
        self.check_connection()
        
        response = self.api.trade.list_open(accountID=self.ACCOUNT_ID)
        
        oanda_open_trades = response.body['trades']
        open_trades = {}
        
        for order in oanda_open_trades:
            new_order = {}
            new_order['order_ID']           = order.id
            new_order['order_stop_price']   = order.price
            new_order['order_limit_price']  = order.price
            new_order['direction']          = np.sign(order.currentUnits)
            new_order['order_time']         = order.openTime
            new_order['instrument']         = order.instrument
            new_order['size']               = order.currentUnits
            new_order['order_price']        = order.price
            new_order['entry_price']        = order.price
            new_order['order_type']         = None
            new_order['strategy']           = None
            new_order['granularity']        = None
            new_order['take_profit']        = None
            new_order['take_distance']      = None
            new_order['stop_type']          = None
            new_order['stop_distance']      = None
            new_order['stop_loss']          = None
            new_order['related_orders']     = None
            
            if instruments is not None and order.instrument in instruments:
                open_trades[order.id] = new_order
            elif instruments is None:
                open_trades[order.id] = new_order
        
        return open_trades
    
    
    def get_open_positions(self, symbol: str = None):
        """Gets the current positions open on the account.
        """
        
        self.check_connection()
        
        response = self.api.position.list_open(accountID=self.ACCOUNT_ID)
        
        oanda_open_positions = response.body['positions']
        open_positions = {}
        
        for position in oanda_open_positions:
            pos = {'long_units': position.long.units,
                   'long_PL': position.long.unrealizedPL,
                   'long_margin': None,
                   'short_units': position.short.units,
                   'short_PL': position.short.unrealizedPL,
                   'short_margin': None,
                   'total_margin': position.marginUsed}
            
            # fetch trade ID'strade_IDs
            trade_IDs = []
            if abs(pos['long_units']) > 0: 
                for ID in position.long.tradeIDs: trade_IDs.append(ID)
            if abs(pos['short_units']) > 0: 
                for ID in position.short.tradeIDs: trade_IDs.append(ID)
            
            pos['trade_IDs'] = trade_IDs
            
            if symbol is not None and position.instrument == symbol:
                open_positions[position.instrument] = pos
            elif symbol is None:
                open_positions[position.instrument] = pos
        
        return open_positions
    
    
    def place_order(self, order_details: dict):
        """Disassemble order_details dictionary to place order.
        """
        
        
        self.check_connection()
        
        if order_details["order_type"] == 'market':
            response = self.place_market_order(order_details)
        elif order_details["order_type"] == 'stop-limit':
            response = self.place_stop_limit_order(order_details)
        elif order_details["order_type"] == 'limit':
            response = self.place_limit_order(order_details)
        elif order_details["order_type"] == 'close':
            response = self.close_position(order_details["instrument"])
        else:
            print("Order type not recognised.")
            return
        
        return response
        
    
    def place_market_order(self, order_details: dict):
        """Places a market order.
        """
        
        # ib_insync.MarketOrder(action, totalQuantity)
        
        stop_loss_details = self.get_stop_loss_details(order_details)
        take_profit_details = self.get_take_profit_details(order_details)
        
        # Check position size
        size = self.check_trade_size(order_details["instrument"], 
                                     order_details["size"])
        
        response = self.api.order.market(accountID = self.ACCOUNT_ID,
                                         instrument = order_details["instrument"],
                                         units = size,
                                         takeProfitOnFill = take_profit_details,
                                         stopLossOnFill = stop_loss_details,
                                         )
        return response
    
    
    def place_stop_limit_order(self, order_details):
        """Places stop-limit order.
        """
        
        # ib_insync.StopLimitOrder(action, totalQuantity, lmtPrice, stopPrice)
        
        stop_loss_details = self.get_stop_loss_details(order_details)
        take_profit_details = self.get_take_profit_details(order_details)
        
        # Check and correct order stop price
        price = self.check_precision(order_details["instrument"], 
                                     order_details["order_stop_price"])
        
        trigger_condition = order_details["trigger_price"] if "trigger_price" in order_details else "DEFAULT"
        
        # Need to test cases when no stop/take is provided (as None type)
        response = self.api.order.market_if_touched(accountID   = self.ACCOUNT_ID,
                                                    instrument  = order_details["instrument"],
                                                    units       = order_details["size"],
                                                    price       = str(price),
                                                    takeProfitOnFill = take_profit_details,
                                                    stopLossOnFill = stop_loss_details,
                                                    triggerCondition = trigger_condition
                                                    )
        return response
    
    
    def place_limit_order(self, order_details):
        """Places limit order.
        """
        # ib_insync.LimitOrder(action, totalQuantity, lmtPrice)


    def get_stop_loss_details(self, order_details):
        """Constructs stop loss details dictionary.
        """
        
        # https://developer.oanda.com/rest-live-v20/order-df/#OrderType
        
        self.check_connection()
        
        if order_details["stop_type"] is not None:
            price = self.check_precision(order_details["instrument"], 
                                         order_details["stop_loss"])
            
            if order_details["stop_type"] == 'trailing':
                # Trailing stop loss order
                stop_loss_details = {"price": str(price),
                                     "type": "TRAILING_STOP_LOSS"}
            else:
                stop_loss_details = {"price": str(price)}
        else:
            stop_loss_details = None
        
        return stop_loss_details
    
    
    def get_take_profit_details(self, order_details: dict):
        """Constructs take profit details dictionary.
        """
        
        self.check_connection()
        
        
        if order_details["take_profit"] is not None:
            price = self.check_precision(order_details["instrument"], 
                                         order_details["take_profit"])
            take_profit_details = {"price": str(price)}
        else:
            take_profit_details = None
        
        return take_profit_details

    
    def close_position(self, symbol: str, long_units: float = None, 
                       short_units: float = None, **kwargs):
        """Closes open position of symbol.
        """
        pass
    
    
    def get_historical_data(self, symbol: str, interval: str, 
                            from_time: str, to_time: str):
        """Returns historical price data.
        """
        pass
    
    
    class Response:
        """Response oject for handling errors."""
        def __init__(self):
            pass