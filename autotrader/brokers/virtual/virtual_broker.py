#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Module: brokers.virtual.virtual_broker
Purpose: AutoTrader virtual broker for backtesting
Author: Kieran Mackle

TODO: 
    - rename variables to clarify (eg. open_positions -> open_trades, etc)
    
Known bug:
    - when closing multiple trades in a single candle, NAV will drop 
      with balance.
'''

import numpy as np

class Broker():
    """
    Virtual broker to simulate trading environment.


    Attributes
    ----------
    broker_config : dict
        the broker configuration dictionary
    
    leverage : int
        the leverage on the account (default 1)
    
    commission : int
        the brokers commission as a percentage (default 0)
        
    spread : int
        the bid/ask spread (default 0)
    
    utils : class
        the broker utilities class
    
    home_curreny : str
        the home currency of the account (used for retrieving quote data)


    Methods
    -------
    place_order(order_details):
        Places an order with the virtual broker.
    
    open_position(order_no, candle, limit_price = None):
        Opens an order to enter the market as a trade. 
    
    update_positions(candle):
        Updates orders and open positions based on current candle. 

    
    
    """
    
    def __init__(self, broker_config, utils):
        self.leverage           = 1
        self.commission         = 0
        self.spread             = 0
        self.margin_available   = 0
        self.portfolio_balance  = 0
        self.pending_orders  = {}
        self.open_positions     = {}
        self.closed_positions   = {}
        self.cancelled_orders   = {}
        self.total_trades       = 0
        self.profitable_trades  = 0
        self.peak_value         = 0
        self.low_value          = 0
        self.max_drawdown       = 0
        self.home_currency      = 'AUD'
        self.NAV                = 0
        self.unrealised_PL      = 0
        self.utils              = utils
        self.verbosity          = broker_config['verbosity']
        

    def place_order(self, order_details):
        '''
            Place order with broker.
        '''
        instrument  = order_details["instrument"]
        size        = order_details["size"]
        order_price = order_details["order_price"]
        stop_loss  = order_details["stop_loss"]
        stop_distance = order_details["stop_distance"]
        take_profit = order_details["take_profit"]
        
        if stop_loss is None and stop_distance is not None:
            pip_value   = self.utils.get_pip_ratio(instrument)
            stop_loss  = order_price - np.sign(size)*stop_distance*pip_value
        
        order_no = self.total_trades + 1
        new_position = order_details.copy()
        new_position['order_ID'] = order_no
        
        # Verify SL and TP prices
        invalid_order = False
        if stop_loss is not None and np.sign(size)*(order_price - stop_loss) < 0:
            direction = 'long' if np.sign(size) > 0 else 'short'
            SL_placement = 'below' if np.sign(size) > 0 else 'above'
            if self.verbosity > 0:
                print("Invalid stop loss request: stop loss must be "+ \
                                f"{SL_placement} the order price for a {direction}" + \
                                " trade order.\n"+ \
                                f"Order Price: {order_price}\nStop Loss: {stop_loss}")
            invalid_order = True
        
        if take_profit is not None and np.sign(size)*(order_price - take_profit) > 0:
            direction = 'long' if np.sign(size) > 0 else 'short'
            TP_placement = 'above' if np.sign(size) > 0 else 'below'
            if self.verbosity > 0:
                print("Invalid take profit request: take profit must be "+ \
                                f"{TP_placement} the order price for a {direction}" + \
                                " trade order.\n"+ \
                                f"Order Price: {order_price}\nTake Profit: {take_profit}")
            invalid_order = True
        
        if invalid_order:
            if self.verbosity > 0:
                print(f"  Order {order_no} rejected.\n")
            # Add position to self.pending_orders
            self.cancelled_orders[order_no] = new_position
            self.cancelled_orders[order_no]['reason'] = "Invalid order request"
            
        else:
            # Add position to self.pending_orders
            self.pending_orders[order_no] = new_position
            
        # Update trade tally
        self.total_trades += 1
    
    
    def open_position(self, order_no, candle, limit_price = None):
        ''' Opens position with broker. '''
        
        # Calculate margin requirements
        current_price   = candle.Open
        pip_value       = self.utils.get_pip_ratio(self.pending_orders[order_no]['instrument'])
        size            = self.pending_orders[order_no]['size']
        HCF             = self.pending_orders[order_no]['HCF']
        position_value  = abs(size) * current_price * HCF
        margin_required = self.calculate_margin(position_value)
        
        spread_cost = abs(size) * self.spread * pip_value
        spread_shift = 0.5 * np.sign(size) * self.spread * pip_value
        
        if margin_required < self.margin_available:
            # Fill order
            new_position = self.pending_orders[order_no]
            new_position['time_filled'] = candle.name
            if limit_price is None:
                new_position['entry_price'] = candle.Open + spread_shift
            else:
                new_position['entry_price'] = limit_price + spread_shift
            self.open_positions[order_no] = new_position
            
            # Subtract spread cost
            self.NAV -= spread_cost
            
        else:
            # Cancel order
            cancel_reason = "Insufficient margin"
            self.cancel_pending_order(order_no, cancel_reason)
    
    def update_positions(self, candle, instrument):
        ''' 
            Updates orders and open positions based on current candle. 
        '''

        # Tally for positions opened this update
        opened_positions = 0
        
        # Update pending positions
        closing_orders = []
        for order_no in self.pending_orders:
            # Filter orders by instrument type since candle is instrument specific            
            if self.pending_orders[order_no]['instrument'] == instrument:
                if self.pending_orders[order_no]['order_time'] != candle.name:
                    if self.pending_orders[order_no]['order_type'] == 'market':
                        # Market order type
                        self.open_position(order_no, candle)
                        opened_positions += 1
                    
                    elif self.pending_orders[order_no]['order_type'] == 'stop-limit':
                        # Stop-limit order type
                        # Check if order_stop_price has been reached yet
                        
                        if candle.Low < self.pending_orders[order_no]['order_stop_price'] < candle.High:
                            # order_stop_price has been reached, change order type to 'limit'
                            self.pending_orders[order_no]['order_type'] = 'limit'
                        
                    # This is in a separate if statement, as stop-limit order may
                    # eventually be changed to limit orders
                    if self.pending_orders[order_no]['order_type'] == 'limit':
                        # Limit order type
                        if self.pending_orders[order_no]['size'] > 0:
                            if candle.Low < self.pending_orders[order_no]['order_limit_price']:
                                self.open_position(order_no, candle, 
                                                   self.pending_orders[order_no]['order_limit_price'])
                                opened_positions += 1
                        else:
                            if candle.High > self.pending_orders[order_no]['order_limit_price']:
                                self.open_position(order_no, candle, 
                                                   self.pending_orders[order_no]['order_limit_price'])
                                opened_positions += 1
                                
                                
                if self.pending_orders[order_no]['order_type'] == 'close':
                    related_order = self.pending_orders[order_no]['related_orders']
                    self.close_position(self.pending_orders[order_no]['instrument'],
                                        candle, 
                                        candle.Close,
                                        order_no = related_order
                                        )
                    opened_positions += 1 # To remove from pending orders
                    closing_orders.append(order_no)
                elif self.pending_orders[order_no]['order_type'] == 'reduce':
                    self.reduce_position(self.pending_orders[order_no])
        
                
        # Remove position from pending positions
        if opened_positions > 0:
            # For orders that were opened
            for order_no in self.open_positions.keys():
                self.pending_orders.pop(order_no, 0)
            
            # For orders that were cancelled
            for order_no in self.cancelled_orders.keys():
                self.pending_orders.pop(order_no, 0)
            
            # For close orders
            for order_no in closing_orders:
                self.pending_orders.pop(order_no, 0)
        
        
        # Update trailing stops
        # For other methods, move the stop update to an external function
        # Can this be moved into the loop below?
        for order_no in self.open_positions:
            if self.open_positions[order_no]['instrument'] == instrument:
                if self.open_positions[order_no]['stop_type'] == 'trailing':
                    # Trailing stop loss is enabled, check if price has moved SL
                    
                    if self.open_positions[order_no]['stop_distance'] is not None:
                        # Stop distance provided 
                        pip_value = self.utils.get_pip_ratio(self.open_positions[order_no]['instrument'])
                        pip_distance = self.open_positions[order_no]['stop_distance']
                        distance = pip_distance*pip_value
                        
                    else:
                        # Stop loss price provided
                        distance = abs(self.open_positions[order_no]['entry_price'] - \
                                       self.open_positions[order_no]['stop_loss'])
                        
                        # Append stop distance to dict
                        pip_value = self.utils.get_pip_ratio(self.open_positions[order_no]['instrument'])
                        self.open_positions[order_no]['stop_distance'] = distance / pip_value
                        
    
                    if self.open_positions[order_no]['size'] > 0:
                        # long position, stop loss only moves up
                        new_stop = candle.High - distance
                        if new_stop > self.open_positions[order_no]['stop_loss']:
                            self.open_positions[order_no]['stop_loss'] = new_stop
                        
                    else:
                        # short position, stop loss only moves down
                        new_stop = candle.Low + distance
                        if new_stop < self.open_positions[order_no]['stop_loss']:
                            self.open_positions[order_no]['stop_loss'] = new_stop
        
        # Update self.open_positions
        open_position_orders = list(self.open_positions.keys())
        unrealised_PL  = 0        # Un-leveraged value
        for order_no in open_position_orders:
            if self.open_positions[order_no]['instrument'] == instrument:
                if self.open_positions[order_no]['size'] > 0:
                    # Long trade
                    if self.open_positions[order_no]['stop_loss'] is not None and \
                        candle.Low < self.open_positions[order_no]['stop_loss']:
                        # Stop loss hit
                        self.close_position(self.open_positions[order_no]['instrument'], 
                                            candle, 
                                            self.open_positions[order_no]['stop_loss'],
                                            order_no)
                    elif self.open_positions[order_no]['take_profit'] is not None and \
                        candle.High > self.open_positions[order_no]['take_profit']:
                        # Take Profit hit
                        self.close_position(self.open_positions[order_no]['instrument'], 
                                            candle, 
                                            self.open_positions[order_no]['take_profit'],
                                            order_no)
                    else:
                        # Position is still open, update value of holding
                        size        = self.open_positions[order_no]['size']
                        entry_price = self.open_positions[order_no]['entry_price']
                        price       = candle.Close
                        HCF         = self.open_positions[order_no]['HCF']
                        trade_PL    = size*(price - entry_price)*HCF
                        unrealised_PL += trade_PL
                        
                        # Update PL of trade
                        self.open_positions[order_no]['last_price'] = price
                        self.open_positions[order_no]['last_time'] = candle.name
                        self.open_positions[order_no]['unrealised_PL'] = trade_PL
                
                else:
                    # Short trade
                    if self.open_positions[order_no]['stop_loss'] is not None and \
                        candle.High > self.open_positions[order_no]['stop_loss']:
                        # Stop loss hit
                        self.close_position(self.open_positions[order_no]['instrument'], 
                                            candle, 
                                            self.open_positions[order_no]['stop_loss'],
                                            order_no)
                    elif self.open_positions[order_no]['take_profit'] is not None and \
                        candle.Low < self.open_positions[order_no]['take_profit']:
                        # Take Profit hit
                        self.close_position(self.open_positions[order_no]['instrument'], 
                                            candle, 
                                            self.open_positions[order_no]['take_profit'],
                                            order_no)
                    else:
                        # Position is still open, update value of holding
                        size        = self.open_positions[order_no]['size']
                        entry_price = self.open_positions[order_no]['entry_price']
                        price       = candle.Close
                        HCF         = self.open_positions[order_no]['HCF']
                        trade_PL    = size*(price - entry_price)*HCF
                        unrealised_PL += trade_PL
                        
                        # Update PL of trade
                        self.open_positions[order_no]['last_price'] = price
                        self.open_positions[order_no]['last_time'] = candle.name
                        self.open_positions[order_no]['unrealised_PL'] = trade_PL
        
        # Update margin available
        self.update_margin()
        
        # Update unrealised P/L
        self.unrealised_PL = unrealised_PL
        
        # Update open position value
        self.NAV = self.portfolio_balance + self.unrealised_PL
    
    
    def close_position(self, instrument, candle, exit_price,
                           order_no=None):
        ''' Closes position. '''
        if order_no is not None:
            # single order specified to close
            self.close_trade(order_no=order_no, 
                             candle=candle, 
                             exit_price=exit_price)
        else:
            # Close all positions for instrument
            for order_no in self.open_positions.copy():
                if self.open_positions[order_no]['instrument'] == instrument:
                    self.close_trade(order_no=order_no, 
                                     candle=candle, 
                                     exit_price=exit_price)
    
    
    def close_trade(self, candle=None, exit_price=None,
                           order_no=None):
        ''' Closes trade by order number. '''
        entry_price = self.open_positions[order_no]['entry_price']
        size        = self.open_positions[order_no]['size']
        HCF         = self.open_positions[order_no]['HCF']
        
        # Update portfolio with profit/loss
        gross_PL    = size*(exit_price - entry_price)*HCF
        open_trade_value    = abs(size)*entry_price*HCF
        close_trade_value   = abs(size)*exit_price*HCF
        commission  = (self.commission/100) * (open_trade_value + close_trade_value)
        net_profit  = gross_PL - commission
        
        self.add_funds(net_profit)
        if net_profit > 0:
            self.profitable_trades += 1
        
        # Add trade to closed positions
        closed_position = self.open_positions[order_no].copy()
        closed_position['profit'] = net_profit
        closed_position['balance'] = self.portfolio_balance
        closed_position['exit_price'] = exit_price
        if candle is None:
            closed_position['exit_time'] = self.open_positions[order_no]['last_time']
        else:
            closed_position['exit_time'] = candle.name 
        
        # Add to closed positions dictionary
        self.closed_positions[order_no] = closed_position
        
        # Remove position from open positions
        self.open_positions.pop(order_no, 0)
        
        # Update maximum drawdown
        self.update_MDD()
    
    def reduce_position(self, order_details):
        ''' 
        Reduces the position of the specified instrument by FIFO. 
        
        The size parameter of the order details is used to specify whether 
        to reduce long units, or to reduce short units. For example, the
        order details below will reduce long units of the position being 
        held.
            order_type: 'reduce' # reduction order
            size: -1 # reduce long units by selling
        '''
        
        # Consired long vs. short units to be reduced
        instrument = order_details['instrument']
        reduction_size = order_details['size']
        reduction_direction = order_details['direction']
        
        # Get open trades for instrument
        open_trades = self.get_open_trades(instrument)
        open_trade_IDs = list(open_trades.keys())
        
        # Modify existing trades until there are no more units to reduce
        units_to_reduce = reduction_size
        while units_to_reduce > 0:
            for order_no in open_trade_IDs:
                if open_trades[order_no]['direction'] != reduction_direction:
                    # Only reduce long trades when reduction direction is -1
                    # Only reduce short trades when reduction direction is 1
                    if units_to_reduce > open_trades[order_no]['size']:
                        # Entire trade must be closed
                        last_price = open_trades[order_no]['last_price']
                        self.close_trade(order_no = order_no, exit_price=last_price)
                        
                        # Update units_to_reduce
                        units_to_reduce -= abs(self.closed_positions[order_no]['size'])
                        
                    else:
                        # Partially close trade
                        self.partial_trade_close(order_no, units_to_reduce)
                        
                        # Update units_to_reduce
                        units_to_reduce = 0
                    
    
    def partial_trade_close(self, trade_ID, units):
        ''' Partially closes a trade. '''
        entry_price = self.open_positions[trade_ID]['entry_price']
        size        = self.open_positions[trade_ID]['size']
        HCF         = self.open_positions[trade_ID]['HCF']
        last_price  = self.open_positions[trade_ID]['last_price']
        remaining_size = size-units
        
        # Update portfolio with profit/loss
        gross_PL    = units*(last_price - entry_price)*HCF
        open_trade_value    = abs(units)*entry_price*HCF
        close_trade_value   = abs(units)*last_price*HCF
        commission  = (self.commission/100) * (open_trade_value + close_trade_value)
        net_profit  = gross_PL - commission
        
        self.add_funds(net_profit)
        
        if net_profit > 0:
            self.profitable_trades += 1
        
        # Add trade to closed positions
        closed_position = self.open_positions[trade_ID].copy()
        closed_position['size'] = units
        closed_position['profit'] = net_profit
        closed_position['balance'] = self.portfolio_balance
        closed_position['exit_price'] = last_price
        closed_position['exit_time'] = self.open_positions[trade_ID]['last_time']
        
        # Add to closed positions dictionary
        partial_trade_close_ID = self.total_trades + 1
        self.closed_positions[partial_trade_close_ID] = closed_position
        self.total_trades += 1
        
        # Modify remaining portion of trade
        self.open_positions[trade_ID]['size'] = remaining_size
        
        # Update maximum drawdown
        self.update_MDD()
        
    
    def get_pending_orders(self, instrument = None):
        ''' Returns pending orders. '''
        
        pending_orders = {}
        
        if instrument is not None:
            for order_no in self.pending_orders:
                if self.pending_orders[order_no]['instrument'] == instrument:
                    pending_orders[order_no] = self.pending_orders[order_no]
        else:
            pending_orders = self.pending_orders.copy()
        
        return pending_orders
    
    def cancel_pending_order(self, order_id, reason):
        ''' Moves an order from pending_orders into cancelled_orders. '''
        
        self.cancelled_orders[order_id] = self.pending_orders[order_id]
        self.cancelled_orders[order_id]['reason'] = reason
    
    def get_open_trades(self, instruments=None):
        ''' Returns open trades for the specified instrument. '''
        
        # Check data type of input
        if instruments is not None:
            # Non-None input provided, check type
            if type(instruments) is str:
                # Single instrument provided, put into list
                instruments = [instruments]
                
        open_trades = {}
        
        if instruments is not None:
            # Specific instruments requested
            for order_no in self.open_positions:
                if self.open_positions[order_no]['instrument'] in instruments:
                    open_trades[order_no] = self.open_positions[order_no]
        else:
            # Return all currently open positions
            open_trades = self.open_positions.copy()
        
        return open_trades
    
    def get_open_positions(self, instruments=None):
        ''' Returns the open positions in the account. '''
        
        if instruments is None:
            # No specific instrument requested, get all open
            instruments = []
            for order_no in self.open_positions: 
                instruments.append(self.open_positions[order_no]['instrument'])
        else:
            # Non-None input provided, check type
            if type(instruments) is str:
                # Single instrument provided, put into list
                instruments = [instruments]
        
        open_positions = {}
        for instrument in instruments:
            # First get open trades
            open_trades = self.get_open_trades(instrument)
            
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
                
                for order_no in open_trades:
                    trade_IDs.append(order_no)
                    total_margin += open_trades[order_no]['margin_required']
                    if open_trades[order_no]['size'] > 0:
                        # Long trade
                        long_units += open_trades[order_no]['size']
                        long_PL += open_trades[order_no]['unrealised_PL']
                        long_margin += open_trades[order_no]['margin_required']
                    else:
                        # Short trade
                        short_units += open_trades[order_no]['size']
                        short_PL += open_trades[order_no]['unrealised_PL']
                        short_margin += open_trades[order_no]['margin_required']
            
                # Construct instrument position dict
                instrument_position = {'long_units': long_units,
                                        'long_PL': long_PL,
                                        'long_margin': long_margin,
                                        'short_units': short_units,
                                        'short_PL': short_PL,
                                        'short_margin': short_margin,
                                        'total_margin': total_margin,
                                        'trade_IDs': trade_IDs}
                
                # Append position dict to open_positions dict
                open_positions[instrument] = instrument_position
                        
        return open_positions
    
    def get_cancelled_orders(self, instrument = None):
        ''' Returns cancelled orders. '''
        
        cancelled_orders = {}
        
        if instrument is not None:
            for order_no in self.cancelled_orders:
                if self.cancelled_orders[order_no]['instrument'] == instrument:
                    cancelled_orders[order_no] = self.cancelled_orders[order_no]
        else:
            cancelled_orders = self.cancelled_orders.copy()
        
        return cancelled_orders
    
    
    def add_funds(self, amount):
        ''' Add's funds to brokerage account. '''
        
        self.portfolio_balance  += amount
    
    def make_deposit(self, deposit):
        '''
        Adds deposit to account balance and NAV.
        '''
        
        if self.portfolio_balance == 0:
            # If this is the initial deposit, set peak and low values for MDD
            self.peak_value = deposit
            self.low_value = deposit
            
        self.portfolio_balance += deposit
        self.NAV += deposit
        self.update_margin()
    
    def get_balance(self):
        ''' Returns balance of account. '''
        return self.portfolio_balance
    
    
    def calculate_margin(self, position_value):
        ''' Calculates margin required to take a position. '''
        margin = position_value / self.leverage
        
        return margin
    
    
    def update_margin(self):
        ''' Updates margin available in account. '''
        
        margin_used = 0
        for order_no in self.open_positions:
            size            = self.open_positions[order_no]['size']
            HCF             = self.open_positions[order_no]['HCF']
            last_price      = self.open_positions[order_no]['last_price']
            # TODO - HCF should be updated for current time.
            position_value  = abs(size) * last_price * HCF
            margin_required = self.calculate_margin(position_value)
            margin_used     += margin_required
            
            # Update margin required in trade dict
            self.open_positions[order_no]['margin_required'] = margin_required
        
        self.margin_available = self.portfolio_balance - margin_used


    def get_price(self, instrument, data=None, conversion_data=None, i=None):
        ''' Returns the price data dict. '''
        
        if data is not None and conversion_data is not None and i is not None:
            ask = data.Close[i]
            bid = data.Close[i]
            conversion_data = conversion_data.Close[i]
            
            if bid == conversion_data:
                negativeHCF = 1
                positiveHCF = 1
            else:
                negativeHCF = 1/conversion_data
                positiveHCF = 1/conversion_data
        else:
            # Allow calling get_price as placeholder for livetrading
            ask = data.Close[i]
            bid = data.Close[i]
            negativeHCF = 1
            positiveHCF = 1
        
        price = {"ask": ask,
                 "bid": bid,
                 "negativeHCF": negativeHCF,
                 "positiveHCF": positiveHCF
                 }
        
        return price
    
    def update_MDD(self):
        ''' Function to calculate maximum portfolio drawdown '''
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
    
    def get_NAV(self):
        ''' Returns Net Asset Value of account. '''
        return self.NAV
    
    def get_margin_available(self):
        ''' Returns the margin available on the account. '''
        return self.margin_available
    
    def modify_order(self):
        ''' Modify order with updated parameters. '''
        # Placeholder method
        # can be used to update stop loss orders, to allow custom function SL