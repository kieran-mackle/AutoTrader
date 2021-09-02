#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTrader Help
"""

import pyfiglet

def usage():
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
    print("Attribute                           Comment")
    print("--------------------------------------------------------------" \
          + "---------------")
    print("Required:")
    print("  config (str)                       filename of config file")
    print("\nOptional:")
    print("  help                               show help for usage")
    print("  verbosity (int)                    set verbosity (0,1,2)")
    print("  backtest                           run in backtesting mode")
    print("  plot                               plot results of backtest")
    print("  notify (int)                       notify by email when ordering")
    print("  log                                log backtest results to file")
    print("  analyse                            run correlation study of indicators")
    print("  scan                               run in scan mode only")
    print("  optimise                           optimise strategy parameters")
    print("  instruments                        specify specific instruments")
    print("  data                               load custom price data file")
    print("")


def option_help(option):
    ''' Print usage instructions. '''
    
    banner = pyfiglet.figlet_format("AUTOTRADER")
    print(banner)
    if option == 'config' or option == 'c':
        print("Help for 'config' option:")
        print("-----------------------------------")
        print("A configuration file must be specified to run AutoTrader. The")
        print("file must be written as a .yaml file according to the template")
        print("provided in the config/ directory.")
        
        print("Note that the file extension should not be included. The full")
        print("file path does not need to be specified, AutoTrader will search")
        print("for the file in the config/ directory.")

        
    elif option == 'verbosity' or option == 'v':
        print("Help for 'verbosity' option:")
        print("-----------------------------------")
        print("The verbosity flag is used to set the level of output")
        print("displayed by the code. A verbosity of zero supresses all")
        print("output, while a value greater than zero will show more details")
        print("of what the code is doing.")
        print("Verbosity settings will not affect error output.")
        
        print("\nDefault value: 0")

        
    elif option == 'backtest' or option == 'b':
        print("Help for 'backtest' option:")
        print("-----------------------------------")
        print("The backtest flag is used to run the strategy in backtest")
        print("mode.")
        
        print("\nDefault value: False")
 
        
    elif option == 'plot' or option == 'p':
        print("Help for 'plot' option:")
        print("-----------------------------------")
        print("The plot option is used to create a plot of the price chart")
        print("and strategy-specific indicators. It may be used for both")
        print("livetrading and backtesting.")
        
        print("\nDefault value: False")

        
    elif option == 'notify' or option == 'n':
        print("Help for 'notify' option:")
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

        
    elif option == 'log' or option == 'l':
        print("Help for 'log' option:")
        print("-----------------------------------")
        print("The log option allows logging of backtest results to a")
        print("logfile. The log file will be written to logfiles/ and")
        print("includes key statistics of the backtest, such as win rate,")
        print("number of trades and profit. The configuration file is also")
        print("embeded in the log file for future reference.")
        
        print("\nDefault value: False")

        
    elif option == 'analyse' or option == 'a':
        print("Help for 'analyse' option:")
        print("-----------------------------------")
        print("Analyser. More information coming soon.")
        
        print("\nDefault value: False")

        
    elif option == 'scan' or option == 's':
        print("Help for 'scan' option:")
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

        
    elif option == 'optimise' or option == 'o':
        print("Help for 'optimise' option:")
        print("-----------------------------------")
        print("When this flag is included, AutoTrader will return a dictionary")
        print("containing backtest results, to be used by the optimiser.")
        print("This option is to be used internally by AutoOptimise.")
        
        print("\nDefault value: False")

    
    elif option == 'data' or option == 'd':
        print("Help for 'data' option:")
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
        
    
    elif option == 'instruments' or option == 'i':
        print("Help for 'instruments' option:")
        print("-----------------------------------")
        print("This flag may be used to specify instruments to run AutoTrader")
        print("on, overwriting the watchlist in the strategy config file.")
        
        print("\nDefault value: None")

        
    elif option == "general":
        print("General help.")
        print("")
        
    else:
        print("Unrecognised flag ({}).".format(option))
    
    if option != "general":
        print("\n\nFor general help, pass 'general' to help.\n")
    

def stream_help(option=None):
    """ 
    Print help for autostream.
    """
    
    if option == 'usage' or option is None:
        banner = pyfiglet.figlet_format("AUTOSTREAM")
        print(banner)
        print("Utility to stream price data and write to text file.")
        print("")
        print("--------------------------------------------------------------" \
              + "---------------")
        print("Flag                                 Comment [short flag]")
        print("--------------------------------------------------------------" \
              + "---------------")
        print("Required:") 
        print("  --instrument 'XXX_YYY'             instrument to stream [-i]")
        print("  --granularity 'M15'                candlestick granularity [-g]")
        print("\nOptional:")
        print("  --help                             show help for usage [-h]")
        print("  --verbosity <int>                  set verbosity (0,1,2) [-v]")
        print("  --max-candles <10>                 max number of candles to store [-N]")
        print("  --index ''                         specify index to stream [-I]")
        print("")
        print("Note: if multiple instruments are requested, they must be entered")
        print("as comma separated text with no spaces. Example:")
        print("-i EUR_USD,USD_JPY,AUD_CAD")

    elif option == 'instrument' or option == 'i':
        print("Help for '--instrument' (-c) option:")
        
        print("\nExample usage:")
        print("./AutoStream.py -c my_config_file")
        
    elif option == 'verbosity' or option == 'v':
        print("Help for '--verbosity' (-v) option:")
        print("-----------------------------------")
        print("The verbosity flag is used to set the level of output.")
    
    elif option == 'index' or option == 'I':
        print("Help for '--verbosity' (-v) option:")
        print("-----------------------------------")
        print("Specify an index to stream. ")
        print("This flag takes precedence over -i if both are specified.")

