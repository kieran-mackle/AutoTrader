#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AutoStream
-----------
Data stream function for Oanda v20 API.
"""

import v20
import json
from datetime import datetime
import sys
import calendar
import time
import re
import os
import traceback
import pandas as pd


class stream_record(object):
    ''' 
    Creates a stream record.
    
    Attributes
    ----------
        data : dict
            A dictionary containing information of the tick; instrument, time,
            bid, ask and mid.
        
        record_type : str
            The type of stream record: either PRICE or HEARTBEAT
    '''
    
    def __init__(self, msg):
        self.data           = {}
        self.record_type    = msg['type']
        
        if msg['type'] == 'PRICE':
            self.dt                  = datetime.strptime(msg['time'][:-4], '%Y-%m-%dT%H:%M:%S.%f')
            self.epoch               = int(calendar.timegm(self.dt.timetuple()))
            self.data['instrument']  = msg["instrument"]
            self.data['time']        = msg["time"]
            self.data['bid']         = msg["closeoutBid"]
            self.data['ask']         = msg["closeoutAsk"]
            self.data['mid']         = (float(msg['closeoutBid']) + float(msg['closeoutAsk']))/2.0
            
        elif msg['type'] == "HEARTBEAT":
            self.dt                  = datetime.strptime(msg['time'][:-4], '%Y-%m-%dT%H:%M:%S.%f')
            self.epoch               = int(calendar.timegm(self.dt.timetuple()))
            self.data['time']        = msg["time"]


class candle_builder(object):
    ''' Builds candles from stream records '''
    
    def __init__(self, instrument, granularity):
        ''' Initialises class based on instrument and candlestick 
            granularity. 
        '''
        self.instrument     = instrument
        self.duration       = self.granularity_to_seconds(granularity)
        self.granularity    = granularity
        self.data           = None
        self.start          = None
        self.end            = None
        
    def initialise_data(self, tick):
        ''' Cosntructs data dictionary for new candle. '''
        self.start  = tick.epoch - (tick.epoch % self.duration)
        self.end    = tick.epoch - (tick.epoch % self.duration) + self.duration
        self.data   = {"instrument"     : self.instrument,
                       "start"          : "%s" % self.seconds_in_time(self.start),
                       "end"            : "%s" % self.seconds_in_time(self.end),
                       "granularity"    : self.granularity,
                       "completed"      : False,
                       "data"           : {"open"   : tick.data['mid'],
                                           "high"   : tick.data['mid'],
                                           "low"    : tick.data['mid'],
                                           "last"   : tick.data['mid'],
                                           "volume" : 1
                                            }
                       }

    def seconds_in_time(self, e):
        ''' Converts a timestamp to datetime object. '''
        w   = time.gmtime(e)
        
        return datetime(*list(w)[0:6])

    def make_candle(self, completed=False):
        ''' Closes candle '''
        
        self.data['completed'] = completed
        
        return self.data.copy()
    
    def granularity_to_seconds(self, granularity):
        ''' Converts a granularity to time in seconds '''
        mfact = {'S': 1,
                 'M': 60,
                 'H': 3600,
                 'D': 86400,
                 }
    
        f, n    = re.match("(?P<f>[SMHD])(?:(?P<n>\d+)|)", granularity).groups()
        n       = n if n else 1
        seconds = mfact[f] * int(n)
        
        return seconds
    
    def process_tick(self, tick):
        ''' Processes tick into candle '''
        if tick.record_type == 'HEARTBEAT':
            if self.data and tick.epoch > self.end:
                # this frame is completed based on the heartbeat timestamp
                candle      = self.make_candle(completed=True)
                self.data   = None     # clear it, reinitialized by the next tick
                
                print("infrequent ticks: %s, %s completed with "
                            "heartbeat (%d secs)" %
                            (self.instrument, self.granularity,
                              (tick.epoch - self.end)))
                
                return candle
            
            else:
                # Candle is still open
                return
            
        
        if not tick.data['instrument'] == self.instrument:
            # Tick data is not for instrument being monitored - exit
            
            return
        
        
        if not self.data:
            # There is no data yet, initialise now
            self.initialise_data(tick)
            
            return None
        
        
        if tick.epoch >= self.start and tick.epoch < self.end:
            # The tick falls within the current candle
            
            if tick.data['mid'] > self.data['data']['high']:
                self.data['data']['high'] = tick.data['mid']
                
            if tick.data['mid'] < self.data['data']['low']:
                self.data['data']['low'] = tick.data['mid']
                
            if tick.data['mid'] != self.data['data']['last']:
                self.data['data']['last'] = tick.data['mid']
                
            # Add tick to candle volume
            self.data['data']['volume'] += 1
            
            return None
        
        # This tick is not within the candle, close the candle.
        candle = self.make_candle(completed = True)
        
        self.initialise_data(tick)
        
        return candle


class AutoStream():
    '''
    AutoStream Class.
    ------------------
    
    Methods:
        main(): Subscribes to stream and builds candlestick price files. 
    
    
    Attributes:
        home_dir : str
            The path of the home directory. If writing stream to file, it will
            be written to home_dir/price_data.
        
        stream_config : dict
            Dictionary containing stream configuration information.
        
        instruments : list
            The instruments to be streamed.
        
        granularity : str
            The granularity of candlesticks to build from the stream.
        
        no_candles : int
            The maximum number of candles to write to file.
        
        record_ticks : bool
            Flag to capture tick data.
        
        record_candles : bool
            Flag to capture candlestick data.
        
        write_to_file : bool
            Flag to write streamed data to csv files.
    '''
    
    def __init__(self, home_dir, stream_config, 
                 instrument, granularity=None, no_candles=10,
                 record_ticks=False, record_candles=False,
                 bot=None, update_bot=False, write_to_file=False):
        '''
        Assign attributes required to stream.
        '''
        
        self.home_dir       = home_dir
        self.instruments    = instrument
        self.granularity    = granularity
        self.no_candles     = no_candles
        self.record_candles = record_candles
        self.record_ticks   = record_ticks
        self.bot            = bot
        self.update_bot     = update_bot
        self.write_to_file  = write_to_file
        self.killfile       = os.path.join(home_dir, 'stopstream')
        self.suspendfile    = os.path.join(home_dir, 'suspendstream')
        self.stopstream     = False
        
        # Runtime attributes
        self.tick_data      = None
        self.candle_data    = None
        
        # Add instruments to stream_config
        stream_config['instruments'] = instrument
        self.stream_config  = stream_config
        
        # Perform initialisation checks
        self.checks_passed = True
        if not record_candles and not record_ticks:
            print("Please specify whether to record ticks, candles or both "+\
                  "using the record_ticks and record_candles attributes.")
            self.checks_passed = False
        
        if record_candles and granularity is None:
            print("Please provide a candlestick granularity when streaming candles.")
            self.checks_passed = False
            
    
    def start(self):
        '''
        Starts stream if all checks have passed.
        '''

        if self.checks_passed:
            # Proceed to run stream
            self.main()
        
    def main(self):
        '''
        Subscribes to stream and builds candlestick price files. 
        '''
        
        data_dir_path   = os.path.join(self.home_dir, 'price_data')
        
        # Initialise tick DataFrame
        if self.record_ticks:
            self.tick_data = pd.DataFrame()
        
        # Initialise candle DataFrame
        if self.record_candles:
            self.candle_data = pd.DataFrame()
        
        # Initialise text file processing
        candle_filenames = {}
        tick_filenames = {}
        candle_builders = {}
        
        if self.write_to_file:
            if not os.path.exists(data_dir_path):
                # The price_data directory doesn't exist, make it
                os.makedirs(data_dir_path)
        
            # Initialise candle factories
            for instrument in self.instruments.split(','):
                if self.record_candles:
                    filename                    = "{0}{1}.txt".format(self.granularity, 
                                                                      instrument)
                    abs_filename                = os.path.join(data_dir_path, filename)
                    candle_filenames[instrument] = abs_filename
                    candle_builders[instrument] = candle_builder(instrument, 
                                                                 self.granularity)
                
                if self.record_ticks:
                    filename                    = "{}_ticks.txt".format(instrument)
                    abs_filename                = os.path.join(data_dir_path, filename)
                    tick_filenames[instrument]  = abs_filename
        
        # Connect to stream and begin processing 
        self.connect_to_stream(self.stream_config)
        
        while True and not self.stopstream:
            try:
                self.process_stream(candle_builders,
                                    candle_filenames,
                                    tick_filenames)
            except BaseException as ex:
                ex_type, ex_value, ex_traceback = sys.exc_info()
                        
                # Extract unformatter stack traces as tuples
                trace_back = traceback.extract_tb(ex_traceback)
            
                # Format stacktrace
                stack_trace = list()
            
                for trace in trace_back:
                    trade_string = "File : %s , Line : %d, " % (trace[0], trace[1]) + \
                                   "Func.Name : %s, Message : %s" % (trace[2], trace[3])
                    stack_trace.append(trade_string)
                
                print("\nWARNING FROM AUTOSTREAM ({}): The following exception was caught:".format(self.instruments))
                print("Time: {}".format(datetime.now().strftime("%b %d %H:%M:%S")))
                print("Exception type : %s " % ex_type.__name__)
                print("Exception message : %s" %ex_value)
                print("Stack trace : %s" %stack_trace)
                print("  Trying again.")
                            
                # Sleep and attempt to re-connect to stream
                time.sleep(3)
                self.connect_to_stream(self.stream_config)
    
    
    def connect_to_stream(self, config):
        ''' Connects to Oanda streaming API '''
        ACCESS_TOKEN    = config["ACCESS_TOKEN"]
        port            = config["PORT"]
        ACCOUNT_ID      = config["ACCOUNT_ID"]
        STREAM_API      = "stream-fxpractice.oanda.com"
        instruments     = config["instruments"]
        
        streamAPI       = v20.Context(hostname = STREAM_API,
                                      token = ACCESS_TOKEN, 
                                      port = port)
        
        # Connect to the stream
        for attempt in range(5):
            try:
                response = streamAPI.pricing.stream(accountID = ACCOUNT_ID, 
                                                    instruments = instruments,
                                                    snapshot = True
                                                    )
                if response.status != 200:
                    print("Warning:")
                    print("Time: {}".format(datetime.now().strftime("%b %d %H:%M:%S")))
                    print(response.reason)
                    break
                    
                else:
                    self.stream = response
            
            except Exception as e:
                print("Caught exception when connecting to stream\n" + str(e))
                time.sleep(3)
            else:
                break
            
        else:
            print("All attempts to connect to stream failed. Exiting.")
            sys.exit(0)
    
    def suspend(self):
        while os.path.exists(self.suspendfile):
            pass
        
    def process_stream(self, candle_builders, candle_filenames, tick_filenames):
        '''
        Processes stream based on run settings.
        '''
        
        print("\nProcessing stream. To stop streaming, create file named " +\
              "stopstream in the home directory. Alternatively, create " +\
              "a file called suspendstream to pause the stream. Then, " +\
              "delete this file to resume streaming.")
        print("Home directory: ", self.home_dir)

        for line in self.stream.lines:
            
            # First check for stop file
            if os.path.exists(self.killfile):
                print("Stop file deteced. Stream stopping.")
                self.stopstream = True
                
                break
            
            # Next check for suspend file
            if os.path.exists(self.suspendfile):
                print("Suspending stream.")
                self.suspend()
                print("Resuming stream.")
            
            # Process each update of stream
            line    = line.decode('utf-8')
            msg     = json.loads(line)
            tick    = stream_record(msg)
            
            if self.record_ticks and msg['type'] == 'PRICE' and tick.data['instrument'] == self.instruments:
                # Create tick df from stream record
                new_tick = {'Bid': tick.data['bid'], 
                            'Ask': tick.data['ask'], 
                            'Mid': tick.data['mid']}
                latest_tick = pd.DataFrame(new_tick, 
                                           index=[tick.data['time']])
                
                # Update tick_data with latest tick
                self.tick_data = self.tick_data.append(latest_tick)
                
                # Check if the length has been exceeded
                if len(self.tick_data) > self.no_candles:
                    self.tick_data = self.tick_data.iloc[-self.no_candles:, :]
                
                # Update bot
                if self.update_bot:
                    self.update_bot_data(self.tick_data)
                
                # Write to file
                if self.write_to_file:
                    # TODO - preprocess time index column to convert to datetime
                    # And add exception handling methods for datetime errors 
                    self.tick_data.index.name = 'Time'
                    self.tick_data.to_csv(tick_filenames[tick.data['instrument']])
                
            if self.record_candles:
                for instrument in candle_builders:
                    
                    candle  = candle_builders[instrument].process_tick(tick)
                    
                    if candle is not None:
                        
                        # Create candle df from stream record
                        new_candle = {'High': candle['data']['high'], 
                                      'Low': candle['data']['low'], 
                                      'Open': candle['data']['open'],
                                      'Close': candle['data']['last']}
                        latest_candle = pd.DataFrame(new_candle, 
                                                     index=[candle['start']])
                        
                        # Update candle_data with latest candle
                        self.candle_data = self.candle_data.append(latest_candle)
                        
                        # Check if the length has been exceeded
                        if len(self.candle_data) > self.no_candles:
                            self.candle_data = self.candle_data.iloc[-self.no_candles:, :]
                        
                        # Update bot
                        if self.update_bot:
                            self.update_bot_data(self.candle_data)
                        
                        # Write to file
                        if self.write_to_file:
                            self.candle_data.index.name = 'Time'
                            self.candle_data.to_csv(candle_filenames[instrument])
            

    def update_bot_data(self, data):
        '''
        Sends updated data to bot.
        '''
        
        # Only pass data if len(data) > 0
        if len(data) > 0:
            # Refresh strategy with latest data
            self.bot._update_strategy_data(data)
            
            # Call bot update to act on latest data
            self.bot._update(-1)
