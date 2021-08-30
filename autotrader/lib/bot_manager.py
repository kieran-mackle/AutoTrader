#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import autostream


# Not sure if the while loop should be in the class, or just in the script 
# being run...


class BotManager():
    """
    AutoTrader Bot Manager
    ----------------------
    
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
    
    def __init__(self, bot):
        self.bot = bot
        
        # while managing:
            # monitor price stream, update bot, check terminal condition
            
            # if terminal condtion reached:
                # kill_bot()
                # managing = False
        
        
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

# Bot being managed

# Write to text file bots deployed