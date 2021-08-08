#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

AutoStream
-----------
Data stream function.

"""

import v20
import json
from datetime import datetime
from getopt import getopt
import sys
import calendar
import time
import re
import os
import pyfiglet
from autotrader.lib import instrument_list


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



def process_stream(stream, candle_builders, file_names, 
                   temp_file_path, no_candles):
    
    for line in stream.lines:
        # Process each update of stream
        line    = line.decode('utf-8')
        msg     = json.loads(line)
        tick    = stream_record(msg)
        
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
    
    return



def main(uo_dict, stream_config):

    ''' Subscribes to stream and build candlestick price files '''
    
    instruments     = uo_dict['instrument']
    if uo_dict["index"] is not None:
        instruments = instrument_list.get_watchlist(uo_dict["index"])
        instruments = ','.join(instruments)
    
    granularity     = uo_dict['granularity']
    no_candles      = uo_dict['max_candles']
    
    home_dir        = os.path.dirname(os.path.abspath(__file__))
    data_dir_path   = os.path.join(home_dir, 'price_data')
    temp_file_path  = os.path.join(data_dir_path, "temp.txt")
    
    if not os.path.exists(data_dir_path):
        # If price data directory doesn't exist, make it
        os.makedirs(data_dir_path)
    
    ''' Initialise candle factories '''
    file_names      = {} 
    candle_builders = {}
    for instrument in instruments.split(','):
        filename                    = "{0}{1}.txt".format(granularity, instrument)
        abs_filename                = os.path.join(data_dir_path, filename)
        file_names[instrument]      = abs_filename
        candle_builders[instrument] = candle_builder(instrument, granularity)
        
        # Check if a price data file exists already
        if not os.path.exists(file_names[instrument]):
            f = open(file_names[instrument], "a+")
            f.write("Time, Open, High, Low, Close\n")
            f.close()
    
    stream = connect_to_stream(stream_config)
    
    # If the code below works, attempts should only count if it immediately 
    # fails to connect. Otherwise, this will always eventaully break.
    for attempt in range(10):
        try:
            process_stream(stream,
                            candle_builders,
                            file_names,
                            temp_file_path,
                            no_candles)
        except:
            stream = connect_to_stream(stream_config)
        else:
            break
    else:
            print("All attempts failed.")
            # we failed all the attempts - deal with the consequences.
    
    # ''' Monitor tick data from stream. '''
    # # requires candle_builders, file_names, temp_file_path, stream_config
    
    # stream = connect_to_stream(stream_config)
    
    # for line in stream.lines:
    #     # Process each update of stream
    #     line    = line.decode('utf-8')
    #     msg     = json.loads(line)
    #     tick    = stream_record(msg)
        
    #     for instrument in candle_builders:
            
    #         candle  = candle_builders[instrument].process_tick(tick)
            
    #         if candle is not None:
    #             Time    = candle['start']
    #             High    = round(candle['data']['high'], 5)
    #             Low     = round(candle['data']['low'], 5)
    #             Open    = round(candle['data']['open'], 5)
    #             Close   = round(candle['data']['last'], 5)
                
    #             # Check if max number of candles has been reached and remove 
    #             # older candles
    #             f = open(file_names[instrument], "r")
    #             line_count = 0
    #             for l in f:
    #                 if l != "\n":
    #                     line_count += 1
    #             f.close()
                
    #             if line_count >= int(no_candles):
    #                 with open(file_names[instrument], "r") as original_file:
    #                     with open(temp_file_path, "w+") as temp_file:  
    #                         for ind, old_line in enumerate(original_file):
    #                             if ind in range(1,line_count - int(no_candles) + 1):
    #                                 continue
    #                             else:
    #                                 temp_file.write(old_line)
                            
    #                         temp_file.close()
                        
    #                     os.remove(file_names[instrument])
    #                     os.replace(temp_file_path, file_names[instrument])
                
    #             # Write new candle to file
    #             f       = open(file_names[instrument], "a+")
    #             f.write("{0}, {1}, {2}, {3}, {4}\n".format(Time, 
    #                                                         Open,
    #                                                         High, 
    #                                                         Low, 
    #                                                         Close)
    #                     )
    #             f.close()



def print_usage():
    """ Print usage options. """
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


def print_help(option):
    ''' Print usage instructions. '''
    
    if option == 'instrument' or option == 'i':
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


short_options = "i:g:v:h:N:I:"
long_options = ['instrument=', 'granularity=', 'verbosity=', 'help=', 
                'max_candles=', 'index=']


if __name__ == '__main__':
    options, r = getopt(sys.argv[1:], 
                          short_options, 
                          long_options
                          )
    
    # Defaults
    instrument      = None
    index           = None
    verbosity       = 0
    show_help       = None
    granularity     = None
    max_candles     = 10
    
    for opt, arg in options:
        if opt in ('-i', '--instrument'):
            instrument = arg
        elif opt in ('-g', '--granularity'):
            granularity = arg
        elif opt in ('-v', '--verbose'):
            verbosity = arg
        elif opt in ('-h', '--help'):
            show_help = arg
        elif opt in ('-N', '--max-candles'):
            max_candles = arg
        elif opt in ('-I', '--index'):
            index = arg
        
    
    uo_dict = {'instrument':    instrument,
               'granularity':   granularity,
               'verbosity':     verbosity,
               'show_help':     show_help,
               'max_candles':   max_candles,
               'index':         index
               }

    if len(options) == 0:
        print_usage()
        
    elif uo_dict['show_help'] is not None:
        print_help(uo_dict['show_help'])
        
    else:
        main(uo_dict)

