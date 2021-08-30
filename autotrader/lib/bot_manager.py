#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import autostream
import threading
import os
import v20
import json
from datetime import datetime
import calendar

# Not sure if the while loop should be in the class, or just in the script 
# being run...


class ManageBot():
    """
    AutoTrader Bot Manager
    ----------------------
    Feeds tick data to bot.
    
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
    
    """
    
    def __init__(self, bot, stream_config):
        self.bot = bot
        self.stream_config = stream_config
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
        
        while self.managing:
            
            # Read stream file rather than run the stream from here, because
            # otherwise it will get too complicated with strategies requiring
            # some price history, as well as checking run conditions.
            # Here, I dont even need to connect to the stream.
            # I could literally just keep downloading the latest data and 
            # refresh the bot with that. Forget the stream for now.
                    
            # Update bot data
            
            
            # Call bot update to act on latest data
            self.bot._update(i)
            
            # The stuff below should probably be in the for loop
            
            # Should terminal condition come from strategy -> bot -> here?
            
            if os.path.exists('killbot'):
                print("Killfile detected. Bot will be terminated.")
                self.managing = False
            
    
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


