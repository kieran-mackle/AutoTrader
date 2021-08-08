#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Virtual broker.

TODO: 
    - add flag to signal long positions only allowed (eg. no CFD)
    
"""

from autotrader.brokers.virtual import utils

class Broker():
    
    def __init__(self, broker_config):
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
    
    
    def place_order(self, order_details):
        ''' 
            Place order with broker.
            
        '''
        order_type  = order_details["order_type"]
        pair        = order_details["instrument"]
        size        = order_details["size"]
        order_price = order_details["price"]
        time        = order_details["order_time"]
        take_price  = order_details["take_profit"]
        HCF         = order_details["HCF"]
        stop_type   = order_details["stop_type"]
        related     = order_details["related_orders"]
        
        if 'stop_distance' not in order_details:
            stop_distance   = None
            stop_price      = order_details["stop_loss"]
        else:
            stop_distance   = order_details['stop_distance']
            stop_price      = None
        
        order_no = self.total_trades + 1
        
        # Add position to self.pending_positions
        new_position = {'order_ID'  : order_no,
                        'type'      : order_type,
                        'pair'      : pair,
                        'order_time': time,
                        'order_price': order_price,
                        'stop'      : stop_price,
                        'take'      : take_price,
                        'size'      : size,
                        'HCF'       : HCF,
                        'distance'  : stop_distance,
                        'stop_type' : stop_type,
                        'related'   : related
                        }
        self.pending_positions[order_no] = new_position
        
        # Update trade tally
        self.total_trades += 1
    
    
    def open_position(self, order_no, candle):
        ''' Opens position with broker. '''
        
        # Calculate margin requirements
        current_price   = candle.Open
        pip_value       = utils.get_pip_ratio(self.pending_positions[order_no]['pair'])
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
            new_position['time_filled']     = candle.name
            new_position['entry_price']     = candle.Open + spread_cost
            self.open_positions[order_no]   = new_position
            
        else:
            self.cancelled_orders[order_no] = self.pending_positions[order_no]
    
    
    def update_positions(self, candle):
        ''' 
            Updates orders and open positions based on current candle. 
        '''
        # Tally for positions opened this update
        opened_positions = 0
        
        # Update pending positions
        closing_orders = []
        for order_no in self.pending_positions:
            if self.pending_positions[order_no]['order_time'] != candle.name:
                if self.pending_positions[order_no]['type'] == 'market':
                    self.open_position(order_no, candle)
                    opened_positions += 1
                elif self.pending_positions[order_no]['type'] == 'limit':
                    if self.open_positions[order_no]['size'] > 0:
                        if candle.Low < self.open_positions[order_no]['order_price']:
                            self.open_position(order_no, candle)
                            opened_positions += 1
                    else:
                        if candle.High > self.open_positions[order_no]['order_price']:
                            self.open_position(order_no, candle)
                            opened_positions += 1
                            
            if self.pending_positions[order_no]['type'] == 'close':
                related_order = self.pending_positions[order_no]['related']
                self.close_position(related_order, 
                                    candle, 
                                    candle.Close
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
            if self.open_positions[order_no]['stop_type'] == 'trailing_stop':
                # Trailing stop loss is enabled, check if price has moved SL
                
                if self.open_positions[order_no]['distance'] is not None:
                    pip_value = utils.get_pip_ratio(self.open_positions[order_no]['pair'])
                    pip_distance = self.open_positions[order_no]['distance']
                    distance = pip_distance*pip_value
                    
                else:
                    distance = abs(self.open_positions[order_no]['entry_price'] - \
                                   self.open_positions[order_no]['stop'])
                

                if self.open_positions[order_no]['size'] > 0:
                    # long position, stop loss only moves up
                    new_stop = candle.High - distance
                    if new_stop > self.open_positions[order_no]['stop']:
                        self.open_positions[order_no]['stop'] = new_stop
                    
                else:
                    # short position, stop loss only moves down
                    new_stop = candle.Low + distance
                    if new_stop < self.open_positions[order_no]['stop']:
                        self.open_positions[order_no]['stop'] = new_stop

        
        # Update self.open_positions
        open_position_orders = list(self.open_positions.keys())
        unrealised_PL  = 0        # Un-leveraged value
        for order_no in open_position_orders:
            if self.open_positions[order_no]['size'] > 0:
                if candle.Low < self.open_positions[order_no]['stop']:
                    # Stop loss hit
                    self.close_position(order_no, 
                                        candle, 
                                        self.open_positions[order_no]['stop']
                                        )
                elif candle.High > self.open_positions[order_no]['take']:
                    # Take Profit hit
                    self.close_position(order_no, 
                                        candle, 
                                        self.open_positions[order_no]['take']
                                        )
                else:
                    # Position is still open, update value of holding
                    size        = self.open_positions[order_no]['size']
                    entry_price = self.open_positions[order_no]['entry_price']
                    price       = candle.Close
                    HCF         = self.open_positions[order_no]['HCF']
                    position_value = size*(price - entry_price)*HCF
                    unrealised_PL += position_value
            
            else:
                if candle.High > self.open_positions[order_no]['stop']:
                    self.close_position(order_no, 
                                        candle, 
                                        self.open_positions[order_no]['stop']
                                        )
                elif candle.Low < self.open_positions[order_no]['take']:
                    self.close_position(order_no, 
                                        candle, 
                                        self.open_positions[order_no]['take']
                                        )
                else:
                    size        = self.open_positions[order_no]['size']
                    entry_price = self.open_positions[order_no]['entry_price']
                    price       = candle.Close
                    HCF         = self.open_positions[order_no]['HCF']
                    position_value = size*(price - entry_price)*HCF
                    unrealised_PL += position_value
        
        # Update margin available
        self.update_margin(candle.Close)
        
        # Update open position value
        self.NAV = self.portfolio_balance + unrealised_PL
        
    
    def close_position(self, order_no, candle, exit_price):
        ''' Closes positions. '''
        # Remove position from self.open_positions and calculate profit
        order_time  = self.open_positions[order_no]['order_time']
        order_price = self.open_positions[order_no]['order_price']
        order_type  = self.open_positions[order_no]['type']
        pair        = self.open_positions[order_no]['pair']
        entry_time  = self.open_positions[order_no]['time_filled']
        entry_price = self.open_positions[order_no]['entry_price']
        size        = self.open_positions[order_no]['size']
        stop_price  = self.open_positions[order_no]['stop']
        take_price  = self.open_positions[order_no]['take']
        HCF         = self.open_positions[order_no]['HCF']
        
        exit_time   = candle.name
        exit_price  = exit_price
        
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
        closed_position = {'order_ID'       : order_no,
                           'type'           : order_type,
                           'pair'           : pair,
                           'order_time'     : order_time,
                           'order_price'    : order_price,
                           'entry_time'     : entry_time, 
                           'entry_price'    : entry_price,
                           'stop_price'     : stop_price,
                           'take_price'     : take_price,
                           'exit_time'      : exit_time,
                           'exit_price'     : exit_price,
                           'size'           : size,
                           'profit'         : net_profit,
                           'balance'        : self.portfolio_balance
                           }
        
        # Add to closed positions dictionary
        self.closed_positions[order_no] = closed_position
        
        # Remove position from open positions
        self.open_positions.pop(order_no, 0)
        
        # Update maximum drawdown
        self.update_MDD()
    
    
    def get_positions(self, pair=None):
        ''' Returns the open positions in the account. '''
        # Note that trades which get closed on the same candle that they are 
        # opened on will not be returned. 
        if pair is not None:
            open_positions = self.open_positions
            current_positions = [v for v in open_positions.values() if pair in v.values()]
            
        else:
            current_positions = self.open_positions
            
        return current_positions
    
    
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
        
        # If the method below is too slow, just assume margin used is constant
        # during position, so that I dont have to iterate open pos. every 
        # candle
        margin_used = 0
        # open_position_orders = list(self.open_positions.keys())
        for order_no in self.open_positions:
            size            = self.open_positions[order_no]['size']
            HCF             = self.open_positions[order_no]['HCF']
            # HCF should be updated for current time.
            position_value  = abs(size) * close_price * HCF
            margin_required = self.calculate_margin(position_value)
            margin_used     += margin_required
        
        self.margin_available = self.portfolio_balance - margin_used


    def get_price(self, pair, data, conversion_data, i):
        ''' Returns the price data dict. '''
        
        # quote_currency = pair[-3:]
        
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
        # also need to initiate peak and low value to be equal to portfolio balance
            # Done in self.add_funds
        # Need to include time in equation
            # I think this is done implicitly 
        # Also need to check that the newest MDD is not less than previous MDD
        if MDD < self.max_drawdown:
            self.max_drawdown = MDD
            
        # Also include logic to do nothing if nothing changes for speed only
        # Isn't accurate yet, since if portfolio only goes up, low will be at
          # initial balance, giving a false MDD
          # Should only update low value if it comes after --- wait
          # I dont think this is true, ignore for now...

    def update_NAV(self):
        # Iterate over open positions to calculate value
        
        
        self.NAV = 0
        
            