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


def connect_to_stream(config):
    ''' Connects to Oanda streaming API '''
    ACCESS_TOKEN    = config["ACCESS_TOKEN"]
    port            = config["PORT"]
    ACCOUNT_ID      = config["ACCOUNT_ID"]
    STREAM_API      = "stream-fxpractice.oanda.com"
    instruments     = config["instruments"]
    
    streamAPI       = v20.Context(hostname = STREAM_API,
                                  token = ACCESS_TOKEN, 
                                  port = port)
    
    try:
        response = streamAPI.pricing.stream(accountID = ACCOUNT_ID, 
                                            instruments = instruments,
                                            snapshot = True
                                            )
        if response.status != 200:
            print("Warning:")
            print(response.reason)
            sys.exit(0)
            
        else:
            return response
    
    except Exception as e:
        print("Caught exception when connecting to stream\n" + str(e)) 


def granularity_to_seconds(granularity):
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


class stream_record(object):
    ''' Creates a stream record '''
    def __init__(self, msg):
        self.record_type    = None
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
        self.duration       = granularity_to_seconds(granularity)
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

def process_stream(stream, candle_builders, file_names, tick_files, temp_file_path, 
                   no_candles, record_ticks=False, record_candles=True):
    
    # TODO - avoid using temp file name, use unique name for temp
    
    for line in stream.lines:
        # Process each update of stream
        line    = line.decode('utf-8')
        msg     = json.loads(line)
        tick    = stream_record(msg)
        
        if record_ticks and msg['type'] == 'PRICE':
            
            # TODO - the below is repeated code: clean it up
            # If the price data file doesn't already exist, initialise it
            # This is an edge case when the file may accidentally be deleted
            # if not os.path.exists(tick_files[tick.data['instrument']]):
            #     f = open(tick_files[tick.data['instrument']], "a+")
            #     f.write("Time, Bid, Ask, Mid\n")
            #     f.close()
            
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
    

class AutoStream():
    '''
    AutoStream Class.
    ------------------
    
    Methods:
        main(stream_config): Subscribes to stream and builds candlestick 
        price files. 
    
    
    Attributes:
        instruments : list
            The instruments to be streamed.
        
        granularity : str
            The granularity of candlesticks to build from the stream.
        
        no_candles : int
            The maximum number of candles to write to file.
        
    '''
    
    def __init__(self, home_dir, stream_config, 
                 instrument, granularity, no_candles=10,
                 record_ticks=False, record_candles=True):
        '''
        Assign attributes required to stream.
        '''
        
        self.home_dir       = home_dir
        self.instruments    = instrument
        self.granularity    = granularity
        self.no_candles     = no_candles
        self.record_candles = record_candles
        self.record_ticks   = record_ticks
        
        # Add instruments to stream_config
        stream_config['instruments'] = instrument
        self.stream_config  = stream_config
        
    def main(self):
        '''
        Subscribes to stream and builds candlestick price files. 
        '''
        
        data_dir_path   = os.path.join(self.home_dir, 'price_data')
        temp_file_path  = os.path.join(data_dir_path, "temp.txt")
        
        if not os.path.exists(data_dir_path):
            # If price data directory doesn't exist, make it
            os.makedirs(data_dir_path)
        
        ''' Initialise candle factories '''
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
                
                # If the price data file doesn't already exist, initialise it
                if not os.path.exists(file_names[instrument]):
                    f = open(file_names[instrument], "a+")
                    f.write("Time, Open, High, Low, Close\n")
                    f.close()

            
            if self.record_ticks:
                filename                    = "{}_ticks.txt".format(instrument)
                abs_filename                = os.path.join(data_dir_path, filename)
                tick_files[instrument]      = abs_filename
                
                # If the price data file doesn't already exist, initialise it
                if not os.path.exists(tick_files[instrument]):
                    f = open(tick_files[instrument], "a+")
                    f.write("Time, Bid, Ask, Mid\n")
                    f.close()
        
        # Connect to stream and begin processing 
        stream = connect_to_stream(self.stream_config)
        
        for attempt in range(10):
            try:
                process_stream(stream,
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
                stream = connect_to_stream(self.stream_config)
            else:
                break
        else:
                print("All attempts failed. Exiting.")

