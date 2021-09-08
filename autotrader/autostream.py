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
                 instrument, granularity, no_candles=10,
                 record_ticks=False, record_candles=True,
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
        
        # Runtime attributes
        self.tick_data      = None
        self.candle_data    = None
        
        # Add instruments to stream_config
        stream_config['instruments'] = instrument
        self.stream_config  = stream_config
        
        # check that one of tick or candle recording is set, or else dont run
        
        # self.main()
        
        
    def main(self):
        '''
        Subscribes to stream and builds candlestick price files. 
        '''
        
        # TODO - do not start stream if it is already running - be careful,
        # this is only appropriate if we are reading from a file, but if the 
        # data is being stored locally in the class instance, it will need it
        
        data_dir_path   = os.path.join(self.home_dir, 'price_data')
        temp_file_path  = os.path.join(data_dir_path, "temp.txt")
        
        # Initialise tick DataFrame
        if self.record_ticks:
            self.tick_data = pd.DataFrame()
        
        # Initialise candle DataFrame
        if self.record_candles:
            self.candle_data = pd.DataFrame()
        
        
        # Initialise text file processing
        if self.write_to_file:
            if not os.path.exists(data_dir_path):
                # The price_data directory doesn't exist, make it
                os.makedirs(data_dir_path)
        
            # TODO - the below hasnt been double checked yet 
            
            # Initialise candle factories
            file_names      = {}
            tick_files      = {}
            candle_builders = {}
            for instrument in self.instruments.split(','):
                if self.record_candles:
                    filename                    = "{0}{1}.txt".format(self.granularity, 
                                                                      instrument)
                    abs_filename                = os.path.join(data_dir_path, filename)
                    file_names[instrument]      = abs_filename
                    candle_builders[instrument] = candle_builder(instrument, 
                                                                 self.granularity)
                    
                    # # If the price data file doesn't already exist, initialise it
                    # if not os.path.exists(file_names[instrument]):
                    #     f = open(file_names[instrument], "a+")
                    #     f.write("Time, Open, High, Low, Close\n")
                    #     f.close()
    
                
                if self.record_ticks:
                    filename                    = "{}_ticks.txt".format(instrument)
                    abs_filename                = os.path.join(data_dir_path, filename)
                    tick_files[instrument]      = abs_filename
                    
                    # # If the price data file doesn't already exist, initialise it
                    # if not os.path.exists(tick_files[instrument]):
                    #     f = open(tick_files[instrument], "a+")
                    #     f.write("Time, Bid, Ask, Mid\n")
                    #     f.close()
        
        # Connect to stream and begin processing 
        stream = self.connect_to_stream(self.stream_config)
        
        for attempt in range(10):
            try:
                self.process_stream(stream,
                               candle_builders,
                               file_names,
                               tick_files,
                               temp_file_path,
                               self.no_candles,
                               self.record_ticks,
                               self.record_candles)
            except Exception as e:
                print("Exception caught:")
                print(e)
                stream = self.connect_to_stream(self.stream_config)
            else:
                break
        else:
                print("All attempts failed. Exiting.")
                
    
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
        
        # TODO - double check the below logic... what does the first break do
        for attempt in range(3):
            try:
                response = streamAPI.pricing.stream(accountID = ACCOUNT_ID, 
                                                    instruments = instruments,
                                                    snapshot = True
                                                    )
                if response.status != 200:
                    print("Warning:")
                    print(response.reason)
                    break
                    
                else:
                    return response
            
            except Exception as e:
                print("Caught exception when connecting to stream\n" + str(e))
            
            else:
                break
            
        else:
            print("All attempts to connect to stream failed. Exiting.")
            sys.exit(0)
    
    
    def process_stream(self, stream, candle_builders, file_names, tick_files, 
                       temp_file_path, no_candles, record_ticks=False, 
                       record_candles=True):
        '''
        Processes stream based on run settings.
        '''
        
        for line in stream.lines:
            # Process each update of stream
            line    = line.decode('utf-8')
            msg     = json.loads(line)
            tick    = stream_record(msg)
            
            # Add logic to pass new ticks / candles directly to strategy 
            
            # Add exception handling methods 
            
            # If file is deleted for some reason, create it again
            
            # TODO - create empty df for tick and candle df's, not sure where
            
            if record_ticks and msg['type'] == 'PRICE':
                
                # TODO - the below is repeated code: clean it up
                # If the price data file doesn't already exist, initialise it
                # This is an edge case when the file may accidentally be deleted
                # if not os.path.exists(tick_files[tick.data['instrument']]):
                #     f = open(tick_files[tick.data['instrument']], "a+")
                #     f.write("Time, Bid, Ask, Mid\n")
                #     f.close()
                
                
                # Update dataframe using latest tick
                tick_data = 0
                
                # Create tick df from stream record
                latest_tick = pd.DataFrame()
                
                tick_data = tick_data.append(latest_tick)
                
                # Need to check if the length has been exceeded
                if len(self.tick_data) > no_candles:
                    tick_data = tick_data.iloc[len(tick_data):, :]
                
                
                # Check max number of lines and remove if necessary
                f = open(tick_files[tick.data['instrument']], "r")
                line_count = 0
                for l in f:
                    if l != "\n":
                        line_count += 1
                f.close()
                
                if line_count >= int(no_candles):
                    with open(tick_files[tick.data['instrument']], "r") as original_file:
                        with open(temp_file_path, "w+") as temp_file:  
                            for ind, old_line in enumerate(original_file):
                                if ind in range(1,line_count - int(no_candles) + 1):
                                    continue
                                else:
                                    temp_file.write(old_line)
                            
                            temp_file.close()
                        
                        # Rename cleaned temp file to original file name
                        os.replace(temp_file_path, tick_files[tick.data['instrument']])
                
                # Write latest tick to file
                f = open(tick_files[tick.data['instrument']], "a+")
                f.write("{0}, {1}, {2}, {3}\n".format(tick.data['time'],
                                                      tick.data['bid'],
                                                      tick.data['ask'],
                                                      tick.data['mid'])
                        )
                f.close()
            
            if record_candles:
                for instrument in candle_builders:
                    
                    candle  = candle_builders[instrument].process_tick(tick)
                    
                    if candle is not None:
                        Time    = candle['start']
                        High    = round(candle['data']['high'], 5)
                        Low     = round(candle['data']['low'], 5)
                        Open    = round(candle['data']['open'], 5)
                        Close   = round(candle['data']['last'], 5)
                        
                        # Check if max number of candles has been reached and remove 
                        # older candles
                        f = open(file_names[instrument], "r")
                        line_count = 0
                        for l in f:
                            if l != "\n":
                                line_count += 1
                        f.close()
                        
                        if line_count >= int(no_candles):
                            with open(file_names[instrument], "r") as original_file:
                                with open(temp_file_path, "w+") as temp_file:  
                                    for ind, old_line in enumerate(original_file):
                                        if ind in range(1,line_count - int(no_candles) + 1):
                                            continue
                                        else:
                                            temp_file.write(old_line)
                                    
                                    temp_file.close()
                                
                                os.remove(file_names[instrument])
                                os.replace(temp_file_path, file_names[instrument])
                        
                        # Write new candle to file
                        f       = open(file_names[instrument], "a+")
                        f.write("{0}, {1}, {2}, {3}, {4}\n".format(Time, 
                                                                    Open,
                                                                    High, 
                                                                    Low, 
                                                                    Close)
                                )
                        f.close()

    def write_to_file(self):
        '''
        Write data to the filepath provided.
        '''

    def create_dataframe(self,):
        '''
        Creates a Pandas dataframe from ...
        '''
        
        df = pd.DataFrame()
        
        return df