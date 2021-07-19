---
title: Getting Started
description: Getting started with AutoTrader
---

# Getting Started

AutoTrader organisation


## Getting AutoTrader
To get AutoTrader, clone the [Github repository]({{ site.repo }}) onto you machine and install the dependencies.

```
$ git clone https://github.com/kieran-mackle/AutoTrader
```


## Usage
AutoTrader is run through the main executable, *AutoTrader.py*. This script accepts multiple options as inputs, which can be passed 
as flags on the command line.

The only flag required to run AutoTrader is the [configuration file](configuration) flag, '-c'. The argument passed to this flag is 
the name of the strategy configuration file you would like to run AutoTrader with. For example,
`$ ./AutoTrader -c macd -b -p -v 1`
will run AutoTrader with the strategy prescribed in the 'macd' configuration file. Note that AutoTrader will search for the configuration 
file in the ./config/ directory, and that no file extension is required.

Also note that this is equivalent to:
```
$ ./AutoTrader --config macd --backtest --plot --verbosity 1
```

## Modes of AutoTrader
AutoTrader has three modes of running:
  1) [Live-trade mode](livetrading), default


  2) [Backtest mode](backtesting), activated with `--backtest` or `-b`


  3) [Scan mode](scanning), activated with `--scan` or `-s`

The default mode is live-trade mode - unless specified otherwise, AutoTrader will run in this mode. 


## User Options

  - `--plot` / `-p`
  - `--config` / `-c`
  - `--instruments` / `-i`
  - `--optimise` / `-o`
  - `--log` / `-l`
  - `--analyse` / `-a`
  - `--data` / `-d`


## Providing AutoTrader with Price Data




## Getting Help
If you are running AutoTrader from the command line, you can get help on any of the options by using the --help (-h) flag. For example,
for help on the flag '--notify', or '-n' for short, you can type `$ ./AutoTrader -h n`, which will produce the following output:

```
    _   _   _ _____ ___ _____ ____      _    ____  _____ ____  
   / \ | | | |_   _/ _ \_   _|  _ \    / \  |  _ \| ____|  _ \ 
  / _ \| | | | | || | | || | | |_) |  / _ \ | | | |  _| | |_) |
 / ___ \ |_| | | || |_| || | |  _ <  / ___ \| |_| | |___|  _ < 
/_/   \_\___/  |_| \___/ |_| |_| \_\/_/   \_\____/|_____|_| \_\
                                                               

Help for '--notify' (-n) option:
-----------------------------------
The notify option may be used to enable email notifications
of livetrade activity and AutoScan results.
Options:
  -n 0: No emails will be sent.
  -n 1: Minimal emails will be sent (summaries only).
  -n 2: All emails will be sent (every order and summary).
Note: if daily email summaries are desired, email_manager must
be employed in another scheduled job to send the summary.

Default value: 0

Example usage:
./AutoTrader.py -c my_config_file -n 1

For general help, use -h general.
```






