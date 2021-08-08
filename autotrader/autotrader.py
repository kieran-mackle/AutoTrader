#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
---------------------------------------------------------------------------
         _   _   _ _____ ___ _____ ____      _    ____  _____ ____  
        / \ | | | |_   _/ _ \_   _|  _ \    / \  |  _ \| ____|  _ \ 
       / _ \| | | | | || | | || | | |_) |  / _ \ | | | |  _| | |_) |
      / ___ \ |_| | | || |_| || | |  _ <  / ___ \| |_| | |___|  _ < 
     /_/   \_\___/  |_| \___/ |_| |_| \_\/_/   \_\____/|_____|_| \_\
    
---------------------------------------------------------------------------
Kieran Mackle
version 0.0.11

"""

from getopt import getopt
from datetime import datetime, timedelta
import sys
import os
import pyfiglet
import yaml
import importlib
import time
import pytz
import numpy as np
import pandas as pd
from autotrader.emailing import emailing
from autotrader.brokers.oanda import Oanda
from autotrader.brokers.virtual.virtual_broker import Broker
from autotrader.lib import logger, instrument_list, environment_manager, autodata
from autotrader import autoplot


class AutoTrader():
    
    def __init__(self):
        self.config_file    = None
        self.custom_config  = None
        self.verbosity      = 0
        self.show_help      = None
        self.notify         = 0
        self.backtest       = False
        self.show_plot      = False
        self.log            = False
        self.analyse        = False
        self.scan           = None
        self.optimise       = False
        self.data_file      = None
        self.instruments    = None
        self.home_dir       = None
        self.validation_file = None
        self.plot_validation_balance = True
    
    def run(self):
        if self.show_help is not None:
            self.print_help(self.show_help)
            return
        
        if self.config_file is None and self.backtest is False:
            self.print_usage()
        else:
            self.main()
    
    def main(self):
        ''' -------------------------------------------------------------- '''
        '''                         Load configuration                     '''
        ''' -------------------------------------------------------------- '''
        if self.home_dir is not None:
            home_dir            = self.home_dir
        else:
            home_dir            = os.getcwd()
        price_data_path         = os.path.join(home_dir, 'price_data')
        
        if self.optimise is True and self.backtest is True:
            config              = self.custom_config
        else:
            config_file         = self.config_file
            config_file_path    = os.path.join(home_dir, 'config', config_file)
            config              = self.read_yaml(config_file_path + '.yaml')
        
        if self.validation_file is not None:
            livetrade_history   = pd.read_csv(self.validation_file, index_col = 0)
            livetrade_history   = livetrade_history.fillna(method='ffill')
        
        # Read configuration file
        interval            = config["STRATEGY"]["INTERVAL"]
        period              = config["STRATEGY"]["PERIOD"]
        params              = config["STRATEGY"]["PARAMETERS"]
        risk_pc             = config["STRATEGY"]["RISK_PC"]
        sizing              = config["STRATEGY"]["SIZING"]
        strat_module        = config["STRATEGY"]["MODULE"]
        strat_name          = config["STRATEGY"]["NAME"]
        environment         = config["ENVIRONMENT"]
        feed                = config["FEED"]
        global_config       = self.read_yaml(home_dir + '/config' + '/GLOBAL.yaml')
        broker_config       = environment_manager.get_config(environment,
                                                             global_config,
                                                             feed)
        get_data            = autodata.GetData(broker_config)
        
        if 'ACCOUNT_ID' in config:
            broker_config['ACCOUNT_ID'] = config['ACCOUNT_ID']
        
        # Get watchlist
        if self.scan is not None:
            watchlist       = instrument_list.get_watchlist(self.scan)
            scan_results    = {}
        elif self.instruments is not None:
            watchlist       = self.instruments.split(',') 
        elif self.validation_file is not None:
            raw_watchlist   = livetrade_history.Instrument.unique() # FOR OANDA
        else:
            watchlist       = config["WATCHLIST"]
        
        module              = importlib.import_module('strategies.' + strat_module)
        strategy            = getattr(module, strat_name)
        
        if self.backtest is True:
            utils           = importlib.import_module('autotrader.brokers.virtual.utils')
            broker          = Broker(broker_config)
            
            from_date       = datetime.strptime(config['BACKTESTING']['FROM']+'+0000', '%d/%m/%Y%z')
            to_date         = datetime.strptime(config['BACKTESTING']['TO']+'+0000', '%d/%m/%Y%z')
            
            initial_deposit = config["BACKTESTING"]["initial_balance"]
            spread          = config["BACKTESTING"]["spread"]
            leverage        = config["BACKTESTING"]["leverage"]
            commission      = config["BACKTESTING"]["commission"]
            base_currency   = config["BACKTESTING"]["base_currency"]
            
            broker.add_funds(initial_deposit)
            broker.fee      = spread
            broker.leverage = leverage
            broker.commission = commission
            broker.spread   = spread
            broker.base_currency = base_currency
            get_data.base_currency = base_currency
            
            if int(self.verbosity) > 0:
                banner = pyfiglet.figlet_format("AutoBacktest")
                print(banner)
            
            if self.validation_file is not None:
                # Also get broker-specific utility functions
                # TODO generalise per broker used
                broker_utils = importlib.import_module('autotrader.brokers.oanda.utils') # FOR OANDA ONLY
                
                # Correct watchlist
                if self.instruments is None:
                    watchlist   = broker_utils.format_watchlist(raw_watchlist)
            
        else:
            # TODO generalise per broker used
            utils           = importlib.import_module('autotrader.brokers.oanda.utils') # FOR OANDA ONLY
            broker          = Oanda.Oanda(broker_config)
        
        if int(self.notify) > 0:
            
            host_email      = None
            mailing_list    = None
            
            if 'EMAILING' in config:
                # Look for host email and mailing list in strategy config
                if "MAILING_LIST" in config["EMAILING"]:
                    mailing_list    = config["EMAILING"]["MAILING_LIST"]
                if "HOST_ACCOUNT" in config["EMAILING"]:
                    host_email      = config["EMAILING"]["HOST_ACCOUNT"]
            
            if "EMAILING" in global_config:
                # Look for host email and mailing list in strategy config, if it
                # was not picked up in strategy config
                if "MAILING_LIST" in global_config["EMAILING"] and mailing_list is None:
                    mailing_list    = global_config["EMAILING"]["MAILING_LIST"]
                if "HOST_ACCOUNT" in global_config["EMAILING"] and host_email is None:
                    host_email      = global_config["EMAILING"]["HOST_ACCOUNT"]
            
            if host_email is None:
                print("Warning: email host account not provided.")
            if mailing_list is None:
                print("Warning: no mailing list provided.")
                
            order_summary_fp = os.path.join(home_dir, 'logfiles/order_history.txt')
        
        
        ''' -------------------------------------------------------------- '''
        '''                 Analyse each instrument in watchlist           '''
        ''' -------------------------------------------------------------- '''
        for instrument in watchlist:
            # Get price history
            if self.backtest is True:
                # Running in backtest mode
                
                if self.validation_file is not None:
                    # Extract instrument-specific trade history as trade summary and trade period
                    formatted_instrument = instrument[:3] + "/" + instrument[-3:]
                    raw_livetrade_summary = livetrade_history[livetrade_history.Instrument == formatted_instrument] # FOR OANDA
                    from_date           = pd.to_datetime(raw_livetrade_summary.Date.values)[0]
                    to_date             = pd.to_datetime(raw_livetrade_summary.Date.values)[-1]
                    
                    # Modify from date to improve backtest
                    from_date = from_date - period*timedelta(seconds = self.granularity_to_seconds(interval))
                    
                    # Modify starting balance
                    broker.portfolio_balance = raw_livetrade_summary.Balance.values[np.isfinite(raw_livetrade_summary.Balance.values)][0]
                    
                    
                starting_balance    = broker.get_balance()
                NAV     = []
                balance = []
                
                if self.data_file is not None:
                    custom_data_file        = self.data_file
                    custom_data_filepath    = os.path.join(price_data_path,
                                                           custom_data_file)
                    if int(self.verbosity) > 1:
                        print("Using data file specified ({}).".format(custom_data_file))
                    data            = pd.read_csv(custom_data_filepath, 
                                                  index_col = 0)
                    data.index = pd.to_datetime(data.index)
                    quote_data      = data
                    
                else:
                    if int(self.verbosity) > 1:
                        print("Downloading extended historical data for",
                              "{}/{}.".format(instrument[:3],instrument[-3:]))
                    
                    if self.optimise is True:
                        # Check if historical data already exists
                        historical_data_name = 'hist_{0}{1}.csv'.format(interval, instrument)
                        historical_quote_data_name = 'hist_{0}{1}_quote.csv'.format(interval, instrument)
                        data_dir_path = os.path.join(home_dir, 'price_data')
                        historical_data_file_path = os.path.join(home_dir, 
                                                                 'price_data',
                                                                 historical_data_name)
                        historical_quote_data_file_path = os.path.join(home_dir, 
                                                                 'price_data',
                                                                 historical_quote_data_name)
                        
                        if not os.path.exists(historical_data_file_path):
                            # Data file does not yet exist
                            data        = getattr(get_data, feed.lower())(instrument,
                                                             granularity = interval,
                                                             start_time = from_date,
                                                             end_time = to_date)
                            quote_data  = getattr(get_data, feed.lower() + '_quote_data')(data,
                                                                                          instrument,
                                                                                          interval,
                                                                                          from_date,
                                                                                          to_date)
                            data, quote_data    = utils.check_dataframes(data, quote_data)
                            
                            # Check if price_data folder exists
                            if not os.path.exists(data_dir_path):
                                # If price data directory doesn't exist, make it
                                os.makedirs(data_dir_path)
                                
                            # Save data in file/s
                            data.to_csv(historical_data_file_path)
                            quote_data.to_csv(historical_quote_data_file_path)
                            
                        else:
                            # Data file does exist, import it as dataframe
                            data = pd.read_csv(historical_data_file_path, 
                                               index_col = 0)
                            quote_data = pd.read_csv(historical_quote_data_file_path, 
                                                     index_col = 0)
                            
                    else:
                        data        = getattr(get_data, feed.lower())(instrument,
                                                             granularity = interval,
                                                             start_time = from_date,
                                                             end_time = to_date)
                        quote_data  = getattr(get_data, feed.lower() + '_quote_data')(data,
                                                                        instrument,
                                                                        interval,
                                                                        from_date,
                                                                        to_date)
                        
                        data, quote_data    = utils.check_dataframes(data, quote_data)
                    
                    
                    if int(self.verbosity) > 1:
                        print("  Done.\n")
                
                start_range         = 0
                end_range           = len(data)
                
            else:
                # Running in livetrade mode
                data                = broker.get_data(instrument, period, interval)
                start_range         = len(data)-1
                end_range           = len(data)
                
                # Check data time alignment
                current_time        = datetime.now(tz=pytz.utc)
                last_candle_closed  = utils.last_period(current_time, interval)
                data_ts             = data.index[-1].to_pydatetime().timestamp()
                
                if data_ts != last_candle_closed.timestamp():
                    # Time misalignment detected - attempt to correct
                    count = 0
                    while data_ts != last_candle_closed.timestamp():
                        print("  Time misalginment detected",
                              "({}/{}).".format(data.index[-1].minute, last_candle_closed.minute),
                              "Trying again...")
                        time.sleep(3) # wait 3 seconds...
                        data    = broker.get_data(instrument, period, interval)
                        data_ts = data.index[-1].to_pydatetime().timestamp()
                        count   += 1
                        if count == 3:
                            break
                    
                    if data_ts != last_candle_closed.timestamp():
                        # Time misalignment still present - attempt to correct
                        # Check price data directory to see if the stream has caught 
                        # the latest candle
                        price_data_filename = "{0}{1}.txt".format(interval, instrument)
                        abs_price_path      = os.path.join(price_data_path, price_data_filename)
                        
                        if os.path.exists(abs_price_path):
                            # Price data file matching instrument and granularity 
                            # exists, check latest candle in file
                            f                   = open(abs_price_path, "r")
                            price_lines         = f.readlines()
                            
                            if len(price_lines) > 1:
                                latest_candle       = price_lines[-1].split(',')
                                latest_candle_time  = datetime.strptime(latest_candle[0],
                                                                        '%Y-%m-%d %H:%M:%S')
                                UTC_last_candle_in_file = latest_candle_time.replace(tzinfo=pytz.UTC)
                                price_data_ts       = UTC_last_candle_in_file.timestamp()
                                
                                if price_data_ts == last_candle_closed.timestamp():
                                    data    = utils.update_data_with_candle(data, latest_candle)
                                    data_ts = data.index[-1].to_pydatetime().timestamp()
                                    print("  Data updated using price stream.")
                    
                    # if data is still misaligned, perform manual adjustment.
                    if data_ts != last_candle_closed.timestamp():
                        print("  Could not retrieve updated data. Manually adjusting.")
                        data = broker.update_data(instrument, interval, data)
            
            
            # Adjust plot output to avoid excessive data visualisation
            if self.show_plot is True:
                if len(data) < 75000:
                    params['view_window']   = len(data)
                    params['show_fig']      = True
                
            # Instantiate strategy for current instrument
            my_strat    = strategy(params, data, instrument)
            
            if int(self.verbosity) > 0:
                print("\nAnalysing {}/{}".format(instrument[:3], instrument[-3:]),
                      "on {} timeframe using {}.".format(interval,
                                                            my_strat.name))
                print("Time: {}".format(datetime.now().strftime("%A, %B %d %Y, "+
                                                                  "%H:%M:%S")))
                if self.backtest is True:
                    print("From: ", from_date)
                    print("To:   ", to_date)
            
            
            ''' -------------------------------------------------------------- '''
            '''                  Analyse price data using strategy             '''
            ''' -------------------------------------------------------------- '''
            for i in range(start_range, end_range):
                open_positions      = broker.open_positions
                candle              = data.iloc[i]
                
                # Run strategy to get signals
                signal_dict = my_strat.generate_signal(i, open_positions)
                signal      = signal_dict["direction"]
                
                if signal != 0:
                    # Signal detected
                    if int(self.verbosity) > 0 and self.backtest is False:
                        print("  Signal detected at {}: {}@{}".format(data.index[i],
                                                                      signal,
                                                                      data.Close[i]
                                                                      ))
                    
                    # if signal_dict["order_type"] == 'close':
                    #     # Exit signal detected
                    #     continue
                        
                    # else:
                    
                    # Entry signal detected
                    if self.backtest is True:
                        datetime_stamp  = data.index[i]
                        price_data      = broker.get_price(instrument, data, 
                                                           quote_data, i)
                    else:
                        datetime_stamp  = datetime.now().strftime("%H:%M:%S")
                        price_data      = broker.get_price(instrument)
                    
                    if signal < 0:
                        price       = price_data['bid']
                        HCF         = price_data['negativeHCF']
                    else:
                        price       = price_data['ask']
                        HCF         = price_data['positiveHCF']
                    
                    # Get exit levels
                    stop_price  = signal_dict["stop_loss"]
                    stop_type   = signal_dict["stop_type"]
                    take_price  = signal_dict["take_profit"]
                    
                    # Calculate risked amount
                    amount_risked   = broker.get_balance() * risk_pc / 100
                    
                    # Calculate size
                    if sizing == 'risk':
                        size            = utils.get_size(instrument,
                                                         amount_risked, 
                                                         price, 
                                                         stop_price, 
                                                         HCF
                                                         )
                    else:
                        size = sizing
                    
                    # Construct order dict
                    order_details = {"order_time":      datetime_stamp,
                                     "strategy":        my_strat.name,
                                     "order_type":      signal_dict["order_type"],
                                     "instrument":      instrument,
                                     "size":            signal*size,
                                     "price":           price,
                                     "stop_loss":       stop_price,
                                     "take_profit":     take_price,
                                     "HCF":             HCF,
                                     "stop_type":       stop_type,
                                     "granularity":     interval,
                                     "related_orders":  signal_dict["related_orders"]
                                     }
                    
                    # Place order
                    if self.backtest is True:
                        broker.place_order(order_details)
                            
                    else:
                        # Running in live-trade mode
                        if self.scan is not None:
                            scan_hit = {"size"  : size,
                                        "entry" : price,
                                        "stop"  : stop_price,
                                        "take"  : take_price,
                                        "signal": signal
                                        }
                            scan_results[instrument] = scan_hit
                        else:
                            output = broker.place_order(order_details)
                            
                            # if int(self.verbosity) > 0:
                            #     print("Order message:")
                            #     print(output['Message'])
                            
                            # Send email
                            if int(self.notify) > 0:
                                utils.write_to_order_summary(order_details, 
                                                             order_summary_fp)
                                
                                if int(self.notify) > 1 and \
                                    mailing_list is not None and \
                                    host_email is not None:
                                    emailing.send_order(order_details,
                                                        output,
                                                        mailing_list,
                                                        host_email)
            
                else:
                    # No signal detected
                    if int(self.verbosity) > 0 and self.backtest is False:
                        print("  No signal detected.\n")
                   
                
                if self.backtest is True:
                    broker.update_positions(candle)
                    NAV.append(broker.NAV)
                    balance.append(broker.portfolio_balance)
                    
                    
            # Iteration complete
            if self.backtest is True:
                trade_summary = utils.trade_summary(instrument, broker.closed_positions)
                cancelled_summary = utils.cancelled_order_summary(instrument, broker.cancelled_orders)
                
                if self.validation_file is not None:
                    livetrade_summary = broker_utils.trade_summary(raw_livetrade_summary,
                                                                            data,
                                                                            interval)
                    final_balance_diff  = NAV[-1] - livetrade_summary.Balance.values[-1]
                    filled_live_orders  = livetrade_summary[livetrade_summary.Transaction == 'ORDER_FILL']
                    no_live_trades      = len(filled_live_orders)
            
            if self.show_plot is True:
                # Plot results
                if self.backtest is True:
                    if len(data) > 75000:
                        print("There is too much data to be plotted",
                              "({} candles).".format(len(data)),
                              "Check saved figure.")
                    else:
                        backtest_dict = {}
                        backtest_dict['data']           = data
                        backtest_dict['NAV']            = NAV
                        backtest_dict['trade_summary']  = trade_summary
                        backtest_dict['indicators']     = my_strat.indicators
                        backtest_dict['pair']           = instrument
                        backtest_dict['interval']       = interval
                        # plot_backtest(backtest_dict)
                        ap = autoplot.AutoPlot()
                        ap.data = data
                        
                        if self.validation_file is None:
                            ap.plot_backtest(backtest_dict)
                        else:
                            ap.plot_validation_balance = self.plot_validation_balance
                            ap.ohlc_height = 350
                            ap.validate_backtest(livetrade_summary, 
                                                 backtest_dict,
                                                 cancelled_summary,
                                                 instrument, 
                                                 interval)
                            
                            
                # Code below is deprecated
                # else:
                #     my_strat.create_price_chart(instrument, interval)
            
            
            ''' -------------------------------------------------------------- '''
            '''              Construct backtest results dictionary             '''
            ''' -------------------------------------------------------------- '''
            if self.backtest is True:
                # initialise dictionary
                backtest_results = {}
                
                # All trades
                no_trades   = len(trade_summary)
                backtest_results['no_trades'] = no_trades
                if no_trades > 0:
                    backtest_results['all_trades'] = {}
                    profit_abs  = broker.portfolio_balance - starting_balance
                    profit_pc   = 100*profit_abs / starting_balance
                    MDD         = round(broker.max_drawdown, 1)
                    wins        = trade_summary[trade_summary.Profit > 0]
                    avg_win     = np.mean(wins.Profit)
                    max_win     = np.max(wins.Profit)
                    loss        = trade_summary[trade_summary.Profit < 0]
                    avg_loss    = abs(np.mean(loss.Profit))
                    max_loss    = abs(np.min(loss.Profit))
                    win_rate    = 100*broker.profitable_trades/no_trades
                    longest_win_streak, longest_lose_streak  = utils.get_streaks(trade_summary)
                    avg_trade_duration = np.mean(trade_summary.Trade_duration.values)
                    min_trade_duration = min(trade_summary.Trade_duration.values)
                    max_trade_duration = max(trade_summary.Trade_duration.values)
                    
                    backtest_results['all_trades']['profit_abs']    = profit_abs
                    backtest_results['all_trades']['profit_pc']     = profit_pc
                    backtest_results['all_trades']['MDD']           = MDD
                    backtest_results['all_trades']['avg_win']       = avg_win
                    backtest_results['all_trades']['max_win']       = max_win
                    backtest_results['all_trades']['avg_loss']      = avg_loss
                    backtest_results['all_trades']['max_loss']      = max_loss
                    backtest_results['all_trades']['win_rate']      = win_rate
                    backtest_results['all_trades']['win_streak']    = longest_win_streak
                    backtest_results['all_trades']['lose_streak']   = longest_lose_streak
                    backtest_results['all_trades']['longest_trade'] = str(timedelta(seconds = int(max_trade_duration)))
                    backtest_results['all_trades']['shortest_trade'] = str(timedelta(seconds = int(min_trade_duration)))
                    backtest_results['all_trades']['avg_trade_duration'] = str(timedelta(seconds = int(avg_trade_duration)))
                
                # Cancelled orders (insufficient margin)
                cancelled_orders    = broker.cancelled_orders
                no_cancelled        = len(cancelled_orders)
                
                # Long trades
                long_trades     = trade_summary[trade_summary.Size > 0]
                no_long         = len(long_trades)
                backtest_results['long_trades'] = {}
                backtest_results['long_trades']['no_trades'] = no_long
                if no_long > 0:
                    long_wins       = long_trades[long_trades.Profit > 0]
                    avg_long_win    = np.mean(long_wins.Profit)
                    max_long_win    = np.max(long_wins.Profit)
                    long_loss       = long_trades[long_trades.Profit < 0]
                    avg_long_loss   = abs(np.mean(long_loss.Profit))
                    max_long_loss   = abs(np.min(long_loss.Profit))
                    long_wr         = 100*len(long_trades[long_trades.Profit > 0])/no_long
                    
                    backtest_results['long_trades']['avg_long_win']     = avg_long_win
                    backtest_results['long_trades']['max_long_win']     = max_long_win 
                    backtest_results['long_trades']['avg_long_loss']    = avg_long_loss
                    backtest_results['long_trades']['max_long_loss']    = max_long_loss
                    backtest_results['long_trades']['long_wr']          = long_wr
                    
                  
                # Short trades
                short_trades    = trade_summary[trade_summary.Size < 0]
                no_short        = len(short_trades)
                backtest_results['short_trades'] = {}
                backtest_results['short_trades']['no_trades'] = no_short
                if no_short > 0:
                    short_wins      = short_trades[short_trades.Profit > 0]
                    avg_short_win   = np.mean(short_wins.Profit)
                    max_short_win   = np.max(short_wins.Profit)
                    short_loss      = short_trades[short_trades.Profit < 0]
                    avg_short_loss  = abs(np.mean(short_loss.Profit))
                    max_short_loss  = abs(np.min(short_loss.Profit))
                    short_wr        = 100*len(short_trades[short_trades.Profit > 0])/no_short
                    
                    backtest_results['short_trades']['avg_short_win']   = avg_short_win
                    backtest_results['short_trades']['max_short_win']   = max_short_win
                    backtest_results['short_trades']['avg_short_loss']  = avg_short_loss
                    backtest_results['short_trades']['max_short_loss']  = max_short_loss
                    backtest_results['short_trades']['short_wr']        = short_wr
                
            
            ''' -------------------------------------------------------------- '''
            '''                     Print output to console                    '''
            ''' -------------------------------------------------------------- '''
            if int(self.verbosity) > 0 and self.backtest is True:
                
                print("\n-------------------------------------------")
                print("            Backtest Results")
                print("-------------------------------------------")
                print("Strategy: {}".format(my_strat.name))
                print("Timeframe:               {}".format(interval))
                print("Risk to reward ratio:    {}".format(params['RR']))
                print("Profitable win rate:     {}%".format(round(100/(1+params['RR']), 1)))
                if no_trades > 0:
                    print("Backtest win rate:       {}%".format(round(win_rate, 1)))
                    
                    print("Total no. trades:        {}".format(broker.total_trades))
                    print("Profit:                  ${} ({}%)".format(round(profit_abs, 3), 
                                                      round(profit_pc, 1)))
                    print("Maximum drawdown:        {}%".format(MDD))
                    print("Max win:                 ${}".format(round(max_win, 2)))
                    print("Average win:             ${}".format(round(avg_win, 2)))
                    print("Max loss:                -${}".format(round(max_loss, 2)))
                    print("Average loss:            -${}".format(round(avg_loss, 2)))
                    print("Longest win streak:      {} trades".format(longest_win_streak))
                    print("Longest losing streak:   {} trades".format(longest_lose_streak))
                    print("Average trade duration   {}".format(backtest_results['all_trades']['avg_trade_duration']))
                    
                    
                else:
                    print("No trades taken.")
                    
                print("Cancelled orders:        {}".format(no_cancelled))
                
                # Long trades
                print("\n         Summary of long trades")
                print("-------------------------------------------")
                if no_long > 0:
                    print("Number of long trades:   {}".format(no_long))
                    print("Long win rate:           {}%".format(round(long_wr, 1)))
                    print("Max win:                 ${}".format(round(max_long_win, 2)))
                    print("Average win:             ${}".format(round(avg_long_win, 2)))
                    print("Max loss:                -${}".format(round(max_long_loss, 2)))
                    print("Average loss:            -${}".format(round(avg_long_loss, 2)))
                else:
                    print("There were no long trades.")
                  
                # Short trades
                print("\n          Summary of short trades")
                print("-------------------------------------------")
                if no_short > 0:
                    print("Number of short trades:  {}".format(no_short))
                    print("short win rate:          {}%".format(round(short_wr, 1)))
                    print("Max win:                 ${}".format(round(max_short_win, 2)))
                    print("Average win:             ${}".format(round(avg_short_win, 2)))
                    print("Max loss:                -${}".format(round(max_short_loss, 2)))
                    print("Average loss:            -${}".format(round(avg_short_loss, 2)))
                    
                else:
                    print("There were no short trades.")
                
                if self.validation_file is not None:
                    print("\n            Backtest Validation")
                    print("-------------------------------------------")
                    print("Difference between final portfolio balance between")
                    print("live-trade account and backtest is ${}.".format(round(final_balance_diff, 2)))
                    print("Number of live trades: {} trades.".format(no_live_trades))
                
                
            if self.log is True and self.backtest is True:
                logger.write_backtest_log(instrument, config, trade_summary)
        
        
        if self.scan is not None:
            # Construct scan details dict
            scan_details    = {'index'      : self.scan,
                               'strategy'   : my_strat.name,
                               'timeframe'  : interval
                               }
            
            # Report AutoScan results
            if int(self.verbosity) > 0 or \
                int(self.notify) == 0:
                if len(scan_results) == 0:
                    print("No hits detected.")
                else:
                    print(scan_results)
            
            if int(self.notify) >= 1:
                # index = self.scan
                if len(scan_results) > 0 and \
                    mailing_list is not None and \
                    host_email is not None:
                    # There was a scanner hit
                    emailing.send_scan_results(scan_results, 
                                               scan_details, 
                                               mailing_list,
                                               host_email)
                elif int(self.verbosity) > 1 and \
                    mailing_list is not None and \
                    host_email is not None:
                    # There was no scan hit, but verbostiy set > 1, so send email
                    # regardless.
                    emailing.send_scan_results(scan_results, 
                                               scan_details, 
                                               mailing_list,
                                               host_email)
        
            # if self.analyse is True and self.backtest is True:
                # print("\nResults of Indicator Analysis:")
                # print("-------------------------------")
                # long_results, short_results = correlator.correlate_indicators(data, trade_summary)
                # print("Long trades:")
                # print(long_results)
                # print("\nShort trades:")
                # print(short_results)
                # return data, trade_summary
        
        if self.optimise is True and self.backtest is True:
            return backtest_results
        
        if self.backtest is True:
            return trade_summary
    


    def read_yaml(self, file_path):
        '''Function to read and extract contents from .yaml file.'''
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    
    def granularity_to_seconds(self, granularity):
        '''Converts the interval to time in seconds'''
        letter = granularity[0]
        
        if len(granularity) > 1:
            number = float(granularity[1:])
        else:
            number = 1
        
        conversions = {'S': 1,
                       'M': 60,
                       'H': 60*60,
                       'D': 60*60*24
                       }
        
        my_int = conversions[letter] * number
        
        return my_int

    def print_usage(self):
        """ Print usage options. """
        banner = pyfiglet.figlet_format("AUTOTRADER")
        print(banner)
        
        print("AutoTrader is an algorithmic trading development platform.")
        print("\nIt has three run modes:")
        print("  1. Backtest mode")
        print("  2. Livetrade mode")
        print("  3. Scan mode")
        print("By default, AutoTrader will run in livetrade mode.\n")
        
        print("The user options are shown below.")
    
        print("--------------------------------------------------------------" \
              + "---------------")
        print("Flag                                 Comment [short flag]")
        print("--------------------------------------------------------------" \
              + "---------------")
        print("Required:")
        print("  --config <path>                    path to config file [-c]")
        print("\nOptional:")
        print("  --help                             show help for usage [-h]")
        print("  --verbosity <int>                  set verbosity (0,1,2) [-v]")
        print("  --backtest                         run in backtesting mode [-b]")
        print("  --plot                             plot results of backtest [-p]")
        print("  --notify <int>                     notify by email when ordering [-n]")
        print("  --log                              log backtest results to file [-l]")
        print("  --analyse                          run correlation study of indicators [-a]")
        print("  --scan                             run in scan mode only [-s]")
        print("  --optimise                         optimise strategy parameters [-o]")
        print("  --instruments                      specify specific instruments [-i]")
        print("  --data                             load custom price data file [-d]")
        # print("\nComing soon:")
        print("")
        print("For more information, try using -h <Option>. For example, use ")
        print(" -h backtest or -h b for more information on the backtesting flag.\n")
    
    
    def print_help(self, option):
        ''' Print usage instructions. '''
        
        banner = pyfiglet.figlet_format("AUTOTRADER")
        print(banner)
        if option == 'config' or option == 'c':
            print("Help for '--config' (-c) option:")
            print("-----------------------------------")
            print("A configuration file must be specified to run AutoTrader. The")
            print("file must be written as a .yaml file according to the template")
            print("provided in the config/ directory.")
            
            print("Note that the file extension should not be included. The full")
            print("file path does not need to be specified, AutoTrader will search")
            print("for the file in the config/ directory.")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file")
            
        elif option == 'verbosity' or option == 'v':
            print("Help for '--verbosity' (-v) option:")
            print("-----------------------------------")
            print("The verbosity flag is used to set the level of output")
            print("displayed by the code. A verbosity of zero supresses all")
            print("output, while a value greater than zero will show more details")
            print("of what the code is doing.")
            print("Verbosity settings will not affect error output.")
            
            print("\nDefault value: 0")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c ConfigFile.yaml -v 1")
            
        elif option == 'backtest' or option == 'b':
            print("Help for '--backtest' (-b) option:")
            print("-----------------------------------")
            print("The backtest flag is used to run the strategy in backtest")
            print("mode.")
            
            print("\nDefault value: False")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -b")
            
        elif option == 'plot' or option == 'p':
            print("Help for '--plot' (-p) option:")
            print("-----------------------------------")
            print("The plot option is used to create a plot of the price chart")
            print("and strategy-specific indicators. It may be used for both")
            print("livetrading and backtesting.")
            
            print("\nDefault value: False")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -b -p")
            
        elif option == 'notify' or option == 'n':
            print("Help for '--notify' (-n) option:")
            print("-----------------------------------")
            print("The notify option may be used to enable email notifications")
            print("of livetrade activity and AutoScan results.")
            
            print("Options:")
            print("  -n 0: No emails will be sent.")
            print("  -n 1: Minimal emails will be sent (summaries only).")
            print("  -n 2: All emails will be sent (every order and summary).")
            
            print("Note: if daily email summaries are desired, email_manager must")
            print("be employed in another scheduled job to send the summary.")
            
            print("\nDefault value: 0")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -n 1")
            
        elif option == 'log' or option == 'l':
            print("Help for '--log' (-l) option:")
            print("-----------------------------------")
            print("The log option allows logging of backtest results to a")
            print("logfile. The log file will be written to logfiles/ and")
            print("includes key statistics of the backtest, such as win rate,")
            print("number of trades and profit. The configuration file is also")
            print("embeded in the log file for future reference.")
            
            print("\nDefault value: False")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -b -l")
            
        elif option == 'analyse' or option == 'a':
            print("Help for '--analyse' (-a) option:")
            print("-----------------------------------")
            print("Analyser. More information coming soon.")
            
            print("\nDefault value: False")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -b -a")
            
        elif option == 'scan' or option == 's':
            print("Help for '--scan' (-s) option:")
            print("-----------------------------------")
            print("Automated market scanner. When running AutoTrader in this mode,")
            print("the market will be scanned for entry conditions based on the")
            print("strategy in the configuration file.")
            print("When the notify flag is included, an email will be sent to")
            print("notify the recipients in the email list of the signal.")
            print("This option requires an index or instrument to scan as an")
            print("input.")
            
            print("Note: if email notifications are enabled and there are no scan")
            print("hits, no email will be sent. However, if you still wish to receive")
            print("emails regardless, set the verbosity of the code to 2. In this")
            print("case, an email will be sent on the completion of each scan,")
            print("regardless of the results.")
            
            print("\nDefault value: False")
    
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -s major -n -v 1")
            
        elif option == 'optimise' or option == 'o':
            print("Help for '--optimise' (-o) option:")
            print("-----------------------------------")
            print("When this flag is included, AutoTrader will return a dictionary")
            print("containing backtest results, to be used by the optimiser.")
            print("This option is to be used internally by AutoOptimise.")
            
            print("\nDefault value: False")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -b -o")
        
        elif option == 'data' or option == 'd':
            print("Help for '--data' (-d) option:")
            print("-----------------------------------")
            print("This flag may be used to specify the filename for custom")
            print("historical price data. Note that if this flag is included,")
            print("the backtesting times specified in the config file will no")
            print("longer be used.")
            
            print("Currently, data must be located in the price data directory")
            print("to be used.")
            
            print("Important: if a data file is provided, this will also be used")
            print("be used for the quote data. That is, currency conversions will")
            print("not be accounted for.")
            
            print("\nDefault value: None")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -b -d EUR_USD.csv")
        
        elif option == 'instruments' or option == 'i':
            print("Help for '--instruments' (-i) option:")
            print("-----------------------------------")
            print("This flag may be used to specify instruments to run AutoTrader")
            print("on, overwriting the watchlist in the strategy config file.")
            
            print("\nDefault value: None")
            
            print("\nExample usage:")
            print("./AutoTrader.py -c my_config_file -b -i EUR_USD")
            
        elif option == "general":
            print("General help.")
            print("")
            
        else:
            print("Unrecognised flag ({}).".format(option))
        
        if option != "general":
            print("\n\nFor general help, use -h general.\n")


short_options = "h:c:v:n:bplas:od:i:"
long_options = ["help=", "config=", "verbosity=", "notify=", "backtest", "plot",
                "log", "analyse", "scan=", "optimise", "data=", "instruments="]


if __name__ == '__main__':
    
    # Instantiate AutoTrader Class 
    autotrader = AutoTrader()
    
    # Extract user inputs
    options, r = getopt(sys.argv[1:], 
                          short_options, 
                          long_options
                          )
    # Default options
    config_file     = None
    verbosity       = 0
    show_help       = None
    notify          = 0
    backtest        = False
    show_plot       = False
    log             = False
    analyse         = False
    scan            = None
    optimise        = False
    data_file       = None
    instruments     = None
    
    for opt, arg in options:
        if opt in ('-c', '--config'):
            config_file = arg
            autotrader.config_file = config_file
        elif opt in ('-v', '--verbose'):
            verbosity = arg
            autotrader.verbosity = verbosity
        elif opt in ('-h', '--help'):
            show_help = arg
            autotrader.show_help = show_help
        elif opt in ('-n', '--notify'):
            notify = arg
            autotrader.notify = notify
        elif opt in ('-b', '--backtest'):
            backtest = True
            autotrader.backtest = backtest
        elif opt in ('-p', '--plot'):
            show_plot = True
            autotrader.show_plot = show_plot
        elif opt in ('-l', '--log'):
            log = True
            autotrader.log = log
        elif opt in ('-a', '--analyse'):
            analyse = True
            autotrader.analyse = analyse
        elif opt in ('-s', '--scan'):
            scan = arg
            autotrader.scan = scan
        elif opt in ('-o', '--optimise'):
            optimise = True
            autotrader.optimise = optimise
        elif opt in ('-d', '--data'):
            data_file = arg
            autotrader.data_file = data_file
        elif opt in ('-i', '--instruments'):
            instruments = arg
            autotrader.instruments = instruments

    if len(options) == 0:
        autotrader.print_usage()
        
    elif show_help is not None:
        autotrader.print_help(show_help)
        
    else:
        autotrader.run()
