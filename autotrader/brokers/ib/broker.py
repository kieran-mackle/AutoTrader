import ib_insync
import numpy as np
from autotrader.brokers.trading import Order, Trade, Position
from autotrader.brokers.ib.utils import Utils


class Broker:
    """AutoTrader-InteractiveBrokers API interface.
    
    Attributes
    ----------
    utils : Utils
        The broker utilities.
    ib : ib_insync connection
        Used to query IB.
    account : str
        The active IB account.
    
    Notes
    -----
        - when closing a position using close_position(), if there are attached SL
          and/or TP orders, they must be closed manually using cancel_pending_order().
          Usually only one of the pair needs to be cancelled, and the other will too.
        - required signal_dict keys for different security types (eg. futures 
          require symbol, exchange and contract_month)
    """
    
    def __init__(self, config: dict, utils: Utils = None) -> None:
        """Initialise AutoTrader-Interactive Brokers API interface.
        
        Parameters
        ----------
        config : dict
            The IB configuration dictionary. This can contain the host, port, 
            clientID and read_only boolean flag.
        utils : Utils, optional
            Broker utilities class instance. The default is None.
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
    
    
    def get_NAV(self) -> float:
        """Returns the net asset/liquidation value of the account.
        """
        self._check_connection()
        summary = self.get_summary()
        return float(summary['NetLiquidation']['value'])
    
    
    def get_balance(self) -> float:
        """Returns account balance.
        """
        self._check_connection()
        summary = self.get_summary()
        return float(summary['TotalCashValue']['value'])
        
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Disassembles order_details dictionary to place order.

        Parameters
        ----------
        order: Order
            The AutoTrader Order.

        Returns
        -------
        None
            Orders will be submitted to IB.
        """
        self._check_connection()
        
        # Assign order_time, order_price, HCF
        price_data = self._get_price(order)
        order_price = price_data['ask'] if order.direction > 0 else price_data['bid']
        
        # Call order with price and time
        order(broker=self, order_price=order_price)
        
        if order.order_type == 'market':
            self._place_market_order(order)
        elif order.order_type == 'stop-limit':
            self._place_stop_limit_order(order)
        elif order.order_type == 'limit':
            self._place_limit_order(order)
        elif order.order_type == 'close':
            self._close_position(order)
        else:
            print("Order type not recognised.")
        
        self._refresh()
        
    
    def get_orders(self, instrument: str = None, **kwargs) -> dict:
        """Returns all pending orders (have not been filled) in the account.

        Parameters
        ----------
        instrument : str, optional
            The trading instrument's symbol. The default is None.

        Returns
        -------
        dict
            Pending orders for the requested instrument. If no instrument is provided,
            all pending orders will be returned.
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
                
                if instrument is not None and contract.symbol == instrument:
                    pending_orders[new_order['order_ID']] = Order._from_dict(new_order)
                elif instrument is None:
                    pending_orders[new_order['order_ID']] = Order._from_dict(new_order)
            
        return pending_orders
    
    
    def cancel_order(self, order_id: int, **kwargs) -> list:
        """Cancels pending order by order ID.
        
        Parameters
        ----------
        order_id : int
            The ID of the order to be concelled.

        Returns
        -------
        list
            A list of the cancelled trades.

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
    
    
    def get_trades(self, instrument: str = None, **kwargs) -> dict:
        """Returns the open trades held by the account. 

        Parameters
        ----------
        instrument : str, optional
            The trading instrument's symbol. The default is None.

        Returns
        -------
        dict
            The open trades.
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
                # Trade order has been filled
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
                
                if instrument is not None and contract.symbol == instrument:
                    open_trades[new_trade['order_ID']] = Trade(new_trade)
                elif instrument is None:
                    open_trades[new_trade['order_ID']] = Trade(new_trade)
        
        return open_trades
    
    
    def get_trade_details(self, trade_ID: str, **kwargs) -> dict:
        """Returns the details of the trade specified by trade_ID.

        Parameters
        ----------
        trade_ID : str
            The ID of the trade.

        Returns
        -------
        dict
            The details of the trade.
        """
        raise NotImplementedError("This method is not available.")
        # self._check_connection()
        # TODO - implement (?)
        # return {}
    
    
    def get_positions(self, instrument: str = None, 
                      local_symbol: str = None, **kwargs) -> dict:
        """Gets the current positions open on the account.
        
        Parameters
        ----------
        instrument : str, optional
            The trading instrument's symbol. The default is None.
        local_symbol : str, optional
            The exchange-local product symbol. The default is None.
            
        Returns
        -------
        open_positions : dict
            A dictionary containing details of the open positions.
        """
        self._check_connection()
        
        symbol_attr = 'symbol' if local_symbol is None else 'localSymbol'
        matching_symbol = instrument if local_symbol is None else local_symbol
        
        all_positions = self.ib.portfolio()
        open_positions = {}
        for position in all_positions:
            units = position.position
            pnl = position.unrealizedPNL
            # pos_symbol = position.contract.symbol
            pos_symbol = getattr(position.contract, symbol_attr)
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
        
            if pos_symbol == matching_symbol:
                # Only add positions in requested symbol
                open_positions[pos_symbol] = Position(**pos_dict)
            else:
                # Append all positions
                open_positions[pos_symbol] = Position(**pos_dict)
        
        return open_positions
    
    
    def get_summary(self) -> dict:
        """Returns account summary.
        """
        self._check_connection()
        raw_summary = self.ib.accountSummary(self.account)
        summary = self.utils.accsum_to_dict(self.account, raw_summary)
        
        return summary
    
    
    def _get_price(self, order: Order, snapshot: bool = False, **kwargs) -> dict:
        """Returns current price (bid+ask) and home conversion factors.
        
        Parameters
        ----------
        order: Order
            The AutoTrader Order.
        snapshot : bool, optional
            Request a snapshot of the price. The default is False.

        Returns
        -------
        dict
            A dictionary containing the bid and ask prices.
        """
        self._check_connection()
        contract = self.utils.build_contract(order)
        self.ib.qualifyContracts(contract)
        ticker = self.ib.reqMktData(contract, snapshot=snapshot)
        while ticker.last != ticker.last: self.ib.sleep(1)
        self.ib.cancelMktData(contract)
        price = {"ask": ticker.ask,
                 "bid": ticker.bid,
                 "negativeHCF": 1,
                 "positiveHCF": 1,}
        return price
    
    
    def _get_historical_data(self, instrument: str, interval: str, 
                            from_time: str, to_time: str):
        """Returns historical price data.
        """
        # self._check_connection()
        # self.ib.reqHistoricalData()
        raise NotImplementedError("This method is not available.")
        
        
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
    
    
    def _close_position(self, order: Order, **kwargs):
        """Closes open position of symbol by placing opposing market order.
        """
        self._check_connection()
        
        instrument = order.instrument
        position = self.get_open_positions(instrument)[instrument]
        position_units = position['position']
        
        # Place opposing market order
        action = 'BUY' if position_units < 0 else 'SELL'
        units = abs(position_units)
        IBorder = ib_insync.MarketOrder(action, units)
        contract = position['contract']
        self.ib.qualifyContracts(contract)
        self.ib.placeOrder(contract, IBorder)
        
    
    def _place_market_order(self, order: Order):
        """Places a market order.
        """
        self._check_connection()
        
        # Build contract
        contract = self.utils.build_contract(order)
        
        # Create market order
        action = 'BUY' if order.size > 0 else 'SELL'
        units = abs(order.size)
        market_order = ib_insync.MarketOrder(action, units, 
                                             orderId=self.ib.client.getReqId(),
                                             transmit=False)
        
        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order, market_order)
        
        # Submit orders
        self._process_orders(contract, orders)
        
    
    def _place_stop_limit_order(self, order):
        """Places stop-limit order.
        """
        self._check_connection()
        
        # Build contract
        contract = self.utils.build_contract(order)
        
        # Create stop limit order
        action = 'BUY' if order.size > 0 else 'SELL'
        units = abs(order.size)
        lmtPrice = order.order_limit_price
        stopPrice = order.order_stop_price
        IBorder = ib_insync.StopLimitOrder(action, units, lmtPrice, stopPrice, 
                                         orderId=self.ib.client.getReqId(),
                                         transmit=False)
        
        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order, IBorder)
        
        # Submit orders
        self._process_orders(contract, orders)
    
    
    def _place_limit_order(self, order):
        """Places limit order.
        """
        self._check_connection()
        
        # Build contract
        contract = self.utils.build_contract(order)
        
        action = 'BUY' if order.size > 0 else 'SELL'
        units = abs(order.size)
        lmtPrice = order.order_limit_price
        IBorder = ib_insync.LimitOrder(action, units, lmtPrice, 
                                     orderId=self.ib.client.getReqId(),
                                     transmit=False)
        
        # Attach SL and TP orders
        orders = self._attach_auxiliary_orders(order, IBorder)
        
        # Submit orders
        self._process_orders(contract, orders)
    
    
    def _attach_auxiliary_orders(self, order: Order, 
                                 parent_order: ib_insync.order) -> list:
        orders = [parent_order]
        
        # TP order
        if order.take_profit is not None:
            takeProfit_order = self._create_take_profit_order(order, 
                                                              parent_order.orderId)
            orders.append(takeProfit_order)
        
        # SL order
        if order.stop_loss is not None:
            stopLoss_order = self._create_stop_loss_order(order,
                                                          parent_order.orderId)
            orders.append(stopLoss_order)
        
        return orders
    
    
    def _process_orders(self, contract: ib_insync.Contract, orders: list) -> None:
        """Processes a list of orders for a given contract.
        """
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
    
    
    def _create_take_profit_order(self, order: Order, parentId: int):
        """Constructs a take profit order.
        """
        quantity = order.size
        takeProfitPrice = order.take_profit
        action = 'BUY' if order.size < 0 else 'SELL'
        takeProfit_order = ib_insync.LimitOrder(action, 
                                                quantity, 
                                                takeProfitPrice,
                                                orderId=self.ib.client.getReqId(),
                                                transmit=False,
                                                parentId=parentId)
        return takeProfit_order
    
    
    def _create_stop_loss_order(self, order: Order, parentId: int):
        """Constructs a stop loss order.
        """
        # TODO - add support for trailing SL
        quantity = order.size
        stopLossPrice = order.stop_loss
        action = 'BUY' if order.size < 0 else 'SELL'
        stopLoss_order = ib_insync.StopOrder(action, 
                                             quantity, 
                                             stopLossPrice,
                                             orderId=self.ib.client.getReqId(),
                                             transmit=True,
                                             parentId=parentId)
        return stopLoss_order
    
