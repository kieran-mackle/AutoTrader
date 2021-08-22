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
     A Python-Based Development Platform For Automated Trading Systems
                             Kieran Mackle
                             Version 0.2.4
                             
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
from autotrader.lib import instrument_list, environment_manager, autodata
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
        self.include_broker = False
        
        # New attributes
        self.config         = None
        self.broker         = None
        self.broker_utils   = None
        self.email_params   = None
        self.strategy       = None
        self.strategy_params = None
        self.get_data       = None
        self.bots_deployed       = []
        
        self.scan_results = {}
        self.order_summary_fp = None
        
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
        if self.home_dir is None:
            self.home_dir       = os.getcwd()
        
        price_data_path         = os.path.join(self.home_dir, 'price_data')
        
        if self.optimise is True and self.backtest is True:
            config              = self.custom_config
        else:
            config_file         = self.config_file
            config_file_path    = os.path.join(self.home_dir, 'config', config_file)
            config              = self.read_yaml(config_file_path + '.yaml')
        
        if self.validation_file is not None:
            livetrade_history   = pd.read_csv(self.validation_file, index_col = 0)
            self.livetrade_history = livetrade_history.fillna(method='ffill')
        
        # Read configuration file
        self.config         = config
        interval            = config["STRATEGY"]["INTERVAL"]
        period              = config["STRATEGY"]["PERIOD"]
        params              = config["STRATEGY"]["PARAMETERS"]
        risk_pc             = config["STRATEGY"]["RISK_PC"]
        sizing              = config["STRATEGY"]["SIZING"]
        strat_module        = config["STRATEGY"]["MODULE"]
        strat_name          = config["STRATEGY"]["NAME"]
        environment         = config["ENVIRONMENT"]
        feed                = config["FEED"]
        
        strategy_params                 = params
        strategy_params['granularity']  = interval
        strategy_params['risk_pc']      = risk_pc
        strategy_params['sizing']       = sizing
        strategy_params['period']       = period
        self.strategy_params            = strategy_params
        
        global_config       = self.read_yaml(self.home_dir + '/config' + '/GLOBAL.yaml')
        broker_config       = environment_manager.get_config(environment,
                                                             global_config,
                                                             feed)
        self.get_data       = autodata.GetData(broker_config)
        
        if 'ACCOUNT_ID' in config:
            broker_config['ACCOUNT_ID'] = config['ACCOUNT_ID']
        
        # Get watchlist
        if self.scan is not None:
            self.watchlist  = instrument_list.get_watchlist(self.scan)
            self.scan_results = {}
            
        elif self.instruments is not None:
            self.watchlist  = self.instruments.split(',') 
        elif self.validation_file is not None:
            self.raw_watchlist = livetrade_history.Instrument.unique() # FOR OANDA
        else:
            self.watchlist  = config["WATCHLIST"]
        
        strat_package_path  = os.path.join(self.home_dir, "strategies")
        strat_module_path   = os.path.join(strat_package_path, strat_module) + '.py'
        strat_spec          = importlib.util.spec_from_file_location(strat_module, strat_module_path)
        strategy_module     = importlib.util.module_from_spec(strat_spec)
        strat_spec.loader.exec_module(strategy_module)
        strategy            = getattr(strategy_module, strat_name)
        
        self.assign_broker(broker_config, config)
        
        self.configure_emailing(config, global_config)
        
        if self.backtest:
            starting_balance = self.broker.get_balance()
            NAV     = []
            balance = []
            margin  = []
        
        if int(self.verbosity) > 0:
            if self.backtest is True:
                print("Begining new backtest.")
                print("  From: ", datetime.strptime(self.config['BACKTESTING']['FROM']+'+0000', '%d/%m/%Y%z'))
                print("  To:   ", datetime.strptime(self.config['BACKTESTING']['TO']+'+0000', '%d/%m/%Y%z'))
                print("  Instruments: ", self.watchlist)
            elif self.scan is not None:
                print("AutoScan:")
                print("Time: {}".format(datetime.now().strftime("%A, %B %d %Y, "+
                                                                  "%H:%M:%S")))
            else:
                print("AutoTrader Livetrade")
                print("--------------------")
                print("Time: {}".format(datetime.now().strftime("%A, %B %d %Y, "+
                                                                  "%H:%M:%S")))
                
        ''' -------------------------------------------------------------- '''
        '''    Assign strategy to bot for each instrument in watchlist     '''
        ''' -------------------------------------------------------------- '''
        for instrument in self.watchlist:
            # Get price history
            data, quote_data = self.retrieve_data(instrument, price_data_path, feed)
            
            # Instantiate strategy for current instrument
            my_strat        = strategy(params, data, instrument)
            self.strategy   = my_strat
            
            if self.include_broker:
                my_strat.broker = self.broker
                my_strat.broker_utils = self.broker_utils
            
            # Create new bot for each instrument in watchlist
            bot = AutoTraderBot(self.broker, my_strat, instrument, data, self)
            
            if self.backtest:
                bot.quote_data = quote_data
            
            self.bots_deployed.append(bot)
            

        ''' -------------------------------------------------------------- '''
        '''                  Analyse price data using strategy             '''
        ''' -------------------------------------------------------------- '''
        if int(self.verbosity) > 0 and self.backtest:
            print("\nTrading...")
        
        start_range, end_range = self.get_iteration_range(data)
        for i in range(start_range, end_range):
            
            # Update each bot with latest data to generate signal
            for bot in self.bots_deployed:
                bot.update(i)
                
                # If backtesting, update virtual broker with latest data
                if self.backtest:
                    bot.update_backtest(i)
            
            if self.backtest is True:
                NAV.append(self.broker.NAV)
                balance.append(self.broker.portfolio_balance)
                margin.append(self.broker.margin_available)
        
        ''' -------------------------------------------------------------- '''
        '''                     Backtest Post-Processing                   '''
        ''' -------------------------------------------------------------- '''
        # Data iteration complete - proceed to post-processing
        if self.backtest is True:
            # Create backtest summary for each bot 
            for bot in self.bots_deployed:
                bot.create_backtest_summary(NAV, margin)            
            
            if int(self.verbosity) > 0:
                print("\nBacktest complete.")
                if len(self.bots_deployed) == 1:
                    bot = self.bots_deployed[0]
                    trade_summary = bot.backtest_summary['trade_summary']
                    backtest_results = self.extract_backtest_results(trade_summary, 
                             self.broker, starting_balance, self.broker_utils) 
                    self.print_backtest_results(backtest_results)
                    
                    if self.validation_file is not None:
                        final_balance_diff = bot.livetrade_results['final_balance_difference']
                        no_live_trades = bot.livetrade_results['no_live_trades']
                        
                        print("\n            Backtest Validation")
                        print("-------------------------------------------")
                        print("Difference between final portfolio balance between")
                        print("live-trade account and backtest is ${}.".format(round(final_balance_diff, 2)))
                        print("Number of live trades: {} trades.".format(no_live_trades))
                else:
                    self.multibot_backtest_results = self.multibot_backtest_analysis()
                    self.print_multibot_backtest_results(self.multibot_backtest_results)
                    
                    print("Results for multiple-instrument backtests have been")
                    print("written to AutoTrader.multibot_backtest_results.")
                    print("Individual bot results can be found in AutoTrader.bots_deployed.")
            
            if self.show_plot:
                if len(self.bots_deployed) == 1:
                    if self.validation_file is None:
                        # ap.plot_backtest(bot.backtest_summary)
                        self.plot_backtest(bot=self.bots_deployed[0])
                    else:
                        self.plot_backtest(bot=self.bots_deployed[0], 
                                           validation_file=self.validation_file)
                
                else:
                    # Backtest run with multiple bots
                    cpl_dict = {}
                    for bot in self.bots_deployed:
                        profit_df = pd.merge(bot.data, 
                                 bot.backtest_summary['trade_summary']['Profit'], 
                                 left_index=True, right_index=True).Profit.cumsum()
                        cpl_dict[bot.instrument] = profit_df
                    
                    ap = autoplot.AutoPlot()
                    ap.data = data
                    ap.plot_multibot_backtest(self.multibot_backtest_results, 
                                              NAV,
                                              cpl_dict)

    
    def plot_backtest(self, bot=None, validation_file=None):
        ap = autoplot.AutoPlot()
        ap.data = bot.data
        profit_df = pd.merge(bot.data, 
                             bot.backtest_summary['trade_summary']['Profit'], 
                             left_index=True, right_index=True).Profit.cumsum()
        
        if validation_file is None:
            ap.plot_backtest(bot.backtest_summary, cumulative_PL=profit_df)
            
        else:
            ap.plot_validation_balance = self.plot_validation_balance # User option flag
            ap.ohlc_height = 350
            ap.validate_backtest(bot.livetrade_results['summary'],
                                 bot.backtest_summary)
                
    
    def multibot_backtest_analysis(self, bots=None):
        '''
        Analyses backtest results of multiple bots to create an overall 
        performance summary.
        
            Parameters:
                bots (list): a list of AutoTrader bots to analyse.
        '''
        
        instruments = []
        win_rate    = []
        no_trades   = []
        avg_win     = []
        max_win     = []
        avg_loss    = []
        max_loss    = []
        no_long     = []
        no_short    = []
        
        if bots is None:
            bots = self.bots_deployed
        
        for bot in bots:
            backtest_results = self.analyse_backtest(bot.backtest_summary)
            
            instruments.append(bot.instrument)
            win_rate.append(backtest_results['all_trades']['win_rate'])
            no_trades.append(backtest_results['no_trades'])
            avg_win.append(backtest_results['all_trades']['avg_win'])
            max_win.append(backtest_results['all_trades']['max_win'])
            avg_loss.append(backtest_results['all_trades']['avg_loss'])
            max_loss.append(backtest_results['all_trades']['max_loss'])
            no_long.append(backtest_results['long_trades']['no_trades'])
            no_short.append(backtest_results['short_trades']['no_trades'])
            
        
        multibot_backtest_results = pd.DataFrame(data={'win_rate': win_rate,
                                                       'no_trades': no_trades,
                                                       'avg_win': avg_win,
                                                       'max_win': max_win,
                                                       'avg_loss': avg_loss,
                                                       'max_loss': max_loss,
                                                       'no_long': no_long,
                                                       'no_short': no_short},
                                                 index=instruments)
        
        return multibot_backtest_results
        
    
    def analyse_backtest(self, backtest_summary):
        '''
        Analyses backtest summary to extract key statistics.
        
            Parameters:
                backtest_summary (dict): summary of backtest performance of bot.
        '''
        
        trade_summary   = backtest_summary['trade_summary']
        instrument      = backtest_summary['instrument']
        
        cpl             = trade_summary.Profit.cumsum()
        
        backtest_results = {}
        
        # All trades
        no_trades   = len(trade_summary)
        backtest_results['no_trades'] = no_trades
        if no_trades > 0:
            backtest_results['all_trades'] = {}
            wins        = trade_summary[trade_summary.Profit > 0]
            avg_win     = np.mean(wins.Profit)
            max_win     = np.max(wins.Profit)
            loss        = trade_summary[trade_summary.Profit < 0]
            avg_loss    = abs(np.mean(loss.Profit))
            max_loss    = abs(np.min(loss.Profit))
            win_rate    = 100*len(wins)/no_trades
            longest_win_streak, longest_lose_streak  = self.broker_utils.get_streaks(trade_summary)
            avg_trade_duration = np.mean(trade_summary.Trade_duration.values)
            min_trade_duration = min(trade_summary.Trade_duration.values)
            max_trade_duration = max(trade_summary.Trade_duration.values)
            
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
            backtest_results['all_trades']['net_pl']        = cpl.values[-1]
            
        # Cancelled and open orders
        cancelled_orders = self.broker.get_cancelled_orders(instrument)
        open_trades      = self.broker.get_open_positions(instrument)
        backtest_results['no_open'] = len(open_trades)
        backtest_results['no_cancelled'] = len(cancelled_orders)
        
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
        
        return backtest_results
        
    
    def print_multibot_backtest_results(self, backtest_results=None):
        '''
        Prints to console the backtest results of a multi-bot backtest.
        
            Parameters:
                backtest_results (dict): dictionary containing backtest results.
        '''
        
        print("\n---------------------------------------------------")
        print("         MultiBot Backtest Results")
        print("---------------------------------------------------")
        print("Instruments traded: ", backtest_results.index.values)
        print("Total no trades:    ", backtest_results.no_trades.sum())
        print("Short trades:       ", backtest_results.no_short.sum(),
              "({}%)".format(round(100*backtest_results.no_short.sum()/backtest_results.no_trades.sum(),2)))
        print("Long trades:        ", backtest_results.no_long.sum(),
              "({}%)".format(round(100*backtest_results.no_long.sum()/backtest_results.no_trades.sum(),2)))
        print("\nInstrument win rates (%):")
        print(backtest_results[['win_rate']])
        print("\nMaximum/Average Win/Loss breakdown ($):")
        print(backtest_results[["max_win", "max_loss", "avg_win", "avg_loss"]])
        print("\nAverage Risk-Reward Ratio (avg win/avg loss):")
        print(round(backtest_results.avg_win / backtest_results.avg_loss,1))
        print("")
        

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


    def retrieve_data(self, instrument, price_data_path, feed):
    
        interval    = self.strategy_params['granularity']
        period      = self.strategy_params['period']
        
        if self.backtest is True:
            # Running in backtest mode
            
            from_date       = datetime.strptime(self.config['BACKTESTING']['FROM']+'+0000', '%d/%m/%Y%z')
            to_date         = datetime.strptime(self.config['BACKTESTING']['TO']+'+0000', '%d/%m/%Y%z')
            
            if self.validation_file is not None:
                # Extract instrument-specific trade history as trade summary and trade period
                livetrade_history = self.livetrade_history
                formatted_instrument = instrument[:3] + "/" + instrument[-3:]
                raw_livetrade_summary = livetrade_history[livetrade_history.Instrument == formatted_instrument] # FOR OANDA
                from_date           = pd.to_datetime(raw_livetrade_summary.Date.values)[0]
                to_date             = pd.to_datetime(raw_livetrade_summary.Date.values)[-1]
                
                self.raw_livetrade_summary = raw_livetrade_summary
                
                # Modify from date to improve backtest
                from_date = from_date - period*timedelta(seconds = self.granularity_to_seconds(interval))
                
                # Modify starting balance
                self.broker.portfolio_balance = raw_livetrade_summary.Balance.values[np.isfinite(raw_livetrade_summary.Balance.values)][0]
                
            if self.data_file is not None:
                custom_data_file        = self.data_file
                custom_data_filepath    = os.path.join(price_data_path,
                                                       custom_data_file)
                if int(self.verbosity) > 1:
                    print("Using data file specified ({}).".format(custom_data_file))
                data            = pd.read_csv(custom_data_filepath, 
                                              index_col = 0)
                data.index = pd.to_datetime(data.index)
                quote_data = data
                
            else:
                if int(self.verbosity) > 1:
                    print("\nDownloading OHLC price data for {}.".format(instrument))
                
                if self.optimise is True:
                    # Check if historical data already exists
                    historical_data_name = 'hist_{0}{1}.csv'.format(interval, instrument)
                    historical_quote_data_name = 'hist_{0}{1}_quote.csv'.format(interval, instrument)
                    data_dir_path = os.path.join(self.home_dir, 'price_data')
                    historical_data_file_path = os.path.join(self.home_dir, 
                                                             'price_data',
                                                             historical_data_name)
                    historical_quote_data_file_path = os.path.join(self.home_dir, 
                                                             'price_data',
                                                             historical_quote_data_name)
                    
                    if not os.path.exists(historical_data_file_path):
                        # Data file does not yet exist
                        data        = getattr(self.get_data, feed.lower())(instrument,
                                                         granularity = interval,
                                                         start_time = from_date,
                                                         end_time = to_date)
                        quote_data  = getattr(self.get_data, feed.lower() + '_quote_data')(data,
                                                                                      instrument,
                                                                                      interval,
                                                                                      from_date,
                                                                                      to_date)
                        data, quote_data    = self.broker_utils.check_dataframes(data, quote_data)
                        
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
                    data        = getattr(self.get_data, feed.lower())(instrument,
                                                         granularity = interval,
                                                         start_time = from_date,
                                                         end_time = to_date)
                    quote_data  = getattr(self.get_data, feed.lower() + '_quote_data')(data,
                                                                    instrument,
                                                                    interval,
                                                                    from_date,
                                                                    to_date)
                    
                    data, quote_data    = self.broker_utils.check_dataframes(data, quote_data)
                
                
                if int(self.verbosity) > 1:
                    print("  Done.\n")
            
            return data, quote_data
            
        else:
            # Running in livetrade mode
            data = getattr(self.get_data, feed.lower())(instrument,
                                                         granularity = interval,
                                                         count=period)
            
            data = self.verify_data_alignment(data, instrument, feed, period, price_data_path)
        
            return data, None

    def verify_data_alignment(self, data, instrument, feed, period, price_data_path):
    
        interval = self.strategy_params['granularity']
        
        # Check data time alignment
        current_time        = datetime.now(tz=pytz.utc)
        last_candle_closed  = self.broker_utils.last_period(current_time, interval)
        data_ts             = data.index[-1].to_pydatetime().timestamp()
        
        if data_ts != last_candle_closed.timestamp():
            # Time misalignment detected - attempt to correct
            count = 0
            while data_ts != last_candle_closed.timestamp():
                print("  Time misalginment detected at {}".format(datetime.now().strftime("%H:%M:%S")),
                      "({}/{}).".format(data.index[-1].minute, last_candle_closed.minute),
                      "Trying again...")
                time.sleep(3) # wait 3 seconds...
                data    = getattr(self.get_data, feed.lower())(instrument,
                                    granularity = interval,
                                    count=period)
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
                            data    = self.broker_utils.update_data_with_candle(data, latest_candle)
                            data_ts = data.index[-1].to_pydatetime().timestamp()
                            print("  Data updated using price stream.")
            
            # if data is still misaligned, perform manual adjustment.
            if data_ts != last_candle_closed.timestamp():
                print("  Could not retrieve updated data. Aborting.")
                sys.exit(0)
        
        return data
    
    def assign_broker(self, broker_config, config):
        if self.backtest is True:
                utils_module    = importlib.import_module('autotrader.brokers.virtual.utils')
                
                utils           = utils_module.Utils()
                broker          = Broker(broker_config, utils)
                
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
                self.get_data.base_currency = base_currency
                
                if int(self.verbosity) > 0:
                    banner = pyfiglet.figlet_format("AutoBacktest")
                    print(banner)
                
                if self.validation_file is not None:
                    # Also get broker-specific utility functions
                    validation_utils = importlib.import_module('autotrader.brokers.{}.utils'.format(config['FEED'].lower()))
                    
                    # Correct watchlist
                    if self.instruments is None:
                        self.watchlist = validation_utils.format_watchlist(self.raw_watchlist)
                
        else:
            utils_module    = importlib.import_module('autotrader.brokers.{}.utils'.format(config['FEED'].lower()))
            utils           = utils_module.Utils()
            broker          = Oanda.Oanda(broker_config, utils)
        
        self.broker = broker
        self.broker_utils = utils
    
    
    def configure_emailing(self, config, global_config):
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
                
            order_summary_fp = os.path.join(self.home_dir, 'logfiles/order_history.txt')
            
            email_params = {'mailing_list': mailing_list,
                            'host_email': host_email}
            self.email_params = email_params
            self.order_summary_fp = order_summary_fp
    
    
    def get_iteration_range(self, data):
        
        if self.backtest:
            start_range         = 0
        else:
            start_range         = len(data)-1
        
        end_range           = len(data)

        return start_range, end_range


    def extract_backtest_results(self, trade_summary, broker, starting_balance, 
                                 utils):
        '''
        Analyses backtest summary to extract key statistics.
        '''
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
        backtest_results['no_open'] = len(broker.open_positions)
        backtest_results['no_cancelled'] = len(cancelled_orders)
        
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
        
        # Save results
        self.backtest_results = backtest_results
        
        return backtest_results
    
    def print_backtest_results(self, backtest_results):
        params      = self.strategy_params
        no_trades   = backtest_results['no_trades']
        win_rate    = backtest_results['all_trades']['win_rate']
        profit_abs  = backtest_results['all_trades']['profit_abs']
        profit_pc   = backtest_results['all_trades']['profit_pc']
        MDD         = backtest_results['all_trades']['MDD']
        max_win     = backtest_results['all_trades']['max_win']
        avg_win     = backtest_results['all_trades']['avg_win']
        max_loss    = backtest_results['all_trades']['max_loss']
        avg_loss    = backtest_results['all_trades']['avg_loss']
        longest_win_streak = backtest_results['all_trades']['win_streak']
        longest_lose_streak = backtest_results['all_trades']['lose_streak']
        
        print("\n-------------------------------------------")
        print("            Backtest Results")
        print("-------------------------------------------")
        print("Strategy: {}".format(self.strategy.name))
        print("Timeframe:               {}".format(params['granularity']))
        if params is not None and 'RR' in params:
            print("Risk to reward ratio:    {}".format(params['RR']))
            print("Profitable win rate:     {}%".format(round(100/(1+params['RR']), 1)))
        if no_trades > 0:
            print("Backtest win rate:       {}%".format(round(win_rate, 1)))
            
            print("Total no. trades:        {}".format(self.broker.total_trades))
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
        
        no_open = backtest_results['no_open']
        no_cancelled = backtest_results['no_cancelled']
        
        if no_open > 0:
            print("Orders still open:       {}".format(no_open))
        if no_cancelled > 0:
            print("Cancelled orders:        {}".format(no_cancelled))
        
        
        # Long trades
        no_long = backtest_results['long_trades']['no_trades']
        print("\n         Summary of long trades")
        print("-------------------------------------------")
        if no_long > 0:
            avg_long_win = backtest_results['long_trades']['avg_long_win']
            max_long_win = backtest_results['long_trades']['max_long_win']
            avg_long_loss = backtest_results['long_trades']['avg_long_loss']
            max_long_loss = backtest_results['long_trades']['max_long_loss']
            long_wr = backtest_results['long_trades']['long_wr']
            
            print("Number of long trades:   {}".format(no_long))
            print("Long win rate:           {}%".format(round(long_wr, 1)))
            print("Max win:                 ${}".format(round(max_long_win, 2)))
            print("Average win:             ${}".format(round(avg_long_win, 2)))
            print("Max loss:                -${}".format(round(max_long_loss, 2)))
            print("Average loss:            -${}".format(round(avg_long_loss, 2)))
        else:
            print("There were no long trades.")
          
        # Short trades
        no_short = backtest_results['short_trades']['no_trades']
        print("\n          Summary of short trades")
        print("-------------------------------------------")
        if no_short > 0:
            avg_short_win = backtest_results['short_trades']['avg_short_win']
            max_short_win = backtest_results['short_trades']['max_short_win']
            avg_short_loss = backtest_results['short_trades']['avg_short_loss']
            max_short_loss = backtest_results['short_trades']['max_short_loss']
            short_wr = backtest_results['short_trades']['short_wr']
            
            print("Number of short trades:  {}".format(no_short))
            print("short win rate:          {}%".format(round(short_wr, 1)))
            print("Max win:                 ${}".format(round(max_short_win, 2)))
            print("Average win:             ${}".format(round(avg_short_win, 2)))
            print("Max loss:                -${}".format(round(max_short_loss, 2)))
            print("Average loss:            -${}".format(round(avg_short_loss, 2)))
            
        else:
            print("There were no short trades.")

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


class AutoTraderBot:
    '''
    AutoTrader Bot.
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
                print("Order placed.")
            else:
                print("No signal detected.")
        
        # Check for orders placed and/or scan hits
        if int(self.notify) > 0:
            
            for order_details in self.latest_orders:
                self.broker_utils.write_to_order_summary(order_details, 
                                                         self.order_summary_fp)
            
            if int(self.notify) > 1 and \
                self.email_params['mailing_list'] is not None and \
                self.email_params['host_email'] is not None:
                    if int(self.verbosity) > 0:
                            print("Sending email...")
                            
                    for order_details in self.latest_orders:
                        emailing.send_order(order_details,
                                            self.email_params['mailing_list'],
                                            self.email_params['host_email'])
                        
                    if int(self.verbosity) > 0:
                            print("  Done.")
            
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
