#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging script. Writes log file.
"""
from datetime import datetime
import glob
import os  
import pyfiglet

def write_backtest_log(pair, config, trade_summary):
    ''' 
    Function to write backtest results to a log file. 
    '''
    # Banner
    banner = pyfiglet.figlet_format("AutoBacktest")

    # Config file
    interval            = config["STRATEGY"]["INTERVAL"]
    period              = config["STRATEGY"]["PERIOD"]
    params              = config["STRATEGY"]["PARAMETERS"]
    risk_pc             = config["STRATEGY"]["RISK_PC"]
    strat_module        = config["STRATEGY"]["MODULE"]
    strat_name          = config["STRATEGY"]["NAME"]
    exit_function       = config["STRATEGY"]["EXIT_FUNCTION"]
    
    from_year           = config["BACKTESTING"]["FROM"]["year"]
    from_month          = config["BACKTESTING"]["FROM"]["month"]
    from_day            = config["BACKTESTING"]["FROM"]["day"]
    to_year             = config["BACKTESTING"]["TO"]["year"]
    to_month            = config["BACKTESTING"]["TO"]["month"]
    to_day              = config["BACKTESTING"]["TO"]["day"]
    
    from_date           = str(from_day) + "/" + str(from_month) + "/" + str(from_year)
    to_date             = str(to_day) + "/" + str(to_month) + "/" + str(to_year)
    
    # Trade summary
    no_trades           = len(trade_summary)
    final_balance       = trade_summary.Balance[-1]
    initial_balance     = trade_summary.Balance[0] - trade_summary.Profit[0]
    profit              = final_balance - initial_balance
    profit_pc           = 100*profit / initial_balance
    profitable_longs        = trade_summary[(trade_summary['Profit'] > 0) 
                                            & (trade_summary['Size'] > 0)]
    profitable_shorts       = trade_summary[(trade_summary['Profit'] > 0) 
                                            & (trade_summary['Size'] < 0)]
    no_profitable_trades    = len(profitable_longs) + len(profitable_shorts)
    win_rate                = 100*no_profitable_trades/no_trades
    
    time            = datetime.now().strftime("%H:%M:%S")
    
    # Create file name
    file_dir        = os.path.dirname(os.path.abspath(__file__))
    log_dir         = os.path.join(file_dir, '..', 'logfiles')
    log_file_dir    = os.path.join(log_dir, '*{}*'.format(strat_module))
    log_files       = glob.glob(log_file_dir)
    if len(log_files) != 0:
        file_no = len(log_files) + 1
    else:
        file_no = 1
    
    outFileName     = strat_module + "_log_" + str(file_no) + ".txt"
    outFileName_abs = os.path.join(log_dir, outFileName)
    
    with open(outFileName_abs, 'w+') as f:
        f.write(banner)
        f.write("Log file created by AutoTrader at {}\n".format(time))
        f.write("-------------------------------------------\n")
        f.write("Strategy: {}\n".format(strat_name))
        f.write("Backtest period: {0} to {1}\n".format(from_date, to_date))
        f.write("\nResults\n")
        f.write("-------\n")
        f.write("  Number of trades: {}\n".format(no_trades))
        f.write("  Starting balance: ${}\n".format(round(initial_balance, 2)))
        f.write("  Final balance: ${}\n".format(round(final_balance, 2)))
        f.write("  Profit: {0} ({1}%)\n".format(round(profit, 2), 
                                                round(profit_pc, 1)))
        f.write("  Win rate: {}%\n".format(round(win_rate, 3)))
        f.write("\n")
        f.write("The configuration file used in this strategy is provided below.\n")
        f.write("\n")
        f.write("STRATEGY:\n")
        f.write("  MODULE: '{}'\n".format(strat_module))
        f.write("  NAME: '{}'\n".format(strat_name))
        f.write("  INTERVAL: '{}'\n".format(interval))
        f.write("  PERIOD: {}\n".format(period))
        f.write("  RISK_PC: {}\n".format(risk_pc))
        f.write("  EXIT_FUNCTION: {}\n".format(exit_function))
        
        f.write("  PARAMETERS: \n")
        for key in params:
            param_str = "    " + key + ": {}\n".format(params[key])
            f.write(param_str)
        f.write("\n")
        
        f.write("BROKER: \n")
        f.write("  initial_balance: {}\n".format(int(initial_balance)))
        f.write("\n")
        
        f.write("WATCHLIST: ['" + pair + "']\n\n")
        
        f.write("BACKTESTING:\n")
        f.write("  FROM:\n")
        f.write("    year: {}\n".format(from_year))
        f.write("    month: {}\n".format(from_month))
        f.write("    day: {}\n".format(from_day))
        f.write("  TO:\n")
        f.write("    year: {}\n".format(to_year))
        f.write("    month: {}\n".format(to_month))
        f.write("    day: {}\n".format(to_day))
        f.write("\n")
    

