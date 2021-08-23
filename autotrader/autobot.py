#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from autotrader.emailing import emailing
import numpy as np

class AutoTraderBot():
    '''
    AutoTrader Bot.
    
    Attributes
    ----------
    broker : class
        The broker class instance.
        
    instrument : str
        The instrument being traded by the bot.
    
    strategy : class
         The strategy being traded by the bot.
    

    Methods
    -------
    update(i):
        Update strategy with latest data and generate latest signal.
    
    '''
    
    def __init__(self, broker, strategy, instrument, data, autotrader_attributes):
        self.broker     = broker
        self.strategy   = strategy
        self.instrument = instrument
        self.data       = data
        self.quote_data = None
        self.latest_orders = []
        
        # Inherit user options from autotrader
        self.strategy_params    = autotrader_attributes.strategy_params
        self.scan               = autotrader_attributes.scan
        self.scan_results       = {}
        self.broker_utils       = autotrader_attributes.broker_utils
        self.email_params       = autotrader_attributes.email_params
        self.notify             = autotrader_attributes.notify
        self.validation_file    = autotrader_attributes.validation_file
        self.verbosity          = autotrader_attributes.verbosity
        self.order_summary_fp   = autotrader_attributes.order_summary_fp
        self.backtest_mode      = autotrader_attributes.backtest
        
        if int(self.verbosity) > 0:
                print("AutoTraderBot assigned to analyse {}".format(instrument),
                      "on {} timeframe using {}.".format(self.strategy_params['granularity'],
                                                         self.strategy.name))
    
    
    def update(self, i):
        '''
        Update strategy with latest data and generate latest signal.
        '''
        
        # First clear self.latest_orders
        self.latest_orders = []
        
        open_positions      = self.broker.get_open_positions(self.instrument)
        
        # Run strategy to get signals
        signal_dict = self.strategy.generate_signal(i, open_positions)
        
        if 0 not in signal_dict:
            # Single order signal, nest in dictionary to allow iteration
            signal_dict = {1: signal_dict}
            
        # Begin iteration over signal_dict to extract each order
        for order in signal_dict:
            order_signal_dict = signal_dict[order].copy()
            
            if order_signal_dict["direction"] != 0:
                self.process_signal(order_signal_dict, i, self.data, 
                                    self.quote_data, self.instrument)
        
        if int(self.verbosity) > 1:
            if len(self.latest_orders) > 0:
                for order in self.latest_orders:
                    order_string = "{}: {} {} order of {} units placed at {}.".format(order['order_time'], order['instrument'], order['order_type'], order['size'], order['order_price'])
                    print(order_string)
            elif int(self.verbosity) > 2:
                print("No signal detected.")
        
        # Check for orders placed and/or scan hits
        if int(self.notify) > 0 and self.backtest_mode is False:
            
            for order_details in self.latest_orders:
                self.broker_utils.write_to_order_summary(order_details, 
                                                         self.order_summary_fp)
            
            if int(self.notify) > 1 and \
                self.email_params['mailing_list'] is not None and \
                self.email_params['host_email'] is not None:
                    if int(self.verbosity) > 0 and len(self.latest_orders) > 0:
                            print("Sending emails ...")
                            
                    for order_details in self.latest_orders:
                        emailing.send_order(order_details,
                                            self.email_params['mailing_list'],
                                            self.email_params['host_email'])
                        
                    if int(self.verbosity) > 0 and len(self.latest_orders) > 0:
                            print("  Done.\n")
            
        # Check scan results
        if self.scan is not None:
            # Construct scan details dict
            scan_details    = {'index'      : self.scan,
                               'strategy'   : self.strategy.name,
                               'timeframe'  : self.strategy_params['granularity']
                                }
            
            # Report AutoScan results
            # Scan reporting with no emailing requested.
            if int(self.verbosity) > 0 or \
                int(self.notify) == 0:
                if len(self.scan_results) == 0:
                    print("No hits detected.")
                else:
                    print(self.scan_results)
            
            if int(self.notify) > 0:
                # Emailing requested
                if len(self.scan_results) > 0 and \
                    self.email_params['mailing_list'] is not None and \
                    self.email_params['host_email'] is not None:
                    # There was a scanner hit and email information is provided
                    emailing.send_scan_results(self.scan_results, 
                                                scan_details, 
                                                self.email_params['mailing_list'],
                                                self.email_params['host_email'])
                elif int(self.notify) > 1 and \
                    self.email_params['mailing_list'] is not None and \
                    self.email_params['host_email'] is not None:
                    # There was no scan hit, but notify set > 1, so send email
                    # regardless.
                    emailing.send_scan_results(self.scan_results, 
                                                scan_details, 
                                                self.email_params['mailing_list'],
                                                self.email_params['host_email'])
                    
    
    def update_backtest(self, i):
        candle = self.data.iloc[i]
        self.broker.update_positions(candle, self.instrument)
    
    
    def process_signal(self, order_signal_dict, i, data, quote_data, 
                       instrument):
        '''
            Process order_signal_dict and send orders to broker.
        '''
        signal = order_signal_dict["direction"]
        
        # Entry signal detected, get price data
        price_data      = self.broker.get_price(instrument=instrument, 
                                                data=data, 
                                                conversion_data=quote_data, 
                                                i=i)
        datetime_stamp  = data.index[i]
        
        if signal < 0:
            order_price = price_data['bid']
            HCF         = price_data['negativeHCF']
        else:
            order_price = price_data['ask']
            HCF         = price_data['positiveHCF']
        
        
        # Define 'working_price' to calculate size and TP
        if order_signal_dict["order_type"] == 'limit' or order_signal_dict["order_type"] == 'stop-limit':
            working_price = order_signal_dict["order_limit_price"]
        else:
            working_price = order_price
        
        # Calculate exit levels
        pip_value   = self.broker_utils.get_pip_ratio(instrument)
        stop_distance = order_signal_dict['stop_distance'] if 'stop_distance' in order_signal_dict else None
        stop_type = order_signal_dict['stop_type'] if 'stop_type' in order_signal_dict else None
        
        if 'stop_loss' not in order_signal_dict and \
            'stop_distance' in order_signal_dict and \
            order_signal_dict['stop_distance'] is not None:
            stop_price = working_price - np.sign(signal)*stop_distance*pip_value
        else:
            stop_price = order_signal_dict['stop_loss'] if 'stop_loss' in order_signal_dict else None
        
        if 'take_profit' not in order_signal_dict and \
            'take_distance' in order_signal_dict and \
            order_signal_dict['take_distance'] is not None:
            # Take profit distance specified
            take_profit = working_price + np.sign(signal)*order_signal_dict['take_distance']*pip_value
        else:
            # Take profit price specified, or no take profit specified at all
            take_profit = order_signal_dict["take_profit"] if 'take_profit' in order_signal_dict else None
        
        # Calculate risked amount
        amount_risked = self.broker.get_balance() * self.strategy_params['risk_pc'] / 100
        
        # Calculate size
        if 'size' in order_signal_dict:
            size = order_signal_dict['size']
        else:
            if self.strategy_params['sizing'] == 'risk':
                size            = self.broker_utils.get_size(instrument,
                                                 amount_risked, 
                                                 working_price, 
                                                 stop_price, 
                                                 HCF,
                                                 stop_distance)
            else:
                size = self.strategy_params['sizing']
        
        # Construct order dict by building on signal_dict
        order_details                   = order_signal_dict
        order_details["order_time"]     = datetime_stamp
        order_details["strategy"]       = self.strategy.name
        order_details["instrument"]     = instrument
        order_details["size"]           = signal*size
        order_details["order_price"]    = order_price
        order_details["HCF"]            = HCF
        order_details["granularity"]    = self.strategy_params['granularity']
        order_details["stop_distance"]  = stop_distance
        order_details["stop_loss"]      = stop_price
        order_details["take_profit"]    = take_profit
        order_details["stop_type"]      = stop_type
        order_details["related_orders"] = order_signal_dict['related_orders'] if 'related_orders' in order_signal_dict else None

        # Place order
        if self.scan is None:
            # Bot is trading
            self.broker.place_order(order_details)
            self.latest_orders.append(order_details)
            
        else:
            # Bot is scanning
            scan_hit = {"size"  : size,
                        "entry" : order_price,
                        "stop"  : stop_price,
                        "take"  : take_profit,
                        "signal": signal
                        }
            self.scan_results[instrument] = scan_hit
            

    def create_backtest_summary(self, NAV, margin):
        trade_summary = self.broker_utils.trade_summary(self.instrument, self.broker.closed_positions)
        open_trade_summary = self.broker_utils.open_order_summary(self.instrument, self.broker.open_positions)
        cancelled_summary = self.broker_utils.cancelled_order_summary(self.instrument, self.broker.cancelled_orders)
        
        if self.validation_file is not None:
            livetrade_summary = self.validation_utils.trade_summary(self.raw_livetrade_summary,
                                                                    self.data,
                                                                    self.strategy_params['granularity'])
            final_balance_diff  = NAV[-1] - livetrade_summary.Balance.values[-1]
            filled_live_orders  = livetrade_summary[livetrade_summary.Transaction == 'ORDER_FILL']
            no_live_trades      = len(filled_live_orders)
            self.livetrade_results = {'summary': livetrade_summary,
                                      'final_balance_difference': final_balance_diff,
                                      'no_live_trades': no_live_trades}
            
        backtest_dict = {}
        backtest_dict['data']           = self.data
        backtest_dict['NAV']            = NAV
        backtest_dict['margin']         = margin
        backtest_dict['trade_summary']  = trade_summary
        backtest_dict['indicators']     = self.strategy.indicators if hasattr(self.strategy, 'indicators') else None
        backtest_dict['instrument']     = self.instrument
        backtest_dict['interval']       = self.strategy_params['granularity']
        backtest_dict['open_trades']    = open_trade_summary
        backtest_dict['cancelled_trades'] = cancelled_summary
        
        self.backtest_summary = backtest_dict