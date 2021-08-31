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
    
    def __init__(self, bot):
        
        self.bot = bot
        self.managing = True
        
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
            # Refresh strategy with latest data
            self.bot._update_strategy_data()
            
            # Call bot update to act on latest data
            self.bot._update(-1)

            # Check for termination signals
            if self.bot.strategy.terminate:
                self.managing = False
            
            # TODO - pass homedir into os.path.exists!
            if os.path.exists('killbot'):
                print("Killfile detected. Bot will be terminated.")
                self.bot.strategy.exit_strategy(-1)
                self.managing = False
                
                # Remove bot from log
                self.remove_bot_from_log()
                
            
            # Pause an amount, depending on granularity
            sleep_time = 0.5*self.granularity_to_seconds(self.bot.strategy_params['granularity'])
            time.sleep(sleep_time)
            
    
    def update_bot_data(self):
        '''
        Passes the latest price data to the bot.
        '''
        
        return
    
    
    def kill_bot(self):
        '''
        Terminates the bot from trading.
        '''
        
        return
    
    def write_bot_to_log(self):
        '''
        Adds the bot being managed to the bots_deployed logfile.
        '''
        
        return
    
    def remove_bot_from_log(self):
        '''
        Removes the bot being managed from the bots_deployed logfile.
        '''
        
        return

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
