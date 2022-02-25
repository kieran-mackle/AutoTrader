# from autotrader.brokers.interactive_brokers.utils import Utils
from utils import Utils
import datetime
# import pandas as pd
import numpy as np
import ib_insync

'''
Notes and considerations:
    - IB does not handle automatic base/quote exchanges, so either need 
      to make that the onus of the user, or automate ... which will
      require knowledge of the account currency
    - close trade might not be as simple as a 'close' order, but rather the
      opposite of what got the trade. Eg. selling a long trade.
      
TODO:
    - Futures contract building

IMPORTANT DOCUMENTATION:
    - when closing a position using close_position(), if there are attached SL
      and/or TP orders, they must be closed manually using cancel_pending_order().
      Usually only one of the pair needs to be cancelled, and the other will too.
    - get_open_trades is ambiguous - use get_open_positions
    - There are some methods missing between virtual broker and this one...
      ideally all public methods should be shared across brokers, and private
      methods can be broker-specific. Can then just use wrappers where necessary.
    - required signal_dict keys for different security types (eg. futures 
      require symbol, exchange and contract_month)
'''

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
        
        self.ib = ib_insync.IB()
        self.ib.connect(host=host, port=port, clientId=client_id, 
                        readonly=read_only, account=account)
        
        self.account = account if account != '' else self._get_account()
        
    
    def __repr__(self):
        return 'AutoTrader-InteractiveBrokers interface'
    
    
    def __str__(self):
        return 'AutoTrader-InteractiveBrokers interface'
    
    
    def _connect(self, host, port, client_id, read_only, account):
        """Connects from IB application.
        """
        self.ib.connect(host=host, port=port, clientId=client_id, 
                        readonly=read_only, account=account)
        
    
    def _disconnect(self):
        """Disconnects from IB application.
        """
        self.ib.disconnect()
        

    def _check_connection(self):
        """Checks if there is an active connection to IB.
        """
        self._refresh()
        connected = self.ib.isConnected()
        if not connected:
            raise ConnectionError("No active connection to IB.")
    
    
    def _refresh(self):
        """Refreshes IB session events.
        """
        self.ib.sleep(0)
    
    
    def _get_account(self,):
        """Gets first managed account.
        """
        self._check_connection()
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
        self._check_connection()
        summary = self.get_summary()
        return float(summary['NetLiquidation']['value'])
    
    
    def get_balance(self):
        """Returns account balance.
        """
        self._check_connection()
        summary = self.get_summary()
        return float(summary['TotalCashValue']['value'])
        
    
    def get_trade_details(self, trade_ID: str):
        """Returns the details of the trade specified by trade_ID.
        """
        self._check_connection()
        # TODO - implement (?)
        
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
        self._check_connection()
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
    
    
    def get_pending_orders(self, symbol=None):
        """Returns all pending orders (have not been filled) in the account.
        """
        self._check_connection()
        
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
    
    
    def cancel_pending_order(self, order_id: int):
        """Cancels pending order by order ID.
        """
        self._check_connection()
        
        open_trades = self.ib.openTrades()
        cancelled_trades = []
        for trade in open_trades:
            order = trade.order
            if order.orderId == order_id:
                cancel_trade = self.ib.cancelOrder(order)
                cancelled_trades.append(cancel_trade)
        
        return cancelled_trades
    
    
    def get_open_trades(self, symbol: str = None):
        """Returns the open trades held by the account. 
        """
        self._check_connection()
        
        # Get all open trades
        all_open_trades = self.ib.openTrades()
        
        open_trades = {}
        for trade in all_open_trades:
            trade_dict = trade.dict()
            contract = trade_dict['contract']
            order_dict = trade_dict['order'].dict()
            order_status_dict = trade_dict['orderStatus'].dict()
            order_status = order_status_dict['status']
            
            if order_status == 'Filled':
                # Order is still active (not yet filled)
                new_trade = {}
                new_trade['order_ID']           = order_dict['orderId']
                new_trade['order_stop_price']   = order_dict['auxPrice']
                new_trade['order_limit_price']  = order_dict['lmtPrice']
                new_trade['direction']          = 1 if order_dict['action'] == 'BUY' else -1
                new_trade['order_time']         = None
                new_trade['instrument']         = contract.symbol
                new_trade['size']               = order_dict['totalQuantity']
                new_trade['order_price']        = None
                new_trade['entry_price']        = order_status_dict['lastFillPrice']
                new_trade['order_type']         = None
                new_trade['take_profit']        = None
                new_trade['take_distance']      = None
                new_trade['stop_type']          = None
                new_trade['stop_distance']      = None
                new_trade['stop_loss']          = None
                new_trade['related_orders']     = None
                new_trade['granularity']        = None
                new_trade['strategy']           = None
                
                if symbol is not None and contract.symbol == symbol:
                    open_trades[new_trade['order_ID']] = new_trade
                elif symbol is None:
                    open_trades[new_trade['order_ID']] = new_trade
        
        return open_trades
    
    
    def get_open_positions(self, symbol: str = None, local_symbol: str = None) -> dict:
        """Gets the current positions open on the account.
        
        Parameters
        ----------
        symbol : str, optional
            The product symbol. The default is None.
        local_symbol : str, optional
            The exchange-local product symbol. The default is None.
            
        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """
        
        # TODO - add optional localSymbol arg for disambiguity :
        # symbol_attr = 'symbol' if local_symbol is None else 'localSymbol'
        # getattr(position.contract, symbol_attr)
        # matching_symbol = symbol if local_symbol is None else local_symbol
        # use matching_symbol to compare to pos_symbol
        
        self._check_connection()
        
        all_positions = self.ib.portfolio()
        open_positions = {}
        for position in all_positions:
            units = position.position
            pnl = position.unrealizedPNL
            pos_symbol = position.contract.symbol
            pos_dict = {'long_units': units if np.sign(units) > 0 else 0,
                        'long_PL': pnl if np.sign(units) > 0 else 0,
                        'long_margin': None,
                        'short_units': units if np.sign(units) < 0 else 0,
                        'short_PL': units if np.sign(units) < 0 else 0,
                        'short_margin': None,
                        'total_margin': None,
                        'trade_IDs': None,
                        'position': units,
                        'PL': pnl,
                        'contract': position.contract}
        
            if symbol is not None and pos_symbol == symbol:
                # Only add positions in requested symbol
                open_positions[pos_symbol] = pos_dict
            elif symbol is None:
                # Append all positions
                open_positions[pos_symbol] = pos_dict
        
        return open_positions
    
    
    def place_order(self, order_details: dict):
        """Disassemble order_details dictionary to place order.
        """
        self._check_connection()
        
        if order_details["order_type"] == 'market':
            self._place_market_order(order_details)
        elif order_details["order_type"] == 'stop-limit':
            self._place_stop_limit_order(order_details)
        elif order_details["order_type"] == 'limit':
            self._place_limit_order(order_details)
        elif order_details["order_type"] == 'close':
            self.close_position(order_details)
        else:
            print("Order type not recognised.")
        
        self._refresh()
        
    
    def get_historical_data(self, symbol: str, interval: str, 
                            from_time: str, to_time: str):
        """Returns historical price data.
        """
        self._check_connection()
        
        # TODO - implement (?)
        self.ib.reqHistoricalData()
        
        
    def _close_position(self, order_details: dict, **kwargs):
        """Closes open position of symbol by placing opposing market order.
        """
        self._check_connection()
        
        symbol = order_details['instrument']
        position = self.get_open_positions(symbol)[symbol]
        position_units = position['position']
        
        # Place opposing market order
        action = 'BUY' if position_units < 0 else 'SELL'
        units = abs(position_units)
        order = ib_insync.MarketOrder(action, units)
        contract = position['contract']
        self.ib.qualifyContracts(contract)
        self.ib.placeOrder(contract, order)
        
    
    def _place_market_order(self, order_details: dict):
        """Places a market order.
        """
        self._check_connection()
        
        # Build contract
        contract = self._build_contract(order_details)
        
        # Create market order
        action = 'BUY' if order_details["size"] > 0 else 'SELL'
        units = abs(order_details["size"])
        market_order = ib_insync.MarketOrder(action, units, 
                                             orderId=self.ib.client.getReqId(),
                                             transmit=False)
        
        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order_details, market_order)
        
        # Submit orders
        self._process_orders(contract, orders)
        
    
    def _place_stop_limit_order(self, order_details):
        """Places stop-limit order.
        """
        self._check_connection()
        
        # Build contract
        contract = self._build_contract(order_details)
        
        # Create stop limit order
        action = 'BUY' if order_details["size"] > 0 else 'SELL'
        units = abs(order_details["size"])
        lmtPrice = order_details["order_limit_price"]
        stopPrice = order_details["order_stop_price"]
        order = ib_insync.StopLimitOrder(action, units, lmtPrice, stopPrice, 
                                         orderId=self.ib.client.getReqId(),
                                         transmit=False)
        
        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order_details, order)
        
        # Submit orders
        self._process_orders(contract, orders)
    
    
    def _place_limit_order(self, order_details):
        """Places limit order.
        """
        self._check_connection()
        
        # Build contract
        contract = self._build_contract(order_details)
        
        action = 'BUY' if order_details["size"] > 0 else 'SELL'
        units = abs(order_details["size"])
        lmtPrice = order_details["order_limit_price"]
        order = ib_insync.LimitOrder(action, units, lmtPrice, 
                                     orderId=self.ib.client.getReqId(),
                                     transmit=False)
        
        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order_details, order)
        
        # Submit orders
        self._process_orders(contract, orders)
    
    
    def _attach_auxiliary_orders(self, order_details: dict, 
                                 parent_order: ib_insync.order) -> list:
        orders = [parent_order]
        
        # TP order
        if order_details["take_profit"] is not None:
            takeProfit_order = self._create_take_profit_order(order_details, 
                                                              parent_order.orderId)
            orders.append(takeProfit_order)
        
        # SL order
        if order_details["stop_loss"] is not None:
            stopLoss_order = self._create_stop_loss_order(order_details,
                                                          parent_order.orderId)
            orders.append(stopLoss_order)
        
        return orders
    
    
    def _process_orders(self, contract: ib_insync.Contract, orders: list) -> None:
        
        self._check_connection()
        
        # Submit orders
        for i, order in enumerate(orders):
            if i == len(orders)-1:
                # Final order; set transmit to True
                order.transmit = True
            else:
                order.transmit = False
            self.ib.placeOrder(contract, order)
    
    
    def _convert_to_oca(self, orders: list, oca_group: str = None, 
                        oca_type: int = 1) -> list:
        """Converts a list of Orders to One Cancels All group of orders.

        Parameters
        ----------
        orders : list
            A list of orders.

        Returns
        -------
        oca_orders : list
            The orders modified to be in a OCA group.
        """
        self._check_connection()
        
        if oca_group is None:
            oca_group = f'OCA_{self.ib.client.getReqId()}'
        
        oca_orders = self.ib.oneCancelsAll(orders, oca_group, oca_type)
        return oca_orders
    
    
    def _create_take_profit_order(self, order_details: dict, parentId: int):
        quantity = order_details["size"]
        takeProfitPrice = order_details["take_profit"]
        action = 'BUY' if order_details["size"] < 0 else 'SELL'
        takeProfit_order = ib_insync.LimitOrder(action, 
                                                quantity, 
                                                takeProfitPrice,
                                                orderId=self.ib.client.getReqId(),
                                                transmit=False,
                                                parentId=parentId)
        return takeProfit_order
    
    
    def _create_stop_loss_order(self, order_details: dict, parentId: int):
        
        # TODO - add support for trailing SL
        quantity = order_details["size"]
        stopLossPrice = order_details["stop_loss"]
        action = 'BUY' if order_details["size"] < 0 else 'SELL'
        stopLoss_order = ib_insync.StopOrder(action, 
                                             quantity, 
                                             stopLossPrice,
                                             orderId=self.ib.client.getReqId(),
                                             transmit=True,
                                             parentId=parentId)
        return stopLoss_order
    
    
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
            # Requires order_details{'instrument', 'exchange', 'contract_month'}
            # TODO - make local_symbol required for futures?
            exchange = order_details['exchange'] if 'exchange' in order_details else 'GLOBEX'
            currency = order_details['currency'] if 'currency' in order_details else 'USD'
            contract_month = order_details['contract_month']
            local_symbol = order_details['local_symbol'] if 'local_symbol' in order_details else '' 
            contract = contract_object(symbol=symbol, 
                                       exchange=exchange, 
                                       currency=currency,
                                       lastTradeDateOrContractMonth=contract_month,
                                       localSymbol=local_symbol)
            
        elif security_type == 'ContFuture':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
            
        elif security_type == 'Forex':
            # pair='', exchange='IDEALPRO', symbol='', currency='', **kwargs)
            exchange = order_details['exchange'] if 'exchange' in order_details else 'IDEALPRO'
            
            contract = contract_object(pair=symbol, exchange=exchange)
            
        elif security_type == 'Index':
            raise NotImplementedError("Contract building for this security type is not supported yet.")
        elif security_type == 'CFD':
            # symbol='', exchange='', currency='',
            exchange = order_details['exchange'] if 'exchange' in order_details else 'SMART'
            currency = order_details['currency'] if 'currency' in order_details else 'USD'
            contract = contract_object(symbol=symbol, exchange=exchange, currency=currency)
            
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
