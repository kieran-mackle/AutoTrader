#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Virtual broker.

TODO: 
    - add flag to signal long positions only allowed (eg. no CFD)
"""

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
        self.pending_positions  = {}
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
    
    
    def place_order(self, order_details):
        '''
            Place order with broker.
        '''
        instrument  = order_details["instrument"]
        size        = order_details["size"]
        order_price = order_details["order_price"]
        stop_loss  = order_details["stop_loss"]
        stop_distance = order_details['stop_distance']
        
        if stop_loss is None and stop_distance is not None:
            pip_value   = self.utils.get_pip_ratio(instrument)
            stop_loss  = order_price - np.sign(size)*stop_distance*pip_value
        
        order_no = self.total_trades + 1
        
        # Create new_position and add position to self.pending_positions
        new_position = order_details.copy()
        new_position['order_ID'] = order_no
        
        self.pending_positions[order_no] = new_position
        
        # Update trade tally
        self.total_trades += 1
    
    
    def open_position(self, order_no, candle, limit_price = None):
        ''' Opens position with broker. '''
        
        # Calculate margin requirements
        current_price   = candle.Open
        pip_value       = self.utils.get_pip_ratio(self.pending_positions[order_no]['instrument'])
        size            = self.pending_positions[order_no]['size']
        HCF             = self.pending_positions[order_no]['HCF']
        position_value  = abs(size) * current_price * HCF
        margin_required = self.calculate_margin(position_value)
        
        if size > 0:
            spread_cost = 0.5*self.spread * pip_value
        else:
            spread_cost = -0.5*self.spread * pip_value
        
        if margin_required < self.margin_available:
            # Fill order
            new_position = self.pending_positions[order_no]
            new_position['time_filled'] = candle.name
            if limit_price is None:
                new_position['entry_price'] = candle.Open + spread_cost
            else:
                new_position['entry_price'] = limit_price + spread_cost
            self.open_positions[order_no] = new_position
            
        else:
            self.cancelled_orders[order_no] = self.pending_positions[order_no]
    
    
    def update_positions(self, candle, instrument):
        ''' 
            Updates orders and open positions based on current candle. 
        '''

        # Tally for positions opened this update
        opened_positions = 0
        
        # Update pending positions
        closing_orders = []
        for order_no in self.pending_positions:
            # Filter orders by instrument type since candle is instrument specific            
            if self.pending_positions[order_no]['instrument'] == instrument:
                if self.pending_positions[order_no]['order_time'] != candle.name:
                    if self.pending_positions[order_no]['order_type'] == 'market':
                        # Market order type
                        self.open_position(order_no, candle)
                        opened_positions += 1
                    
                    elif self.pending_positions[order_no]['order_type'] == 'stop-limit':
                        # Stop-limit order type
                        # Check if order_stop_price has been reached yet
                        
                        if candle.Low < self.pending_positions[order_no]['order_stop_price'] < candle.High:
                            # order_stop_price has been reached, change order type to 'limit'
                            self.pending_positions[order_no]['order_type'] = 'limit'
                        
                    # This is in a separate if statement, as stop-limit order may
                    # eventually be changed to limit orders
                    if self.pending_positions[order_no]['order_type'] == 'limit':
                        # Limit order type
                        if self.pending_positions[order_no]['size'] > 0:
                            if candle.Low < self.pending_positions[order_no]['order_limit_price']:
                                self.open_position(order_no, candle, 
                                                   self.pending_positions[order_no]['order_limit_price'])
                                opened_positions += 1
                        else:
                            if candle.High > self.pending_positions[order_no]['order_limit_price']:
                                self.open_position(order_no, candle, 
                                                   self.pending_positions[order_no]['order_limit_price'])
                                opened_positions += 1
                                
                                
                if self.pending_positions[order_no]['order_type'] == 'close':
                    related_order = self.pending_positions[order_no]['related_orders']
                    self.close_position(self.pending_positions[order_no]['instrument'],
                                        candle, 
                                        candle.Close,
                                        order_no = related_order
                                        )
                    opened_positions += 1 # To remove from pending orders
                    closing_orders.append(order_no)
        
                
        # Remove position from pending positions
        if opened_positions > 0:
            # For orders that were opened
            for order_no in self.open_positions.keys():
                self.pending_positions.pop(order_no, 0)
            
            # For orders that were cancelled
            for order_no in self.cancelled_orders.keys():
                self.pending_positions.pop(order_no, 0)
            
            # For close orders
            for order_no in closing_orders:
                self.pending_positions.pop(order_no, 0)
        
        
        # Update trailing stops
        # For other methods, move the stop update to an external function
        # Can this be moved into the loop below?
        for order_no in self.open_positions:
            if self.open_positions[order_no]['instrument'] == instrument:
                if self.open_positions[order_no]['stop_type'] == 'trailing_stop':
                    # Trailing stop loss is enabled, check if price has moved SL
                    
                    if self.open_positions[order_no]['stop_distance'] is not None:
                        pip_value = self.utils.get_pip_ratio(self.open_positions[order_no]['instrument'])
                        pip_distance = self.open_positions[order_no]['stop_distance']
                        distance = pip_distance*pip_value
                        
                    else:
                        distance = abs(self.open_positions[order_no]['entry_price'] - \
                                       self.open_positions[order_no]['stop_loss'])
                    
    
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
                        position_value = size*(price - entry_price)*HCF
                        unrealised_PL += position_value
                
                else:
                    if self.open_positions[order_no]['stop_loss'] is not None and \
                        candle.High > self.open_positions[order_no]['stop_loss']:
                        self.close_position(self.open_positions[order_no]['instrument'], 
                                            candle, 
                                            self.open_positions[order_no]['stop_loss'],
                                            order_no)
                    elif self.open_positions[order_no]['take_profit'] is not None and \
                        candle.Low < self.open_positions[order_no]['take_profit']:
                        self.close_position(self.open_positions[order_no]['instrument'], 
                                            candle, 
                                            self.open_positions[order_no]['take_profit'],
                                            order_no)
                    else:
                        size        = self.open_positions[order_no]['size']
                        entry_price = self.open_positions[order_no]['entry_price']
                        price       = candle.Close
                        HCF         = self.open_positions[order_no]['HCF']
                        position_value = size*(price - entry_price)*HCF
                        unrealised_PL += position_value
        
        # Update margin available
        self.update_margin(candle.Close)
        
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
        closed_position['exit_time'] = candle.name
        
        # Add to closed positions dictionary
        self.closed_positions[order_no] = closed_position
        
        # Remove position from open positions
        self.open_positions.pop(order_no, 0)
        
        # Update maximum drawdown
        self.update_MDD()
        
    
    def get_pending_orders(self, instrument = None):
        ''' Returns pending orders. '''
        
        pending_orders = {}
        
        if instrument is not None:
            for order_no in self.pending_positions:
                if self.pending_positions[order_no]['instrument'] == instrument:
                    pending_orders[order_no] = self.pending_positions[order_no]
        else:
            pending_orders = self.pending_positions.copy()
        
        return pending_orders
    
    def cancel_pending_order(self, order_id):
        self.pending_positions.pop(order_id, 0)
    
    def get_open_positions(self, instrument=None):
        ''' Returns the open positions in the account. '''
        
        open_positions = {}
        
        if instrument is not None:
            for order_no in self.open_positions:
                if self.open_positions[order_no]['instrument'] == instrument:
                    open_positions[order_no] = self.open_positions[order_no]
        else:
            open_positions = self.open_positions.copy()
        
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
        
        if self.portfolio_balance == 0:
            # If this is the initial deposit, set peak and low values for MDD
            self.peak_value = amount
            self.low_value = amount
            
        self.portfolio_balance  += amount
        # self.margin_available   += amount
    
    
    def get_balance(self):
        ''' Returns balance of account. '''
        return self.portfolio_balance
    
    
    def calculate_margin(self, position_value):
        ''' Calculates margin required to take a position. '''
        margin = position_value / self.leverage
        
        return margin
    
    
    def update_margin(self, close_price):
        ''' Updates margin available in account. '''
        
        margin_used = 0
        for order_no in self.open_positions:
            size            = self.open_positions[order_no]['size']
            HCF             = self.open_positions[order_no]['HCF']
            # HCF should be updated for current time.
            position_value  = abs(size) * close_price * HCF
            margin_required = self.calculate_margin(position_value)
            margin_used     += margin_required
        
        self.margin_available = self.portfolio_balance - margin_used


    def get_price(self, instrument, data, conversion_data, i):
        ''' Returns the price data dict. '''
        
        ask = data.Close[i]
        bid = data.Close[i]
        conversion_data = conversion_data.Close[i]
        
        if bid == conversion_data:
            negativeHCF = 1
            positiveHCF = 1
        else:
            negativeHCF = 1/conversion_data
            positiveHCF = 1/conversion_data
        
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
        return self.NAV
