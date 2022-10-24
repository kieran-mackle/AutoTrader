(cli)=
# Command Line Interface

As of `v0.7.0`, AutoTrader features a Command Line Interface (CLI) for 
various tasks. 

```plaintext
Usage: autotrader [OPTIONS] COMMAND [ARGS]...

  AutoTrader command line interface.

Options:
  --help  Show this message and exit.

Commands:
  demo      Runs a demo backtest in AutoTrader.
  init      Initialises the directory NAME for trading with AutoTrader.
  monitor   Monitors a broker and serves the information to a prometheus...
  snapshot  Prints a snapshot of the trading account of a broker PICKLE...
  version   Shows the installed version number of AutoTrader.
```

## Installed Version Number
To quickly check what version of AutoTrader you have installed, you can
use:

```plaintext
autotrader version
```

Note that you can also get this information from Python using the snippet below.

```python
import autotrader

print(autotrader.__version__)
```


## Demo Backtest
```plaintext
Usage: autotrader demo [OPTIONS]

  Runs a demo backtest in AutoTrader.
```

## Directory Initialisation
To quickly initialise your directory to the 
[recommended structure](rec-dir-struc), you can use `autotrader init`.


```plaintext
Usage: autotrader init [OPTIONS] [NAME]

  Initialises the directory NAME for trading with AutoTrader. If no directory
  NAME is provided, the current directory will be initialised.

  To include ready-to-go strategies in the initialised directory, specify them
  using the strategies option. You can provide the following arguments:

  - template: a strategy template module
  - config: a strategy configuration template
  - strategy_name: the name of a strategy to load

  Strategies are loaded from the AutoTrader demo repository here:
  https://github.com/kieran-mackle/autotrader-demo

Options:
  -s, --strategies TEXT  The name of strategies to include in the initialised
                         directory.
  --help                 Show this message and exit.
```


## Trading Monitor
Docs coming soon!


## Paper Trading Snapshot
Docs coming soon!
