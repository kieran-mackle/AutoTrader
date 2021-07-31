#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Virtual broker.

"""

import v20
from autotrader.brokers.virtual import utils

class Broker():
    
    def __init__(self, broker_config):
        # Create v20 context
        API                     = broker_config["API"]
        ACCESS_TOKEN            = broker_config["ACCESS_TOKEN"]
        port                    = broker_config["PORT"]
        
        self.ACCOUNT_ID         = broker_config["ACCOUNT_ID"]
        self.api                = v20.Context(hostname=API, token=ACCESS_TOKEN, port=port)
        
        self.fee                = 0
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
        self.base_currency      = 'AUD'
    
    
    def place_order(self, order_details):
        ''' 
            Place order with broker. Currently only supports market 
            order types. 
            
        '''
        order_type  = order_details["order_type"]
        pair        = order_details["instrument"]
        size        = order_details["size"]
        order_price = order_details["price"]
        time        = order_details["order_time"]
        take_price  = order_details["take_profit"]
        HCF         = order_details["HCF"]
        stop_type   = order_details["stop_type"]
        
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
                        'stop_type' : stop_type
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
        
        
        # Remove position from pending positions
        if opened_positions > 0:
            for order_no in self.open_positions.keys():
                self.pending_positions.pop(order_no, 0)
            
            for order_no in self.cancelled_orders.keys():
                self.pending_positions.pop(order_no, 0)
        
        
        # Update trailing stops
        # For other methods, move the stop update to an external function
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
        for order_no in open_position_orders:
            if self.open_positions[order_no]['size'] > 0:
                if candle.Low < self.open_positions[order_no]['stop']:
                    self.close_position(order_no, 
                                        candle, 
                                        self.open_positions[order_no]['stop']
                                        )
                elif candle.High > self.open_positions[order_no]['take']:
                    self.close_position(order_no, 
                                        candle, 
                                        self.open_positions[order_no]['take']
                                        )
            
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
        
        # Update margin available
        self.update_margin(candle.Close)
        
    
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
    
    
    def get_data(self, pair, interval, period=None, start=None, end=None):
        ''' Get historical price data of a pair. '''
        # specifying a start and end takes precedence over specifying a period.

        # what if I wanted to request 25,000 candles, rather than specifying 
        # a time range? Would need to modify function again...
        #       Ignore this as an edge case for now. 
        # This would basically be the inverse of what I have already done, 
        # instead of stepping forward, I would step backward with partial_to
        # times until my requested count is hit.
        
        if period is not None:
            # either of period, start+period, end+period (or start+end+period)
            # if period is provided, period must be less than 5000
            if start is None and end is None:
                # period
                response    = self.api.instrument.candles(pair,
                                             granularity = interval,
                                             count = period
                                             )
                data        = utils.response_to_df(response)
                
            elif start is not None and end is None:
                # start+period
                from_time   = start.timestamp()
                response    = self.api.instrument.candles(pair,
                                             granularity = interval,
                                             count = period,
                                             fromTime = from_time
                                             )
                data        = utils.response_to_df(response)
            
            elif end is not None and start is None:
                # end+period
                to_time     = end.timestamp()
                response    = self.api.instrument.candles(pair,
                                             granularity = interval,
                                             count = period,
                                             toTime = to_time
                                             )
                data        = utils.response_to_df(response)
                
            else:
                # start+end+period
                print("Ignoring period input since start and end",
                       "times have been specified.")
                from_time       = start.timestamp()
                to_time         = end.timestamp()
            
                # try to get data 
                response        = self.api.instrument.candles(pair,
                                                         granularity = interval,
                                                         fromTime = from_time,
                                                         toTime = to_time
                                                         )
                
                # If the request is rejected, max candles likely exceeded
                if response.status != 200:
                    data        = self.get_extended_data(pair,
                                                         interval,
                                                         from_time,
                                                         to_time)
                else:
                    data        = utils.response_to_df(response)
                
        else:
            # period is None
            # Assume that both start and end have been specified.
            from_time       = start.timestamp()
            to_time         = end.timestamp()
            
            # try to get data 
            response        = self.api.instrument.candles(pair,
                                                     granularity = interval,
                                                     fromTime = from_time,
                                                     toTime = to_time
                                                     )
            
            # If the request is rejected, max candles likely exceeded
            if response.status != 200:
                data        = self.get_extended_data(pair,
                                                     interval,
                                                     from_time,
                                                     to_time)
            else:
                data        = utils.response_to_df(response)
        
        
        # if livetesting, specify end time and count (end=now, count=300)
        # if backtesting, specify start time and count (start=last_start+interval, count=300)
        # OR
        # if backtesting, specify end time and count (end=last_end+interval, count=300)
        # This is closer to the sliding window method of backtesting
        
        return data
    
    
    def get_extended_data(self, pair, interval, from_time, to_time):
        ''' Returns historical data between a date range. '''
        # Currently does not accept period (count) input, but in the future...
        
        max_candles     = 5000
        
        my_int          = utils.interval_to_seconds(interval)
        end_time        = to_time - my_int
        partial_from    = from_time
        response        = self.api.instrument.candles(pair,
                                                 granularity = interval,
                                                 fromTime = partial_from,
                                                 count = max_candles
                                                 )
        data            = utils.response_to_df(response)
        last_time       = data.index[-1].timestamp()
        
        while last_time < end_time:
            partial_from    = last_time
            response        = self.api.instrument.candles(pair,
                                                     granularity = interval,
                                                     fromTime = partial_from,
                                                     count = max_candles
                                                     )
            
            partial_data    = utils.response_to_df(response)
            data            = data.append(partial_data)
            last_time       = data.index[-1].timestamp()
            
        return data
    
    
    def get_quote_data(self, data, pair, interval, period=None, start=None, end=None):
        # Currently wont work if period is given, onyl start and end
        
        quote_currency  = pair[-3:]
        base_currency   = pair[:3]

        if quote_currency == self.base_currency:
            conversion_data = data
        else:
            conversion_pair = self.base_currency + "_" + quote_currency
            conversion_data = self.get_data(conversion_pair,
                                            interval,
                                            start=start,
                                            end=end
                                            )
        
        return conversion_data
        
    
    def get_price(self, pair, data, conversion_data, i):
        ''' Returns the price data dict. '''
        
        quote_currency = pair[-3:]
        
        ask = data.Close[i]
        bid = data.Close[i]
        conversion_data = conversion_data.Close[i]
        
        if quote_currency == self.base_currency:
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
        
            