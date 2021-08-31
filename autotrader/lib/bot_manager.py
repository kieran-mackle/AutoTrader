#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import autostream
import threading
import time
import os

# Not sure if the while loop should be in the class, or just in the script 
# being run...


class ManageBot():
    """
    AutoTrader Bot Manager
    ----------------------
    Detaches from AutoTrader run script to allow for a single deployment.
    
    Attributes
    ----------
    bot: class
        The bot being managed.
    
    Methods 
    --------
    update_bot_data():
        Passes the latest price data to the bot.
    
    kill_bot():
        Terminates the bot from trading.
    
    write_bot_to_log():
        Adds the bot being managed to the bots_deployed logfile.
    
    remove_bot_from_log():
        Removes the bot being managed from the bots_deployed logfile.
    
    
    Strategies being deployed to bot manager must have the following methods:
        - initialise_strategy()
        - exit_strategy(i)
    
    As well as a "terminate" attribute.
    
    """
    
    def __init__(self, bot, home_dir, bot_name_string):
        
        self.bot = bot
        self.home_dir = home_dir
        self.managing = True
        
        self.bot_deployed_logfile = os.path.join(home_dir, 'bots_deployed.txt')
        self.killfile = os.path.join(self.home_dir, 'killbot')
        
        # Create name string for logfile
        self.bot_name_string = bot_name_string
        
        # Spawn new thread for bot manager
        thread = threading.Thread(target=self.manage_bot, args=(), 
                                  daemon=True)
        print("Bot recieved. Now managing bot.")
        print("To kill bot, create file named 'killbot'.")
        thread.start()
        
        
    def manage_bot(self):
        '''
        Manages bot until terminal condition is met.
        '''
        
        # Add bot to log
        self.write_bot_to_log()
        
        while self.managing:
            
            # First check for any termination signals
            if self.bot.strategy.terminate:
                self.managing = False
            
            if os.path.exists(self.killfile):
                print("Killfile detected. Bot will be terminated.")
                self.bot.strategy.exit_strategy(-1)
                self.managing = False
                
                # Remove bot from log
                self.remove_bot_from_log()
            
            # Refresh strategy with latest data
            self.bot._update_strategy_data()
            
            # Call bot update to act on latest data
            self.bot._update(-1)
            
            # Pause an amount, depending on granularity
            sleep_time = 0.5*self.granularity_to_seconds(self.bot.strategy_params['granularity'])
            time.sleep(sleep_time)
            
    
    def write_bot_to_log(self):
        '''
        Adds the bot being managed to the bots_deployed logfile.
        '''
        
        # First check if file exists. If not, create, and write header
        if not os.path.exists(self.bot_deployed_logfile):
            f = open(self.bot_deployed_logfile, "w")
            f.write("The following bots are currently deployed:\n")
            f.close()
        
        f = open(self.bot_deployed_logfile, "a")
        f.write("{}\n".format(self.bot_name_string))
        f.close()
        
    
    def remove_bot_from_log(self):
        '''
        Removes the bot being managed from the bots_deployed logfile.
        '''
        with open(self.bot_deployed_logfile, "r") as f:
            lines = f.readlines()
        
        with open(self.bot_deployed_logfile, "w") as f:
            for line in lines:
                if line.strip("\n") != self.bot_name_string:
                    f.write(line)
        

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
        
        seconds = conversions[letter] * number
        
        return seconds
