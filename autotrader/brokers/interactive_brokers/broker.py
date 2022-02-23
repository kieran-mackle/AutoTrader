# from autotrader.brokers.interactive_brokers.utils import Utils
from utils import Utils
import datetime
# import pandas as pd
import numpy as np
import ib_insync


class InteractiveBroker:
    def __init__(self, config: dict, utils: Utils = None) -> None:
        """AutoTrader-InteractiveBroker Class constructor.
        """
        
        self.utils = utils if utils is not None else Utils()
        
        host = config['host'] if 'host' in config else '127.0.0.1'
        port = config['port'] if 'port' in config else 7497
        client_id = config['clientID'] if 'clientID' in config else 1
        read_only = config['read_only'] if 'read_only' in config else False
        account = config['account'] if 'account' in config else ''
        
        # Set security type
        self._security_type = 'stock' # Stock, Forex, CFD, Future, Option, Bond, Crypto
        
        self.ib = ib_insync.IB()
        self.ib.connect(host=host, port=port, clientId=client_id, 
                        readonly=read_only, account=account)
        
        self.account = account if account != '' else self._get_account()
        
    
    def __repr__(self):
        return 'AutoTrader-InteractiveBrokers interface'
    
    
    def __str__(self):
        return 'AutoTrader-InteractiveBrokers interface'
    
    
    def _disconnect(self):
        """Disconnects from IB application.
        """
        self.ib.disconnect()
        

    def _check_connection(self):
        """Checks if there is an active connection to IB.
        """
        connected = self.ib.isConnected()
        
        if not connected:
            raise ConnectionError("No active connection to IB.")
        
    
    def _get_account(self,):
        """Gets first managed account.
        """
        accounts = self.ib.managedAccounts()
        return accounts[0]
    
    
    def get_summary(self):
        """Returns account summary.
        """
        
        self._check_connection()
        raw_summary = self.ib.accountSummary(self.account)
        
        summary = self.utils.accsum_to_dict(self.account, raw_summary)
        
        return summary
    
    
    def get_NAV(self):
        """Returns the net asset/liquidation value of the account.
        """
        summary = self.get_summary()
        return float(summary['NetLiquidation']['value'])
    
    
    def get_balance(self):
        """Returns account balance.
        """
        summary = self.get_summary()
        return float(summary['TotalCashValue']['value'])
        
    
    def get_position(self, symbol: str = None):
        """Returns details of the current position in the requested symbol. 

        Parameters
        ----------
        symbol : str, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        
        # Get all positions
        all_positions = self.ib.positions()
        
        # Filter by symbol
        if symbol is not None:
            # TODO - implement
            pass
        
        return all_positions
    
    
    def get_trade_details(self, trade_ID: str):
        """Returns the details of the trade specified by trade_ID.
        """
        # TODO - implement
        
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
        # TODO - verify functionality
        contract = self._build_contract(symbol)
        self.ib.qualifyContracts(contract)
        data = self.ib.reqMktData(contract, snapshot=snapshot)
        
        price = {"ask": data.ask,
                 "bid": data.bid,
                 "negativeHCF": 1,
                 "positiveHCF": 1,
                 }
        
        return price
    
    
    @staticmethod
    def _build_contract(order_details: dict) -> ib_insync.contract.Contract:
        """Builds IB contract based on provided symbol and security type.
        """
        
        symbol = order_details['instrument']
        security_type = order_details['secType']
        
        # Get contract object
        contract_object = getattr(ib_insync, security_type)
        
        if security_type == 'Stock':
            # symbol='', exchange='', currency=''
            exchange = order_details['exchange'] if 'exchange' in order_details else 'SMART'
            currency = order_details['currency'] if 'currency' in order_details else 'USD'
            contract = contract_object(symbol=symbol, exchange=exchange, currency=currency)
            
        elif security_type == 'Options':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'Future':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'ContFuture':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
            
        elif security_type == 'Forex':
            # pair='', exchange='IDEALPRO', symbol='', currency='', **kwargs)
            exchange = order_details['exchange'] if 'exchange' in order_details else 'IDEALPRO'
            contract = contract_object(pair=symbol, exchange=exchange)
            
        elif security_type == 'Index':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'CFD':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'Commodity':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'Bond':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'FuturesOption':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'MutualFund':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'Warrant':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'Bag':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'Crypto':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        
        return contract
    
    
    def get_pending_orders(self, symbol=None):
        """Returns all pending orders (have not been filled) in the account.
        """
        # Get all open trades
        open_trades = self.ib.openTrades()
        
        pending_orders = {}
        for trade in open_trades:
            trade_dict = trade.dict()
            contract = trade_dict['contract']
            order_dict = trade_dict['order'].dict()
            order_status_dict = trade_dict['orderStatus'].dict()
            order_status = order_status_dict['status']
            
            if order_status in ib_insync.OrderStatus.ActiveStates:
                # Order is still active (not yet filled)
                new_order = {}
                new_order['order_ID']           = order_dict['orderId']
                new_order['order_type']         = order_dict['orderType']
                new_order['order_stop_price']   = order_dict['auxPrice']
                new_order['order_limit_price']  = order_dict['lmtPrice']
                new_order['direction']          = 1 if order_dict['action'] == 'BUY' else -1
                new_order['order_time']         = None
                new_order['instrument']         = contract.symbol
                new_order['size']               = order_dict['totalQuantity']
                new_order['order_price']        = None
                new_order['take_profit']        = None
                new_order['take_distance']      = None
                new_order['stop_type']          = None
                new_order['stop_distance']      = None
                new_order['stop_loss']          = None
                new_order['related_orders']     = None
                new_order['granularity']        = None
                new_order['strategy']           = None
                
                if symbol is not None and contract.symbol == symbol:
                    pending_orders[new_order['order_ID']] = new_order
                elif symbol is None:
                    pending_orders[new_order['order_ID']] = new_order
            
        return pending_orders
    
    
    def cancel_pending_order(self, order_id):
        """Cancels pending order by order ID.
        """
        # TODO - need to retrieve order object
        self.ib.cancelOrder()
        
        pass
    
    
    def get_open_trades(self, instruments=None):
        """Returns the open trades held by the account. 
        """
        # Get all open trades
        open_trades = self.ib.openTrades()
        
        self._check_connection()
        
        
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
        
        self._check_connection()
        
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
        self._check_connection()
        
        action = 'BUY' if order_details["size"] > 0 else 'SELL'
        units = abs(order_details["size"])
        order = ib_insync.MarketOrder(action, units)
        contract = self._build_contract(order_details)
        trade = self.ib.placeOrder(contract, order)
        
        # order = self.ib.bracketOrder('BUY',
        #                         100000,
        #                         limitPrice=1.19,
        #                         takeProfitPrice=1.20,
        #                         stopLossPrice=1.18
        #                         )
        # for ord in eurusd_bracket_order:
        #     self.ib.placeOrder(eur_usd_contract, ord)
        
        return trade
    
    
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
        
        self._check_connection()
        
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
        
        self._check_connection()
        
        
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
        self.ib.reqHistoricalData()
        pass
    
    
    class Response:
        """Response oject for handling errors."""
        def __init__(self):
            pass