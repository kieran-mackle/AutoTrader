from __future__ import annotations
import numpy as np
import pandas as pd
from autotrader.brokers.trading import Order, Trade, Position
from autotrader.brokers.broker_utils import BrokerUtils


class Broker:
    """Autotrader virtual broker to simulate trading in backtest.

    Attributes
    ----------
    orders : dict
        A dictionary containing Orders submitted.
    trades : dict
        A dictionary containing all trades.
    leverage : int
        The account leverage.
    spread : float
        The average spread to use when opening and closing trades.
    margin_available : float
        The margin available on the account.
    equity : float
        The account equity balance.
    hedging : bool
        Flag whethere hedging is enabled on the account. The default is False.
    home_currency : str
        The default is 'AUD'.
    NAV : float
        The net asset value of the account.
    floating_pnl : float
        The floating PnL.
    verbosity : int
        The verbosity of the broker.
    commission_scheme : str
        The default is 'percentage'.
    commission : float
        The commission value.

    """
    
    def __init__(self, broker_config: dict, utils: BrokerUtils) -> None:
        self.utils = utils
        
        # Orders
        self.pending_orders = {}
        self.open_orders = {}
        self.filled_orders = {}
        self.cancelled_orders = {}
        self._order_id_instrument = {} # mapper from order_id to instrument
        
        # Trades
        self.open_trades = {}
        self.closed_trades = {}
        self._trade_id_instrument = {} # mapper from order_id to instrument
        
        # Account 
        self.home_currency = 'AUD'
        self.NAV = 0                    # Net asset value
        self.equity = 0                 # Account equity (balance)
        self.floating_pnl = 0
        self.margin_available = 0
        
        self.leverage = 1
        self.spread = 0
        self.hedging = False            # Allow simultaneous trades on opposing sides
        self.margin_closeout = 0.0      # Fraction at margin call
        
        self.verbosity = broker_config['verbosity']
        
        # Commissions
        self.commission_scheme = 'percentage'
        self.commission = 0
        
        # History
        self._NAV_hist = []
        self._equity_hist = []
        self._margin_hist = []
        self._time_hist = []
        self.holdings = []
        
        # Last order and trade counts
        self._last_order_id = 0
        self._last_trade_id = 0
        
    
    def __repr__(self):
        return 'AutoTrader Virtual Broker'
    
    
    def __str__(self):
        return 'AutoTrader Virtual Broker'
    
    
    def get_NAV(self) -> float:
        """Returns Net Asset Value of account.
        """
        return self.NAV
    
    
    def get_balance(self) -> float:
        """Returns balance of account.
        """
        return self.equity
    
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Place order with broker.
        """
        
        # Call order to set order time
        datetime_stamp = kwargs['order_time']
        order(order_time = datetime_stamp)
        
        if order.order_type == 'limit' or order.order_type == 'stop-limit':
            working_price = order.order_limit_price
        elif order.order_type == 'modify':
            # Get direction of related trade
            related_trade = self.open_trades[order.instrument][order.related_orders]
            order.direction = related_trade.direction
            working_price = order.order_price
        else:
            working_price = order.order_price
        
        # Convert stop distance to price
        if order.stop_loss is None and order.stop_distance:
            order.stop_loss = working_price - order.direction * \
                order.stop_distance*order.pip_value
        
        # Verify SL price
        invalid_order = False
        if order.stop_loss and order.direction*(working_price - order.stop_loss) < 0:
            direction = 'long' if order.direction > 0 else 'short'
            SL_placement = 'below' if order.direction > 0 else 'above'
            reason = "Invalid stop loss request: stop loss must be "+ \
                    f"{SL_placement} the order price for a {direction}" + \
                    " trade order.\n"+ \
                    f"Order Price: {working_price}\nStop Loss: {order.stop_loss}"
            invalid_order = True
        
        # Verify TP price
        if order.take_profit is not None and order.direction*(working_price - order.take_profit) > 0:
            direction = 'long' if order.direction > 0 else 'short'
            TP_placement = 'above' if order.direction > 0 else 'below'
            reason = "Invalid take profit request: take profit must be "+ \
                  f"{TP_placement} the order price for a {direction}" + \
                  " trade order.\n"+ \
                  f"Order Price: {working_price}\nTake Profit: {order.take_profit}"
            invalid_order = True
        
        # Assign order ID
        order.id = self._get_new_order_id()
        self._order_id_instrument[order.id] = order.instrument
        
        # Move order to pending_orders dict
        order.status = 'pending'
        try:
            self.pending_orders[order.instrument][order.id] = order
        except KeyError:
            self.pending_orders[order.instrument] = {order.id: order}
        
        # Submit order
        if invalid_order:
            if self.verbosity > 0:
                print(f"  Order {order.id} rejected.\n")
            self.cancel_order(order.id, reason, 'pending_orders')
        else:
            # Either move order to open_orders or leave in pending, depending on type
            immediate_orders = ['close', 'reduce', 'modify']
            if order.order_type in immediate_orders:
                # Move to open orders
                self._move_order(order, from_dict='pending_orders',
                                    to_dict='open_orders', new_status='open')
        
    
    def get_orders(self, instrument: str = None, 
                   order_status: str = 'open') -> dict:
        """Returns orders.
        """
        all_orders = getattr(self, order_status+'_orders')
        if instrument:
            try:
                orders = all_orders[instrument]
            except KeyError:
                orders = {}
        else:
            orders = {}
            for instr, instr_orders in all_orders.items():
                orders.update(instr_orders)
        return orders.copy()
    
    
    def cancel_order(self, order_id: int, reason: str = None, 
                     from_dict: str = 'open_orders') -> None:
        """Cancels the order.
        """
        instrument = self._order_id_instrument[order_id]
        from_dict = getattr(self, from_dict)[instrument]
        
        if instrument not in self.cancelled_orders: 
            self.cancelled_orders[instrument] = {}
        self.cancelled_orders[instrument][order_id] = from_dict.pop(order_id)
        self.cancelled_orders[instrument][order_id].reason = reason
        self.cancelled_orders[instrument][order_id].status = 'cancelled'
        
        if self.verbosity > 0 and reason:
            print(reason)
    
    
    def get_trades(self, instrument: str = None,
                   trade_status: str = 'open') -> dict:
        """Returns open trades for the specified instrument.
        """
        all_trades = getattr(self, trade_status+'_trades')
        if instrument:
            # Specific instruments requested
            try:
                trades = all_trades[instrument]
            except KeyError:
                trades = {}
        else:
            # Return all currently open trades
            trades = {}
            for instr, instr_trades in all_trades.items():
                trades.update(instr_trades)
        return trades.copy()
    
    
    def get_trade_details(self, trade_ID: int) -> Trade:
        """Returns the trade specified by trade_ID.
        """
        instrument = self._trade_id_instrument[trade_ID]
        return self.open_trades[instrument][trade_ID]
    
    
    def get_positions(self, instrument: str = None) -> dict:
        """Returns the open positions (including all open trades) in the account.
        """
        if instrument:
            # instrument provided
            instruments = [instrument]
        else:
            # No specific instrument requested, use all
            instruments = list(self.open_trades.keys())
            
        open_positions = {}
        for instrument in instruments:
            # First get open trades
            open_trades = self.get_trades(instrument) 
            if len(open_trades) > 0:
                long_units = 0
                long_PL = 0
                long_margin = 0
                short_units = 0
                short_PL = 0
                short_margin = 0
                total_margin = 0
                trade_IDs = []
                
                for trade_id, trade in open_trades.items():
                    trade_IDs.append(trade.id)
                    total_margin += trade.margin_required
                    if trade.direction > 0:
                        # Long trade
                        long_units += trade.size
                        long_PL += trade.unrealised_PL
                        long_margin += trade.margin_required
                    else:
                        # Short trade
                        short_units += trade.size
                        short_PL += trade.unrealised_PL
                        short_margin += trade.margin_required
            
                # Construct instrument position dict
                instrument_position = {'long_units': long_units,
                                       'long_PL': long_PL,
                                       'long_margin': long_margin,
                                       'short_units': short_units,
                                       'short_PL': short_PL,
                                       'short_margin': short_margin,
                                       'total_margin': total_margin,
                                       'trade_IDs': trade_IDs,
                                       'instrument': instrument,
                                       'net_position': long_units-short_units}
                
                instrument_position = Position(**instrument_position)
                
                # Append position dict to open_positions dict
                open_positions[instrument] = instrument_position
                
        return open_positions
    
    
    def get_margin_available(self) -> float:
        """Returns the margin available on the account.
        """
        return self.margin_available
    
    
    def _fill_order(self, instrument: str, order_id: int, 
                    candle: pd.core.series.Series, 
                    limit_price: float = None) -> None:
        """Fills an open order.
        
        Notes
        -----
        If hedging is not enabled, any orders which are contrary to an open
        position will first reduce (or close) the open position before 
        being filled. If the units remaining of the order after reducing the 
        open position exceed margin requirements, the entire order will be 
        cancelled, and the original position will not be impacted.
        """
        order = self.open_orders[instrument][order_id]
        
        close_existing_position = False
        if not self.hedging:
            # Check if current order will reduce or add to existing position
            current_position = self.get_positions(instrument)
            net_position = current_position[order.instrument].net_position \
                if current_position else order.direction
            if order.direction != np.sign(net_position):
                if order.size > abs(net_position):
                    # Modify order size to net remaining units
                    order.size -= abs(net_position)
                    close_existing_position = True
                else:
                    # Reduce the current position
                    self._reduce_position(order)
                    self._move_order(order)
                    return
            
        # Calculate margin requirements
        current_price = candle.Open
        position_value = order.size * current_price * order.HCF
        margin_required = self._calculate_margin(position_value)
        spread_shift = 0.5 * order.direction * self.spread
        
        if margin_required < self.margin_available:
            # Determine working price
            if limit_price is None:
                working_price = candle.Open + spread_shift
            else:
                working_price = limit_price + spread_shift
                
            if close_existing_position:
                # Close the open position before proceeding
                self._close_position(instrument, candle, working_price)
            
            # Fill order
            trade_id = self._get_new_trade_id()
            self._trade_id_instrument[trade_id] = instrument
            trade = Trade(order)
            trade.id = trade_id
            trade.fill_price = working_price
            trade.last_price = working_price
            trade.time_filled = candle.name
            trade.margin_required = margin_required
            trade.value = position_value
            try:
                self.open_trades[instrument][trade_id] = trade
            except KeyError:
                self.open_trades[instrument] = {trade_id: trade}
            
            # Move order to filled_orders dict
            self._move_order(order)
            
        else:
            # Cancel order
            cancel_reason = "Insufficient margin to fill order."
            self.cancel_order(order_id, cancel_reason)
    
    
    def _move_order(self, order: Order, from_dict: str = 'open_orders', 
                        to_dict: str = 'filled_orders', 
                        new_status: str = 'filled'):
        """Moves an order from the from_dict to the to_dict."""
        order.status = new_status
        from_dict = getattr(self, from_dict)[order.instrument]
        to_dict = getattr(self, to_dict)
        popped_item = from_dict.pop(order.id)
        try:
            to_dict[order.instrument][order.id] = popped_item
        except KeyError:
            to_dict[order.instrument] = {order.id: popped_item}
    
    
    def _update_positions(self, candle: pd.core.series.Series, 
                          instrument: str) -> None:
        """Updates orders and open positions based on current candle.
        """
        
        # Open pending orders
        pending_orders = self.get_orders(instrument, 'pending').copy()
        for order_id, order in pending_orders.items():
            if candle.name > order.order_time:
                self._move_order(order, from_dict='pending_orders',
                                 to_dict='open_orders', new_status='open')
        
        # Update open orders for current instrument
        open_orders = self.get_orders(instrument).copy()
        for order_id, order in open_orders.items():
            if order.order_type == 'market':
                # Market order type - proceed to fill
                self._fill_order(instrument, order_id, candle)
            
            elif order.order_type == 'stop-limit':
                # Check if order_stop_price has been reached yet
                if candle.Low < order.order_stop_price < candle.High:
                    # order_stop_price has been reached, change order type to 'limit'
                    order.order_type = 'limit'
            
            elif order.order_type == 'modify':
                # Modification order
                self._modify_order(order)
            
            elif order.order_type == 'close':
                related_order = order.related_orders
                self._close_position(order.instrument, candle, 
                                     candle.Close, trade_id = related_order)
                self._move_order(order)
                
            elif order.order_type == 'reduce':
                self._reduce_position(order)
                self._move_order(order)
                
            # Check for limit orders
            if order.order_type == 'limit':
                # Limit order type
                if order.direction > 0:
                    if candle.Low < order.order_limit_price:
                        self._fill_order(instrument, order_id, candle, 
                                         order.order_limit_price)
                else:
                    if candle.High > order.order_limit_price:
                        self._fill_order(instrument, order_id, candle, 
                                         order.order_limit_price)
        
        # Update margin available after any order changes 
        self._update_margin(instrument, candle)

        # Update open trades
        open_trades = self.get_trades(instrument).copy()
        for trade_id, trade in open_trades.items():
            # Update stop losses
            if trade.stop_type == 'trailing':
                # Trailing stop loss type, check if price has moved SL
                if trade.stop_distance is not None:
                    # pip_value = self.utils.get_pip_ratio(trade.instrument)
                    pip_distance = trade.stop_distance
                    distance = pip_distance*trade.pip_value # price units
                else:
                    distance = abs(trade.fill_price - trade.stop_loss)
                    # pip_value = self.utils.get_pip_ratio(trade.instrument)
                    trade.stop_distance = distance / trade.pip_value
                    
                if trade.direction > 0:
                    # long position, stop loss only moves up
                    new_stop = candle.High - distance
                    if new_stop > trade.stop_loss:
                        self._update_stop_loss(instrument, trade_id, new_stop, 
                                               new_stop_type='trailing')
                else:
                    # short position, stop loss only moves down
                    new_stop = candle.Low + distance
                    if new_stop < trade.stop_loss:
                        self._update_stop_loss(instrument, trade_id, new_stop, 
                                               new_stop_type='trailing')
            
            # Update trades
            # TODO - below could be generalised by trade direction multiplier
            if trade.direction > 0:
                # Long trade
                if trade.stop_loss and \
                    candle.Low < trade.stop_loss:
                    # Stop loss hit
                    self._close_position(trade.instrument, 
                                        candle, 
                                        trade.stop_loss,
                                        trade_id)
                elif trade.take_profit and \
                    candle.High > trade.take_profit:
                    # Take Profit hit
                    self._close_position(trade.instrument, 
                                        candle, 
                                        trade.take_profit,
                                        trade_id)
                else:
                    # Position is still open, update value of holding
                    trade.last_price = candle.Close
                    trade.last_time = candle.name
                    trade.unrealised_PL = trade.direction*trade.size * \
                        (trade.last_price - trade.fill_price)*trade.HCF
            
            else:
                # Short trade
                if trade.stop_loss is not None and \
                    candle.High > trade.stop_loss:
                    # Stop loss hit
                    self._close_position(trade.instrument, candle, 
                                        trade.stop_loss, trade_id)
                elif trade.take_profit is not None and \
                    candle.Low < trade.take_profit:
                    # Take Profit hit
                    self._close_position(trade.instrument, candle, 
                                         trade.take_profit, trade_id)
                else:
                    # Position is still open, update value of holding
                    trade.last_price = candle.Close
                    trade.last_time = candle.name
                    trade.unrealised_PL = trade.direction*trade.size * \
                        (trade.last_price - trade.fill_price)*trade.HCF
                            
        # Update floating pnl and margin available 
        self._update_margin(instrument, candle)
        
        # Update open position value
        self.NAV = self.equity + self.floating_pnl
        
        # Update account history
        self._NAV_hist.append(self.NAV)
        self._equity_hist.append(self.equity)
        self._margin_hist.append(self.margin_available)
        self._time_hist.append(candle.name)
        
        holdings = self._get_holding_allocations()
        self.holdings.append(holdings)
        
    
    def _close_position(self, instrument: str, candle: pd.core.series.Series, 
                        exit_price: float, trade_id=None) -> None:
        """Closes position in instrument.
        """
        
        if trade_id:
            # single trade specified to close
            self._close_trade(instrument, trade_id=trade_id, 
                              exit_price=exit_price, candle=candle)
        else:
            # Close all positions for instrument
            open_trades = self.open_trades[instrument].copy()
            for trade_id, trade in open_trades.items():
                self._close_trade(instrument, trade_id=trade_id, 
                                  exit_price=exit_price, candle=candle)
    
    
    def _close_trade(self, instrument: str, trade_id: int = None, 
                     exit_price: float = None,
                     candle: pd.core.series.Series = None) -> None:
        """Closes trade by order number.

        Parameters
        ----------
        trade_id : int, optional
            The trade id. The default is None.
        exit_price : float, optional
            The trade exit price. The default is None.
        candle : pd.core.series.Series, optional
            Slice of OHLC data. The default is None.

        Returns
        -------
        None
            The trade will be marked as closed.
        """
        trade = self.open_trades[instrument][trade_id]
        fill_price = trade.fill_price
        size = trade.size
        direction = trade.direction
        HCF = trade.HCF
        
        # Account for missing inputs
        exit_price = trade.last_price if not exit_price else exit_price
        
        # Update portfolio with profit/loss
        gross_PL = direction*size*(exit_price - fill_price)*HCF
        commission = self._calculate_commissions(instrument, trade_id, exit_price, size)
        net_profit = gross_PL - commission
        
        # Add trade to closed positions
        trade.profit = net_profit
        trade.balance = self.equity
        trade.exit_price = exit_price
        trade.fees = commission
        if candle is None:
            trade.exit_time = trade.last_time
        else:
            trade.exit_time = candle.name 
        trade.status = 'closed'
        
        popped_trade = self.open_trades[instrument].pop(trade_id)
        try:
            self.closed_trades[instrument][trade_id] = popped_trade
        except KeyError:
            self.closed_trades[instrument] = {trade_id: popped_trade}
        
        # Update account
        self._add_funds(net_profit)
    
    
    def _reduce_position(self, order: Order) -> None:
        """Reduces the position of the specified instrument by FIFO. 
        
        The direction parameter of the order is used to specify whether 
        to reduce long units, or to reduce short units. For example, the
        order details below will reduce long units of the position being 
        held.
        """
        # Consired long vs. short units to be reduced
        instrument = order.instrument
        reduction_size = order.size
        reduction_direction = order.direction
        
        # Get open trades for instrument
        open_trades = self.open_trades[instrument].copy()
        
        # Modify existing trades until there are no more units to reduce
        units_to_reduce = reduction_size
        while units_to_reduce > 0:
            for trade_id, trade in open_trades.items():
                if trade.direction != reduction_direction:
                    # Only reduce long trades when reduction direction is -1
                    # Only reduce short trades when reduction direction is 1
                    if units_to_reduce >= trade.size:
                        # Entire trade must be closed
                        last_price = trade.last_price
                        self._close_trade(instrument, trade_id=trade_id, 
                                          exit_price=last_price)
                        
                        # Update units_to_reduce
                        units_to_reduce -= abs(trade.size)
                        
                    else:
                        # Partially close trade
                        self._partial_trade_close(instrument, trade_id, 
                                                  units_to_reduce)
                        
                        # Update units_to_reduce
                        units_to_reduce = 0
                    
    
    def _partial_trade_close(self, instrument: str, trade_id: int, 
                             units: float) -> None:
        """Partially closes a trade.
        
        The original trade ID remains, but the trade size may be reduced. The
        portion that gets closed is assigned a new ID.
        """
        trade = self.open_trades[instrument][trade_id]
        
        # Create new trade for reduced amount
        partial_trade = Trade._split(trade, units)
        partial_trade_id = self._get_new_trade_id()
        partial_trade.id = partial_trade_id
        self.open_trades[instrument][partial_trade_id] = partial_trade
        
        # Close partial trade
        self._close_trade(instrument, partial_trade_id)

        # Keep track of partial trade id
        self._trade_id_instrument[partial_trade_id] = instrument
        
    
    def _calculate_commissions(self, instrument: str, trade_id: int, 
                               exit_price: float, units: float = None) -> float:
        """Calculates trade commissions.
        """
        if self.commission_scheme == 'percentage':
            fill_price = self.open_trades[instrument][trade_id].fill_price
            size = self.open_trades[instrument][trade_id].size if units is None else units
            HCF = self.open_trades[instrument][trade_id].HCF
            
            open_trade_value = abs(size)*fill_price*HCF
            close_trade_value = abs(size)*exit_price*HCF
            commission  = (self.commission/100) * (open_trade_value + close_trade_value)
        
        elif self.commission_scheme == 'fixed':
            size = self.open_trades[instrument][trade_id].size if units is None else units
            commission = self.commission * size
            
        return commission
    
    
    def _add_funds(self, amount: float) -> None:
        """Adds funds to brokerage account.
        """
        self.equity += amount
        self._update_margin()
    
    
    def _make_deposit(self, deposit: float) -> None:
        """Adds deposit to account balance and NAV.
        """
        self.equity += deposit
        self.NAV += deposit
        self._update_margin()
    
    
    def _calculate_margin(self, position_value: float) -> float:
        """Calculates margin required to take a position.
        """
        margin = position_value / self.leverage
        return margin
    
    
    def _update_margin(self, instrument: str = None, 
                       candle: pd.core.series.Series = None) -> None:
        """Updates margin available in account.
        """
        margin_used = 0
        floating_pnl = 0
        open_trades = self.get_trades()
        for trade_id, trade in open_trades.items():
            size = trade.size
            HCF = trade.HCF
            last_price = trade.last_price
            trade_value = abs(size) * last_price * HCF
            margin_required = self._calculate_margin(trade_value)
            margin_used += margin_required
            
            # Update margin required in trade dict
            trade.margin_required = margin_required
            trade.value = trade_value
            
            # Floating pnl
            floating_pnl += trade.unrealised_PL
                
        # Update unrealised PnL
        self.floating_pnl = floating_pnl
        
        # Update margin available
        self.margin_available = self.NAV - margin_used
        
        # Check for margin call
        # TODO - due to ordering of updates, margin call could occur on the last
        # instrument, just by chance...
        if self.leverage > 1 and self.margin_available/self.NAV < self.margin_closeout:
            # Margin call
            if self.verbosity > 0:
                print("MARGIN CALL: closing all positions.")
            self._margin_call(instrument, candle)

    
    def _modify_order(self, order: Order) -> None:
        """Modify order with updated parameters. Called when order_type = 'modify', 
        modifies trade specified by related_orders key.
        """
        # Get ID of trade to modify
        modify_trade_id = order.related_orders
        instrument = order.instrument
        
        if order.stop_loss is not None:
            # New stop loss provided
            self._update_stop_loss(instrument, modify_trade_id, order.stop_loss, 
                                   order.stop_type)
            
        if order.take_profit is not None:
            self._update_take_profit(instrument, modify_trade_id, order.take_profit)
        
        # Move order to filled_orders dict
        self._move_order(order)
        
        
    def _update_stop_loss(self, instrument: str, trade_id: int, 
                          new_stop_loss: float, 
                          new_stop_type: str = 'limit') -> None:
        """Updates stop loss on open trade.
        """
        self.open_trades[instrument][trade_id].stop_loss = new_stop_loss
        self.open_trades[instrument][trade_id].stop_type = new_stop_type
    
    
    def _update_take_profit(self, instrument: str, trade_id: int, 
                            new_take_profit: float) -> None:
        """Updates take profit on open trade.
        """
        self.open_trades[instrument][trade_id].take_profit = new_take_profit
        
        
    def _get_new_order_id(self):
        self._last_order_id += 1
        return self._last_order_id
    
    
    def _get_new_trade_id(self):
        self._last_trade_id += 1
        return self._last_trade_id
    
    
    def _margin_call(self, instrument: str, candle: pd.core.series.Series):
        """Closes open positions.
        """
        self._close_position(instrument, candle, candle.Close)
    
    
    def _get_holding_allocations(self):
        """Returns a dictionary containing the nominal value of
        all open trades."""
        open_trades = self.get_trades()
        values = {}
        for trade_id, trade in open_trades.items():
            if trade.instrument in values:
                values[trade.instrument] += trade.size * trade.last_price
            else:
                values[trade.instrument] = trade.size * trade.last_price
                
        if len(values) == 0:
            values = {None: None}
            
        return values
    
