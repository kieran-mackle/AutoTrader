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
                             Version 0.2.7
                             
"""

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
from autotrader.brokers.oanda import Oanda
from autotrader.brokers.virtual.virtual_broker import Broker
from autotrader.lib import instrument_list, environment_manager, autodata, printout
from autotrader import autoplot
from autotrader.autobot import AutoTraderBot


class AutoTrader():
    """
    AutoTrader: A Python-Based Development Platform For Automated Trading Systems.

    Attributes
    ----------
    config_file : str
        The strategy configuration file.
    
    verbosity : int
        The code verbosity.
    
    notify : int
         The emailing verbosity of the code.
    

    Methods
    -------
    run():
        Runs AutoTrader.
    
    plot_backtest(bot=None, validation_file=None):
        Plots backtest results of an AutoTrader Bot.
    
    """
    
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
        
        self.config         = None
        self.broker         = None
        self.broker_utils   = None
        self.email_params   = None
        self.strategy       = None
        self.strategy_params = None
        self.get_data       = None
        self.bots_deployed  = []
        
        self.scan_results = {}
        self.order_summary_fp = None
        
        # Backtesting Parameters
        self.data_start = None
        self.data_end   = None
        self.backtest_initial_balance = None
        self.backtest_spread = None
        self.backtest_commission = None
        self.backtest_leverage = None
        self.backtest_base_currency = None
        
        
    def run(self):
        if self.show_help is not None:
            printout.option_help(self.show_help)
        
        if self.config_file is None and self.backtest is False:
            printout.usage()
        else:
            self.main()
    
    def usage(self):
        '''
        Prints usage instructions for AutoTrader.
        '''
        printout.usage()
    
    def option_help(self, option):
        '''
        Prints help for a user option of AutoTrader.
        
            Parameters:
                option (str): user option to request help for.
        '''
        printout.option_help(option)
        
    def main(self):
        '''
        Main run file of autotrader.py. This method is called internally 
        from the "run" method.
        '''
        
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
        # self.config         = config
        # interval            = config["STRATEGY"]["INTERVAL"]
        # period              = config["STRATEGY"]["PERIOD"]
        # params              = config["STRATEGY"]["PARAMETERS"]
        # risk_pc             = config["STRATEGY"]["RISK_PC"]
        # sizing              = config["STRATEGY"]["SIZING"]
        # strat_module        = config["STRATEGY"]["MODULE"]
        # strat_name          = config["STRATEGY"]["NAME"]
        # environment         = config["ENVIRONMENT"]
        # feed                = config["FEED"]
        
        # strategy_params                 = params
        # strategy_params['granularity']  = interval
        # strategy_params['risk_pc']      = risk_pc
        # strategy_params['sizing']       = sizing
        # strategy_params['period']       = period
        # self.strategy_params            = strategy_params
        
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
        
        # strat_package_path  = os.path.join(self.home_dir, "strategies")
        # strat_module_path   = os.path.join(strat_package_path, strat_module) + '.py'
        # strat_spec          = importlib.util.spec_from_file_location(strat_module, strat_module_path)
        # strategy_module     = importlib.util.module_from_spec(strat_spec)
        # strat_spec.loader.exec_module(strategy_module)
        # strategy            = getattr(strategy_module, strat_name)
        
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
        # There will be a bot assigned for every unique strategy/instrument pair
        # One strategy trading 4 instruments -> 4 bots
        # Two strategies trading 4 instruments each -> 8 bots
        
        # for instrument in self.watchlist:
            # Get price history
            # data, quote_data = self.retrieve_data(instrument, price_data_path, feed)
            
            # Instantiate strategy for current instrument
            # my_strat        = strategy(params, data, instrument)
            # self.strategy   = my_strat
            
            # if self.include_broker:
            #     my_strat.broker = self.broker
            #     my_strat.broker_utils = self.broker_utils
            
            # Create new bot for each instrument in watchlist
            # bot = AutoTraderBot(self.broker, my_strat, instrument, data, self)
            
            # if self.backtest:
            #     bot.quote_data = quote_data
            
            # self.bots_deployed.append(bot)
            

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
                    ap.data = bot.data
                    ap.plot_multibot_backtest(self.multibot_backtest_results, 
                                              NAV,
                                              cpl_dict)

    
    
    def configure_backtest(self, start=None, end=None, initial_balance=1000,
                           spread=0, commission=0, leverage=1, base_currency='AUD',
                           start_dt=None, end_dt=None):
        '''
        Configures settings for backtesting.
        
            Parameters:
                start (str): start date for backtesting, in format d/m/yyyy.
                
                end (str): end date for backtesting, in format d/m/yyyy.
                
                initial_balance (float): initial account balance in base currency 
                units.
                
                spread (float): bid/ask spread of instrument.
                
                commission (float): trading commission as percentage per trade.
                
                leverage (int): account leverage.
                
                base_currency (str): base currency of account.
                
                start_dt (datetime): datetime object corresponding to start time.
                
                end_dt (datetime): datetime object corresponding to end time.
                
            Note: 
                Start and end times must be specified as the same type. For
                example, both start and end arguments must be provided together, 
                or alternatively, start_dt and end_dt must both be provided.
        '''
        
        # Convert start and end strings to datetime objects
        if start_dt is None and end_dt is None:
            start_dt    = datetime.strptime(start + '+0000', '%d/%m/%Y%z')
            end_dt      = datetime.strptime(end + '+0000', '%d/%m/%Y%z')
        
        # Assign attributes
        self.data_start = start_dt
        self.data_end   = end_dt
        self.backtest_initial_balance = initial_balance
        self.backtest_spread = spread
        self.backtest_commission = commission
        self.backtest_leverage = leverage
        self.backtest_base_currency = base_currency
    
    
    def plot_backtest(self, bot=None, validation_file=None):
        '''
        Plots backtest results of an AutoTrader Bot.
            
            Parameters:
                bot (class): AutoTrader bot class containing backtest results.
                
                validation_file (str): filepath of backtest validation file.
        '''
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
        print(backtest_results[['win_rate', 'no_trades']])
        print("\nMaximum/Average Win/Loss breakdown ($):")
        print(backtest_results[["max_win", "max_loss", "avg_win", "avg_loss"]])
        print("\nAverage Reward to Risk Ratio:")
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



if __name__ == '__main__':
    autotrader = AutoTrader()
    autotrader.usage()
