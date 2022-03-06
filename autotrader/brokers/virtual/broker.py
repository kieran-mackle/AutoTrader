from __future__ import annotations
import numpy as np
import pandas as pd
from autotrader.brokers.trading import Order, Trade, Position
from autotrader.brokers.broker_utils import BrokerUtils


class Broker:
    """Autotrader virtual broker to simulate trading.
    """
    
    def __init__(self, broker_config: dict, utils: BrokerUtils) -> None:
        self.utils = utils
        
        # Orders
        self.orders = {}
        
        # Trades
        self.trades = {}
        
        # Account 
        self.leverage = 1
        self.spread = 0 # TODO - pips or price units? Add docs
        self.margin_available = 0
        self.portfolio_balance = 0
        
        self.profitable_trades = 0
        self.peak_value = 0
        self.low_value = 0
        self.max_drawdown = 0
        self.home_currency = 'AUD'
        self.NAV = 0
        self.unrealised_PL = 0
        self.verbosity = broker_config['verbosity']
        
        # Commissions
        self.commission_scheme = 'percentage'
        self.commission = 0
        
    
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
        return self.portfolio_balance
    
    
    def place_order(self, order: Order, **kwargs) -> None:
        """Place order with broker.
        """
        # Assign order_time, order_price, HCF
        price_data = self._get_price(instrument=order.instrument, 
                                     data=kwargs['data'], 
                                     conversion_data=kwargs['quote_data'], 
                                     i=kwargs['i'])
        datetime_stamp = kwargs['data'].index[kwargs['i']]
        
        if order.direction < 0:
            order_price = price_data['bid']
            HCF = price_data['negativeHCF']
        else:
            order_price = price_data['ask']
            HCF = price_data['positiveHCF']
        
        # Call order with price and time
        order(self, order_price, datetime_stamp, HCF)
        
        if order.order_type == 'limit' or order.order_type == 'stop-limit':
            working_price = order.order_limit_price
        else:
            working_price = order.order_price
        
        # Convert stop distance to price
        if not order.stop_loss and order.stop_distance:
            pip_value = self.utils.get_pip_ratio(order.instrument)
            order.stop_loss = working_price - np.sign(order.size)*order.stop_distance*pip_value
        
        # Verify SL price
        invalid_order = False
        if order.stop_loss and np.sign(order.size)*(working_price - order.stop_loss) < 0:
            direction = 'long' if np.sign(order.size) > 0 else 'short'
            SL_placement = 'below' if np.sign(order.size) > 0 else 'above'
            reason = "Invalid stop loss request: stop loss must be "+ \
                    f"{SL_placement} the order price for a {direction}" + \
                    " trade order.\n"+ \
                    f"Order Price: {working_price}\nStop Loss: {order.stop_loss}"
            invalid_order = True
        
        # Verify TP price
        if order.take_profit is not None and np.sign(order.size)*(working_price - order.take_profit) > 0:
            direction = 'long' if np.sign(order.size) > 0 else 'short'
            TP_placement = 'above' if np.sign(order.size) > 0 else 'below'
            reason = "Invalid take profit request: take profit must be "+ \
                  f"{TP_placement} the order price for a {direction}" + \
                  " trade order.\n"+ \
                  f"Order Price: {working_price}\nTake Profit: {order.take_profit}"
            invalid_order = True
        
        # Submit order
        order.id = self._get_new_order_id()
        if invalid_order:
            if self.verbosity > 0:
                print(f"  Order {order.id} rejected.\n")
            self.cancel_order(order.id, reason)
        else:
            immediate_orders = ['close', 'reduce']
            status = 'open' if order.order_type in immediate_orders else 'pending'
            order.status = status
        
        # Append order to orders 
        self.orders[order.id] = order
        
    
    def get_orders(self, instrument: str = None, 
                   order_status: str = 'open') -> dict:
        """Returns orders.
        """
        orders = {}
        if instrument:
            for order_id, order in self.orders.items():
                if order.instrument == instrument and order.status == order_status:
                    orders[order_id] = order
        else:
            for order_id, order in self.orders:
                if order.status == order_status:
                    orders[order_id] = order
        return orders
    
    
    def cancel_order(self, order_id: int, reason: str = None) -> None:
        """Changes the status of an order to cancelled.
        """
        self.orders[order_id].reason = reason
        self.orders[order_id].status = 'cancelled'
        
        if self.verbosity > 0 and reason:
            print(reason)
    
    
    def get_trades(self, instruments: str | list = None,
                   trade_status: str = 'open') -> dict:
        """Returns open trades for the specified instrument.
        """
        open_trades = {}
        if instruments:
            # Specific instruments requested
            if type(instruments) is str:
                # Single instrument provided, put into list
                instruments = [instruments]
                
            for trade_id, trade in self.trades.items():
                if trade.instrument in instruments and trade.status == trade_status:
                    open_trades[trade_id] = trade
        else:
            # Return all currently open positions
            for trade_id, trade in self.trades.items():
                if trade.status == trade_status:
                    open_trades[trade_id] = trade
        
        return open_trades
    
    
    def get_trade_details(self, trade_ID: int) -> Trade:
        """Returns the trade specified by trade_ID.
        """
        return self.trades[trade_ID]
    
    
    def get_positions(self, instruments: str = None, 
                      as_dict: bool = False) -> Position:
        """Returns the open positions (including all open trades) in the account.
        """
        # TODO - as_dict - make method of Positions not arg here
        if instruments:
            # instruments provided, check type
            if type(instruments) is str:
                # Single instrument provided, put into list
                instruments = [instruments]
        else:
            # No specific instrument requested, get all open
            instruments = []
            for trade_id, trade in self.trades.items(): 
                instruments.append(trade.instrument)
            
        open_positions = {}
        for instrument in instruments:
            # First get open trades
            open_trades = self.get_trades(instrument)
            
            if len(open_trades) > 0:
                # Trades exist for current instrument, collate
                long_units = 0
                long_PL = 0
                long_margin = 0
                short_units = 0
                short_PL = 0
                short_margin = 0
                total_margin = 0
                trade_IDs = []
                
                for trade_id in open_trades:
                    trade_IDs.append(trade_id)
                    total_margin += open_trades[trade_id].margin_required
                    if open_trades[trade_id].size > 0:
                        # Long trade
                        long_units += open_trades[trade_id].size
                        long_PL += open_trades[trade_id].unrealised_PL
                        long_margin += open_trades[trade_id].margin_required
                    else:
                        # Short trade
                        short_units += open_trades[trade_id].size
                        short_PL += open_trades[trade_id].unrealised_PL
                        short_margin += open_trades[trade_id].margin_required
            
                # Construct instrument position dict
                instrument_position = {'long_units': long_units,
                                       'long_PL': long_PL,
                                       'long_margin': long_margin,
                                       'short_units': short_units,
                                       'short_PL': short_PL,
                                       'short_margin': short_margin,
                                       'total_margin': total_margin,
                                       'trade_IDs': trade_IDs,
                                       'instrument': instrument,}
                
                if not as_dict:
                    instrument_position = Position(**instrument_position)
                
                # Append position dict to open_positions dict
                open_positions[instrument] = instrument_position
                        
        return open_positions
    
    
    def get_margin_available(self) -> float:
        """Returns the margin available on the account.
        """
        return self.margin_available
    
    
    def _get_price(self, instrument: str, data: pd.core.series.Series = None, 
                   conversion_data: pd.core.series.Series = None, 
                   i: int = None) -> dict:
        """Returns the price data dict.
        """
        # TODO - where is this method called from? Can it be split to the feed
        # for autodata?
        # TODO - include bid/ask spread here
        if conversion_data is not None:
            ask = data.Close[i]
            bid = data.Close[i]
            conversion_price = conversion_data.Close[i]
            
            if bid == conversion_price:
                negativeHCF = 1
                positiveHCF = 1
            else:
                negativeHCF = 1/conversion_price
                positiveHCF = 1/conversion_price
        else:
            # Allow calling get_price as placeholder for livetrading
            ask = data.Close[i]
            bid = data.Close[i]
            negativeHCF = 1
            positiveHCF = 1
        
        price = {"ask": ask,
                 "bid": bid,
                 "negativeHCF": negativeHCF,
                 "positiveHCF": positiveHCF}
        
        return price
    
    
    def _fill_order(self, order_id: int, candle: pd.core.series.Series, 
                       limit_price: float = None) -> None:
        """Fills an open order.
        """
        order = self.orders[order_id]
        
        # Calculate margin requirements
        current_price = candle.Open
        pip_value = self.utils.get_pip_ratio(order.instrument)
        size = self.orders[order_id].size
        HCF = self.orders[order_id].HCF
        position_value = abs(size) * current_price * HCF
        margin_required = self._calculate_margin(position_value)
        
        spread_cost = abs(size) * self.spread * pip_value
        spread_shift = 0.5 * np.sign(size) * self.spread * pip_value
        
        if margin_required < self.margin_available:
            # Fill order
            trade = Trade(order)
            
            # Trade id
            trade_id = self._get_new_trade_id()
            trade.id = trade_id
            trade.time_filled = candle.name
            
            if limit_price is None:
                trade.entry_price = candle.Open + spread_shift
            else:
                trade.entry_price = limit_price + spread_shift
            self.trades[trade_id] = trade
            
            # Subtract spread cost from account NAV
            self.NAV -= spread_cost
            
        else:
            # Cancel order
            cancel_reason = "Insufficient margin to fill order."
            self.cancel_order(order_id, cancel_reason)
    
    
    def _update_positions(self, candle: pd.core.series.Series, 
                          instrument: str) -> None:
        """Updates orders and open positions based on current candle.
        """
        # Open pending orders
        pending_orders = self.get_orders(instrument, 'pending')
        for order_id, order in pending_orders.items():
            if candle.name > order.order_time:
                order.status = 'open'
        
        # Update open orders
        for order_id, order in self.orders.items():
            # Filter orders by instrument type since candle is instrument specific
            if order.instrument == instrument and order.status == 'open':
                if order.order_type == 'market':
                    # Market order type - proceed to fill
                    self._fill_order(order_id, candle)
                
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
                    order.status = 'closed'
                elif order.order_type == 'reduce':
                    self._reduce_position(order)
                    order.status = 'closed'
                    
                # Check for limit orders
                if order.order_type == 'limit':
                    # Limit order type
                    if order.size > 0:
                        if candle.Low < order.order_limit_price:
                            self._fill_order(order_id, candle, 
                                             order.order_limit_price)
                    else:
                        if candle.High > order.order_limit_price:
                            self._fill_order(order_id, candle, 
                                             order.order_limit_price)
                
        # Update open trades
        unrealised_PL = 0 # Un-leveraged value
        for trade_id, trade in self.trades.items():
            if trade.instrument == instrument and trade.status == 'open':
                # Update stop losses
                if trade.stop_type == 'trailing':
                    # Trailing stop loss type, check if price has moved SL
                    if trade.stop_distance is not None:
                        pip_value = self.utils.get_pip_ratio(trade.instrument)
                        pip_distance = trade.stop_distance
                        distance = pip_distance*pip_value # price units
                    else:
                        distance = abs(trade.entry_price - \
                                       trade.stop_loss)
                        pip_value = self.utils.get_pip_ratio(trade.instrument)
                        trade.stop_distance = distance / pip_value
                        
                    if trade.size > 0:
                        # long position, stop loss only moves up
                        new_stop = candle.High - distance
                        if new_stop > trade.stop_loss:
                            self._update_stop_loss(trade_id, new_stop, 
                                                   new_stop_type='trailing')
                        
                    else:
                        # short position, stop loss only moves down
                        new_stop = candle.Low + distance
                        if new_stop < trade.stop_loss:
                            self._update_stop_loss(trade_id, new_stop, 
                                                   new_stop_type='trailing')
                
                # Update trades
                if trade.size > 0:
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
                        size        = trade.size
                        entry_price = trade.entry_price
                        price       = candle.Close
                        HCF         = trade.HCF
                        trade_PL    = size*(price - entry_price)*HCF
                        unrealised_PL += trade_PL
                        
                        # Update PL of trade
                        trade.last_price = price
                        trade.last_time = candle.name
                        trade.unrealised_PL = trade_PL
                
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
                        size        = trade.size
                        entry_price = trade.entry_price
                        price       = candle.Close
                        HCF         = trade.HCF
                        trade_PL    = size*(price - entry_price)*HCF
                        unrealised_PL += trade_PL
                        
                        # Update PL of trade
                        trade.last_price = price
                        trade.last_time = candle.name
                        trade.unrealised_PL = trade_PL
        
        # Update margin available
        self._update_margin()
        
        # Update unrealised P/L
        self.unrealised_PL = unrealised_PL
        
        # Update open position value
        self.NAV = self.portfolio_balance + self.unrealised_PL
    
    
    def _close_position(self, instrument: str, candle: pd.core.series.Series, 
                        exit_price: float, trade_id=None) -> None:
        """Closes position in instrument.
        """
        if trade_id:
            # single trade specified to close
            self._close_trade(trade_id=trade_id, exit_price=exit_price,
                              candle=candle)
        else:
            # Close all positions for instrument
            for trade_id, trade in self.trades.items():
                if trade.instrument == instrument and trade.status == 'open':
                    self._close_trade(trade_id=trade_id, exit_price=exit_price,
                                      candle=candle)
    
    
    def _close_trade(self, trade_id: int = None, exit_price: float = None,
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
        trade = self.trades[trade_id]
        entry_price = trade.entry_price
        size = trade.size
        HCF = trade.HCF
        
        # Account for missing inputs
        exit_price = trade.last_price if not exit_price else exit_price
        
        # Update portfolio with profit/loss
        gross_PL = size*(exit_price - entry_price)*HCF
        commission = self._calculate_commissions(trade_id, exit_price, size)
        net_profit = gross_PL - commission
        
        if net_profit > 0:
            self.profitable_trades += 1
        
        # Add trade to closed positions
        trade.profit = net_profit
        trade.balance = self.portfolio_balance
        trade.exit_price = exit_price
        trade.fees = commission
        if candle is None:
            trade.exit_time = trade.last_time
        else:
            trade.exit_time = candle.name 
        trade.status = 'closed'
        
        # Update account
        self._add_funds(net_profit)
        self._update_MDD()
    
    
    def _reduce_position(self, order: Order) -> None:
        """Reduces the position of the specified instrument by FIFO. 
        
        The size parameter of the order details is used to specify whether 
        to reduce long units, or to reduce short units. For example, the
        order details below will reduce long units of the position being 
        held.
            order_type: 'reduce' # reduction order
            size: -1 # reduce long units by selling
        """
        # Consired long vs. short units to be reduced
        instrument = order.instrument
        reduction_size = order.size
        reduction_direction = order.direction
        
        # Get open trades for instrument
        open_trades = self.get_trades(instrument)
        # open_trade_IDs = list(open_trades.keys())
        
        # Modify existing trades until there are no more units to reduce
        units_to_reduce = reduction_size
        while units_to_reduce > 0:
            for trade_id, trade in open_trades:
                if trade.direction != reduction_direction:
                    # Only reduce long trades when reduction direction is -1
                    # Only reduce short trades when reduction direction is 1
                    if units_to_reduce > trade.size:
                        # Entire trade must be closed
                        last_price = trade.last_price
                        self._close_trade(order_id=trade_id, exit_price=last_price)
                        
                        # Update units_to_reduce
                        units_to_reduce -= abs(trade.size)
                        
                    else:
                        # Partially close trade
                        self._partial_trade_close(trade_id, units_to_reduce)
                        
                        # Update units_to_reduce
                        units_to_reduce = 0
                    
    
    def _partial_trade_close(self, trade_id: int, units: float) -> None:
        """Partially closes a trade.
        
        The original trade ID remains, but the trade size may be reduced. The
        portion that gets closed is assigned a new ID.
        """
        trade = self.trades[trade_id]
        
        # Create new trade for reduced amount
        partial_trade = Trade._split(trade, units)
        partial_trade_id = self._get_new_trade_id()
        partial_trade.id = partial_trade_id
        self.trades[partial_trade_id] = partial_trade
        
        # Close partial trade
        self._close_trade(partial_trade_id)
        
    
    def _calculate_commissions(self, trade_id: int, exit_price: float, 
                               units: float = None) -> float:
        """Calculates trade commissions.
        """
        if self.commission_scheme == 'percentage':
            entry_price = self.trades[trade_id].entry_price
            size = self.trades[trade_id].size if units is None else units
            HCF = self.trades[trade_id].HCF
            
            open_trade_value = abs(size)*entry_price*HCF
            close_trade_value = abs(size)*exit_price*HCF
            commission  = (self.commission/100) * (open_trade_value + close_trade_value)
        
        elif self.commission_scheme == 'fixed':
            size = self.trades[trade_id].size if units is None else units
            commission = self.commission * size
            
        return commission
    
    
    def _add_funds(self, amount: float) -> None:
        """Adds funds to brokerage account.
        """
        self.portfolio_balance  += amount
    
    
    def _make_deposit(self, deposit: float) -> None:
        """Adds deposit to account balance and NAV.
        """
        if self.portfolio_balance == 0:
            # If this is the initial deposit, set peak and low values for MDD
            self.peak_value = deposit
            self.low_value = deposit
            
        self.portfolio_balance += deposit
        self.NAV += deposit
        self._update_margin()
    
    
    def _calculate_margin(self, position_value: float) -> float:
        """Calculates margin required to take a position.
        """
        margin = position_value / self.leverage
        return margin
    
    
    def _update_margin(self) -> None:
        """Updates margin available in account.
        """        
        margin_used = 0
        for trade_id, trade in self.trades.items():
            if trade.status == 'open':
                size = trade.size
                HCF = trade.HCF
                last_price = trade.last_price
                position_value = abs(size) * last_price * HCF
                margin_required = self._calculate_margin(position_value)
                margin_used += margin_required
                
                # Update margin required in trade dict
                trade.margin_required = margin_required
        
        self.margin_available = self.portfolio_balance - margin_used


    def _update_MDD(self) -> None:
        """Function to calculate maximum portfolio drawdown.
        """
        balance     = self.portfolio_balance
        peak_value  = self.peak_value
        low_value   = self.low_value
        
        if balance > peak_value:
            self.peak_value = balance
            self.low_value = balance
            
        elif balance < low_value:
            self.low_value = balance
        
        MDD = 100*(low_value - peak_value)/peak_value
        
        if MDD < self.max_drawdown:
            self.max_drawdown = MDD
    
    
    def _modify_order(self, order: Order) -> None:
        """Modify order with updated parameters. Called when order_type = 'modify', 
        modifies trade specified by related_orders key.
        """
        # Get ID of trade to modify
        modify_trade_id = order.related_orders
        
        if order.stop_loss is not None:
            # New stop loss provided
            self._update_stop_loss(modify_trade_id, order.stop_loss, 
                                   order.stop_type)
            
        if order.take_profit is not None:
            self._update_take_profit(modify_trade_id, order.take_profit)
        
        
    def _update_stop_loss(self, trade_id: int, new_stop_loss: float, 
                          new_stop_type: str = 'limit') -> None:
        """Updates stop loss on open trade.
        """
        self.trades[trade_id].stop_loss = new_stop_loss
        self.trades[trade_id].stop_type = new_stop_type
    
    
    def _update_take_profit(self, trade_id: int, new_take_profit: float) -> None:
        """Updates take profit on open trade.
        """
        self.trades[trade_id].take_profit = new_take_profit
        
    
        
    def _get_new_order_id(self):
        return len(self.orders) + 1
    
    
    def _get_new_trade_id(self):
        return len(self.trades) + 1
    
    
    def _margin_call(self):
        # TODO - implement margin calls
        pass