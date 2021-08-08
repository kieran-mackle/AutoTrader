#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

AuotOptimise
-------------

Want to use a walk-forward optimisation approach. 

Plot output as heatmap: parameter grid coloured by objective function

Consider sample size, print as warning 

TODO: move into autotrader.py somehow...


"""

from autotrader.autotrader import AutoTrader
import yaml
import os
from getopt import getopt
import sys
from scipy.optimize import brute
import timeit
from ast import literal_eval


class Optimise():
    '''
    
    opt_params  = ['param1', 'param2', ...]
    bounds      = [  (),       (),     ...]
        
    '''
    
    def __init__(self):
        self.config_file    = None
        self.verbosity      = 1
        self.show_help      = None
        self.log            = False
        self.home_dir       = None
        self.opt_params     = None
        self.bounds         = None
        self.Ns             = 4
        self.objective      = 'profit + MDD'
    
    def read_yaml(self, file_path):
        '''Function to read and extract contents from .yaml file.'''
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    
    
    def helper_function(self, params, config_dict, opt_params, verbosity):
        '''
            Helper function for optimising strategy in AutoTrader.
            This function will parse the ordered params into the config dict.
            
        '''
        
        ''' ------------------------------------------------------------------ '''
        '''   Edit strategy parameters in config_dict using supplied params    '''
        ''' ------------------------------------------------------------------ '''
        for parameter in config_dict['STRATEGY']['PARAMETERS']:
            if parameter in opt_params:
                config_dict['STRATEGY']['PARAMETERS'][parameter] = params[opt_params.index(parameter)]
            else:
                continue
        
        ''' ------------------------------------------------------------------ '''
        '''           Run AutoTrader and evaluate objective function           '''
        ''' ------------------------------------------------------------------ '''
        at                  = AutoTrader()
        at.backtest         = True
        at.optimise         = True
        at.custom_config    = config_dict
        
        backtest_results    = at.run()
        
        try:
            objective           = -backtest_results['all_trades']['profit_pc']  - \
                                  backtest_results['all_trades']['MDD']
        except:
            objective           = 100
                              
        print("Parameters/objective:", params, "/", objective)
        
        return objective
    
    
    def optimise(self):
        
        ''' ------------------------------------------------------------------ '''
        '''                          Unpack user options                       '''
        ''' ------------------------------------------------------------------ '''
        if self.home_dir is not None:
            home_dir            = self.home_dir
        else:
            home_dir            = os.getcwd()
        config_file_path    = os.path.join(home_dir, 'config', self.config_file)
        config_dict         = self.read_yaml(config_file_path + '.yaml')
        verbosity           = self.verbosity
        
        ''' ------------------------------------------------------------------ '''
        '''                      Define optimisation inputs                    '''
        ''' ------------------------------------------------------------------ '''
        if type(self.bounds) == str:
            full_tuple = literal_eval(self.bounds)
            bounds = [(x[0], x[-1]) for x in full_tuple]
        else:
            bounds = self.bounds

        if type(self.opt_params) == str:
            opt_params = self.opt_params.split(',')
        else:
            opt_params = self.opt_params
            
        my_args     = (config_dict, opt_params, verbosity)
        
        ''' ------------------------------------------------------------------ '''
        '''                             Run Optimiser                          '''
        ''' ------------------------------------------------------------------ '''
        start = timeit.default_timer()
        result = brute(func         = self.helper_function, 
                       ranges       = bounds, 
                       args         = my_args, 
                       Ns           = self.Ns,
                       full_output  = True)
        stop = timeit.default_timer()
        
        ''' ------------------------------------------------------------------ '''
        '''      Delete historical data file after running optimisation        '''
        ''' ------------------------------------------------------------------ '''
        granularity             = config_dict["STRATEGY"]["INTERVAL"]
        pair                    = config_dict["WATCHLIST"][0]
        historical_data_name    = 'hist_{0}{1}.csv'.format(granularity, pair)
        historical_quote_data_name = 'hist_{0}{1}_quote.csv'.format(granularity, pair)
        historical_data_file_path = os.path.join(home_dir, 
                                                 'price_data',
                                                 historical_data_name)
        historical_quote_data_file_path = os.path.join(home_dir, 
                                                 'price_data',
                                                 historical_quote_data_name)
        os.remove(historical_data_file_path)
        os.remove(historical_quote_data_file_path)
        
        
        opt_params = result[0]
        opt_value = result[1]
        
        # TODO - use the below for heatmap plotting
        grid_points = result[2]
        grid_values = result[3]
        
        
        ''' ------------------------------------------------------------------ '''
        '''                            Print output                            '''
        ''' ------------------------------------------------------------------ '''
        print("\nOptimisation complete.")
        print('Time to run: {}s'.format(round((stop - start), 3)))
        print("Optimal parameters:")
        print(opt_params)
        print("Objective:")
        print(opt_value)
        
    
    def print_usage(self):
        print("Help is on its way! Check back again later.")
    
    def print_help(self, option):
        print("Help is on its way! Check back again later.")



short_options = "h:c:v:lo:b:"
long_options = ["help=", "config=", "verbosity=", "log", "optimise=", 
                "bounds="]

if __name__ == '__main__':
    
    # Instantiate Optimiser
    optimiser = Optimise()
    
    # Extract User Inputs
    options, r = getopt(sys.argv[1:], 
                        short_options, 
                        long_options
                        )
    
    # Default Options
    config_file     = None
    verbosity       = 0
    show_help       = None
    log             = False
    opt_params      = None
    bounds          = None
    
    for opt, arg in options:
        if opt in ('-c', '--config'):
            config_file = arg
            optimiser.config_file = arg
        elif opt in ('-v', '--verbose'):
            verbosity = arg
            optimiser.verbose = arg
        elif opt in ('-h', '--help'):
            show_help = arg
            optimiser.show_help = arg
        elif opt in ('-l', '--log'):
            log = True
            optimiser.log = True
        elif opt in ('-o', '--optimise'):
            opt_params = arg
            optimiser.opt_params = arg
        elif opt in ('-b', '--bounds'):
            opt_params = arg
            optimiser.bounds = arg
            

    if len(options) == 0:
        optimiser.print_usage()
        
    elif show_help is not None:
        optimiser.print_help(show_help)
        
    else:
        optimiser.optimise()