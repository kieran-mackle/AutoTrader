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
"""

from datetime import datetime, timedelta
import sys
import os
import pyfiglet
import importlib
import numpy as np
import pandas as pd
import timeit
from scipy.optimize import brute
from ast import literal_eval
from autotrader.brokers.oanda import Oanda
from autotrader.brokers.virtual.virtual_broker import Broker
from autotrader.lib import instrument_list, environment_manager, printout
from autotrader.lib.read_yaml import read_yaml
from autotrader import autoplot
from autotrader.autobot import AutoTraderBot
from autotrader.lib.bot_manager import ManageBot


class AutoTrader():
    """
    AutoTrader: A Python-Based Development Platform For Automated Trading Systems.
    ------------------------------------------------------------------------------
    Website: https://kieran-mackle.github.io/AutoTrader/
    
    GitHub: https://github.com/kieran-mackle/AutoTrader
    
    Author: Kieran Mackle
    
    Version: 0.4.x

    Attributes
    ----------
    Note: many of the following attributes are set from the configure method of AutoTrader.
    
    feed : str 
        The data feed to be used (eg. Yahoo, Oanda).
                
    verbosity : int
        The verbosity of AutoTrader (0, 1 or 2).
    
    notify : int
        The level of email notification (0, 1 or 2).
    
    home_dir : str 
        The project home directory.
    
    use_stream : bool 
        Set to True to use price stream as data feed.
    
    detach_bot : bool 
        Set to True to spawn new thread for each bot deployed. Bots will then
        continue to trade until a termination signal is recieved from the strategy.
    
    check_data_alignment : bool
        Verify time of latest candle in data recieved against current time.
    
    allow_dancing_bears : bool
        Allow incomplete candles to be passed to strategy.
    
    account_id : str
        The brokerage account ID to use in this instance.
    
    environment : str
        The trading environment of this instance.
    
    show_plot : bool
        Automatically display plot of results.
    
    MTF_initialisation : bool
        Only download mutliple time frame data when initialising the strategy, 
        rather than every update.


    Methods
    -------
    run():
        Runs AutoTrader.
    
    configure(feed='yahoo', verbosity=1, notify=0, home_dir=None,
              use_stream=False, detach_bot=False,
              check_data_alignment=True, allow_dancing_bears=False,
              account_id=None, environment='demo', show_plot=False,
              MTF_initialisation=False):
        Configures various run settings for AutoTrader.
    
    add_strategy(strategy_filename=None, strategy_dict=None)
        Adds a strategy to AutoTrader. 
    
    plot_backtest(bot=None):
        Plots backtest results of an AutoTrader Bot.
    
    """
    
    def __init__(self):
        '''
        AutoTrader initialisation. Called when creating new AutoTrader instance.
        '''
        
        self.home_dir       = None
        self.order_summary_fp = None
        
        self.verbosity      = 1
        self.notify         = 0
        self.email_params   = None
        self.show_help      = None
        self.show_plot      = False
        
        # Livetrade Parameters
        self.detach_bot     = False
        self.check_data_alignment = True
        self.allow_dancing_bears = False
        self.use_stream     = False
        self.MTF_initialisation = False
        self.stream_config  = None
        
        self.broker         = None
        self.broker_utils   = None
        self.environment    = 'demo'
        self.account_id     = None
        
        self.strategies     = {}
        self._uninitiated_strat_files = []
        self._uninitiated_strat_dicts = []
        self.feed           = 'yahoo'
        self.bots_deployed  = []
        
        # Backtesting Parameters
        self.backtest_mode = False
        self.data_start = None
        self.data_end   = None
        self.data_file  = None
        self.backtest_initial_balance = None
        self.backtest_spread = None
        self.backtest_commission = None
        self.backtest_leverage = None
        self.backtest_base_currency = None
        
        # Optimisation Parameters
        self.optimisation_config = None
        self.optimise_mode = False
        self.opt_params = None
        self.bounds = None
        self.Ns = None
        
        # Scan Parameters
        self.scan_mode = False
        self.scan_index = None
        self.scan_results = {}
        
        
    def run(self):
        '''
        Run AutoTrader.
        '''
        
        # Define home_dir if undefined
        if self.home_dir is None:
            self.home_dir = os.getcwd()
        
        # Load uninitiated strategies
        for strat_dict in self._uninitiated_strat_dicts:
            self.add_strategy(strategy_dict=strat_dict)
        for strat_config_file in self._uninitiated_strat_files:
            self.add_strategy(strategy_filename=strat_config_file)
        
        # Print help
        if self.show_help is not None:
            printout.option_help(self.show_help)
        
        if len(self.strategies) == 0:
            print("Error: no strategy has been provided. Do so by using the" +\
                  " 'add_strategy' method of AutoTrader.")
            sys.exit(0)
            
        if sum([self.backtest_mode, self.scan_mode]) > 1:
            print("Error: backtest mode and scan mode are both set to True," +\
                  " but only one of these can run at a time.")
            print("Please check your inputs and try again.")
            sys.exit(0)
        
        if self.backtest_mode:
            if self.notify > 0:
                print("Warning: notify set to {} ".format(self.notify) + \
                      "during backtest. Setting to zero to prevent emails.")
                self.notify = 0
        
        if self.optimise_mode:
            if self.backtest_mode:
                self._run_optimise()
            else:
                print("Please set backtest parameters to run optimisation.")
        else:
            self._main()
    
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
        
    def _main(self):
        '''
        Main run file of autotrader.py. This method is called internally 
        from the "run" method.
        '''
        
        ''' -------------------------------------------------------------- '''
        '''                         Load configuration                     '''
        ''' -------------------------------------------------------------- '''
        # Construct broker config
        global_config_fp = os.path.join(self.home_dir, 'config', 'GLOBAL.yaml')
        if os.path.isfile(global_config_fp):
            global_config = read_yaml(global_config_fp)
        else:
            global_config = None
        broker_config = environment_manager.get_config(self.environment,
                                                       global_config,
                                                       self.feed)
        
        # Construct stream_config dict
        if self.use_stream:
            self.stream_config = broker_config
        
        if self.account_id is not None:
            # Overwrite default account in global config
            broker_config['ACCOUNT_ID'] = self.account_id
        
        self._assign_broker(broker_config)
        self._configure_emailing(global_config)
        
        if self.backtest_mode:
            starting_balance = self.broker.get_balance()
            NAV     = []
            balance = []
            margin  = []
        
        if int(self.verbosity) > 0:
            if self.backtest_mode:
                print("Beginning new backtest.")
                print("  From: ", datetime.strftime(self.data_start,'%d/%m/%Y %H:%M'))
                print("  To:   ", datetime.strftime(self.data_end,'%d/%m/%Y %H:%M'))
                # print("  Instruments: ", self.watchlist)
            elif self.scan_mode:
                print("AutoScan:")
                print("Time: {}".format(datetime.now().strftime("%A, %B %d %Y, "+
                                                                  "%H:%M:%S")))
            else:
                print("AutoTrader Livetrade")
                print("--------------------")
                print("Time: {}\n".format(datetime.now().strftime("%A, %B %d %Y, "+
                                                                  "%H:%M:%S")))
        
        ''' -------------------------------------------------------------- '''
        '''    Assign strategy to bot for each instrument in watchlist     '''
        ''' -------------------------------------------------------------- '''
        for strategy in self.strategies:
            for instrument in self.strategies[strategy]['WATCHLIST']:
                bot = AutoTraderBot(instrument, self.strategies[strategy],
                                        self.broker, self)
                
                if self.detach_bot is True and self.backtest_mode is False:
                    # Send bot to bot manager to monitor stream
                    print("Passing bot to bot manager...")
                    bot_name_string = "{}_{}_{}".format(strategy.replace(' ',''),
                                                        self.strategies[strategy]['INTERVAL'].split(',')[0],
                                                        instrument)
                    ManageBot(bot, self.home_dir, bot_name_string, self.use_stream)
                else:
                    self.bots_deployed.append(bot)
                    
        
        ''' -------------------------------------------------------------- '''
        '''                  Analyse price data using strategy             '''
        ''' -------------------------------------------------------------- '''
        if int(self.verbosity) > 0 and self.backtest_mode:
            print("\nTrading...")
        
        # TODO - add check that data ranges are consistent across bots
        # For now, assume correct and use first bot.
        if not self.detach_bot:
            start_range, end_range = self.bots_deployed[0]._get_iteration_range()
            for i in range(start_range, end_range):
                
                # Update each bot with latest data to generate signal
                for bot in self.bots_deployed:
                    bot._update(i)
                    
                    # If backtesting, update virtual broker with latest data
                    if self.backtest_mode:
                        bot._update_backtest(i)
                
                if self.backtest_mode is True:
                    NAV.append(self.broker.NAV)
                    balance.append(self.broker.portfolio_balance)
                    margin.append(self.broker.margin_available)
        
        ''' -------------------------------------------------------------- '''
        '''                     Backtest Post-Processing                   '''
        ''' -------------------------------------------------------------- '''
        # Data iteration complete - proceed to post-processing
        if self.backtest_mode is True:
            # Create backtest summary for each bot 
            for bot in self.bots_deployed:
                bot.create_backtest_summary(balance, NAV, margin)            
            
            if int(self.verbosity) > 0:
                print("\nBacktest complete.")
                if len(self.bots_deployed) == 1:
                    bot = self.bots_deployed[0]
                    trade_summary = bot.backtest_summary['trade_summary']
                    backtest_results = self.extract_backtest_results(trade_summary, 
                             self.broker, starting_balance, self.broker_utils) 
                    self.print_backtest_results(backtest_results)
                    
                else:
                    self.multibot_backtest_results = self.multibot_backtest_analysis()
                    self.print_multibot_backtest_results(self.multibot_backtest_results)
                    
                    print("Results for multiple-instrument backtests have been")
                    print("written to AutoTrader.multibot_backtest_results.")
                    print("Individual bot results can be found in AutoTrader.bots_deployed.")
            
            if self.show_plot:
                if len(self.bots_deployed) == 1:
                    if len(self.bots_deployed[0].backtest_summary['trade_summary']) > 0:
                        self.plot_backtest(bot=self.bots_deployed[0])
                
                else:
                    # Backtest run with multiple bots
                    cpl_dict = {}
                    for bot in self.bots_deployed:
                        
                        profit_df = pd.merge(bot.data, 
                                 bot.backtest_summary['trade_summary']['Profit'], 
                                 left_index=True, right_index=True).Profit.cumsum()
                        cpl_dict[bot.instrument] = profit_df
                    
                    ap = autoplot.AutoPlot(bot.data)
                    ap._plot_multibot_backtest(self.multibot_backtest_results, 
                                              NAV,
                                              cpl_dict)

    def _clear_strategies(self):
        '''
        Removes all strategies saved in autotrader instance.
        '''
        
        self.strategies = {}
    
    def _clear_bots(self):
        '''
        Removes all deployed bots in autotrader instance.
        '''
        
        self.bots_deployed = []
        
    
    def add_strategy(self, strategy_filename=None, 
                     strategy_dict=None):
        '''
        Adds a strategy to AutoTrader. 
        
            Parameters:
                strategy_filename (str): prefix of yaml strategy
                configuration file, located in home_dir/config.
                
                strategy_dict (dict): alternative to strategy_filename,
                the strategy dictionary can be passed directly.
        '''
        
        if self.home_dir is None:
            # Home directory has not yet been set, postpone strategy addition
            if strategy_filename is None:
                self._uninitiated_strat_dicts.append(strategy_dict)
            else:
                self._uninitiated_strat_files.append(strategy_filename)
            
        else:
            if strategy_dict is None:
                config_file_path = os.path.join(self.home_dir, 'config', strategy_filename)
                new_strategy = read_yaml(config_file_path + '.yaml')
            else:
                new_strategy = strategy_dict
            
            name = new_strategy['NAME']
            
            if name in self.strategies:
                print("Warning: duplicate strategy name deteced. Please check " + \
                      "the NAME field of your strategy configuration file and " + \
                      "make sure it is not the same as other strategies being " + \
                      "run from this instance.")
                print("Conflicting name:", name)
            
            self.strategies[name] = new_strategy
    
    
    def backtest(self, start=None, end=None, initial_balance=1000, spread=0, 
                 commission=0, leverage=1, base_currency='AUD', start_dt=None, 
                 end_dt=None):
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
        self.backtest_mode = True
        self.data_start = start_dt
        self.data_end   = end_dt
        self.backtest_initial_balance = initial_balance
        self.backtest_spread = spread
        self.backtest_commission = commission
        self.backtest_leverage = leverage
        self.backtest_base_currency = base_currency
    
    
    def configure(self, feed='yahoo', verbosity=1, notify=0, home_dir=None,
                  use_stream=False, detach_bot=False,
                  check_data_alignment=True, allow_dancing_bears=False,
                  account_id=None, environment='demo', show_plot=False,
                  MTF_initialisation=False):
        '''
        AutoTrader Run Configuration
        -------------------------------
        
        Configures various run settings for AutoTrader.
        
            Parameters:
                feed (str): the data feed to be used (eg. Yahoo, Oanda).
                
                verbosity (int): the verbosity of AutoTrader (0, 1 or 2).
                
                notify (int): the level of email notification (0, 1 or 2).
                
                home_dir (str): the project home directory.
                
                use_stream (bool): set to True to use price stream as data feed.
                
                detach_bot (bool): set to True to spawn new thread for each bot
                deployed.
                
                check_data_alignment (bool): verify time of latest candle in
                data recieved against current time.
                
                allow_dancing_bears (bool): allow incomplete candles to be 
                passed to strategy.
                
                account_id (str): the brokerage account ID to use in this instance.
                
                environment (str): the trading environment of this instance.
                
                show_plot (bool): automatically display plot of results.
                
                MTF_initialisation (bool): only download mutliple time frame 
                data when initialising the strategy, rather than every update.
        '''
        
        self.feed = feed
        self.verbosity = verbosity
        self.notify = notify
        self.home_dir = home_dir if home_dir is not None else os.getcwd()
        self.use_stream = use_stream
        self.detach_bot = detach_bot
        self.check_data_alignment = check_data_alignment
        self.allow_dancing_bears = allow_dancing_bears
        self.account_id = account_id
        self.environment = environment
        self.show_plot = show_plot
        self.MTF_initialisation = MTF_initialisation
        
    
    def scan(self, scan_index=None):
        '''
        Configure AutoTrader scan. 
            
            Parameters:
                scan_index (str): index to scan.
        '''
        
        # If scan index provided, use that. Else, use strategy watchlist
        if scan_index is not None:
            scan_watchlist = instrument_list.get_watchlist(scan_index)
            
            # Update strategy watchlist
            for strategy in self.strategies:
                self.strategies[strategy]['WATCHLIST'] = scan_watchlist
        else:
            scan_index = 'Strategy watchlist'
            
        
        self.scan_mode = True
        self.scan_index = scan_index
    
    
    def plot_backtest(self, bot=None):
        '''
        Plots backtest results of an AutoTrader Bot.
            
            Parameters:
                bot (class): AutoTrader bot class containing backtest results.
        '''
        ap = autoplot.AutoPlot(bot.data)
        profit_df = pd.merge(bot.data, 
                             bot.backtest_summary['trade_summary']['Profit'], 
                             left_index=True, right_index=True).Profit.cumsum()
        
        ap.plot(bot.backtest_summary, cumulative_PL=profit_df)
                
    
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
            no_trades.append(backtest_results['no_trades'])
            if backtest_results['no_trades'] > 0:
                win_rate.append(backtest_results['all_trades']['win_rate'])
                avg_win.append(backtest_results['all_trades']['avg_win'])
                max_win.append(backtest_results['all_trades']['max_win'])
                avg_loss.append(backtest_results['all_trades']['avg_loss'])
                max_loss.append(backtest_results['all_trades']['max_loss'])
                no_long.append(backtest_results['long_trades']['no_trades'])
                no_short.append(backtest_results['short_trades']['no_trades'])
            else:
                win_rate.append(np.nan)
                avg_win.append(np.nan)
                max_win.append(np.nan)
                avg_loss.append(np.nan)
                max_loss.append(np.nan)
                no_long.append(np.nan)
                no_short.append(np.nan)
            
        
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
        print("Final NAV:           ${}".format(round(self.broker.NAV, 2)))
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
        
    
    def _assign_broker(self, broker_config):
        '''
        Configures and assigns appropriate broker for trading.
        '''
        
        if self.backtest_mode is True:
                utils_module    = importlib.import_module('autotrader.brokers.virtual.utils')
                
                utils           = utils_module.Utils()
                broker          = Broker(broker_config, utils)
                
                initial_deposit = self.backtest_initial_balance
                spread          = self.backtest_spread
                leverage        = self.backtest_leverage
                commission      = self.backtest_commission
                base_currency   = self.backtest_base_currency
                
                broker.make_deposit(initial_deposit)
                broker.fee      = spread
                broker.leverage = leverage
                broker.commission = commission
                broker.spread   = spread
                broker.base_currency = base_currency
                # self.get_data.base_currency = base_currency
                
                if int(self.verbosity) > 0:
                    banner = pyfiglet.figlet_format("AutoBacktest")
                    print(banner)
                
                
        else:
            utils_module    = importlib.import_module('autotrader.brokers.{}.utils'.format(self.feed.lower()))
            utils           = utils_module.Utils()
            broker          = Oanda.Oanda(broker_config, utils)
        
        self.broker = broker
        self.broker_utils = utils
    
    
    def _configure_emailing(self, global_config):
        '''
        Configure email settings.
        '''
        
        # TODO - allow setting email in this method
        
        if int(self.notify) > 0:
            host_email      = None
            mailing_list    = None
            
            # TODO - what if no email provided?
            
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
                
            email_params = {'mailing_list': mailing_list,
                            'host_email': host_email}
            self.email_params = email_params
            
            logfiles_path = os.path.join(self.home_dir, 'logfiles')
            order_summary_fp = os.path.join(logfiles_path, 'order_history.txt')
            
            if not os.path.isdir(logfiles_path):
                os.mkdir(logfiles_path)
            
            self.order_summary_fp = order_summary_fp


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
        # params      = self.strategy_params
        no_trades   = backtest_results['no_trades']
        if no_trades > 0:
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
        # TODO - the below are all strategy specific. Maybe if only one strategy
        # is used (ie len(self.strategies) = 1), that can be used. Otherwise,
        # not sure. However, the granularity has to be the same ... until 
        # time indexing becomes a thing
        # print("Strategy: {}".format(self.strategy.name))
        # print("Timeframe:               {}".format(params['granularity']))
        # if params is not None and 'RR' in params:
        #     print("Risk to reward ratio:    {}".format(params['RR']))
        #     print("Profitable win rate:     {}%".format(round(100/(1+params['RR']), 1)))
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


    def optimise(self, opt_params, bounds, Ns=4):
        '''
        Optimisation configuration.
        
            Parameters: 
                opt_params (list): the parameters to be optimised, as they 
                are named in the strategy configuration file.
                
                bounds (list of tuples): the bounds on each of the 
                parameters to be optimised, specified as a tuple of the form
                (lower, upper) for each parameter.
                
                Ns (int): the number of points along each dimension of the 
                optimisation grid.
                
        '''
        
        if type(bounds) == str:
            full_tuple = literal_eval(bounds)
            bounds = [(x[0], x[-1]) for x in full_tuple]

        if type(opt_params) == str:
            opt_params = opt_params.split(',')
        
        self.optimise_mode = True
        self.opt_params = opt_params
        self.bounds = bounds
        self.Ns = Ns
        
        
    def _run_optimise(self):
        '''
        Runs optimisation of strategy parameters.
        '''
        
        # Modify verbosity for optimisation
        verbosity = self.verbosity
        self.verbosity = 0
        self.show_plot = False
        
        self.objective      = 'profit + MDD'
        
        ''' --------------------------------------------------------------- '''
        '''                          Unpack user options                    '''
        ''' --------------------------------------------------------------- '''
        
        # Look in self.strategies for config
        if len(self.strategies) > 1:
            print("Error: please optimise one strategy at a time.")
            print("Exiting.")
            sys.exit(0)
        else:
            config_dict = self.strategies[list(self.strategies.keys())[0]]
                
        ''' --------------------------------------------------------------- '''
        '''                      Define optimisation inputs                 '''
        ''' --------------------------------------------------------------- '''
        my_args     = (config_dict, self.opt_params, self.verbosity)
        
        ''' --------------------------------------------------------------- '''
        '''                             Run Optimiser                       '''
        ''' --------------------------------------------------------------- '''
        start = timeit.default_timer()
        result = brute(func         = self._optimisation_helper_function, 
                       ranges       = self.bounds, 
                       args         = my_args, 
                       Ns           = self.Ns,
                       full_output  = True)
        stop = timeit.default_timer()
        
        ''' --------------------------------------------------------------- '''
        '''      Delete historical data file after running optimisation     '''
        ''' --------------------------------------------------------------- '''
        granularity             = config_dict["INTERVAL"]
        pair                    = config_dict["WATCHLIST"][0]
        historical_data_name    = 'hist_{0}{1}.csv'.format(granularity, pair)
        historical_quote_data_name = 'hist_{0}{1}_quote.csv'.format(granularity, pair)
        historical_data_file_path = os.path.join(self.home_dir, 
                                                 'price_data',
                                                 historical_data_name)
        historical_quote_data_file_path = os.path.join(self.home_dir, 
                                                       'price_data',
                                                       historical_quote_data_name)
        os.remove(historical_data_file_path)
        os.remove(historical_quote_data_file_path)
        
        opt_params = result[0]
        opt_value = result[1]
        
        # TODO - use the below for heatmap plotting
        # grid_points = result[2]
        # grid_values = result[3]
        
        ''' --------------------------------------------------------------- '''
        '''                           Print output                          '''
        ''' --------------------------------------------------------------- '''
        print("\nOptimisation complete.")
        print('Time to run: {}s'.format(round((stop - start), 3)))
        print("Optimal parameters:")
        print(opt_params)
        print("Objective:")
        print(opt_value)
        
        # Reset verbosity
        self.verbosity = verbosity
    
    
    def _optimisation_helper_function(self, params, config_dict, opt_params, verbosity):
        '''
        Helper function for optimising strategy parameters in AutoTrader.
        This function will parse the ordered params into the config dict.
        
        '''
        
        ''' ------------------------------------------------------------------ '''
        '''   Edit strategy parameters in config_dict using supplied params    '''
        ''' ------------------------------------------------------------------ '''
        for parameter in config_dict['PARAMETERS']:
            if parameter in opt_params:
                config_dict['PARAMETERS'][parameter] = params[opt_params.index(parameter)]
            else:
                continue
        
        ''' ------------------------------------------------------------------ '''
        '''           Run AutoTrader and evaluate objective function           '''
        ''' ------------------------------------------------------------------ '''
        self._clear_strategies()
        self._clear_bots()
        self.add_strategy(strategy_dict = config_dict)
        self._main()
        
        bot = self.bots_deployed[0]
        
            
        backtest_results    = self.analyse_backtest(bot.backtest_summary)
        
        try:
            objective           = -backtest_results['all_trades']['net_pl']
        except:
            objective           = 1000
                              
        print("Parameters/objective:", params, "/", objective)
        
        return objective
    
    

if __name__ == '__main__':
    autotrader = AutoTrader()
    autotrader.usage()
