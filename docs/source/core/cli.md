(cli)=
# Command Line Interface

As of `v0.7.0`, AutoTrader features a Command Line Interface (CLI) for 
various tasks. 

```
Usage: autotrader [OPTIONS] COMMAND [ARGS]...

  AutoTrader command line interface.

Options:
  --help  Show this message and exit.

Commands:
  init      Initialises the directory NAME for trading with AutoTrader.
  monitor   Monitors a broker PICKLE and serves the information to a...
  snapshot  Prints a snapshot of the trading account of a broker PICKLE...
```

## Directory Initialisation
To quickly initialise your directory to the 
[recommended structure](rec-dir-struc), you can use `autotrader init`.


```
Usage: autotrader init [OPTIONS] [NAME]

  Initialises the directory NAME for trading with AutoTrader. If no directory
  NAME is provided, the current directory will be initialised.

Options:
  -m, --minimal          Minimal directory initialisation.
  -s, --strategies TEXT  The name of strategies to include in the initialised
                         directory.
  --help                 Show this message and exit.
```

